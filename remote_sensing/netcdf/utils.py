""" Utilities for working with netCDF files. """

import numpy as np
import xarray

from . import sst

lat_coords = ['lat', 'latitude']
lon_coords = ['lon', 'longitude']

def find_coord(ds:xarray.Dataset, coord:str):

    if coord == 'lat':
        coords = lat_coords
    elif coord == 'lon':
        coords = lon_coords
    else:
        raise IOError(f"Bad coord {coord}")

    for icoord in coords:
        if icoord in ds.coords:
            return icoord

    # If we get here, we failed to find the coordinate
    return None
            

def find_variable(ds:xarray.Dataset, 
                  vtype:str,
                  verbose:bool=False):
    """
    Find the SST variable in the dataset

    Parameters
    ----------
    ds : xarray.Dataset
    verbose : bool, optional

    Returns
    -------
    str or None
        Variable name
    """

    # Check for SST
    if vtype == 'sst':
        return sst.find_variable(ds, verbose=verbose)
    else:
        raise IOError("Bad vtype")

    return None

def gen_mask_for_dataset(ds:xarray.Dataset, variable:str):
    """
    Generate a mask for a dataset based on a variable.

    Parameters
    ----------
    ds : xarray.Dataset
        Dataset containing the variable
    variable : str
        Variable name

    Returns
    -------
    mask : numpy.ndarray
        Mask for the variable
    """
    mask = None

    # Quality control
    if variable in sst.variables:
        mask = sst.quality_control(ds)
    
    return mask


def build_mask(dfield, qual, qual_thresh=2, lower_qual=True,
               temp_bounds=(-2,33), field='SST'):
    """
    Generate a mask based on NaN, qual, and other bounds

    Parameters
    ----------
    dfield : np.ndarray
        Full data image
    qual : np.ndarray of int
        Quality image
    qual_thresh : int, optional
        Quality threshold value  
    lower_qual : bool, optional
        If True, the qual_thresh is a lower bound, i.e. mask values above this  
        Otherwise, mask those below!
    temp_bounds : tuple
        Temperature interval considered valid
        Used for SST
    field : str, optional
        Options: SST, aph_443

    Returns
    -------
    masks : np.ndarray
        mask;  True = bad

    """
    # Mask val
    qual_maskval = 999999 if lower_qual else -999999

    dfield[np.isnan(dfield)] = np.nan
    if field == 'SST':
        if qual is None:
            qual = np.zeros_like(dfield).astype(int)
        qual[np.isnan(dfield)] = qual_maskval
    else:
        if qual is None:
            raise IOError("Need to deal with qual for color.  Just a reminder")
        # Deal with NaN
    masks = np.logical_or(np.isnan(dfield), qual==qual_maskval)

    # Quality
    # TODO -- Do this right for color
    qual_masks = np.zeros_like(masks)

    if qual is not None and qual_thresh is not None:
        if lower_qual:
            qual_masks[~masks] = (qual[~masks] > qual_thresh) 
        else:
            qual_masks[~masks] = (qual[~masks] < qual_thresh) 

    # Temperature bounds
    #
    value_masks = np.zeros_like(masks)
    if field == 'SST':
        value_masks[~masks] = (dfield[~masks] <= temp_bounds[0]) | (dfield[~masks] > temp_bounds[1])
    # Union
    masks = np.logical_or(masks, qual_masks, value_masks)

    # Return
    return masks