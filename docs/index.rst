.. include:: ../README.rst

----

.. _bibtex:


Remote Sensing
==============

A Python package for processing and analyzing remote sensing data, with a focus on sea surface temperature (SST) data and HEALPix mapping.

Features
--------

* HEALPix map processing and visualization
* Sea Surface Temperature (SST) data handling
* Sea Surface Height (SSH) data access and processing
* PODAAC data downloading interface
* Copernicus Marine data integration
* Global map visualization tools
* KML file generation for Google Earth
* Comprehensive I/O utilities

Installation
------------

.. code-block:: bash

   pip install remote-sensing

Contents
--------

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   installation
   quickstart
   tutorials/index
   scripts/index

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/healpix
   api/sst
   api/ssh
   api/visualization
   api/download
   api/io

.. toctree::
   :maxdepth: 1
   :caption: Development

   contributing
   changelog

Indices and Tables
-----------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`