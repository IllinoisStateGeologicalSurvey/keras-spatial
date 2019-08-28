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

from scipy import signal
def terrain_analysis(array, size):
    """calculate terrain derivatives based on the Evans Young method

    Args:
      array (ndarray): elevation data array
      size (float,float): size of sample in projected coordinates

    Returns:
      (ndarray): 3d array with original elevation data and derivatives
    """

    px, py = size[0]/array.shape[-1], size[1]/array.shape[-2]

    g = [[(-1/(6*px)), 0 , (1/(6*px))],
         [(-1/(6*px)), 0 , (1/(6*px))],
         [(-1/(6*px)), 0 , (1/(6*px))]]
    h = [[(1/(6*py)),(1/(6*py)),(1/(6*py))],
         [0,0,0],
         [(-1/(6*py)),(-1/(6*py)),(-1/(6*py))]]
    d = [[(1/(3*(px**2))),(-2/(3*(px**2))),(1/(3*(px**2)))],
         [(1/(3*(px**2))),(-2/(3*(px**2))),(1/(3*(px**2)))],
         [(1/(3*(px**2))),(-2/(3*(px**2))),(1/(3*(px**2)))]]
    e = [[(1/(3*(py**2))),(1/(3*(py**2))),(1/(3*(py**2)))],
         [(-2/(3*(py**2))),(-2/(3*(py**2))),(-2/(3*(py**2)))],
         [(1/(3*(py**2))),(1/(3*(py**2))),(1/(3*(py**2)))]]
    f = [[(-1/(4*(px*py))),0, (1/(4*(px*py)))],
         [0,0,0],
         [(1/(4*(px*py))),0,(-1/(4*(px*py)))]]

    gi = signal.convolve2d(array, g, boundary='symm', mode='same')
    hi = signal.convolve2d(array, h, boundary='symm', mode='same')
    di = signal.convolve2d(array, d, boundary='symm', mode='same')
    ei = signal.convolve2d(array, e, boundary='symm', mode='same')
    fi = signal.convolve2d(array, f, boundary='symm', mode='same')

    slope  = np.sqrt (np.power(hi,2)+np.power(gi,2))
    aspect = np.arctan(hi/gi)
    planc  = -1*((np.power(hi, 2)*di)-(2*gi*hi*fi)+(np.power(gi,2)*ei)/(np.power((np.power(gi,2)+np.power(hi,2)),1.5)))
    profc  = -1*(((np.power(gi,2)*di)+(2*gi*hi*fi) +(np.power(hi,2)*ei))/ ((np.power(gi,2)+np.power(hi,2))*(np.power( (1+np.power(gi,2)+np.power(hi,2)),1.5)) ))
    meanc  = -1 *( ((1+np.power(hi,2))*di) -(2*gi*hi*fi) +((1+np.power(gi,2))*ei) / (2*np.power( (1+np.power(gi,2)+np.power(hi,2)),1.5)  ))

    return np.stack([array, slope, aspect, planc, profc,meanc], axis=0)

