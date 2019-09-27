#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
import keras_spatial.grid as grid

__author__ = "Jeff Terstriep"
__copyright__ = "Jeff Terstriep"
__license__ = "mit"


def test_raster_meta():
    bounds, size, crs = grid.raster_meta('data/small.tif')
    assert len(bounds) == 4
    assert len(size) == 2
    assert crs

def test_regular_grid():
    bounds, _, _ = grid.raster_meta('data/small.tif')
    size = (bounds[2]-bounds[0], bounds[3]-bounds[1])
    size = [i/10 for i in size]

    df = grid.regular_grid(*bounds, *size)
    assert len(df) == 100
    assert df.total_bounds[0] >= bounds[0]
    assert df.total_bounds[1] >= bounds[1]
    assert df.total_bounds[2] <= bounds[2]
    assert df.total_bounds[3] <= bounds[3]

def test_regular_grid_overlap():
    bounds, _, _ = grid.raster_meta('data/small.tif')
    size = (bounds[2]-bounds[0], bounds[3]-bounds[1])
    size = [i/10 for i in size]

    df = grid.regular_grid(*bounds, *size, overlap=.5)
    assert len(df) == 400
    assert df.total_bounds[0] >= bounds[0]
    assert df.total_bounds[1] >= bounds[1]
    assert df.total_bounds[2] <= bounds[2]
    assert df.total_bounds[3] <= bounds[3]

def test_random_grid():
    bounds, _, _ = grid.raster_meta('data/small.tif')
    size = (bounds[2]-bounds[0], bounds[3]-bounds[1])
    size = [i/10 for i in size]

    df = grid.random_grid(*bounds, *size, count=100)
    assert len(df) == 100
    assert df.total_bounds[0] >= bounds[0]
    assert df.total_bounds[1] >= bounds[1]
    assert df.total_bounds[2] <= bounds[2]
    assert df.total_bounds[3] <= bounds[3]

def test_sample_size():
    bounds, _, _ = grid.raster_meta('data/small.tif')
