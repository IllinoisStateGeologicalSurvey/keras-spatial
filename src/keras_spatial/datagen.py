#!/usr/bin/env python
# -*- coding: utf-8 -*-

import rasterio
from rasterio.vrt import WarpedVRT
from rasterio.warp import Resampling
import geopandas as gpd
import numpy as np

import keras_spatial.grid as grid

class SpatialDataGenerator(object):

    def __init__(self, source=None, indexes=None, 
            width=0, height=0, batch_size=32,
            crs=None, interleave='band', resampling=Resampling.nearest,
            preprocess=None):
        """

        Args:
          width (int): sample width in pixels
          height (int): sample height in pixels
          source (str): raster file path or OPeNDAP server
          indexes (int|[int]): raster file band (int) or bands ([int,...])
                               (default=None for all bands)
          crs (CRS): produces patches in different crs
          resampling (int): interpolation method used when resampling
          interleave (str): type of interleave, 'pixel' or 'band'
          preprocess (function): callback invoked on each sample 
        """

        self.src = None
        if source: 
            self.source = source
        if indexes is not None:
            self.indexes = indexes
        self.width = width
        self.height = height
        self.batch_size = batch_size
        self.crs=crs
        self.resampling = resampling
        self.interleave = interleave
        self.preprocess = preprocess

    def _close(self):
        if self.src:
            self.src.close()
            self.src = None

    @property
    def extent(self):
        if self.src:
            return tuple(self.src.bounds)
        else:
            return None

    @property
    def profile(self):
        """Return dict of parameters that are likely to re-used."""

        return dict(width=self.width, height=self.height, crs=self.crs, 
                interleave=self.interleave, resampling=self.resampling)

    @profile.setter
    def profile(self, profile):
        """Set parameters from profile dictionary."""

        self.width = profile['width']
        self.height = profile['height']
        self.crs = profile['crs']
        self.interleave = profile['interleave']
        self.resampling = profile['resampling']

    @property
    def crs(self):
        if self._crs:
            return self._crs
        elif self.src:
            return self.src.crs
        else:
            return None

    @crs.setter
    def crs(self, crs):
        self._crs = crs

    @property
    def source(self):
        return self._source

    @source.setter
    def source(self, source):
        """Save and open the source string

        Args:
          source (str): local file path or URL using dap
        """

        self._close()
        self._source = source

        self.src = rasterio.open(source)

        idx = getattr(self, 'indexes', None)
        if idx is None:
            self.indexes = list(range(1, self.src.count+1))

    def regular_grid(self, width, height, overlap=0.0):
        """Create a dataframe that defines the a regular grid of samples.

        The width and height are given in pixels and multiplied by the
        pixel size of the raster to create samples at the native
        resolution of the raster.

        Args:
          width (int): sample size in pixels
          height (int): sample size in pixels
          overlap (float): percentage overlap (default=0.0)

        Returns:
          (GeoDataframe)
        """

        if not self.src:
            raise RuntimeError('source not set or failed to open')

        dims = width * self.src.res[0], height * self.src.res[1]
        gdf = grid.regular_grid(*self.src.bounds, *dims, overlap=overlap)
        gdf.crs = self.src.crs
        return gdf

    def random_grid(self, width, height, count):
        """Create a dataframe that defines a random set of samples.

        The width and height are given in pixels and multiplied by the
        pixel size of the raster to create samples at the native
        resolution of the raster.

        Args:
          width (int): sample size in pixels
          height (int): sample size in pixels
          count (int): number of samples

        Returns:
          (GeoDataframe)
        """

        if not self.src:
            raise RuntimeError('source not set or failed to open')

        dims = width * self.src.res[0], height * self.src.res[1]
        gdf = grid.random_grid(*self.src.bounds, *dims, count)
        gdf.crs = self.src.crs
        return gdf

    def get_batch(self, src, geometries):
        """Get batch of patches from source raster

        Args:
          src (rasterio): data source opened with rasterio
          geometries (GeoSeries): boundaries to extract from raster

        Returns:
          (numpy array)

        This leverages rasterio's virtual warping to normalize data to
        a consistent grid.
        """

        batch = []
        for bounds in geometries.bounds.itertuples():
            bot, left = src.index(bounds[1], bounds[2])
            top, right = src.index(bounds[3], bounds[4])
            window = rasterio.windows.Window(left, top, right-left, bot-top)
            batch.append(src.read(indexes=self.indexes, window=window))
            if self.interleave == 'pixel' and len(batch[-1].shape) == 3:
                batch[-1] = np.moveaxis(batch[-1], 0, -1)
            if self.preprocess:
                batch[-1] = self.preprocess(batch[-1])

        return np.stack(batch)

    def flow_from_dataframe(self, dataframe, width=0, height=0, batch_size=0):
        """extracts data from source based on sample extents

        Args:
          dataframe (geodataframe): dataframe with spatial extents
          batch_size (int): batch size to process (default=32)

        Returns:
    
        """

        width = width if width else self.width
        height = height if height else self.height
        if width < 1 or height < 1:
            raise ValueError('desired sample size must be set')
        batch_size = batch_size if batch_size else self.batch_size
        if batch_size < 1:
            raise ValueError('batch size must be specified')

        df = dataframe.to_crs(self.crs) if self.crs else dataframe

        xres = df.bounds.apply(lambda row: row.maxx - row.minx, 
                axis=1).mean() / width
        yres = df.bounds.apply(lambda row: row.maxy - row.miny, 
                axis=1).mean() / height

        minx, miny, maxx, maxy = df.total_bounds
        width = (maxx - minx) / xres
        height = (maxy - miny) / yres
        transform = rasterio.transform.from_origin(minx, maxy, xres, yres)

        # use VRT to ensure correct projection and size
        vrt = WarpedVRT(self.src, crs=df.crs, 
                width=width, height=height,
                transform=transform,
                resampling=self.resampling)

        for i in range(0, len(df), batch_size):
            yield self.get_batch(vrt, df.iloc[i:i+batch_size]['geometry'])

        vrt.close()

