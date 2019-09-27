# -*- coding: utf-8 -*-
import os
import geopandas as gpd
import numpy as np
import rasterio
from rasterio.errors import RasterioIOError
from pydap.client import open_url
from pydap.net import HTTPError

from keras_spatial.datagen import SpatialDataGenerator


class DapDataGenerator:

    def __init__(self, source=None, variables=None, geotransform=None,
            target_crs=None, target_size=None, interleave='pixel',
            interpolation='nearest', shuffle=False):
        """

        Args:
          source (str): URL to OPeNDAP Dataset
          target_crs (str): proj4 definition defaults to dataframe.crs
          target_size ((int,int)): tuple with patch size
          interleave (str): 'band' or 'pixel' if multiple bands are returned
          shuffle (bool): shuffle batch of data
          interpolation (str): interpolation method used with target_size
        """

        self.dataset = None

        self.source = source
        self.variables = variables
        self.geotransform = geotransform
        self.target_crs = target_crs
        self.target_size = target_size
        self.interleave = interleave
        self.interpolation = interpolation
        self.shuffle = shuffle

    @property
    def source(self):
        """Return source URL"""

        return self._source

    @source.setter()
    def source(self, source):
        """Open Dataset and extract variables and geotransform

        Args:
          source (str): URL to OPeNDAP Dataset
        """

        self._source = source
        if source:
            self.dataset = open_url(source)

    def get_batch(self, geometries):
        """Get batch of patches from source raster

        Args:
          geometries (GeoSeries): boundaries to extract from raster

        Returns:
          (numpy array)
        """
        
        batch = []
        for bounds in geometries.bounds.itertuples():
            bot, left = self.src.index(bounds[1], bounds[2])
            top, right = self.src.index(bounds[3], bounds[4])
            window = rasterio.windows.Window(left, top, right-left, bot-top)
            batch.append(self.src.read(self.bands, window=window))

        return np.stack(batch)

    def _check_dataset(self):
        """Ensure the dataset, variables, and geotransform are sane"""

        if not self.dataset:
            raise RuntimeError('dataset is not open, set source')

        _vars = self.dataset.variables.keys()
        if not self.variables:
            self.variables = _vars
        elif not all(v in _vars for v in self.variables):
            raise RuntimeError('variable {} not in dataset'.format(v))

        if not self.geotransform:




    def flow_from_dataframe(self, df, target_crs=None, batch_size=32):
        """extracts data from source based on dataframe extents

        Args:
          df (geodataframe): dataframe with spatial extents
          target_crs (str): proj4 definition defaults to dataframe.crs
          batch_size (int): batch size to process

        Returns:
    
        """

        self._check_dataset()


        if self.shuffle:
            df = df.reindex(np.random.permutation(df.index))

        if not df.crs == self.src.crs:
            df = df.to_crs(self.src.crs)

        for i in range(0, len(df), batch_size):
            yield self.get_batch(df.iloc[i:i+batch_size]['geometry'])


if __name__ == '__main__':
    dg = DapDataGenerator()
