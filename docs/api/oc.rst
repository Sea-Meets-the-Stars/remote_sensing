Ocean Color (OC) Module
=======================

The OC module provides functionality for loading and processing ocean color
data, specifically MODIS Aqua Level-2 products.

.. automodule:: remote_sensing.netcdf.oc
   :members:
   :undoc-members:
   :show-inheritance:


Constants
---------

Wavelengths
~~~~~~~~~~~

.. code-block:: python

   # MODIS Aqua ocean color wavelengths (nm)
   MODIS_OC_WAVELENGTHS = [412, 443, 469, 488, 531, 547, 555, 645, 667, 678]

   # Rrs variable names in MODIS L2 files
   RRS_VARIABLES = ['Rrs_412', 'Rrs_443', ..., 'Rrs_678']

L2 Flags
~~~~~~~~

.. code-block:: python

   # Standard L2 flag definitions (bit positions)
   L2_FLAGS = {
       'ATMFAIL': 0,      # Atmospheric correction failure
       'LAND': 1,         # Land
       'PRODWARN': 2,     # Product algorithm warning
       'HIGLINT': 3,      # High sun glint
       'HILT': 4,         # High TOA radiance
       'HISATZEN': 5,     # High sensor view zenith
       'COASTZ': 6,       # Shallow water (<30m)
       'STRAYLIGHT': 8,   # Straylight contamination
       'CLDICE': 9,       # Cloud or ice
       'COCCOLITH': 10,   # Coccolithophores detected
       'TURBIDW': 11,     # Turbid water
       'HISOLZEN': 12,    # High solar zenith
       'LOWLW': 14,       # Low Lw @ 555nm
       'CHLFAIL': 15,     # Chlorophyll algorithm failure
       'NAVWARN': 16,     # Navigation warning
       'ABSAER': 17,      # Absorbing aerosol
       'MAXAERITER': 19,  # Max aerosol iterations
       'MODGLINT': 20,    # Moderate sun glint
       'CHLWARN': 21,     # Chlorophyll warning
       'ATMWARN': 22,     # Atmospheric correction warning
       'SEAICE': 24,      # Sea ice
       'NAVFAIL': 25,     # Navigation failure
       'FILTER': 26,      # Pixel filtered
       'BOWTIEDEL': 28,   # Bowtie deleted
       'HIPOL': 29,       # High polarization
       'PRODFAIL': 30,    # Product algorithm failed
   }

   # Default flags for conservative quality masking
   DEFAULT_MASK_FLAGS = [
       'ATMFAIL', 'LAND', 'HILT', 'HISATZEN', 'STRAYLIGHT',
       'CLDICE', 'HISOLZEN', 'CHLFAIL', 'NAVWARN', 'NAVFAIL',
       'FILTER', 'BOWTIEDEL', 'PRODFAIL'
   ]


Data Loading
------------

.. code-block:: python

   def load(filename, wavelengths=None, verbose=True):
       """
       Load MODIS Aqua L2 ocean color file.

       Parameters
       ----------
       filename : str
           Path to MODIS L2 NetCDF file
       wavelengths : list of int, optional
           Specific wavelengths to load (nm). If None, loads all.
       verbose : bool, optional
           Print loading information

       Returns
       -------
       rrs_dict : dict
           Dictionary of Rrs arrays: {wavelength: np.ndarray}
       l2_flags : np.ndarray
           L2 quality flags (32-bit integer)
       latitude : np.ndarray
           Latitude coordinates
       longitude : np.ndarray
           Longitude coordinates
       time : pandas.Timestamp
           Observation time
       """


Quality Control
---------------

.. code-block:: python

   def check_flag(l2_flags, flag_name):
       """
       Check if a specific L2 flag is set.

       Parameters
       ----------
       l2_flags : np.ndarray
           L2 flags array (uint32)
       flag_name : str
           Flag name from L2_FLAGS dictionary

       Returns
       -------
       np.ndarray
           Boolean array where True = flag is set
       """

   def create_quality_mask(l2_flags, mask_flags=None, verbose=False):
       """
       Create quality mask from L2 flags.

       Parameters
       ----------
       l2_flags : np.ndarray
           L2 flags array (uint32)
       mask_flags : list of str, optional
           List of flag names to mask. Default: DEFAULT_MASK_FLAGS
       verbose : bool, optional
           Print masking statistics

       Returns
       -------
       mask : np.ndarray
           Boolean mask where True = bad/masked pixel
       """

   def quality_control(ds):
       """
       Sensor/product specific quality control for xarray datasets.

       Compatible with remote_sensing.netcdf.utils.gen_mask_for_dataset()
       """


Spectrum Extraction
-------------------

.. code-block:: python

   def extract_rrs_spectrum(rrs_dict, row, col):
       """
       Extract Rrs spectrum at a specific pixel.

       Parameters
       ----------
       rrs_dict : dict
           Dictionary of Rrs arrays from load()
       row, col : int
           Pixel coordinates

       Returns
       -------
       wavelengths : np.ndarray
           Wavelengths in nm
       rrs : np.ndarray
           Rrs values (sr^-1)
       """

   def get_wavelength_array():
       """
       Get standard MODIS Aqua ocean color wavelengths.

       Returns
       -------
       np.ndarray
           Wavelengths in nm [412, 443, ..., 678]
       """


Example Usage
-------------

Basic Loading
~~~~~~~~~~~~~

.. code-block:: python

   from remote_sensing.netcdf import oc

   # Load file
   rrs_dict, l2_flags, lat, lon, time = oc.load(
       'AQUA_MODIS.20240115T012000.L2.OC.nc'
   )

   print(f"Shape: {lat.shape}")
   print(f"Time: {time}")
   print(f"Rrs bands: {list(rrs_dict.keys())} nm")

Quality Masking
~~~~~~~~~~~~~~~

.. code-block:: python

   # Conservative masking (default)
   mask = oc.create_quality_mask(l2_flags, verbose=True)

   # Apply mask to Rrs data
   for wl in rrs_dict:
       rrs_dict[wl][mask] = np.nan

   # Permissive masking (only critical flags)
   mask_permissive = oc.create_quality_mask(
       l2_flags,
       mask_flags=['ATMFAIL', 'LAND', 'CLDICE']
   )

Spectral Analysis
~~~~~~~~~~~~~~~~~

.. code-block:: python

   import matplotlib.pyplot as plt

   # Find clean pixel
   clean = np.where(~mask)
   row, col = clean[0][0], clean[1][0]

   # Extract spectrum
   wl, rrs = oc.extract_rrs_spectrum(rrs_dict, row, col)

   # Plot
   plt.plot(wl, rrs, 'o-')
   plt.xlabel('Wavelength (nm)')
   plt.ylabel('Rrs (sr$^{-1}$)')
   plt.title(f'Rrs at {lat[row, col]:.2f}N, {lon[row, col]:.2f}E')
