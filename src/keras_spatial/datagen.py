#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numbers
import geopandas as gpd
import numpy as np
import rasterio
from rasterio.vrt import WarpedVRT
from rasterio.warp import Resampling
from rasterio.errors import RasterioIOError
from pydap.client import open_url
from pydap.net import HTTPError


class SpatialDataGenerator(object):

    def __init__(self, width, height,
            source=None, 
            indexes=None, 
            crs=None,
            resampling=Resampling.nearest,
            shuffle=False):
        """

        Args:
          width (int): patch width in pixels
          height (int): patch height in pixels
          source (str): raster file path or OPeNDAP server
          indexes (int|[int]): raster file band (int) or bands ([int,...])
                               (default=None for all bands)
          crs (CRS): produces patches in different crs
          resampling (str): interpolation method used with target_size
          shuffle (bool): shuffle batch of data
        """

        self.width = width
        self.height = height
        if source: 
            self.source = source
        self.indexes = indexes
        self.crs=crs
        self.resampling = resampling
        self.shuffle = shuffle

    def _close(self):
        if hasattr(self, 'src') and self.src:
            self.src.close()
            self.src = None

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

        # try to use rasterio to open local file
        try:
            self.src = rasterio.open(source)
            self._mode = 'local'
            return
        except RasterioIOError as e:
            pass

        # try to use pydap to open remote dataset
        try:
            self.src = open_url(source)
            self._mode = 'dap'
            return
        except HTTPError as e:
            pass

        raise OSError('source not found')

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
            window = rasterio.windows.Window(left, top, 
                    right-left, bot-top)
            batch.append(src.read(indexes=self.indexes, window=window))

        return np.stack(batch)

    def flow_from_dataframe(self, dataframe, batch_size=32):
        """extracts data from source based on dataframe extents

        Args:
          dataframe (geodataframe): dataframe with spatial extents
          batch_size (int): batch size to process (default=32)

        Returns:
    
        """

        df = dataframe
        if self.shuffle:
            df = df.reindex(np.random.permutation(df.index))

        if self.crs:
            df = df.to_crs(self.crs)

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

