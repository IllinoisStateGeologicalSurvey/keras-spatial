#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This is a skeleton file that can serve as a starting point for a Python
console script. To run this script uncomment the following lines in the
[options.entry_points] section in setup.cfg:

    console_scripts =
         fibonacci = keras_spatial.skeleton:run

Then run `python setup.py install` which will install the command `fibonacci`
inside your current environment.
Besides console scripts, the header (i.e. until _logger...) of this file can
also be used as template for Python modules.

Note: This skeleton file can be safely removed if not needed!
"""

import argparse
import sys
import logging
import numpy as np
from shapely.geometry import box
import rasterio as rio
import geopandas as gpd

from keras_spatial import __version__

__author__ = "Jeff Terstriep"
__copyright__ = "Jeff Terstriep"
__license__ = "mit"

_logger = logging.getLogger(__name__)


def raster_meta(fname):
    """Return some metadata from a raster file.
    
    Args:
      fname (str): file path

    Returns:
      :tuple(bounds, size, crs)
    """

    with rio.open(fname) as src:
        return (src.bounds, (src.width, src.height), src.crs)


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

    left, bottom, right, top = df.iloc[0].bounds
    return (left - right, top - bottom)


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
      :obj:`geopandas.GeoDataFrame`:
    """

    x = np.random.rand(count) * (xmax-xmin-xsize) + xmin
    y = np.random.rand(count) * (ymax-ymin-ysize) + ymin
    polys = [box(x, y, x+xsize, y+ysize) for x,y in np.nditer([x,y])]

    gdf = gpd.GeoDataFrame({'geometry':polys})
    gdf.crs = crs
    return gdf


def get_parser():
    """Configure command line arguments

    Returns:
      :obj:`argparse.ArgumentParser`: 
    """
    parser = argparse.ArgumentParser(
        description="Generate geodataframe containing spatial patches")
    parser.add_argument(
        'output',
        metavar='FILE',
        help='output vector file')
    parser.add_argument(
        'size',
        metavar='SIZE',
        type=float,
        nargs=2,
        help='patch size in projection units')
    parser.add_argument(
        '--size-in-pixels',
        action='store_true',
        default=False,
        help='if size is specified in pixels (raster mode only)')
    parser.add_argument(
        '-f', '--format',
        metavar='FORMAT',
        default='GPKG',
        help='output file format (default=GPKG)')
    parser.add_argument(
        '--random-count',
        metavar='COUNT',
        type=int,
        default=0,
        help='number of randomly placed patches (default=0)')
    parser.add_argument(
        '--overlap',
        metavar='PERCENT',
        type=float,
        default=0.0,
        help='percent of overlap (default=0.0)')
    parser.add_argument(
        '-e', '--extent',
        type=float,
        nargs=4,
        metavar='FLOAT',
        help='spatial extent (minx, miny, maxx, maxy)')
    parser.add_argument(
        '--extent-crs',
        metavar='PROJ',
        default='EPSG:4326',
        help='projection of extents (default=EPSG:4326)')
    parser.add_argument(
        '-r', '--raster',
        metavar='FILE',
        help='raster file used to define extents and projection')
    parser.add_argument(
        '-m', '--mask',
        metavar='FILE',
        help='vector file used to define irregular study area')
    parser.add_argument(
        '-t', '--target-crs',
        metavar='PROJ',
        help='target projection if different from source projection')
    parser.add_argument(
        '-V', '--version',
        action='version',
        version='keras-spatial {ver}'.format(ver=__version__))
    parser.add_argument(
        '-v', '--verbose',
        dest="loglevel",
        help="set loglevel to INFO",
        action='store_const',
        const=logging.INFO)
    parser.add_argument(
        '-vv', '--very-verbose',
        dest="loglevel",
        help="set loglevel to DEBUG",
        action='store_const',
        const=logging.DEBUG)
    return parser


def setup_logging(loglevel):
    """Setup basic logging

    Args:
      loglevel (int): minimum loglevel for emitting messages
    """
    logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    logging.basicConfig(level=loglevel, stream=sys.stdout,
                        format=logformat, datefmt="%Y-%m-%d %H:%M:%S")


def main(args):
    """Main entry point allowing external calls

    Args:
      args ([str]): command line parameter list
    """
    parser = get_parser()
    args = parser.parse_args(args)
    setup_logging(args.loglevel)

    # TODO
    if args.size_in_pixels:
        _logger.error('--size-in-pixels not implemented')
        sys.exit(-1)

    if args.overlap < 0 or args.overlap >= 100:
        _logger.error('overlap must be between 0-100')
        sys.exit(-1)
    else:
        args.overlap /= 100.0

    if args.raster:
        args.extent, _, args.extent_crs = raster_meta(args.raster)

    if not args.extent:
        _logger.error('raster file or extent must be provided')
        sys.exit(-1)

    if args.random_count > 0:
        df = random_grid(*args.extent, *args.size, args.random_count)
    else:
        df = regular_grid(*args.extent, *args.size, args.overlap)

    df.crs = args.extent_crs
    
    if args.target_crs:
        df.to_crs(args.target_crs)

    df.to_file(args.output, driver=args.format)


def run():
    """Entry point for console_scripts
    """
    main(sys.argv[1:])


if __name__ == "__main__":
    run()
