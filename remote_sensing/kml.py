""" Methods for working with KML files. 

with contributions from Michael Dalsin
"""

import simplekml
import matplotlib.pyplot as plt
from simplekml import (Kml, OverlayXY, ScreenXY, Units, RotationXY,
                       AltitudeMode, Camera)

def colorbar(im:plt, label:str, filename:str):
    # im = matplotlib plot 

    fig = plt.figure(figsize=(1.0, 4.0), facecolor=None, frameon=False)
    ax = fig.add_axes([0.0, 0.05, 0.2, 0.9])
    cb = fig.colorbar(im, cax=ax)
    cb.set_label(label,color='white',rotation=90)
    cb.ax.tick_params(which='both', color='white', labelcolor='white')
    fig.savefig(filename, transparent=True, format='png',dpi=100) 


def make_kml(llcrnrlon, llcrnrlat, urcrnrlon, urcrnrlat,
             figs, colorbar=None,cbarX=0,cbarY=0, **kw):
    """TODO: LatLon bbox, list of figs, optional colorbar figure,
    and several simplekml kw..."""

    kml = Kml()
    altitude = kw.pop('altitude', 2e7)
    roll = kw.pop('roll', 0)
    tilt = kw.pop('tilt', 0)
    altitudemode = kw.pop('altitudemode', AltitudeMode.relativetoground)
    camera = Camera(latitude=np.mean([urcrnrlat, llcrnrlat]),
                    longitude=np.mean([urcrnrlon, llcrnrlon]),
                    altitude=altitude, roll=roll, tilt=tilt,
                    altitudemode=altitudemode)

    kml.document.camera = camera
    draworder = 0
    for fig in figs:  # NOTE: Overlays are limited to the same bbox.
        draworder += 1
        ground = kml.newgroundoverlay(name='GroundOverlay')
        ground.draworder = draworder
        ground.visibility = kw.pop('visibility', 1)
        ground.name = kw.pop('name', 'overlay')
        ground.color = kw.pop('color', '9effffff')
        ground.atomauthor = kw.pop('author', 'ocefpaf')
        ground.latlonbox.rotation = kw.pop('rotation', 0)
        ground.description = kw.pop('description', 'Matplotlib figure')
        ground.gxaltitudemode = kw.pop('gxaltitudemode',
                                       'clampToSeaFloor')
        ground.icon.href = fig
        ground.latlonbox.east = llcrnrlon
        ground.latlonbox.south = llcrnrlat
        ground.latlonbox.north = urcrnrlat
        ground.latlonbox.west = urcrnrlon

    if colorbar:  # Options for colorbar are hard-coded (to avoid a big mess).
        screen = kml.newscreenoverlay(name='ScreenOverlay')
        screen.icon.href = colorbar
        screen.overlayxy = OverlayXY(x=cbarX, y=cbarY,
                                     xunits=Units.fraction,
                                     yunits=Units.fraction)
        screen.screenxy = ScreenXY(x=0.015, y=0.075,
                                   xunits=Units.fraction,
                                   yunits=Units.fraction)
        screen.rotationXY = RotationXY(x=0.5, y=0.5,
                                       xunits=Units.fraction,
                                       yunits=Units.fraction)
        screen.size.x = 0
        screen.size.y = 0
        screen.size.xunits = Units.fraction
        screen.size.yunits = Units.fraction
        screen.visibility = 1

    kmzfile = kw.pop('kmzfile', 'overlay.kmz')
    kml.savekmz(kmzfile)

import numpy as np
import matplotlib.pyplot as plt


def gearth_fig(llcrnrlon, llcrnrlat, urcrnrlon, urcrnrlat, pixels=1024):
    """Return a Matplotlib `fig` and `ax` handles for a Google-Earth Image."""
    aspect = np.cos(np.mean([llcrnrlat, urcrnrlat]) * np.pi/180.0)
    xsize = np.ptp([urcrnrlon, llcrnrlon]) * aspect
    ysize = np.ptp([urcrnrlat, llcrnrlat])
    aspect = ysize / xsize

    if aspect > 1.0:
        figsize = (10.0 / aspect, 10.0)
    else:
        figsize = (10.0, 10.0 * aspect)

    if False:
        plt.ioff()  # Make `True` to prevent the KML components from poping-up.
    fig = plt.figure(figsize=figsize,
                     frameon=False,
                     dpi=pixels//10,
                     facecolor=None)
    # KML friendly image.  If using basemap try: `fix_aspect=False`.
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(llcrnrlon, urcrnrlon)
    ax.set_ylim(llcrnrlat, urcrnrlat)
    return fig, ax

def png_to_kml(input_file, output_file, var_name, vmin, vmax, cmap='viridis'):
    kml = simplekml.Kml()

    # Add a color scale legend
    screen = kml.newscreenoverlay(name='Color Scale')
    screen.icon.href = 'temp_colorbar.png'
    screen.overlayxy = simplekml.OverlayXY(x=0, y=0,
                                          xunits=simplekml.Units.fraction,
                                          yunits=simplekml.Units.fraction)
    screen.screenxy = simplekml.ScreenXY(x=0.02, y=0.02,
                                        xunits=simplekml.Units.fraction,
                                        yunits=simplekml.Units.fraction)
    screen.size.x = 0.2
    screen.size.y = 0.05
    screen.size.xunits = simplekml.Units.fraction
    screen.size.yunits = simplekml.Units.fraction
    
    # Create and save the colorbar
    fig, ax = plt.subplots(figsize=(6, 1))
    plt.colorbar(plt.cm.ScalarMappable(norm=plt.Normalize(vmin, vmax), cmap=cmap),
                cax=ax, orientation='horizontal',
                label=f'{var_name.upper()} (°C)')
    plt.savefig('temp_colorbar.png', bbox_inches='tight', dpi=100)
    plt.close()
    
    # Save the KML file
    kml.save(output_file)


def scatter_to_kml_advanced(lon:np.ndarray, lat:np.ndarray, colors=None, 
                            sizes=None, labels=None, 
                            output_file='output.kml'):
    """ Scatter plot to KML file with advanced styling options.

    Args:
        lon (np.ndarray): Array of longitudes
        lat (np.ndarray): Array of latitudes
        colors (list): List of colors for each point
        sizes (list): List of sizes for each point
        labels (list): List of labels for each point
        output_file (str): Output KML file
    """
    kml = simplekml.Kml()
    
    for i, (lo, la) in enumerate(zip(lon, lat)):
        pnt = kml.newpoint()
        pnt.coords = [(lo, la)]
        
        # Add style
        if colors is not None:
            pnt.style.iconstyle.color = colors[i]
        if sizes is not None:
            pnt.style.iconstyle.scale = sizes[i]
        if labels is not None:
            pnt.name = str(labels[i])
            
        # Additional styling options
        pnt.style.iconstyle.icon.href = 'http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png'
        
    kml.save(output_file)
    print(f"Saved {output_file}")