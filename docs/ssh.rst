Sea Surface Height (SSH)
========================

This module provides functionality for accessing, processing, and analyzing Sea Surface Height data from multiple sources.

Available Data Sources
----------------------

SSH data is available from both PODAAC and Copernicus Marine, with different products suitable for various research needs.

PODAAC SSH Products
~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   SWOT_L2_LR_SSH_EXPERT_2.0

The SWOT (Surface Water and Ocean Topography) mission provides high-resolution SSH measurements. This dataset contains low-resolution sea surface height data from the SWOT satellite mission.

For more details, visit: https://podaac.jpl.nasa.gov/dataset/SWOT_L2_LR_SSH_EXPERT_2.0

Copernicus Marine SSH Products
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Copernicus Marine provides several SSH products:

Historical Data
***************

.. code-block:: text

   cmems_obs-sl_glo_phy-ssh_my_allsat-l4-duacs-0.125deg_P1D

Near Real-Time (NRT) Data
*************************

.. code-block:: text

   cmems_obs-sl_glo_phy-ssh_nrt_allsat-l4-duacs-0.125deg_P1D

This dataset provides NRT (Near Real-Time) global sea level anomalies computed with respect to a twenty-year mean [1993, 2012]. The sea level anomaly is estimated by Optimal Interpolation, merging the L3 along-track measurements from multiple altimeter missions.

Product details: `SEALEVEL_GLO_PHY_L4_NRT_008_046 <https://data.marine.copernicus.eu/product/SEALEVEL_GLO_PHY_L4_NRT_008_046/download>`

Data Access
-----------

The package supports two methods for accessing SSH data:

Using PODAAC
~~~~~~~~~~~~

.. code-block:: python

   from remote_sensing.download import podaac
   
   # Get SWOT SSH data
   files, checksums = podaac.grab_file_list(
       'SWOT_L2_LR_SSH_EXPERT_2.0',
       dt_past={'days': 7},
       bbox='127,18,134,23'
   )
   
   # Download the files
   local_files = podaac.download_files(files)

Using Copernicus Marine
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import copernicusmarine
   
   # Login to Copernicus Marine (requires account)
   copernicusmarine.login(username=os.getenv('CM_USER'), password=os.getenv('CM_PASS'))
   
   # Download SSH data for a specific region and time
   response = copernicusmarine.subset(
       dataset_id="cmems_obs-sl_glo_phy-ssh_nrt_allsat-l4-duacs-0.125deg_P1D",
       variables=["sla", "err_sla"],
       maximum_longitude=134.0,
       minimum_longitude=127.0,
       minimum_latitude=18.0,
       maximum_latitude=23.0,
       start_datetime="2025-02-10",
       end_datetime="2025-02-10",
       file_format="netcdf",
       output_directory="data"
   )

Data Processing
---------------

Once SSH data is downloaded, it can be processed using xarray:

.. code-block:: python

   import xarray as xr
   
   # Open the NetCDF file
   ds = xr.open_dataset('path/to/ssh_file.nc')
   
   # Access sea level anomaly data
   sla = ds.isel(time=0).sla
   
   # Plot the data
   sla.plot()

Converting to HEALPix
~~~~~~~~~~~~~~~~~~~~~

For consistent processing with other remote sensing data types, SSH data can be converted to HEALPix format:

.. code-block:: python

   from remote_sensing.healpix import rs_healpix
   
   # Create HEALPix map from dataset
   hp_ssh = rs_healpix.RS_Healpix.from_dataset_file(
       'ssh_file.nc',
       'sla',
       resol_km=25
   )
   
   # Visualize
   hp_ssh.plot(
       vmin=-0.2, 
       vmax=0.2,
       cmap='coolwarm',
       cb_lbl='Sea Level Anomaly (m)'
   )

Authentication
--------------

Accessing SSH data requires authentication:

PODAAC
~~~~~~

Requires an Earthdata account and setup as described in the PODAAC documentation.

Copernicus Marine
~~~~~~~~~~~~~~~~~

Requires a Copernicus Marine account. Set environment variables:

.. code-block:: bash

   export CM_USER="your_username"
   export CM_PASS="your_password"

Or authenticate programmatically:

.. code-block:: python

   import copernicusmarine
   copernicusmarine.login(username="your_username", password="your_password")

API Reference
-------------

.. automodule:: remote_sensing.ssh
   :members:
   :undoc-members:
   :show-inheritance: