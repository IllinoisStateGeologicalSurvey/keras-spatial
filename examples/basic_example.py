#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" 
A simple, standalone example of using Keras Spatial to extract
samples from a remote raster source.
"""

from keras_spatial import SpatialDataGenerator

def example():
    sdg = SpatialDataGenerator()
    sdg.source = 'http://lidar.ncsa.illinois.edu:9000/test/mclean_roi.tif'

    df = sdg.regular_grid(200, 200)

    gen = sdg.flow_from_dataframe(df, 128, 128)
    arr = next(gen)

    print(arr.shape, arr.min(), arr.max())

if __name__ == '__main__':
    example()
