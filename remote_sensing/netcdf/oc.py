""" Methods for ocean color data loading and processing.

This module handles MODIS Aqua Level-2 ocean color products including:
- Remote sensing reflectance (Rrs) at multiple wavelengths
- Inherent optical properties (IOPs)
- Derived products (chlorophyll-a, POC, PIC)

MODIS Aqua L2 OC structure:
- Geophysical data: /geophysical_data/ group
- Navigation: /navigation_data/ group
- Flags: l2_flags variable (32-bit bitmask)
"""

import numpy as np
import xarray
import pandas

# MODIS Aqua ocean color wavelengths (nm)
MODIS_OC_WAVELENGTHS = [412, 443, 469, 488, 531, 547, 555, 645, 667, 678]

# Rrs variable names in MODIS L2 files
RRS_VARIABLES = [f'Rrs_{wl}' for wl in MODIS_OC_WAVELENGTHS]

# Standard L2 flag definitions (bit positions)
L2_FLAGS = {
    'ATMFAIL': 0,      # Atmospheric correction failure
    'LAND': 1,         # Land
    'PRODWARN': 2,     # One or more product algorithms generated a warning
    'HIGLINT': 3,      # High sun glint
    'HILT': 4,         # High (or saturating) TOA radiance
    'HISATZEN': 5,     # High sensor view zenith angle
    'COASTZ': 6,       # Shallow water (<30m)
    'SPARE': 7,        # Spare
    'STRAYLIGHT': 8,   # Straylight contamination
    'CLDICE': 9,       # Cloud or ice contamination
    'COCCOLITH': 10,   # Coccolithophores detected
    'TURBIDW': 11,     # Turbid water
    'HISOLZEN': 12,    # High solar zenith angle
    'SPARE': 13,       # Spare
    'LOWLW': 14,       # Low Lw @ 555nm (possible cloud shadow)
    'CHLFAIL': 15,     # Chlorophyll algorithm failure
    'NAVWARN': 16,     # Navigation quality warning
    'ABSAER': 17,      # Absorbing aerosol
    'SPARE': 18,       # Spare
    'MAXAERITER': 19,  # Maximum aerosol iterations reached
    'MODGLINT': 20,    # Moderate sun glint
    'CHLWARN': 21,     # Chlorophyll algorithm warning
    'ATMWARN': 22,     # Atmospheric correction warning
    'SPARE': 23,       # Spare
    'SEAICE': 24,      # Sea ice contamination
    'NAVFAIL': 25,     # Navigation failure
    'FILTER': 26,      # Pixel filtered
    'SPARE': 27,       # Spare
    'BOWTIEDEL': 28,   # Bowtie deleted pixel
    'HIPOL': 29,       # High degree of polarization
    'PRODFAIL': 30,    # One or more product algorithms failed
    'SPARE': 31        # Spare
}

# Standard quality control flags to mask (conservative approach)
DEFAULT_MASK_FLAGS = [
    'ATMFAIL', 'LAND', 'HILT', 'HISATZEN', 'STRAYLIGHT',
    'CLDICE', 'HISOLZEN', 'CHLFAIL', 'NAVWARN', 'NAVFAIL',
    'FILTER', 'BOWTIEDEL', 'PRODFAIL'
]


def find_rrs_variables(ds, verbose=False):
    """
    Find all Rrs variables in the dataset.

    Parameters
    ----------
    ds : xarray.Dataset
        MODIS L2 ocean color dataset
    verbose : bool, optional
        Print found variables

    Returns
    -------
    dict : Dictionary mapping wavelength (int) -> variable name (str)
        Example: {412: 'Rrs_412', 443: 'Rrs_443', ...}
    """
    rrs_dict = {}

    # Try standard naming convention
    for wl in MODIS_OC_WAVELENGTHS:
        var_name = f'Rrs_{wl}'
        if var_name in ds.variables:
            rrs_dict[wl] = var_name

    if verbose:
        print(f"Found {len(rrs_dict)} Rrs variables: {list(rrs_dict.keys())} nm")

    return rrs_dict


def load(filename, wavelengths=None, verbose=True):
    """
    Load MODIS Aqua L2 ocean color file.

    Parameters
    ----------
    filename : str
        Path to MODIS L2 NetCDF file
    wavelengths : list of int, optional
        Specific wavelengths to load (nm). If None, loads all available.
        Example: [443, 555, 667] for RGB approximation
    verbose : bool, optional
        Print loading information

    Returns
    -------
    rrs_dict : dict
        Dictionary of Rrs arrays: {wavelength: np.ndarray}
    l2_flags : np.ndarray
        L2 quality flags (32-bit integer)
    latitude : np.ndarray
        Latitude coordinates
    longitude : np.ndarray
        Longitude coordinates
    time : pandas.Timestamp
        Observation time

    Notes
    -----
    MODIS L2 files have hierarchical structure:
    - /geophysical_data/Rrs_XXX
    - /navigation_data/latitude, longitude
    - /geophysical_data/l2_flags

    Returns None for all outputs if file is corrupt or missing data.
    """
    try:
        # Open dataset
        ds = xarray.open_dataset(
            filename,
            engine='h5netcdf',
            mask_and_scale=True,
            group='geophysical_data'  # MODIS L2 groups data here
        )

        # Load navigation separately
        ds_nav = xarray.open_dataset(
            filename,
            engine='h5netcdf',
            group='navigation_data'
        )

    except Exception as e:
        if verbose:
            print(f"Error opening file: {e}")
        return None, None, None, None, None

    # Extract time from global attributes
    try:
        # MODIS L2 time in attributes
        time_coverage_start = ds.attrs.get('time_coverage_start', None)
        if time_coverage_start:
            time = pandas.to_datetime(time_coverage_start)
        else:
            # Fallback to filename parsing
            import os
            basename = os.path.basename(filename)
            # Format: AQUA_MODIS.YYYYMMDDTHHMMSS.L2.OC.nc
            time_str = basename.split('.')[1]
            time = pandas.to_datetime(time_str, format='%Y%m%dT%H%M%S')
    except Exception as e:
        if verbose:
            print(f"Warning: Could not parse time: {e}")
        time = None

    # Find available Rrs variables
    rrs_vars = find_rrs_variables(ds, verbose=verbose)

    if not rrs_vars:
        if verbose:
            print("No Rrs variables found!")
        return None, None, None, None, None

    # Filter by requested wavelengths
    if wavelengths is not None:
        rrs_vars = {wl: var for wl, var in rrs_vars.items() if wl in wavelengths}
        if verbose:
            print(f"Loading Rrs at {list(rrs_vars.keys())} nm")

    # Load Rrs data
    rrs_dict = {}
    try:
        for wl, var_name in rrs_vars.items():
            rrs_dict[wl] = ds[var_name].data[:]

        # Load L2 flags
        if 'l2_flags' in ds.variables:
            l2_flags = ds['l2_flags'].data[:].astype(np.uint32)
        else:
            if verbose:
                print("Warning: No l2_flags found, creating dummy flags")
            # Create dummy flags (all zeros = no issues)
            l2_flags = np.zeros_like(list(rrs_dict.values())[0], dtype=np.uint32)

        # Load coordinates
        latitude = ds_nav['latitude'].data[:]
        longitude = ds_nav['longitude'].data[:]

    except Exception as e:
        if verbose:
            print(f"Data is corrupt or missing: {e}")
        return None, None, None, None, None
    finally:
        ds.close()
        ds_nav.close()

    return rrs_dict, l2_flags, latitude, longitude, time


def check_flag(l2_flags, flag_name):
    """
    Check if a specific L2 flag is set.

    Parameters
    ----------
    l2_flags : np.ndarray
        L2 flags array (uint32)
    flag_name : str
        Flag name from L2_FLAGS dictionary

    Returns
    -------
    np.ndarray : Boolean array where True = flag is set
    """
    if flag_name not in L2_FLAGS:
        raise ValueError(f"Unknown flag: {flag_name}. Valid flags: {list(L2_FLAGS.keys())}")

    bit_position = L2_FLAGS[flag_name]
    return (l2_flags & (1 << bit_position)) != 0


def create_quality_mask(l2_flags, mask_flags=None, verbose=False):
    """
    Create quality mask from L2 flags.

    Parameters
    ----------
    l2_flags : np.ndarray
        L2 flags array (uint32)
    mask_flags : list of str, optional
        List of flag names to mask. If None, uses DEFAULT_MASK_FLAGS.
        Example: ['ATMFAIL', 'LAND', 'CLDICE']
    verbose : bool, optional
        Print masking statistics

    Returns
    -------
    mask : np.ndarray
        Boolean mask where True = bad/masked pixel

    Notes
    -----
    Conservative masking removes:
    - Atmospheric correction failures
    - Land, cloud, ice
    - Navigation issues
    - Sensor saturation

    For permissive masking, use: ['ATMFAIL', 'LAND', 'CLDICE']
    """
    if mask_flags is None:
        mask_flags = DEFAULT_MASK_FLAGS

    # Initialize mask (all good)
    mask = np.zeros(l2_flags.shape, dtype=bool)

    # Apply each flag
    for flag_name in mask_flags:
        if flag_name in L2_FLAGS:
            flag_mask = check_flag(l2_flags, flag_name)
            mask |= flag_mask

            if verbose:
                n_flagged = np.sum(flag_mask)
                pct = 100 * n_flagged / flag_mask.size
                print(f"  {flag_name}: {n_flagged} pixels ({pct:.1f}%)")

    if verbose:
        n_masked = np.sum(mask)
        pct = 100 * n_masked / mask.size
        print(f"Total masked: {n_masked} pixels ({pct:.1f}%)")

    return mask


def quality_control(ds):
    """
    Sensor/product specific quality control.

    Parameters
    ----------
    ds : xarray.Dataset
        MODIS L2 ocean color dataset

    Returns
    -------
    mask : np.ndarray
        Boolean mask where True = bad pixel

    Notes
    -----
    For MODIS L2 OC, applies standard L2 flag masking.
    Compatible with remote_sensing.netcdf.utils.gen_mask_for_dataset()
    """
    if 'l2_flags' in ds.variables:
        l2_flags = ds['l2_flags'].data[:].astype(np.uint32)
        mask = create_quality_mask(l2_flags, verbose=False)
        return mask
    else:
        # No flags available - mask only NaN/invalid values
        return None


def extract_rrs_spectrum(rrs_dict, row, col):
    """
    Extract Rrs spectrum at a specific pixel.

    Parameters
    ----------
    rrs_dict : dict
        Dictionary of Rrs arrays from load()
    row, col : int
        Pixel coordinates

    Returns
    -------
    wavelengths : np.ndarray
        Wavelengths in nm
    rrs : np.ndarray
        Rrs values (sr^-1)
    """
    wavelengths = np.array(sorted(rrs_dict.keys()))
    rrs = np.array([rrs_dict[wl][row, col] for wl in wavelengths])

    return wavelengths, rrs


def get_wavelength_array():
    """
    Get standard MODIS Aqua ocean color wavelengths.

    Returns
    -------
    np.ndarray : Wavelengths in nm
    """
    return np.array(MODIS_OC_WAVELENGTHS)
