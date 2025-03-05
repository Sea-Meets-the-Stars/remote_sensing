""" Methods for downloading data from the Copernicus Marine archive."""

import os

import copernicusmarine

from remote_sensing.download import utils as down_utils

from IPython import embed

if os.getenv('OS_RS') is not None:
    copernicus_path = os.path.join(os.getenv('OS_RS'), 'COPERN')
else:
    copernicus_path = os.path.join('./', 'COPERN')

def login(force_overwrite:bool=True):
    try:
        assert copernicusmarine.login(
            username=os.getenv('COPERNICUSMARINE_SERVICE_USERNAME'), 
            password=os.getenv('COPERNICUSMARINE_SERVICE_PASSWORD'),
            force_overwrite=force_overwrite)
    except AssertionError:
        print("COPERNICUSMARINE_SERVICE_USERNAME and COPERNICUSMARINE_SERVICE_PASSWORD must be set as environment variables")



def grab_download_file(dataset_id:str, variables:list,
              time_range:tuple=None, 
              t_end:str=None,
              dt_past:dict=None, 
              lon_lim=(None,None), 
              lat_lim=(None,None),
              outdir:str=None,
              skip_download:bool=False,
              skip_existing:bool=True, 
              overwrite:bool=False,
              debug:bool=False):
    # Login
    login()

    # Outdir
    if outdir is None:
        outdir = os.path.join(copernicus_path,
                              dataset_id)

    # Parse the times
    start_datetime, end_datetime = down_utils.find_startend_datetime(
        time_range, t_end, dt_past)

    if debug:
        embed(header='51 of copernicus.py')
    response_default_service = copernicusmarine.subset(
        dataset_id=dataset_id, #"cmems_obs-sl_glo_phy-ssh_nrt_allsat-l4-duacs-0.125deg_P1D",
        variables=variables, #["sla", "err_sla"],
        maximum_longitude=lon_lim[1],
        minimum_longitude=lon_lim[0],
        minimum_latitude=lat_lim[0],
        maximum_latitude=lat_lim[1],
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        file_format="netcdf",
        overwrite=overwrite,
        skip_existing=skip_existing,
        dry_run=skip_download,
        output_directory=outdir,
    ) 

    # Return
    return str(response_default_service.file_path)
