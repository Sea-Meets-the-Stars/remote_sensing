""" Script to view a variable in a NetCDF file """

from IPython import embed

def parser(options=None):
    import argparse
    # Parse
    parser = argparse.ArgumentParser(description='View a variable in a NetCDF file')
    parser.add_argument("netcdf_file", type=str, help="File+path to NetCDF file.  If you use a wildcard, e.g. *.nc, all files will be shown, one by one")
    parser.add_argument("variable", type=str, help="Variable to view (or a 'shortcut', e.g. sst)")
    # Optional arguments
    parser.add_argument("--lat_min", type=float, help="Minimum latitude")
    parser.add_argument("--lat_max", type=float, help="Maximum latitude")
    parser.add_argument("--lon_min", type=float, help="Minimum longitude")
    parser.add_argument("--lon_max", type=float, help="Maximum longitude")  
    parser.add_argument("--projection", type=str, default='mollweide', help="Projection for the plot; (mollweide, platecarree)")
    parser.add_argument("--ssize", type=float, default=1., help="Size of the points")
    parser.add_argument("--cmap", type=str, help="Color map")
    parser.add_argument("--vmin", type=float, help="Lower bound of the colorbar")
    parser.add_argument("--vmax", type=float, help="Lower bound of the colorbar")

    parser.add_argument("--itime", type=int, default=0, help="Time index to view, if applicable")

    if options is None:
        pargs = parser.parse_args()
    else:
        pargs = parser.parse_args(options)
    return pargs

def show_one(one_file:str, pargs):

    import numpy as np
    from matplotlib import pyplot as plt
    import xarray

    from remote_sensing.plotting import globe
    from remote_sensing.plotting import utils as putils
    from remote_sensing.netcdf import utils as nc_utils
    from remote_sensing.netcdf import sst as nc_sst

    # Load 
    ds = xarray.open_dataset(one_file)

    # Grab the coords
    lat = nc_utils.find_coord(ds, 'lat')
    lon = nc_utils.find_coord(ds, 'lon')

    # Grab the variable
    found_it = False
    if pargs.variable in ds.variables:
        found_it = True
        variable = pargs.variable
    elif pargs.variable == 'sst':
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
        da = da.isel(time=pargs.itime)
        

    # Unpack
    if da[lat].ndim == 2:
        # Going to Healpix
        lats = da[lat].values
        lons = da[lon].values
    elif da[lat].ndim == 1:
        if da[lat][0] > da[lat][1]:
            lat_slice = slice(pargs.lat_max, pargs.lat_min)
        else:
            lat_slice = slice(pargs.lat_min, pargs.lat_max)
        lon_slice = slice(pargs.lon_min, pargs.lon_max)

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
    if pargs.lat_min is not None:
        lat_lim[0] = pargs.lat_min
    if pargs.lat_max is not None:
        lat_lim[1] = pargs.lat_max
    if pargs.lon_min is not None:
        lon_lim[0] = pargs.lon_min
    if pargs.lon_max is not None:
        lon_lim[1] = pargs.lon_max
        

    # Options
    kwargs = {}
    kwargs['show'] = True
    kwargs['lon_lim'] = lon_lim
    kwargs['lat_lim'] = lat_lim
    kwargs['projection'] = pargs.projection
    kwargs['ssize'] = pargs.ssize
    if pargs.cmap is not None:
        kwargs['cmap'] = pargs.cmap
    if pargs.vmin is not None:
        kwargs['vmin'] = pargs.vmin
    if pargs.vmax is not None:
        kwargs['vmax'] = pargs.vmax

    # Plot
    ax, im = globe.plot_lons_lats_vals(
        lons, lats, vals, **kwargs)


def main(pargs):
    """ Run
    """
    import glob

    # Grab em all
    files = glob.glob(pargs.netcdf_file)
    files.sort()

    for one_file in files:
        show_one(one_file, pargs)
