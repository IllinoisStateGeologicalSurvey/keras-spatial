#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import fiona

def mask(df, mask):
    """intersect the geodataframe with a polygon

    Args:
      df (GeoDataFrame): the sample dataframe
      mask (str): name of a vector data source

    Returns:
      (GeoDataFrame): subset of the original dataframe where all samples
              reside within the mask boundary
    """

    pass


