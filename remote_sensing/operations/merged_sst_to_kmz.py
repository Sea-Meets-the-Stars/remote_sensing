""" Generate a Merged SST product from two 
SST sources (microwave and IR)

This example was used for the ARCTERX 2025, Leg 2"""
import os

import xarray
import argparse

from remote_sensing.download import podaac
from remote_sensing.healpix import rs_healpix
from remote_sensing import io as rs_io
from remote_sensing import kml as rs_kml

from IPython import embed

# Globals
lon_lim = (127.,134)
lat_lim = (18.,23)
#lon_lim = (129.,132)
#lat_lim = (19.,22.5)

def main(args):

    if args.use_json is None:
        # Grab the latest data
        amsr2_files, _ = podaac.grab_file_list(
            'AMSR2-REMSS-L2P_RT-v8.2', 
            t_end=args.t_end,
            dt_past=dict(days=args.ndays),
            bbox='127,18,134,23')

        h09_files, _ = podaac.grab_file_list(
            'H09-AHI-L3C-ACSPO-v2.90', dt_past=dict(days=args.ndays),
            t_end=args.t_end,
            bbox='127,18,134,23')

        # Download
        print("Downloading AMSR2 files")
        local_amsr2 = podaac.download_files(amsr2_files, verbose=args.verbose)
        print("Downloading Himawari files")
        local_h09 = podaac.download_files(h09_files, verbose=args.verbose)
        print("All done")

        sdict = {}
        sdict['local_amsr2'] = local_amsr2
        sdict['local_h09'] = local_h09
        sdict['namsr2'] = args.namsr2
        sdict['nh09'] = args.nh09

    else:
        # Load filenames from JSON
        sdict = rs_io.loadjson(args.use_json)
        amsr2_files = sdict['local_amsr2']
        h09_files = sdict['local_h09']
        if 'namsr2' not in sdict:
            sdict['namsr2'] = args.namsr2
            sdict['nh09'] = args.nh09

    # Use the latest H09 file for the timestamp
    ds = xarray.open_dataset(sdict['local_h09'][0])
    time_root = str(ds.time.data[0]).replace(':','')[0:13]

    # Outfile
    outfile = f'Merged_SST_{time_root}.kmz'

    # Skip if exists and not --clobber
    if os.path.exists(os.path.join(args.outdir, outfile)) and not args.clobber:
        print(f"{outfile} exists.  Use --clobber to overwrite")
        return

    if args.use_json is None:
        # Save files to a JSON file
        json_file = f'Merged_SST_{time_root}.json'
        jdict = rs_io.jsonify(sdict)
        rs_io.savejson(json_file, jdict, overwrite=True)
        print(f"Wrote: {json_file}")

    # #############################
    # Healpix time
    # #############################

    # AMSR2
    amsr2_hpxs = []

    print("--------------------")
    print("Generating AMSR2 stack")
    print("--------------------")

    for data_file in sdict['local_amsr2'][0:sdict['namsr2']]:
        # Objectify
        rs_hpx = rs_healpix.RS_Healpix.from_dataset_file(
            data_file, 'sea_surface_temperature',
            time_isel=0, resol_km=11., 
            lat_slice=(18,23.),  lon_slice=(127., 134.))
        #
        print(f"Generated RS_Healpix from {data_file}")
        # Add
        amsr2_hpxs.append(rs_hpx)

    if args.debug:
        #pass
        #embed(header='93 of gen')
        rs_hpx.save_to_nc('test.nc', full_healpix=False)

    # Combine?
    if args.namsr2 > 1:
        amsr2_stack = rs_healpix.RS_Healpix.from_list(amsr2_hpxs)
    else:
        amsr2_stack = amsr2_hpxs[0]

    if args.show:
        print("Showing AMSR2 stack")
        amsr2_stack.plot(figsize=(10.,6), cmap='jet', 
                           lon_lim=lon_lim, lat_lim=lat_lim, 
                           projection='platecarree', ssize=40., 
                           vmin=23.7, vmax=27., show=True)
        #if args.debug:
        #    embed(header='Check AMSR2 stack')

    print("--------------------")
    print("Generating H09 stack")
    print("--------------------")

    # #############################
    h09_hpxs = []
    if args.debug:
        from importlib import reload
        embed(header='110 of gen')
    for data_file in sdict['local_h09'][0:sdict['nh09']]:
        # Objectify
        rs_hpx = rs_healpix.RS_Healpix.from_dataset_file(
            data_file, 'sea_surface_temperature',
            lat_slice=slice(23,18),  lon_slice=slice(127., 134.), 
            time_isel=0, debug=args.debug)
        # 
        print(f"Generated RS_Healpix from {data_file}")
        # Add
        h09_hpxs.append(rs_hpx)
        del(rs_hpx)
    # Stack
    h09_stack = rs_healpix.RS_Healpix.from_list(h09_hpxs)
    if args.show:
        h09_stack.plot(figsize=(10.,6), cmap='jet', 
                       lon_lim=lon_lim, lat_lim=lat_lim, 
                       projection='platecarree',
                       show=True)

    # Fill in
    h09_stack.fill_in(amsr2_stack, (lon_lim[0], lon_lim[1], 
                                      lat_lim[0], lat_lim[1]))
    if args.show:
        h09_stack.plot(figsize=(10.,6), cmap='jet', 
                       lon_lim=lon_lim, lat_lim=lat_lim,
                       projection='platecarree', vmin=20.)

    # #############################33
    # KMZ
    _, img = h09_stack.plot(figsize=(10.,6), cmap='jet', 
                             lon_lim=lon_lim, lat_lim=lat_lim, 
                             add_colorbar=False, 
                             projection='platecarree', vmin=20., 
                             savefig='kml_test.png', dpi=1200, 
                             marker=',')
    rs_kml.colorbar(img, 'SST (C)', 'colorbar.png')

    # Write
    rs_kml.make_kml(llcrnrlon=lon_lim[0], llcrnrlat=lat_lim[0],
        urcrnrlon=lon_lim[1], urcrnrlat=lat_lim[1],
        figs=['kml_test.png'], colorbar='colorbar.png',
        kmzfile=os.path.join(args.outdir,outfile), 
        name='Merged SST')
    print(f"Generated: {outfile}")

    # NetCDF ?
    if args.create_nc:
        outfile = outfile.replace('.kmz', '.nc')
        # Save to netCDF
        h09_stack.save_to_nc(
            os.path.join(args.outdir, outfile),
            full_healpix=False)


def parse_option():
    """
    This is a function used to parse the arguments in the training.
    
    Returns:
        args: (dict) dictionary of the arguments.
    """
    parser = argparse.ArgumentParser("Merged SST KMZ script")
    parser.add_argument("--namsr2", type=int, 
                        default=1, help="Number of exposures of AMSR2 to combine")
    parser.add_argument("--nh09", type=int, 
                        default=10, help="Number of hours of Himawari images to combine")
    parser.add_argument("--ndays", type=int, 
                        default=2, help="Number of days into the past to consdier for images")
    parser.add_argument("--t_end", type=str, 
                        help="End time, ISO format e.g. 2025-02-07T04:00:00Z")
    parser.add_argument("--outdir", type=str, default='./',
                        help="Output directory")
    parser.add_argument('--debug', default=False, action='store_true',
                        help='Debug?')
    parser.add_argument('-n', '--create_nc', default=False, action='store_true',
                        help='Create netCDF file too?')
    parser.add_argument('-s', '--show', default=False, action='store_true',
                        help='show extra plots?')
    parser.add_argument('--verbose', default=False, action='store_true',
                        help='Print more to the screen?')
    parser.add_argument('--clobber', default=False, action='store_true',
                        help='Clobber existing files')
    parser.add_argument('--use_json', type=str, 
                        help='Load files from the JSON file')

    args = parser.parse_args()
    
    return args

        
if __name__ == "__main__":
    # get the argument of training.
    args = parse_option()
    main(args)
    