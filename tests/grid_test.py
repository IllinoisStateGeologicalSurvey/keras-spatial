#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
import numpy as np
from shapely.geometry import Point
from geopandas import GeoSeries, GeoDataFrame

import keras_spatial.grid as grid
from keras_spatial.samples import regular_grid, random_grid, point_grid


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

    df = regular_grid(*bounds, *size)
    assert len(df) == 100
    assert df.total_bounds[0] >= bounds[0]
    assert df.total_bounds[1] >= bounds[1]
    assert df.total_bounds[2] <= bounds[2]
    assert df.total_bounds[3] <= bounds[3]

def test_regular_grid_overlap():
    bounds, _, _ = grid.raster_meta('data/small.tif')
    size = (bounds[2]-bounds[0], bounds[3]-bounds[1])
    size = [i/10 for i in size]

    df = regular_grid(*bounds, *size, overlap=.5)
    assert len(df) == 400
    assert df.total_bounds[0] >= bounds[0]
    assert df.total_bounds[1] >= bounds[1]
    assert df.total_bounds[2] <= bounds[2]
    assert df.total_bounds[3] <= bounds[3]

def test_random_grid():
    bounds, _, _ = grid.raster_meta('data/small.tif')
    size = (bounds[2]-bounds[0], bounds[3]-bounds[1])
    size = [i/10 for i in size]

    df = random_grid(*bounds, *size, count=100)
    assert len(df) == 100
    assert df.total_bounds[0] >= bounds[0]
    assert df.total_bounds[1] >= bounds[1]
    assert df.total_bounds[2] <= bounds[2]
    assert df.total_bounds[3] <= bounds[3]

def test_point_grid():
    bounds, _, _ = grid.raster_meta('data/small.tif')
    xmin, ymin, xmax, ymax = bounds
    xsize, ysize = xmax - xmin, ymax - ymin
    xc = xsize * np.random.random(200) + xmin
    yc = ysize * np.random.random(200) + ymin
    pts = GeoSeries([Point(x, y) for x, y in zip(xc, yc)])
    df = GeoDataFrame(geometry=pts)

    dfout = point_grid(df, xsize/50.0, ysize/50.0)
    assert len(df) == 200
    

def test_sample_size():
    bounds, _, _ = grid.raster_meta('data/small.tif')
