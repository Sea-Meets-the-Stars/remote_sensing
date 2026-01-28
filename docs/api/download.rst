Download Module
===============

Tools for downloading remote sensing data from PODAAC and EarthData/OB.DAAC.

PODAAC Interface
----------------

.. automodule:: remote_sensing.download.podaac
   :members:
   :undoc-members:
   :show-inheritance:

Key Functions
~~~~~~~~~~~~~

.. code-block:: python

   def grab_file_list(collection, dt_past=None, time_range=None, bbox=None):
       """
       Get list of available files from PODAAC.

       Parameters
       ----------
       collection : str
           PODAAC collection identifier
       dt_past : dict, optional
           Time delta for past data (e.g., {'days': 1})
       time_range : tuple, optional
           (start_time, end_time) in ISO format
       bbox : str, optional
           Bounding box 'min_lon,min_lat,max_lon,max_lat'

       Returns
       -------
       tuple
           (data_files, checksums)
       """

   def download_files(data_files, checksums=None, output_dir=None,
                     clobber=False):
       """
       Download files from PODAAC.

       Parameters
       ----------
       data_files : list
           List of file URLs to download
       checksums : list, optional
           List of file checksums
       output_dir : str, optional
           Download directory (default: $OS_RS/PODAAC/collection)
       clobber : bool, optional
           Whether to overwrite existing files
       """


EarthAccess Interface
---------------------

Interface to NASA EarthData via the ``earthaccess`` library.
Supports OB.DAAC ocean color products.

.. automodule:: remote_sensing.download.earthaccess
   :members:
   :undoc-members:
   :show-inheritance:

MODIS Ocean Color Functions
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def query_modis_oc(time_range=None, bbox=None, cloud_cover=None,
                      nrt=False, verbose=True):
       """
       Query MODIS Aqua Level-2 ocean color data from OB.DAAC.

       Parameters
       ----------
       time_range : tuple, optional
           Temporal range as (start, end) in 'YYYY-MM-DD' format
       bbox : tuple, optional
           Bounding box as (lon_min, lat_min, lon_max, lat_max)
       cloud_cover : tuple, optional
           Cloud cover range as (min_percent, max_percent)
       nrt : bool, default=False
           If True, query near-real-time data (MODISA_L2_OC_NRT)
           If False, query standard processed data (MODISA_L2_OC)
       verbose : bool, default=True
           Print query information

       Returns
       -------
       list
           List of earthaccess DataGranule objects
       """

   def download_modis_oc(granules, download_dir=None, verbose=True):
       """
       Download MODIS Aqua L2 ocean color granules.

       Parameters
       ----------
       granules : list
           List of earthaccess DataGranule objects
       download_dir : str, optional
           Download directory (default: './MODIS_L2_OC/')
       verbose : bool, default=True
           Print download progress

       Returns
       -------
       list
           List of paths to downloaded files
       """

Metadata Functions
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def extract_spatial_extent(granule):
       """Extract spatial extent (polygons, bounding boxes) from granule."""

   def extract_temporal_extent(granule):
       """Extract start and end times from granule."""

   def granules_to_dict(granules):
       """Convert granule list to dictionary keyed by native-id."""

   def build_granule_table(granules, fix_antimeridian=False):
       """Build pandas DataFrame with granule metadata."""

   def plot_spatial_extent(granule, granule_title="Data Granule", show=True):
       """Plot granule spatial extent on a map."""


Authentication
--------------

Authentication is required for downloading from PODAAC and EarthData. You need to:

1. Have an Earthdata account (https://urs.earthdata.nasa.gov/)
2. Setup authentication:

   - For PODAAC: See `data-subscriber documentation <https://github.com/podaac/data-subscriber>`_
   - For EarthAccess: Use ``earthaccess.login()`` or set environment variables

Example Usage
-------------

PODAAC Download
~~~~~~~~~~~~~~~

.. code-block:: python

   from remote_sensing.download import podaac

   # Get recent AMSR2 data
   files, checksums = podaac.grab_file_list(
       'AMSR2-REMSS-L2P_RT-v8.2',
       dt_past={'days': 1},
       bbox='127,18,134,23'
   )

   # Download the files
   podaac.download_files(files)

EarthAccess/OB.DAAC Download
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import earthaccess
   from remote_sensing.download import earthaccess as ea

   # Login to EarthData
   earthaccess.login()

   # Query MODIS L2 OC data
   granules = ea.query_modis_oc(
       time_range=('2024-01-15', '2024-01-16'),
       bbox=(127, 18, 134, 23),
       cloud_cover=(0, 50)
   )

   # Download
   files = ea.download_modis_oc(granules, download_dir='./data/')

Directory Structure
-------------------

Downloaded files are organized as follows:

.. code-block:: text

   $OS_RS/
   └── PODAAC/
       └── {collection}/
           └── downloaded_files...

   ./MODIS_L2_OC/
       └── AQUA_MODIS.*.L2.OC.nc

If the ``OS_RS`` environment variable is not set, PODAAC files are downloaded to ``./PODAAC/{collection}/``.
