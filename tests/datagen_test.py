#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
from keras_spatial.datagen import SpatialDataGenerator
from geopandas import GeoDataFrame

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

def test_class():
    dg = SpatialDataGenerator()
    dg.source = 'data/small.tif'
    assert dg.mode == 'local'

def test_missing_raster():
    dg = SpatialDataGenerator()
    with pytest.raises(OSError):
        dg.source = 'xx'

def test_get_batch():
    df = GeoDataFrame.from_file('data/grid.gpkg')
    dg = SpatialDataGenerator()
    dg.source = 'data/small.tif'
    gen = dg.flow_from_dataframe(df, batch_size=60)
    count = sum([batch.shape[0] for batch in gen])
    assert count == len(df)
        
