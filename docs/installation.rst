Installation Guide
=================

This guide will help you install the Remote Sensing package and its dependencies.

Prerequisites
------------

Before installing, ensure you have the following:

* Python 3.8 or later
* pip (Python package installer)
* numpy
* matplotlib
* cartopy
* healpy
* xarray
* pandas

Basic Installation
----------------

You can install the Remote Sensing package using pip:

.. code-block:: bash

   pip install remote-sensing

For development installation:

.. code-block:: bash

   git clone https://github.com/username/remote-sensing.git
   cd remote-sensing
   pip install -e .

Dependencies
-----------

Required Dependencies
~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   numpy>=1.20.0
   matplotlib>=3.3.0
   cartopy>=0.18.0
   healpy>=1.14.0
   xarray>=0.16.0
   pandas>=1.2.0
   simplekml>=1.3.0

Optional Dependencies
~~~~~~~~~~~~~~~~~~~

For PODAAC downloads:

.. code-block:: text

   requests
   earthdata-download

Environment Variables
------------------

For PODAAC downloads, set the following:

1. Set the ``OS_RS`` environment variable to specify the data directory:

   .. code-block:: bash

      export OS_RS="/path/to/data/directory"

2. Configure Earthdata credentials (required for PODAAC):
   
   Create a ``.netrc`` file in your home directory with:

   .. code-block:: text

      machine urs.earthdata.nasa.gov
          login your-username
          password your-password
    
    Set the permissions to 600:

    .. code-block:: bash

       chmod 600 ~/.netrc

Troubleshooting
-------------

Common Issues
~~~~~~~~~~~~

1. HEALPix Installation
   
   If you encounter issues installing healpy, try:

   .. code-block:: bash

      conda install healpy

2. Cartopy Installation
   
   On Ubuntu/Debian, you may need:

   .. code-block:: bash

      sudo apt-get install libproj-dev proj-data proj-bin
      sudo apt-get install libgeos-dev

3. PODAAC Authentication
   
   If you get authentication errors, verify:
   
   - Your Earthdata account is active
   - Your .netrc file permissions are set to 600
   - Your credentials are correct