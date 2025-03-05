""" Utility functions for working with HEALPix data. """


import healpy
import numpy as np

import xarray

from remote_sensing.utils import utils

from IPython import embed

def get_nside_from_angular_size(angular_size_deg):
    """
    Find the appropriate HEALPix NSIDE parameter for a given angular size in degrees.
    Returns the NSIDE value that gives pixel sizes just smaller than the requested size.
    
    Parameters:
    -----------
    angular_size_deg : float
        Desired angular resolution in degrees
        
    Returns:
    --------
    nside : int
        HEALPix NSIDE parameter (must be a power of 2)
    actual_pixel_size : float
        Actual pixel size in degrees for the returned NSIDE
    """
    
    # Convert degrees to radians
    angular_size_rad = np.deg2rad(angular_size_deg)
    
    # HEALPix pixel area is approximately (4*pi)/(12*NSIDE^2) steradians
    # For small angles, pixel size ≈ sqrt(pixel area)
    # Solve for NSIDE
    nside_exact = np.sqrt(np.pi/(3 * angular_size_rad**2))
    
    # NSIDE must be a power of 2
    # Get the next power of 2 that gives bigger pixels than requested
    nside = 2**(np.ceil(np.log2(nside_exact))-1)
    
    # Calculate actual pixel size for this NSIDE
    pixel_area_rad = healpy.nside2pixarea(int(nside))
    actual_pixel_size_deg = np.rad2deg(np.sqrt(pixel_area_rad))
    
    return int(nside), actual_pixel_size_deg

# Example usage:
# angular_size = 1.0  # degrees
# nside, pixel_size = get_nside_from_angular_size(angular_size)
# print(f"For {angular_size}° resolution, use NSIDE={nside} (actual pixel size: {pixel_size:.2f}°)")

def get_nside_from_lats(lats:np.ndarray):
    """
    Find the appropriate HEALPix NSIDE parameter for a given xarray Dataset
    using the latitutdes

    Returns the NSIDE value that gives pixel sizes just smaller than the smallest pixel size in the dataset.
    
    Parameters:
    -----------
    lats : np.ndarray
        
    Returns:
    --------
    nside : int
        HEALPix NSIDE parameter (must be a power of 2)
    actual_pixel_size : float
        Actual pixel size in degrees for the returned NSIDE
    """
    if lats.ndim != 1:
        raise ValueError("We expect a 1D array of latitudes")
    
    # Find the median latitude setp size
    delta_lat = np.abs(np.nanmedian(np.diff(lats)))

    # nside
    return get_nside_from_angular_size(delta_lat)



def arrays_to_healpix(lat:np.ndarray, 
                      lon:np.ndarray, 
                      vals:np.ndarray, 
                      stat:str='mean', 
                      nside:int=None):
    """
    Generate a healpix map of where the input
    MHW Systems are located on the globe

    Parameters
    ----------
    lat : np.ndarray
        Latitude array
    lon : np.ndarray
        Longitude array
    vals : np.ndarray
        Values to map
    stat : str, optional
        Statistic to calculate. Default is 'mean'
    nside : int, optional
        HEALPix NSIDE parameter. Default is None
        If None, the NSIDE is calculated from the input data
    
    Returns
    -------
    healpix_array : healpy.ma (number of items contributing)
    healpix_array : healpy.ma1 (combined statistic)
    lats : np.ndarray
    lons : np.ndarray
    """
    if stat != 'mean':
        raise IOError("stat != 'mean' not implemented yet")

    # Unpack
    if lat.ndim == 2:
        lats = lat
        lons = lon
    elif lat.ndim == 1:
        # Convert to 2D
        lons, lats = np.meshgrid(lon, lat)
    else:
        raise ValueError("Bad lat/lon shape")

    # Flatten
    lats = lats.flatten()
    lons = lons.flatten()

    # Pixels
    if nside is None:
        nside, _ = get_nside_from_lats(lat)
    npix_hp = healpy.nside2npix(nside)
    
    # Deal with NaNs
    vals = vals.flatten()
    finite = np.isfinite(vals)

    # 
    idx_all = np.zeros(vals.size, dtype='int') -1

    # Healpix coords
    theta = (90 - lats) * np.pi / 180. 
    phi = lons * np.pi / 180.

    gd = np.isfinite(lats) & np.isfinite(lons) & finite

    idx_all[gd] = healpy.pixelfunc.ang2pix(
        nside, theta[gd], phi[gd])

    # Count events
    all_events = np.ma.masked_array(np.zeros(npix_hp, dtype='int'))
    all_values = np.ma.masked_array(np.zeros(npix_hp, dtype='float'))

    # Calculate median values
    upixels = np.unique(idx_all)
    upixels.sort()

    gdi = np.where(idx_all >= 0)[0]

    # Add em in
    for ii in gdi:
        jj = idx_all[ii]
        # Count
        all_events[jj] += 1
        all_values[jj] += vals[ii]
    #embed(header='155 of utils')
    # Mean
    pos = all_events > 0
    all_values[pos] /= all_events[pos]

    # HP Mask 
    # Yes, the counts need to be a float (for now)
    hpma = healpy.ma(all_events.astype(float))
    hpma1 = healpy.ma(all_values)

    zero = all_events == 0 
    hpma.mask = zero # current mask set to zero array, where Trues (no events) are masked
    hpma1.mask = zero 

    # Angles (convenient)
    hp_lons, hp_lats = healpy.pixelfunc.pix2ang(nside, np.arange(npix_hp), lonlat=True)

    # Return
    return hpma, hpma1, hp_lons, hp_lats, nside

def masked_in_box(hp:healpy.ma, box:tuple):
    """ Find which healpix pixels are masked
    in the box 

    Args:
        hp (healpy.ma): healpix masked array
        box (list): bounding box of the form
            [lon_min, lon_max, lat_min, lat_max]

    
    """
    nside = healpy.npix2nside(hp.size)
    lons, lats = healpy.pix2ang(nside, np.arange(hp.size), lonlat=True)

    # In box?
    gd_lats = (lats > box[2]) & (lats < box[3])
    if box[0] < box[1]:
        gd_lons = (lons > box[0]) & (lons < box[1])
    else:
        gd_lons = (lons > box[0]) | (lons < box[1])
    in_box = gd_lats & gd_lons

    # Masked?
    masked = hp.mask & in_box

    # Done
    return np.where(masked)[0]

def check_masked(hp:healpy.ma, lons:np.ndarray, lats:np.ndarray):
    """ Check whether the HealPIX is masked at the input locations

    Args:
        hp (healpy.ma): _description_
        lons (np.ndarray): _description_
        lats (np.ndarray): _description_

    Returns:
        np.ndarray: True = masked
    """

    nside = healpy.npix2nside(hp.size)

    # Healpix coords
    theta = (90 - lats) * np.pi / 180. 
    phi = lons * np.pi / 180.

    idx = healpy.pixelfunc.ang2pix(
        nside, theta, phi) 

    # Check 
    return hp.mask[idx]