""" Generate a Merged SSH product from two 
SSH sources (AVISO+ and SWOT)

This example was used for the ARCTERX 2025, Leg 2"""
import os

import xarray
import argparse

from remote_sensing.download import podaac
from remote_sensing.download import copernicus
from remote_sensing.healpix import rs_healpix
from remote_sensing.healpix import utils as hp_utils
from remote_sensing import io as rs_io
from remote_sensing import kml as rs_kml
from remote_sensing.process import swot_ssh_utils 

from IPython import embed

# Globals
lon_lim = (127.,134)
lat_lim = (18.,23)

def main(args):

    if args.use_json is None:

        # Grab the latest Level 4 data
        print("Downloading Level 4 file")
        local_geol4 = [copernicus.grab_download_file(
                "cmems_obs-sl_glo_phy-ssh_nrt_allsat-l4-duacs-0.125deg_P1D", 
                ["sla", "err_sla"],
                lon_lim=lon_lim, lat_lim=lat_lim,
            t_end=args.t_end,
            dt_past=dict(days=1),
            debug=args.debug)]

        # Grab SWOT
        swot_files, _ = podaac.grab_file_list(
            'SWOT_L2_LR_SSH_EXPERT_2.0',
            dt_past=dict(days=args.ndays),
            t_end=args.t_end,
            bbox=f'{lon_lim[0]},{lat_lim[0]},{lon_lim[1]},{lat_lim[1]}')

        # Download
        print("Downloading SWOT files")
        local_swot = podaac.download_files(
            swot_files, verbose=args.verbose)
        print("All done")

        sdict = {}
        sdict['local_geol4'] = local_geol4
        sdict['local_swot'] = local_swot
        sdict['nswot'] = args.nswot

    else:
        # Load filenames from JSON
        sdict = rs_io.loadjson(args.use_json)
        local_geol4 = sdict['local_geol4']
        local_swot = sdict['local_swot']
        sdict['nswot'] = args.nswot

    # Use the latest SWOT file for the timestamp
    ds = xarray.open_dataset(sdict['local_swot'][0])
    time_root = str(ds.time.data[0]).replace(':','')[0:13]

    if args.use_json is None:
        # Save files to a JSON file
        json_file = f'Merged_SST_{time_root}.json'
        jdict = rs_io.jsonify(sdict)
        rs_io.savejson(json_file, jdict, overwrite=True)
        print(f"Wrote: {json_file}")

    # #############################
    # Healpix time
    # #############################


    print("--------------------")
    print("Generating GEOL4")
    print("--------------------")

    data_file = sdict['local_geol4'][0]
    # Objectify
    geol4_stack = rs_healpix.RS_Healpix.from_dataset_file(
            data_file, 'sla',
            time_isel=0, 
            lat_slice=slice(lat_lim[0], lat_lim[1]),
            lon_slice=slice(lon_lim[0], lon_lim[1]))
        #
    print(f"Generated RS_Healpix from {data_file}")


    # Combine?
    if args.show:
        print("Showing GEOL4 stack")
        geol4_stack.plot(figsize=(10.,6), cmap='seismic', 
                         lon_lim=lon_lim, lat_lim=lat_lim, 
                         projection='platecarree', ssize=100., 
                         show=True)
        #if args.debug:
        #    embed(header='Check GEOL4 stack')


    print("--------------------")
    print("Generating SWOT stack")
    print("--------------------")

    # #############################
    swot_hpxs = []
    for data_file in sdict['local_swot'][0:sdict['nswot']]:
        # Load the data
        if args.debug:
            from importlib import reload
            embed(header='110 of gen')

        ds = xarray.open_dataset(data_file)

        ds2 = swot_ssh_utils.process_ds(ds, lat_lim=lat_lim)
        da = ds2['ssha_1']

        embed(header='122 of merged')
        # Translate to deg
        delta_lat = 2. / 111.1
        nside, _ = hp_utils.get_nside_from_angular_size(delta_lat)
        
        # Objectify
        rs_hpx = rs_healpix.RS_Healpix.from_dataarray(da, nside=nside)
        # 
        print(f"Generated RS_Healpix from {data_file}")
        # Add
        swot_hpxs.append(rs_hpx)
        del(rs_hpx)
    # Stack
    swot_stack = rs_healpix.RS_Healpix.from_list(swot_hpxs)
    if args.show:
        swot_stack.plot(figsize=(10.,6), cmap='seismic', 
                       lon_lim=lon_lim, lat_lim=lat_lim, 
                       projection='platecarree',
                       show=True)

    # Fill in
    swot_stack.fill_in(geol4_stack, (lon_lim[0], lon_lim[1], 
                                      lat_lim[0], lat_lim[1]))
    if args.show:
        swot_stack.plot(figsize=(10.,6), cmap='jet', 
                       lon_lim=lon_lim, lat_lim=lat_lim,
                       projection='platecarree', vmin=20.,
                       show=True)


    # #############################33
    # KMZ
    _, img = swot_stack.plot(figsize=(10.,6), cmap='seismic', 
                             lon_lim=lon_lim, lat_lim=lat_lim, 
                             add_colorbar=False, 
                             ssize=40.,
                             vmin=-0.1, vmax=0.1,
                             projection='platecarree', #vmin=20., 
                             savefig='kml_test.png', dpi=300, 
                             #marker=',')
    )
    rs_kml.colorbar(img, 'SSHa (cm)', 'colorbar.png')

    # Write
    outfile = f'Merged_SSH_{time_root}.kmz'
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
        h09_stack.save_to_nc(os.path.join(args.outdir, outfile))


def parse_option():
    """
    This is a function used to parse the arguments in the training.
    
    Returns:
        args: (dict) dictionary of the arguments.
    """
    parser = argparse.ArgumentParser("Merged SSH KMZ script")
    parser.add_argument("--nswot", type=int, 
                        default=10, help="Number of SWOT images to combine (default=10)")
    parser.add_argument("--ndays", type=int, 
                        default=10, help="Number of days into the past to consdier for images (default=10)")
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
    