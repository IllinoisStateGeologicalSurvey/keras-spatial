#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
"""

import logging
import collections

import numpy as np
import geopandas as gpd
from shapely.geometry import box

from keras_spatial import __version__

__author__ = "Jeff Terstriep"
__copyright__ = "University of Illinois Board of Trustees"
__license__ = "ncsa"

_logger = logging.getLogger(__name__)


## TODO complete
def mask_grid(dataframe, fname, hard=False):
    """Filter dataframe removing patches outside an area.

    Args:
      dataframe (GeoDataFrame): dataframe contain grid
      fname (str): file path to vector boundary
      hard (bool): if true, patches must be fully within boundary

    Returns:
      geopandas.GeoDataFrame:
    """  

    if isinstance(fname, str):
        with fiona.open(fname) as mask:
            pass


def sample_size(dataframe):
    """Return the sample size in coordinate space.

    Args:
      dataframe (GeoDataFrame): dataframe containing samples

    Returns:
      tuple(float, float): tuple with width and height in map units
    """

    left, bottom, right, top = dataframe.iloc[0].geometry.bounds
    return (abs(left - right), abs(top - bottom))


def regular_grid(xmin, ymin, xmax, ymax, xsize, ysize, overlap=0, crs=None):
    """Generate regular grid over extent.

    Args:
      xmin (float): extent left boundary
      ymin (float): extent bottom boundary
      xmax (float): extent right boundary
      ymax (float): extent top boundary
      xsize (float): patch width
      ysize (float): patch height
      overlap (float): percentage of patch overlap (optional)
      crs (CRS): crs to assign geodataframe 

    Returns:
      geopandas.GeoDataFrame:
    """

    x = np.linspace(xmin, xmax-xsize, num=(xmax-xmin)//(xsize-xsize*overlap))
    y = np.linspace(ymin, ymax-ysize, num=(ymax-ymin)//(ysize-ysize*overlap))
    X,Y = np.meshgrid(x, y)
    polys = [box(x, y, x+xsize, y+ysize) for x,y in np.nditer([X,Y])]

    gdf = gpd.GeoDataFrame({'geometry':polys})
    gdf.crs = crs
    return gdf


def random_grid(xmin, ymin, xmax, ymax, xsize, ysize, count, crs=None):
    """Generate random grid over extent.

    Args:
      xmin (float): extent left boundary
      ymin (float): extent bottom boundary
      xmax (float): extent right boundary
      ymax (float): extent top boundary
      xsize (float): patch width
      ysize (float): patch height
      count (int): number of patches
      crs (CRS): crs to assign geodataframe 

    Returns:
      (GeoDataFrame)
    """

    x = np.random.rand(count) * (xmax-xmin-xsize) + xmin
    y = np.random.rand(count) * (ymax-ymin-ysize) + ymin
    polys = [box(x, y, x+xsize, y+ysize) for x,y in np.nditer([x,y])]

    gdf = gpd.GeoDataFrame({'geometry':polys})
    gdf.crs = crs
    return gdf


class AttributeGenerator(object):

    def __init__(self):

        self.callbacks = collections.OrderedDict()

    def append(self, name, func, *args, **kwargs):
        """Append callback function to AttributeGenerator

        Args:
          name (str): name of the callback
          func (function): function to be called
          args (list): arguments to be passed to the callback
          kwargs (dict): keyword arguments to be passed to callback
        """

        self.callbacks[name] = (func, args, kwargs)

    def fill(self, df, sdg, width=0, height=0):
        """Fill dataframe with attributes by each sample individually

        Args:
          df (dataframe): a geodataframe which defines sample boundaries
          sdg (SpatialDataGenerator): the SDG for the raster source
          width (int): sample width
          height (int): sample height

        Returns:
          (GeoDataFrame): original dataframe with new attributes
        """

        attributes = collections.defaultdict(list)
        for arr in sdg.flow_from_dataframe(df, width, height, batch_size=1):
            for name,callback in self.callbacks.items():
                func, args, kwargs = callback
                attributes[name].append(func(arr, *args, **kwargs))

        for name,values in attributes.items():
            df[name] = values

        return df

    def nodata(self, value):
        """convenience method to add callback to count nodata cells"""

        def _nodata(arr, value):
            return (arr == value).sum()

        self.append('nodata', _nodata, value)

    def minmax(self):
        """convenience method to add callbacks for min and max"""

        self.append('min', np.amin)
        self.append('max', np.amax)

    def stats(self):
        """convenience method to add basic stats"""

        self.minmax()
        self.append('mean', np.mean)
        self.append('std', np.std)

