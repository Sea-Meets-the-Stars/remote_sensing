""" A light-weight class for holding HEALPix maps 
for Remote Sensing. """

from importlib import reload
import os

import numpy as np
import healpy
import xarray
import pandas

from remote_sensing.healpix import utils as hp_utils 
from remote_sensing.plotting import globe
from remote_sensing.healpix import combine as hp_combine
from remote_sensing import units
from remote_sensing.netcdf import utils as nc_utils


from IPython import embed

class RS_Healpix(object):

    def __init__(self, nside:int):
        """
        Initialize the RS_Healpix object.
        Parameters
        ----------
        nside : int
            HEALPix NSIDE parameter (must be a power of 2)
        """
        self.nside = nside
        self.npix = healpy.nside2npix(nside)

        self.hp = None
        self.counts = None

        # File?
        self.filename = None
        self.variable = None
    
    @property
    def lons_lats(self):
        """ Return the lats and lons. """
        return healpy.pixelfunc.pix2ang(
            self.nside, np.arange(self.npix), lonlat=True)

    @property
    def lats(self):
        """ Return the longitudes. """
        return self.lons_lats[1]

    @property
    def lons(self):
        """ Return the longitudes. """
        return self.lons_lats[0]


    @property
    def pix_resol(self):
        """ Return the pixel size in degrees. """
        return healpy.nside2resol(self.nside, arcmin=True) / 60.

    @property
    def pix_area(self):
        """ Return the pixel area in square degrees. """
        return healpy.nside2pixarea(self.nside, degrees=True)

    @property
    def basename(self):
        """ Return the pixel area in square degrees. """
        if self.filename is not None:
            return os.path.basename(self.filename)

    @classmethod
    def from_list(cls, rs_list:list):
        """
        Initialize the RS_Healpix object from a list of RS_Healpix objects.

        Parameters
        ----------
        rs_list : list
            List of RS_Healpix objects to average

        Returns
        -------
        RS_Healpix

        """
        # Check
        nside = rs_list[0].nside
        for rs in rs_list:
            if rs.nside != nside:
                raise ValueError("All RS_Healpix objects must have the same NSIDE")
                
        # Average
        hp_values = hp_combine.average_masked_arrays([rs.hp for rs in rs_list])

        # Instantiate
        rsh = RS_Healpix(nside)
        rsh.hp = hp_values

        # A bit more
        if rs_list[0].filename is not None:
            rsh.filename = f'Avg[{rs_list[0].basename}-{rs_list[-1].basename}]'
        if rs_list[0].variable is not None:
            rsh.variable = rs_list[0].variable

        # Return
        return rsh

    @classmethod
    def from_dataset_file(cls, filename:str, variable:str, 
                            lat_slice:slice=None, 
                            lon_slice:slice=None,
                            time_isel:int=None,
                            resol_km:float=None,
                            debug:bool=False):
        """
        Initialize the RS_Healpix object from a dataarray file.

        Parameters
        ----------
        filename : str
            Filename of the dataset file
        variable : str
            Variable to extract from the dataarray
        lat_slice : slice, optional
            Slice to apply to the latitude dimension
        lon_slice : slice, optional
            Slice to apply to the longitude dimension

        Returns
        -------
        RS_Healpix

        """
        nside = None
        # Load
        ds = xarray.open_dataset(filename)

        # Grab the coords
        lat = nc_utils.find_coord(ds, 'lat')
        lon = nc_utils.find_coord(ds, 'lon')

        if ds[lat].ndim == 1:
            if lat_slice is not None:
                #embed(header='Check lat_slice')
                ds = ds.sel({lat: lat_slice})
            if lon_slice is not None:
                ds = ds.sel({lon: lon_slice})
        if ds[lat].ndim == 2:
            # Deal with junk
            junk = ds[lat] < -1000.
            ds[lat].data[junk] = np.nan
            #
            junk = ds[lon] < -1000.
            ds[lon].data[junk] = np.nan

            # Cut with NaNs
            if lat_slice is not None:
                junk = (ds[lat] < lat_slice[0]) | (ds[lat] > lat_slice[1])
                ds[lat].data[junk] = np.nan
            if lon_slice is not None:
                junk = (ds[lon] < lon_slice[0]) | (ds[lon] > lon_slice[1])
                ds[lon].data[junk] = np.nan
            # nside 
            if resol_km is None:
                raise ValueError("Must provide resol_km for 2D lat/lon arrays")
            # Translate to deg
            delta_lat = resol_km / 111.1
            nside, _ = hp_utils.get_nside_from_angular_size(delta_lat)
        
        # Time slice
        if time_isel is not None:
            ds = ds.isel(time=time_isel)

        # Quality control
        da = ds[variable]
        junk = nc_utils.gen_mask_for_dataset(ds, variable)
        if junk is not None:
            da.data[junk] = np.nan

        # Instantiate
        # If SST, convert to Celsius
        if da.units in ['K', 'kelvin', 'Kelvin']:
            da = units.kelvin_to_celsius(da)
        rsh =  cls.from_dataarray(da, nside=nside)

        # Fill in
        rsh.filename = filename
        rsh.variable = variable

        # Return
        return rsh

        
    @classmethod
    def from_dataarray(cls, da:xarray.DataArray,
                       nside:int=None):
        """
        Initialize the RS_Healpix object from an xarray dataset.

        Parameters
        ----------
        da : xarray.DataArray
            Dataset containing the HEALPix data
        nside : int, optional

        Returns
        -------
        RS_Healpix

        """
        reload(hp_utils)

        # Unpack
        # Grab the coords
        lat = nc_utils.find_coord(da, 'lat')
        lon = nc_utils.find_coord(da, 'lon')
        try:
            lat = da[lat].data
        except:
            embed(header='Check lat')
        lon = da[lon].data

        
        hp_counts, hp_values, hp_lons, hp_lats, nside = \
            hp_utils.arrays_to_healpix(
                lat, lon, da.data, nside=nside)

        # Instantiate
        rsh = cls(nside)

        # Time
        rsh.time = pandas.to_datetime(da.time.data)

        # Fill
        rsh.hp = hp_values
        rsh.counts = hp_counts

        # Return
        return rsh


    def fill_in(self, rs_hp, bbox:tuple):
        """
        Fill in the RS_Healpix object from another RS_Healpix object.

        Parameters
        ----------
        rs_hp : RS_Healpix
            Object containing the HEALPix data
        bbox : tuple
            Bounding box to fill in
            (lon_min, lon_max, lat_min, lat_max)

        """
        # Find the missing healpixels
        missing = hp_utils.masked_in_box(self.hp, bbox)
        miss_lats = self.lats[missing]
        miss_lons = self.lons[missing]

        # Interpolate
        missing_values = healpy.pixelfunc.get_interp_val(
            rs_hp.hp, miss_lons, miss_lats, lonlat=True)

        # Fill in
        self.hp.data[missing] = missing_values
        self.hp.mask[missing] = False

        print("Filled in {:d} pixels".format(np.sum(missing)))
        
    def plot(self, **kwargs):
        """ Plot the HEALPix map. """
        return globe.plot_lons_lats_vals(
            self.lons, self.lats, self.hp, **kwargs)

    def save_to_nc(self, outfile:str,
                   full_healpix:bool=True):
        """ Save the HEALPix map to a NetCDF file. """

        # Reduce
        if full_healpix:
            good = np.ones_like(self.hp.data, dtype=bool)
        else:
            good = ~self.hp.mask

        # Create the dataset
        da = xarray.DataArray(
            data=self.hp.data[good].astype(np.float32),
            coords={
                'healpix': np.arange(self.hp.data.size)[good],  # Index coordinate
                'lat': ('healpix', self.lats[good].astype(np.float32)),
                'lon': ('healpix', self.lons[good].astype(np.float32))
            },
            dims=['healpix'],
            name='sea_surface_temperature',
            attrs={
                'units': '°C',
                'long_name': 'Sea Surface Temperature',
                'standard_name': 'sea_surface_temperature'
            }
        )

        # Save with encoding
        da.to_netcdf(outfile)
            #encoding={'sea_surface_temperature': {'zlib': True}})
        print(f"Saved to {outfile}")
        

    def __repr__(self):
        rstr = f'<RS_Healpix: nside={self.nside}, resol={self.pix_resol}deg'
        if self.filename is not None:
            rstr = f'{rstr}\n file={self.basename}'
        if self.variable is not None:
            rstr = f'{rstr}, var="{self.variable}"'
        rstr = f'{rstr}>'
        # Return
        return rstr