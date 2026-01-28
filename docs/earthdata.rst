.. highlight:: rest

*****************
EarthData Access
*****************

This document describes accessing NASA EarthData products,
particularly ocean color data from OB.DAAC (Ocean Biology DAAC).

Authentication
--------------

All EarthData access requires authentication. Create an account at:
https://urs.earthdata.nasa.gov/

The ``earthaccess`` library handles credentials via:

1. Environment variables (``EARTHDATA_USERNAME``, ``EARTHDATA_PASSWORD``)
2. ``.netrc`` file
3. Interactive prompt

.. code-block:: python

   import earthaccess
   earthaccess.login()


MODIS Aqua L2 Ocean Color
-------------------------

MODIS Aqua Level-2 ocean color products provide remote sensing reflectance
(Rrs) at 10 wavelengths, plus derived products like chlorophyll-a.

Collections
+++++++++++

* **MODISA_L2_OC** - Standard reprocessed data (R2022.0)
* **MODISA_L2_OC_NRT** - Near-real-time data

Rrs Wavelengths
+++++++++++++++

MODIS Aqua provides Rrs at the following wavelengths (nm):

.. code-block:: text

   412, 443, 469, 488, 531, 547, 555, 645, 667, 678

Querying Data
+++++++++++++

Use ``query_modis_oc()`` to search for granules:

.. code-block:: python

   from remote_sensing.download import earthaccess as ea

   # Query standard MODIS L2 OC data
   granules = ea.query_modis_oc(
       time_range=('2024-01-15', '2024-01-16'),
       bbox=(127, 18, 134, 23),  # lon_min, lat_min, lon_max, lat_max
       cloud_cover=(0, 50),       # Optional: filter by cloud cover
       nrt=False,                 # False=standard, True=NRT
       verbose=True
   )

Downloading Data
++++++++++++++++

.. code-block:: python

   # Download granules
   files = ea.download_modis_oc(
       granules,
       download_dir='./MODIS_L2_OC/',
       verbose=True
   )

Loading and Processing
++++++++++++++++++++++

Use the ``oc`` module to load and process downloaded files:

.. code-block:: python

   from remote_sensing.netcdf import oc

   # Load file
   rrs_dict, l2_flags, lat, lon, time = oc.load(
       'AQUA_MODIS.20240115T012000.L2.OC.nc',
       verbose=True
   )

   # Create quality mask
   mask = oc.create_quality_mask(l2_flags, verbose=True)

   # Extract spectrum at a pixel
   wavelengths, rrs = oc.extract_rrs_spectrum(rrs_dict, row=100, col=200)


L2 Quality Flags
----------------

MODIS L2 products include a 32-bit quality flag array (``l2_flags``).
Key flags include:

.. list-table:: Common L2 Flags
   :header-rows: 1
   :widths: 20 10 40

   * - Flag Name
     - Bit
     - Description
   * - ATMFAIL
     - 0
     - Atmospheric correction failure
   * - LAND
     - 1
     - Land pixel
   * - CLDICE
     - 9
     - Cloud or ice contamination
   * - HISOLZEN
     - 12
     - High solar zenith angle
   * - CHLFAIL
     - 15
     - Chlorophyll algorithm failure
   * - NAVFAIL
     - 25
     - Navigation failure
   * - PRODFAIL
     - 30
     - Product algorithm failed

Checking Flags
++++++++++++++

.. code-block:: python

   from remote_sensing.netcdf import oc

   # Check individual flag
   land_mask = oc.check_flag(l2_flags, 'LAND')

   # Create combined quality mask (conservative)
   mask = oc.create_quality_mask(l2_flags)

   # Permissive masking (only critical flags)
   mask = oc.create_quality_mask(
       l2_flags,
       mask_flags=['ATMFAIL', 'LAND', 'CLDICE']
   )


Granule Metadata
----------------

Extract spatial and temporal metadata from granules:

.. code-block:: python

   from remote_sensing.download import earthaccess as ea

   # Convert to dictionary format
   granules_dict = ea.granules_to_dict(granules)

   # Build summary table with polygons, time, cloud cover
   df = ea.build_granule_table(granules_dict, fix_antimeridian=True)

   # Plot spatial extent
   fig = ea.plot_spatial_extent(granules[0])


Short Names Reference
---------------------

NASA EarthData standard product short names:
https://www.earthdata.nasa.gov/learn/earth-observation-data-basics/standard-data-products

Ocean Color Products
++++++++++++++++++++

.. list-table:: OB.DAAC Collections
   :header-rows: 1
   :widths: 30 40

   * - Short Name
     - Description
   * - MODISA_L2_OC
     - MODIS Aqua L2 Ocean Color (standard)
   * - MODISA_L2_OC_NRT
     - MODIS Aqua L2 Ocean Color (near-real-time)
   * - PACE_OCI_L2_BGC
     - PACE OCI L2 Biogeochemistry
   * - VIIRS_SNPP_L2_OC
     - VIIRS SNPP L2 Ocean Color

