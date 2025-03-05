""" Methods for downloading data from the PO.DAAC archive. 

Makes use of code taken from the podaac_data_downloader package script,
aka subscriber.podaac_data_downloader

"""

import os

from datetime import datetime, timedelta, timezone

from subscriber import podaac_access as pa

from urllib.error import HTTPError

from remote_sensing.download import utils as down_utils

from IPython import embed

page_size = 2000
provider = 'POCLOUD'

if os.getenv('OS_RS') is not None:
    podaac_path = os.path.join(os.getenv('OS_RS'), 'PODAAC')
else:
    podaac_path = os.path.join('./', 'PODAAC')

def grab_file_list(collection:str, 
                   time_range:tuple=None, 
                   t_end:str=None,
                   dt_past:dict=None, 
                   bbox:str=None,
                   verbose:bool=True):
    """ Grab a list of files from the PO.DAAC archive.

    Args:
        collection (str): PO.DAAC collection name.
        verbose (bool, optional): Print verbose output. Defaults to True.
        time_range (tuple, optional): Start and end date in ISO format, 
            e.g. (2025-01-01T00:00:00Z, 2025-01-02T00:00:00Z).
            Defaults to None.
        t_end (str, optional): Current time in ISO format.
            If not provided, it will be set to the current time.
        dt_past (dict, optional): Time range in the past, which
            must be resolve by timedelta, e.g. dict(days=1).
            Defaults to None but will be set to 1 day if time_range is None
            and time_range is not specified.
            Relative to t_now.
        bbox (str, optional): Bounding box in the format of
            "lon_min,lat_min,lon_max,lat_max" in deg 
            Defaults to None.

    Raises:
        e: _description_

    Returns:
        tuple:
            - list: List of files.
            - list: List of checksums.
    """
    
    # Authenicate with Earthdata Login
    pa.setup_earthdata_login_auth(pa.edl)
    token = pa.get_token(pa.token_url)

    # Colleection ID
    collection_id = pa.get_cmr_collection_id(
        collection_short_name=collection,
        provider=provider,
        token=token,
        verbose=verbose)


    # Times
    start_datetime, end_datetime = down_utils.find_startend_datetime(
        time_range, t_end, dt_past)

    # Temporal range
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    temporal_range = pa.get_temporal_range(
        start_datetime, end_datetime, now)
    params = [
            ('page_size', page_size),
            ('sort_key', "-start_date"),
            ('provider', provider),
            ('ShortName', collection),
            ('temporal', temporal_range),
            ('token', token),
        ]
    if bbox is not None:
        params.append(('bounding_box', bbox))

    # If 401 is raised, refresh token and try one more time
    try:
        results = pa.get_search_results(params, verbose)
    except HTTPError as e:
        if e.code == 401:
            token = pa.refresh_token(token)
            # Updated: This is not always a dictionary...
            # in fact, here it's always a list of tuples
            for  i, p in enumerate(params) :
                if p[1] == "token":
                    params[i] = ("token", token)
            results = pa.get_search_results(params, verbose)
        else:
            raise e

    # Downloads
    downloads_all = []
    downloads_data = [[u['URL'] for u in r['umm']['RelatedUrls'] if
                       u['Type'] == "GET DATA" and ('Subtype' not in u or u['Subtype'] != "OPENDAP DATA")] for r in
                      results['items']]
    downloads_metadata = [[u['URL'] for u in r['umm']['RelatedUrls'] if u['Type'] == "EXTENDED METADATA"] for r in
                          results['items']]

    for f in downloads_data:
        downloads_all.append(f)
    for f in downloads_metadata:
        downloads_all.append(f)

    downloads = [item for sublist in downloads_all for item in sublist]

    # filter list based on extension
    filtered_downloads = []
    for f in downloads:
        for extension in pa.extensions:
            if pa.search_extension(extension, f):
                filtered_downloads.append(f)

    downloads = filtered_downloads
    checksums = pa.extract_checksums(results['items'])

    # Return
    return downloads, checksums


def download_files(file_list:list, 
                   download_dir:str=None, 
                   clobber:bool=False,
                   verbose:bool=True):
    """ Download files from the PO.DAAC archive.

    Parameters
    -----------
    file_list : list
        List of files to download.
    download_dir : str, optional
        Directory to download files to. Default is the podaac_path
        A sub-directory is created for each collection.
    clobber : bool, optional
        Overwrite existing files. Default is False.
    verbose : bool, optional
        Print verbose output. Default is True.

    Returns
    --------
    list : List of local files that were successfully downloaded.

    """
    local_files = [None]*len(file_list)

    # Authenicate with Earthdata Login
    pa.setup_earthdata_login_auth(pa.edl)
    token = pa.get_token(pa.token_url)

    if download_dir is None:
        print(f"Using default download directory: {podaac_path}")
        download_dir = podaac_path
    if not os.path.isdir(download_dir):
        os.makedirs(download_dir)

    # Loop on files
    success_cnt = failure_cnt = skip_cnt = 0
    for ss, f in enumerate(file_list):

        # Parse filename
        fparse = f.split('/')

        # Collection
        collection = fparse[-2]

        full_path = os.path.join(download_dir, collection)
        if not os.path.isdir(full_path):
            print(f'Creating directory: {full_path}')
            os.makedirs(full_path)

        # Filename
        filename = fparse[-1]


        # Download

        try:
            # -d flag, args.outputDirectory
            output_path = os.path.join(full_path, filename)
            
            # decide if we should actually download this file (e.g. we may already have the latest version)
            if os.path.isfile(output_path) and not clobber:# and pa.checksum_does_match(output_path, checksums)):
                if verbose:
                    print(f'File exists: {filename}\n  --- Use clobber=True to overwrite')
                skip_cnt += 1
                local_files[ss] = output_path
                continue

            pa.download_file(f,output_path)
            success_cnt = success_cnt + 1
            local_files[ss] = output_path

            # Success
            if verbose:
                print(f'File downloaded: {output_path}')

        except Exception:
            print(f'File failed to download: {filename}.') 
            failure_cnt = failure_cnt + 1

    print(f"Downloaded {success_cnt} files, failed on {failure_cnt} files, skipped {skip_cnt} existing files.")

    # Return
    return local_files