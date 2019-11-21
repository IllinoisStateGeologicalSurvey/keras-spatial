# -*- coding: utf-8 -*-

import pytest
import numpy as np
from keras_spatial import SpatialDataGenerator
from keras_spatial.samples import AttributeGenerator
from keras_spatial.samples import sample_size

def test_sample_size():
    sdg = SpatialDataGenerator(source='data/small.tif')
    df = sdg.regular_grid(100, 100)
    sizex, sizey = sample_size(df)
    assert (sizex == 100) and (sizey == 100)

def test_minmax():
    sdg = SpatialDataGenerator(source='data/small.tif')
    df = sdg.regular_grid(100, 100)

    ag = AttributeGenerator()
    ag.minmax()
    ag.fill(df, sdg, 64, 64)
    assert 'min' in df.columns
    assert 'max' in df.columns

def test_nodata():
    sdg = SpatialDataGenerator(source='data/small.tif')
    df = sdg.regular_grid(100, 100)

    ag = AttributeGenerator()
    ag.nodata(sdg.src.nodata)
    ag.fill(df, sdg, 64, 64)
    assert 'nodata' in df.columns

