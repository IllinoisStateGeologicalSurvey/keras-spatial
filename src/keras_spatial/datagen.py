#!/usr/bin/env python
# -*- coding: utf-8 -*-

import rasterio
from rasterio.vrt import WarpedVRT
from rasterio.warp import Resampling
import geopandas as gpd
import numpy as np

import keras_spatial.grid as grid

class SpatialDataGenerator(object):

    def __init__(self, width=0, height=0, source=None, indexes=None, 
            crs=None, interleave='band', resampling=Resampling.nearest):
        """

        Args:
          width (int): patch width in pixels
          height (int): patch height in pixels
          source (str): raster file path or OPeNDAP server
          indexes (int|[int]): raster file band (int) or bands ([int,...])
                               (default=None for all bands)
          crs (CRS): produces patches in different crs
          resampling (int): interpolation method used when resampling
          interleave (str): type of interleave, 'pixel' or 'band'
        """

        self.src = None
        self.width = width
        self.height = height
        if source: 
            self.source = source
        self.indexes = indexes
        self.crs=crs
        self.resampling = resampling
        self.interleave = interleave

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
        if self.indexes == None:
            self.indexes = list(range(1,src.count+1))

    def regular_grid(self, pct_width, pct_height, overlap=0.0):
        """Create a dataframe that divides the spatial extent of the raster.

        Args:
          pct_width (float): patch size as percentage of spatial extent
          pct_height (float): patch size as percentage of spatial extent
          overlap (float): percentage overlap (default=0.0)

        Returns:
          (GeoDataframe)
        """

        if not self.src:
            raise RuntimeError('source not set or failed to open')

        width = (self.src.bounds.right - self.src.bounds.left) * pct_width
        height = (self.src.bounds.top - self.src.bounds.bottom) * pct_height
        gdf = grid.regular_grid(*self.src.bounds, width, height)
        gdf.crs = self.src.crs
        return gdf

    def random_grid(self, pct_width, pct_height, count):
        """Create a dataframe that divides the spatial extent of the raster.

        Args:
          pct_width (float): patch size relative to spatial extent
          pct_height (float): patch size relative to spatial extent
          count (int): number of patches

        Returns:
          (GeoDataframe)
        """

        if not self.src:
            raise RuntimeError('source not set or failed to open')

        width = (self.src.bounds.right - self.src.bounds.left) * pct_width
        height = (self.src.bounds.top - self.src.bounds.bottom) * pct_height
        gdf = grid.regular_grid(*self.src.bounds, width, height, count)
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

        return np.stack(batch)

    def flow_from_dataframe(self, dataframe, batch_size=32):
        """extracts data from source based on dataframe extents

        Args:
          dataframe (geodataframe): dataframe with spatial extents
          batch_size (int): batch size to process (default=32)

        Returns:
    
        """

        df = dataframe.to_crs(self.crs) if self.crs else dataframe

        xres = df.bounds.apply(lambda row: row.maxx - row.minx, 
                axis=1).mean() / self.width
        yres = df.bounds.apply(lambda row: row.maxy - row.miny, 
                axis=1).mean() / self.height

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

