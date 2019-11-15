#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
from keras_spatial.datagen import SpatialDataGenerator
import keras_spatial.grid as grid
from geopandas import GeoDataFrame
from rasterio.crs import CRS
import numpy as np

__author__ = "Jeff Terstriep"
__copyright__ = "Jeff Terstriep"
__license__ = "mit"


#def test_fib():
#    assert fib(1) == 1
#    assert fib(2) == 1
#    assert fib(7) == 13
#    with pytest.raises(AssertionError):
#        fib(-10)

def test_init():
    dg = SpatialDataGenerator()
    assert dg

def test_source_property():
    dg = SpatialDataGenerator()
    dg.source = 'data/small.tif'
    assert dg.src

def test_source_parameter():
    dg = SpatialDataGenerator(source='data/small.tif')
    assert dg.src

def test_source_indexes():
    dg = SpatialDataGenerator(source='data/small.tif')
    assert hasattr(dg, 'indexes')
    assert dg.indexes is not None

def test_source_indexes_parameter():
    dg = SpatialDataGenerator(source='data/small.tif', indexes=1)
    assert dg.indexes == 1

def test_indexes_parameter_post_source():
    dg = SpatialDataGenerator(indexes=1)
    dg.source = 'data/small.tif'
    assert dg.indexes == 1

def test_width_height_parameters():
    dg = SpatialDataGenerator(width=100, height=100)
    assert dg.width == 100
    assert dg.height == 100

def test_missing_local_file():
    dg = SpatialDataGenerator()
    with pytest.raises(OSError):
        dg.source = 'xx'

def test_missing_url():
    dg = SpatialDataGenerator()
    with pytest.raises(OSError):
        dg.source = 'http://lidar.ncsa.illinois.edu:9000/test/xx'

def test_extent():
    dg = SpatialDataGenerator()
    dg.source = 'data/small.tif'
    minx, miny, maxx, maxy = dg.extent
    assert maxx > minx and maxy > miny

def test_regular_grid():
    dg = SpatialDataGenerator()
    dg.source = 'data/small.tif'
    df = dg.regular_grid(64, 64)
    assert len(df) > 0

def test_random_grid():
    dg = SpatialDataGenerator()
    dg.source = 'data/small.tif'
    df = dg.random_grid(64, 64, 100)
    assert len(df) == 100

def test_sample_size():
    sdg = SpatialDataGenerator()
    sdg.source = 'data/small.tif'
    df = sdg.regular_grid(64,64)

    gen = sdg.flow_from_dataframe(df, 64, 64)
    arr = next(gen)


    assert len(arr.shape) == 4
    assert arr.shape[0] == min(sdg.batch_size, len(df))
    assert arr.shape[1] == 64 and arr.shape[2] == 64

def test_get_size_upscale():
    size = (64,64)
    sdg = SpatialDataGenerator()
    sdg.source = 'data/small.tif'
    df = sdg.regular_grid(size[0]//4, size[1]//4)

    gen = sdg.flow_from_dataframe(df, *size)
    arr = next(gen)

    assert len(arr.shape) == 4
    assert arr.shape[0] == min(sdg.batch_size, len(df))

def test_get_size_downscale():
    size = (16,16)
    sdg = SpatialDataGenerator()
    sdg.source = 'data/small.tif'
    df = sdg.regular_grid(size[0]*4, size[1]*4)

    gen = sdg.flow_from_dataframe(df, *size)
    arr = next(gen)

    assert len(arr.shape) == 4
    assert arr.shape[0] == min(sdg.batch_size, len(df))
    assert arr.shape[1] == size[1] and arr.shape[2] == size[0]

def test_get_batch_size():
    size = (64, 64)
    batch_size = 2
    sdg = SpatialDataGenerator()
    sdg.source = 'data/small.tif'
    sdg.batch_size = batch_size
    df = sdg.regular_grid(*size)

    gen = sdg.flow_from_dataframe(df, *size)
    arr = next(gen)

    assert len(arr.shape) == 4
    assert arr.shape[0] == min(batch_size, len(df))
    assert arr.shape[1] == size[1] and arr.shape[2] == size[0]

def test_get_batch_size_override():
    size = (64,64)
    batch_size = 2
    sdg = SpatialDataGenerator()
    sdg.source = 'data/small.tif'
    df = sdg.regular_grid(*size)

    gen = sdg.flow_from_dataframe(df, *size, batch_size=batch_size)
    arr = next(gen)

    assert len(arr.shape) == 4
    assert arr.shape[0] == min(batch_size, len(df))
    assert arr.shape[1] == size[1] and arr.shape[2] == size[0]

def test_get_batch_match_frame_len():
    size = (64,64)
    sdg = SpatialDataGenerator()
    sdg.source = 'data/small.tif'
    df = sdg.regular_grid(*size)

    gen = sdg.flow_from_dataframe(df, *size, batch_size=3)
    count = sum([batch.shape[0] for batch in gen])
    assert count == len(df)

#def test_get_batch_url_match_frame_len():
#    size = (64,64)
#    sdg = SpatialDataGenerator()
#    sdg.source = 'http://lidar.ncsa.illinois.edu:9000/test/mclean_roi.tif'
#    sdg.width, sdg.height = size
#    df = sdg.regular_grid(*size)
#
#    gen = sdg.flow_from_dataframe(df, batch_size=3)
#    count = sum([batch.shape[0] for batch in gen])
#    assert count == len(df)

def test_preprocess_modify_array():

    def pre(arr, maxval):
        return arr / maxval

    size = (64,64)
    sdg = SpatialDataGenerator()
    sdg.source = 'data/small.tif'
    sdg.indexes = 1
    sdg.width, sdg.height = size
    df = sdg.regular_grid(*size)
    df['max'] = [a.max() for a in sdg.flow_from_dataframe(df, batch_size=1)]

    sdg.add_preprocess_callback('normalize', pre, df['max'].max())
    arr = next(sdg.flow_from_dataframe(df))
    assert len(arr.shape) == 3
    assert arr.shape[0] == min(sdg.batch_size, len(df))
    assert arr.shape[-2] == size[0] and arr.shape[-1] == size[1]
    assert arr.max() <= 1.0

def test_preprocess_add_array():

    def pre(arr):
        return np.stack((arr, arr/10))

    size = (64,64)
    sdg = SpatialDataGenerator()
    sdg.source = 'data/small.tif'
    sdg.indexes = 1
    sdg.width, sdg.height = size
    df = sdg.regular_grid(*size)

    sdg.add_preprocess_callback('pre', pre)
    arr = next(sdg.flow_from_dataframe(df))
    assert len(arr.shape) == 4
    assert arr.shape[0] == min(sdg.batch_size, len(df))
    assert arr.shape[1] == 2
    assert arr.shape[-2] == size[0] and arr.shape[-1] == size[1]

