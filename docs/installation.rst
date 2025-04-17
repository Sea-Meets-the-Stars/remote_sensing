Installation Guide
=================

This guide will help you install the Remote Sensing package and its dependencies.

Prerequisites
------------

Before installing, ensure you have the following:

* Python 3.11 or later
* pip (Python package installer)
* numpy
* matplotlib
* cartopy
* healpy
* xarray
* pandas

Basic Installation
----------------

You may find it best to start from a fresh `conda`_ install:

.. code-block:: console

    conda create -n remote python=3.11
    conda activate remote

Currently one has to install from GitHub: 

.. code-block:: bash

   git clone https://github.com/Sea-Meets-the-Stars/remote_sensing.git
   cd remote_sensing
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

For Copernicus downloads:

`Copernicus marine package <https://pypi.org/project/copernicusmarine/>`

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

For Copernicus downloads, set the following:

   .. code-block:: bash

      export COPERNICUSMARINE_SERVICE_USERNAME=your_username
      export COPERNICUSMARINE_SERVICE_PASSWORD=your_password


Troubleshooting
-------------

Common Issues
~~~~~~~~~~~~

1. PODAAC Authentication
   
   If you get authentication errors, verify:
   
   - Your Earthdata account is active
   - Your .netrc file permissions are set to 600
   - Your credentials are correct