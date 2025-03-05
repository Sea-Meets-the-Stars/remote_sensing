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



def main(pargs):
    """ Run
    """
    import glob

    from remote_sensing.plotting import utils as putils

    # Grab em all
    files = glob.glob(pargs.netcdf_file)
    files.sort()

    # 3. Convert the parsed arguments to a dictionary
    kwargs = vars(pargs)

    # Remove netcdf_file
    kwargs.pop('netcdf_file')

    for one_file in files:
        putils.show_one(one_file, **kwargs)
