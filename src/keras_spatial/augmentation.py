#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
import geopandas as gpd

def normalize(arr, gmin, gmax, layer=0):
    """scales the array to the range (0,1) based on the sample set min and max

    Args:
      arr (ndarray): the sample array to be processed
      gmin (float): the sample set minimum
      gmax (float): the sample set maximum
      layer (int): the layer index of the sample array

    Returns:
      (ndarray): 
    """

    if len(arr.shape) == 2:
        return (arr - gmin) / (gmax - gmin)
    elif len(arr.shape) == 3:
        arr[layer,:,:] = (arr[layer] - gmin) / (gmax - gmin)
        return arr


