import os
import geopandas as gpd
import numpy as np
import rasterio
from rasterio.errors import RasterioIOError
from pydap.client import open_url
from pydap.net import HTTPError

class SpatialDataGenerator(object):

    def __init__(self, source=None, indexes=None, target_crs=None,
            target_size=None, interpolation='nearest',
            shuffle=False):
        """

        Args:
          source (str): raster file path or OPeNDAP server
          indexes (int|[int]): raster file band (int) or bands ([int,...])
                               (default=None for all bands)
          target_crs (str): proj4 definition defaults to dataframe.crs
          shuffle (bool): shuffle batch of data
          target_size ((int,int)): tuple with patch size
          interpolation (str): interpolation method used with target_size
        """

        self._mode = ''
        self.src = None
        self.source = source
        self.indexes = indexes
        self.target_size = target_size
        self.interpolation = interpolation
        self.shuffle = shuffle

    @property
    def source(self):
        return self._source

    @source.setter
    def source(self, source):
        """Save and open the source string

        Args:
          source (str): local file path or URL using dap
        """

        self._source = source
        if not source:
            return

        # TODO if src is set close it?
        if self.src:
            self._mode = None
            pass

        # try to use rasterio to open local file
        try:
            self._mode = 'local'
            self.src = rasterio.open(source)
            return
        except RasterioIOError as e:
            pass

        # try to use pydap to open remote dataset
        try:
            self._mode = 'dap'
            self.src = open_url(source)
            return
        except HTTPError as e:
            pass

        raise OSError('source not found')

    @property
    def mode(self):
        return self._mode

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
            batch.append(self.src.read(indexes=self.indexes, window=window))

        return np.stack(batch)

    def flow_from_dataframe(self, df, target_crs=None, batch_size=32):
        """extracts data from source based on dataframe extents

        Args:
          df (geodataframe): dataframe with spatial extents
          target_crs (str): proj4 definition defaults to dataframe.crs
          batch_size (int): batch size to process

        Returns:
    
        """

        if self.shuffle:
            df = df.reindex(np.random.permutation(df.index))

        if not df.crs == self.src.crs:
            df = df.to_crs(self.src.crs)

        for i in range(0, len(df), batch_size):
            yield self.get_batch(df.iloc[i:i+batch_size]['geometry'])


