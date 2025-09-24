""" Routines to plot healpix data. """

import numpy as np

from matplotlib import pyplot as plt
import cartopy.crs as ccrs

from remote_sensing.plotting import utils as putils

from IPython import embed

def plot_lons_lats_vals(lons, lats, values,
                      tricontour=False, 
               figsize=(12,8), 
               vmin:float=None, vmax:float=None,
               projection:str='mollweide',
               ssize:float=1.,
               add_colorbar:bool=True,
               cb_lbl=None, 
               cb_lsize:float=14.,
               cb_tsize:float=12.,
               dpi:int=300,
               marker:str=None,
               cmap='viridis', show=False,
               lon_lim:tuple=None, lat_lim:tuple=None,
               land:bool=False,
               ax=None, savefig:str=None,
               transparent:bool=True):
    """Generate a global map of mean LL of the input
    cutouts
    Args:
        lons (np.ndarray): Longitudes
        lats (np.ndarray): Latitudes
        values (np.ndarray): Values to plot
        tricontour (bool, optional): Use tricontour.  Defaults to False.
        figsize (tuple, optional): Size of the figure.  Defaults to (12,8).
        vmin (float, optional): Minimum value for the color scale.  Defaults to None.
        vmax (float, optional): Maximum value for the color scale.  Defaults to None.
        projection (str, optional): Projection for the plot.  Defaults to 'mollweide'.
        ssize (float, optional): Size of the points.  Defaults to 1..
        add_colorbar (bool, optional): Add a colorbar.  Defaults to True.
        cb_lbl ([type], optional): Label for the colorbar.  Defaults to None.
        cb_lsize (float, optional): Label size for the colorbar.  Defaults to 14..
        cb_tsize (float, optional): Tick size for the colorbar.  Defaults to 12..
        cmap (str, optional): Colormap.  Defaults to 'viridis'.
        show (bool, optional): Show the plot.  Defaults to False.
        lon_lim (tuple, optional): x limits.  Defaults to None.
        lat_lim (tuple, optional): y limits.  Defaults to None.
        ax ([type], optional): Axis to use.  Defaults to None.
        savefig (str, optional): If not None, save the figure to this file.  Defaults to None
        transparent (bool, optional): Make the background transparent.  Defaults to True.
        land (bool, optional): Overlay land mask.  Defaults to False.

    Returns:
        matplotlib.Axis: axis holding the plot
        matplotlib.image: image object
    """
    
    # Figure
    if ax is None:
        fig = plt.figure(figsize=figsize)
        plt.clf()

    tformM = ccrs.Mollweide()
    tformP = ccrs.PlateCarree()

    if projection == 'mollweide':
        tform = tformM
    elif projection == 'platecarree':
        tform = tformP
    else:
        raise ValueError(f"Bad projection: {projection}")

    if ax is None:
        ax = plt.axes(projection=tform)

    if tricontour:
        cm = plt.get_cmap(cmap)
        img = ax.tricontourf(lons, lats, values, 
                             transform=tform,
                         levels=20, cmap=cm)#, zorder=10)
    else:
        cm = plt.get_cmap(cmap)
        # Cut
        if hasattr(values, 'mask'):
            # Masked array
            good = np.invert(values.mask)
        else:
            good = np.ones(lons.shape, dtype=bool)
        img = ax.scatter(x=lons[good],
            y=lats[good],
            c=values[good], 
            vmin=vmin, vmax=vmax,
            marker=marker,
            cmap=cm,
            s=ssize,
            transform=tformP)

    # Colorbar
    if add_colorbar:
        cb = plt.colorbar(img, orientation='horizontal', pad=0.)
        if cb_lbl is not None:
            cb.set_label(cb_lbl, fontsize=cb_lsize)
        cb.ax.tick_params(labelsize=cb_tsize)

    # Coast lines
    if not tricontour or land:
        #embed(header="Plotting coastlines")
        ax.coastlines(zorder=10)
        ax.set_global()
        putils.add_gridlines(ax)

    # Limits
    if lon_lim is not None:
        ax.set_xlim(lon_lim)
    if lat_lim is not None:
        ax.set_ylim(lat_lim)

    plt.tight_layout()

    # Save?
    if savefig is not None:
        plt.savefig(savefig, bbox_inches='tight', dpi=dpi,
                    transparent=transparent)

    # Layout and save
    if show:
        plt.show()

    return ax, img
