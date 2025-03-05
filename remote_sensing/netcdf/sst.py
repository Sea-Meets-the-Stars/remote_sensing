""" Methods for SST data download. """
import numpy as np
import xarray
import pandas

from remote_sensing import units 
    
variables = ['sea_surface_temperature', 'analysed_sst']

def find_variable(ds, verbose:bool=False):
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
    for variable in ['sea_surface_temperature', 'analysed_sst']:
        if variable in ds.variables:
            if verbose: 
                print(f'Using SST variable: {variable}')
            return variable 
    return None

def load(filename:str, verbose:bool=True):
    """
    Load a .nc file of SST

    Parameters
    ----------
    filename : str
        NetCDF file to load
        It must include the time dimension
    verbose : bool, optional

    Returns
    -------
    sst, qual, latitude, longitude, time : np.ndarray, np.ndarray, np.ndarray np.ndarray, datetime.datetime
        Temperture map
        Quality
        Latitutides
        Longitudes
        or 4 None's if the data is corrupt!
    """

    ds = xarray.open_dataset(
        filename_or_obj=filename,
        engine='h5netcdf',
        mask_and_scale=True,
        decode_timedelta=False)

    # Deal with time
    if 'time' in ds.coords:
        time = pandas.to_datetime(ds.time.data[0])
        ds = ds.isel(time=0)
    else:
        raise IOError("No time coordinate found")

    # Find the variable
    variable = find_variable(ds, verbose=verbose)
    if variable is None:
        if verbose:
            print("No SST variable found!")
        return None, None, None, None

    da = ds[variable]

    try:
        # Fails if data is corrupt
        sst = units.kelvin_to_celsius(da).data[:]
        qual = ds.quality_level.data[...].astype(int)
        #qual = ds.l2p_flags.data[0,...]
        latitude = ds.lat.data[:]
        longitude = ds.lon.data[:]
    except:
        if verbose:
            print("Data is corrupt!")
            import pdb; pdb.set_trace()
        return None, None, None, None

    ds.close()

    # Return
    return sst, qual, latitude, longitude, time

def quality_control(ds):
    """ Sensor / Product specific quality control. """

    bad = None
    if ds.attrs['sensor'] == 'AMSR2':
        bad = ds.quality_level < 2
    elif ds.attrs['sensor'] == 'VIIRS':
        bad = ds.quality_level < 5
    elif ds.attrs['sensor'] == 'AHI':
        bad = ds.quality_level < 5

    return bad
