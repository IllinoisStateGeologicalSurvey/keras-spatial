# -*- coding: utf-8 -*-

import pytest
import numpy as np
from keras_spatial import SpatialDataGenerator
from keras_spatial.samples import AttributeGenerator


def test_ag():
    sdg = SpatialDataGenerator(source='data/small.tif')
    df = sdg.regular_grid(100, 100)

    ag = AttributeGenerator()
    ag.minmax()
    ag.fill(df, sdg, 64, 64)
    assert 'min' in df.columns
    assert 'max' in df.columns
