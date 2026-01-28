MODIS Ocean Color Tutorial
==========================

This tutorial demonstrates how to access, download, and process
MODIS Aqua Level-2 ocean color data using the remote_sensing package.

Prerequisites
-------------

1. **EarthData Account**: Create at https://urs.earthdata.nasa.gov/
2. **Install earthaccess**: ``pip install earthaccess``


Step 1: Authentication
----------------------

.. code-block:: python

   import earthaccess

   # Login (will prompt for credentials if needed)
   earthaccess.login()

Credentials can also be set via environment variables:

.. code-block:: bash

   export EARTHDATA_USERNAME=your_username
   export EARTHDATA_PASSWORD=your_password


Step 2: Query Available Data
----------------------------

Search for MODIS L2 OC granules over a region of interest:

.. code-block:: python

   from remote_sensing.download import earthaccess as ea

   # Define search parameters
   time_range = ('2024-01-15', '2024-01-16')
   bbox = (127, 18, 134, 23)  # lon_min, lat_min, lon_max, lat_max

   # Query standard processing
   granules = ea.query_modis_oc(
       time_range=time_range,
       bbox=bbox,
       cloud_cover=(0, 50),  # Optional: filter by cloud cover
       verbose=True
   )

   print(f"Found {len(granules)} granules")


Step 3: Examine Metadata
------------------------

Before downloading, examine granule metadata:

.. code-block:: python

   # Build summary table
   granules_dict = ea.granules_to_dict(granules)
   df = ea.build_granule_table(granules_dict, fix_antimeridian=True)

   # View table
   print(df[['id', 'time', 'CC']].head())

   # Plot spatial coverage
   if len(granules) > 0:
       ea.plot_spatial_extent(granules[0])


Step 4: Download Data
---------------------

.. code-block:: python

   # Download to local directory
   files = ea.download_modis_oc(
       granules[:3],  # Download first 3 granules
       download_dir='./MODIS_L2_OC/',
       verbose=True
   )


Step 5: Load and Process
------------------------

.. code-block:: python

   from remote_sensing.netcdf import oc

   # Load downloaded file
   rrs_dict, l2_flags, lat, lon, time = oc.load(files[0], verbose=True)

   print(f"File time: {time}")
   print(f"Shape: {lat.shape}")
   print(f"Lat range: {lat.min():.2f} to {lat.max():.2f}")
   print(f"Lon range: {lon.min():.2f} to {lon.max():.2f}")
   print(f"Rrs wavelengths: {list(rrs_dict.keys())} nm")


Step 6: Quality Control
-----------------------

Apply L2 quality flags to mask bad pixels:

.. code-block:: python

   import numpy as np

   # Create quality mask (conservative)
   mask = oc.create_quality_mask(l2_flags, verbose=True)

   # Count valid pixels
   n_valid = np.sum(~mask)
   n_total = mask.size
   print(f"Valid pixels: {n_valid} / {n_total} ({100*n_valid/n_total:.1f}%)")

   # Apply mask to Rrs data
   for wl in rrs_dict:
       rrs_dict[wl][mask] = np.nan


Step 7: Extract and Plot Spectrum
---------------------------------

.. code-block:: python

   import matplotlib.pyplot as plt

   # Find a valid (unmasked) pixel
   valid_pixels = np.where(~mask)
   if len(valid_pixels[0]) > 0:
       row, col = valid_pixels[0][0], valid_pixels[1][0]

       # Extract spectrum
       wavelengths, rrs = oc.extract_rrs_spectrum(rrs_dict, row, col)

       # Plot
       plt.figure(figsize=(10, 5))
       plt.plot(wavelengths, rrs, 'o-', linewidth=2, markersize=8)
       plt.xlabel('Wavelength (nm)', fontsize=12)
       plt.ylabel('Rrs (sr$^{-1}$)', fontsize=12)
       plt.title(f'MODIS Rrs at {lat[row, col]:.2f}N, {lon[row, col]:.2f}E')
       plt.grid(True, alpha=0.3)
       plt.show()


Complete Example
----------------

.. code-block:: python

   import earthaccess
   import numpy as np
   import matplotlib.pyplot as plt
   from remote_sensing.download import earthaccess as ea
   from remote_sensing.netcdf import oc

   # 1. Login
   earthaccess.login()

   # 2. Query
   granules = ea.query_modis_oc(
       time_range=('2024-01-15', '2024-01-16'),
       bbox=(127, 18, 134, 23),
       cloud_cover=(0, 30)
   )

   # 3. Download (first granule only)
   if len(granules) > 0:
       files = ea.download_modis_oc(granules[:1])

       # 4. Load
       rrs_dict, l2_flags, lat, lon, time = oc.load(files[0])

       # 5. Quality mask
       mask = oc.create_quality_mask(l2_flags)

       # 6. Apply mask
       for wl in rrs_dict:
           rrs_dict[wl][mask] = np.nan

       # 7. Plot Rrs at 443 nm
       plt.figure(figsize=(10, 8))
       plt.pcolormesh(lon, lat, rrs_dict[443], cmap='viridis',
                      vmin=0, vmax=0.02)
       plt.colorbar(label='Rrs_443 (sr$^{-1}$)')
       plt.xlabel('Longitude')
       plt.ylabel('Latitude')
       plt.title(f'MODIS Aqua Rrs at 443 nm\n{time}')
       plt.show()


Notebook Example
----------------

For an interactive example, see the Jupyter notebook:
``nb/EarthData/Access_MODIS_OC.ipynb``


Further Reading
---------------

* :doc:`../earthdata` - EarthData access documentation
* :doc:`../api/oc` - Ocean Color module API reference
* :doc:`../api/download` - Download module API reference
