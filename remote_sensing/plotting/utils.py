import numpy as np
from matplotlib import pyplot as plt
import xarray

from remote_sensing.plotting import globe
from remote_sensing.plotting import utils as putils
from remote_sensing.netcdf import utils as nc_utils
from remote_sensing.netcdf import sst as nc_sst

def set_fontsize(ax, fsz):
    """
    Set the fontsize throughout an Axis

    Args:
        ax (Matplotlib Axis):
        fsz (float): Font size

    Returns:

    """
    for item in ([ax.title, ax.xaxis.label, ax.yaxis.label] +
                 ax.get_xticklabels() + ax.get_yticklabels()):
        item.set_fontsize(fsz)


def show_one(one_file:str, variable:str, lat_min:float=None, 
             lat_max:float=None, lon_min:float=None, lon_max:float=None, 
             projection:str='mollweide', ssize:float=1., cmap:str=None, 
             vmin:float=None, vmax:float=None, itime:int=0):


    # Load 
    ds = xarray.open_dataset(one_file)

    # Grab the coords
    lat = nc_utils.find_coord(ds, 'lat')
    lon = nc_utils.find_coord(ds, 'lon')

    # Grab the variable
    found_it = False
    if variable in ds.variables:
        found_it = True
    elif variable == 'sst':
        variable = nc_sst.find_variable(ds, verbose=False)
        if variable is not None:
            found_it = True
            
        for variable in ['sea_surface_temperature', 'analysed_sst']:
            if variable in ds.variables:
                found_it = True
                break
    if not found_it:
        raise IOError("Variable not found in the NetCDF file")
    da = ds[variable]

    # Mask bad data
    junk = nc_utils.gen_mask_for_dataset(ds, variable)
    if junk is not None:
        da.data[junk] = np.nan

    # Time?
    if 'time' in da.dims:
        da = da.isel(time=itime)
        

    # Unpack
    if da[lat].ndim == 2:
        # Going to Healpix
        lats = da[lat].values
        lons = da[lon].values
    elif da[lat].ndim == 1:
        if da[lat][0] > da[lat][1]:
            lat_slice = slice(lat_max, lat_min)
        else:
            lat_slice = slice(lat_min, lat_max)
        lon_slice = slice(lon_min, lon_max)

        # 
        da = da.sel({lat:lat_slice, lon:lon_slice})
        da.plot()
        # Fuss
        fig = plt.gcf()
        fig.set_size_inches(15, 10)
        ax = plt.gca()
        putils.set_fontsize(ax, 18.)
        plt.show()
        # Finish
        return
    else:
        raise ValueError("Bad lat/lon shape")

    # Masked array for the values
    vals = np.ma.array(da.values)

    # Mask me more
    bad = np.isnan(vals)
    vals.mask = bad

    # BBOX
    lon_lim = [None, None]
    lat_lim = [None, None]
    if lat_min is not None:
        lat_lim[0] = lat_min
    if lat_max is not None:
        lat_lim[1] = lat_max
    if lon_min is not None:
        lon_lim[0] = lon_min
    if lon_max is not None:
        lon_lim[1] = lon_max
        

    # Options
    kwargs = {}
    kwargs['show'] = True
    kwargs['lon_lim'] = lon_lim
    kwargs['lat_lim'] = lat_lim
    kwargs['projection'] = projection
    kwargs['ssize'] = ssize
    if cmap is not None:
        kwargs['cmap'] = cmap
    if vmin is not None:
        kwargs['vmin'] = vmin
    if vmax is not None:
        kwargs['vmax'] = vmax

    # Plot
    ax, im = globe.plot_lons_lats_vals(
        lons, lats, vals, **kwargs)