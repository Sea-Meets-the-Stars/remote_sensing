import numpy as np
from matplotlib import pyplot as plt

import xarray
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER

from remote_sensing.plotting import globe
from remote_sensing.netcdf import utils as nc_utils
from remote_sensing.netcdf import sst as nc_sst

from IPython import embed

def add_gridlines(ax):
    
    gl = ax.gridlines(crs=ccrs.PlateCarree(), linewidth=1, 
        color='black', alpha=0.5, linestyle=':', draw_labels=True)
    gl.xlabels_top = False
    gl.ylabels_left = True
    gl.ylabels_right=False
    gl.xlines = True
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER
    gl.xlabel_style = {'color': 'black'}# 'weight': 'bold'}
    gl.ylabel_style = {'color': 'black'}# 'weight': 'bold'}
    #gl.xlocator = mticker.FixedLocator([-180., -160, -140, -120, -60, -20.])
    #gl.xlocator = mticker.FixedLocator([-240., -180., -120, -65, -60, -55, 0, 60, 120.])
    #gl.ylocator = mticker.FixedLocator([0., 15., 30., 45, 60.])


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
             vmin:float=None, vmax:float=None, itime:int=0,
             land:bool=False):
    """
    Display a variable from a NetCDF file on a map with optional spatial and 
    visual customizations.
    Parameters:
    -----------
    one_file : str
        Path to the NetCDF file to be visualized.
    variable : str
        Name of the variable to plot. If 'sst', attempts to find a sea surface 
        temperature variable.
    lat_min : float, optional
        Minimum latitude for the region of interest. Default is None.
    lat_max : float, optional
        Maximum latitude for the region of interest. Default is None.
    lon_min : float, optional
        Minimum longitude for the region of interest. Default is None.
    lon_max : float, optional
        Maximum longitude for the region of interest. Default is None.
    projection : str, optional
        Map projection to use for plotting. Default is 'mollweide'.
    ssize : float, optional
        Marker size for the plot. Default is 1.0.
    cmap : str, optional
        Colormap to use for the plot. Default is None.
    vmin : float, optional
        Minimum value for the color scale. Default is None.
    vmax : float, optional
        Maximum value for the color scale. Default is None.
    itime : int, optional
        Time index to select if the variable has a time dimension. Default is 0.
    land : bool, optional
        If True, overlays a land mask on the plot. Default is False.

    Raises:
    -------
    IOError
        If the specified variable is not found in the NetCDF file.
    ValueError
        If the latitude or longitude dimensions have an unsupported shape.
    Notes:
    ------
    - The function supports both 1D and 2D latitude/longitude coordinates.
    - If latitude and longitude bounds are provided, the data is sliced 
        accordingly.
    - The function uses a masked array to handle invalid or NaN values in the 
        data.
    - The plot is displayed using matplotlib and optionally customized with 
        the provided parameters.
    """


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

        # Create a figure with projection
        fig = plt.figure(figsize=(15, 10))
        ax = plt.axes(projection=ccrs.PlateCarree())

        # Plot your data
        da.plot(ax=ax, transform=ccrs.PlateCarree(), cmap=cmap, vmin=vmin, vmax=vmax)

        # Add coastlines
        ax.coastlines()
        add_gridlines(ax)

        # Optional: Add more geographic features
        ax.add_feature(cfeature.BORDERS, linestyle=':')
        ax.add_feature(cfeature.LAND, alpha=0.5)
        ax.add_feature(cfeature.OCEAN)

        set_fontsize(ax, 18.)
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
    if land:
        kwargs['land'] = True

    embed(header='178 of utils')

    # Plot
    ax, im = globe.plot_lons_lats_vals(
        lons, lats, vals, **kwargs)