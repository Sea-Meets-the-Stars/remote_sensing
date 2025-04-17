.. |forks| image:: https://img.shields.io/github/forks/AI-for-Ocean-Science/remote_sensing?style=social 
   :target: https://github.com/AI-for-Ocean-Science/remote_sensing

.. |stars| image:: https://img.shields.io/github/stars/AI-for-Ocean-Science/remote_sensing?style=social
   :target: https://github.com/AI-for-Ocean-Science/remote_sensing


Remote Sensing |forks| |stars|
==============================

.. image:: https://readthedocs.org/projects/remote-sensing/badge/?version=latest
    :target: https://remote-sensing.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

A Python package for processing and analyzing remote sensing data, 
with a (current) focus on sea surface temperature (SST) data and HEALPix 
mapping.

The package is also designed for use in the field, e.g. in 
support of active cruises.

Features
--------

* Sea Surface Temperature (SST) data handling
* PODAAC data downloading interface
* Global map visualization tools
* HEALPix map processing and visualization
* KML file generation for Google Earth
* Comprehensive I/O utilities

Quick Start
----------

Installation
~~~~~~~~~~~

Clone the repository and install in development mode:

.. code-block:: bash

    git clone https://github.com/Sea-Meets-the-Stars/remote_sensing.git
    cd remote_sensing
    pip install -e .

Basic Usage
~~~~~~~~~~

Download SST data from PODAAC:

.. code-block:: python

    from remote_sensing.download import podaac

    # Get recent AMSR2 data
    files, checksums = podaac.grab_file_list(
        'AMSR2-REMSS-L2P_RT-v8.2',
        dt_past={'days': 1}
    )

    # Download the files
    podaac.download_files(files)

Create and visualize a HEALPix map:

.. code-block:: python

    from remote_sensing.rs_healpix import RS_Healpix

    # Create HEALPix map from dataset
    hp_map = RS_Healpix.from_dataset_file(
        'sst_file.nc',
        'sea_surface_temperature',
        resol_km=25
    )

    # Plot the map
    hp_map.plot(
        vmin=0, vmax=30,
        cmap='viridis',
        cb_lbl='Temperature (°C)'
    )

Requirements
-----------

* Python 3.11+
* numpy
* matplotlib
* cartopy
* healpy
* xarray
* pandas
* simplekml

For PODAAC downloads:

* requests
* earthdata-download

Documentation
------------

Full documentation is available at `https://remote-sensing.readthedocs.io/ <https://remote-sensing.readthedocs.io/>`_

Contributing
-----------

We welcome contributions! Please see our `Contributing Guide <CONTRIBUTING.md>`_ for details.

1. Fork the repository
2. Create your feature branch (``git checkout -b feature/amazing-feature``)
3. Commit your changes (``git commit -m 'Add some amazing feature'``)
4. Push to the branch (``git push origin feature/amazing-feature``)
5. Open a Pull Request

License
-------

This project is licensed under the MIT License - see the `LICENSE <LICENSE>`_ file for details.

Authors
-------

* J. Xavier Prochaska - *Initial work*

Contact
-------

* Email: jxp@ucsc.edu
* Project Link: https://github.com/username/remote-sensing

Acknowledgments
-------------

* HEALPix for the hierarchical pixelization scheme
* PODAAC for providing access to remote sensing data
* Contributors who have helped improve this package