# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Python package for processing and analyzing oceanographic remote sensing data, with focus on Sea Surface Temperature (SST) and Sea Surface Height (SSH). Designed for both research and field deployment (e.g., active cruise support).

**Core Technology**: HEALPix hierarchical pixelization for spherical Earth data representation.

## Development Commands

### Installation
```bash
pip install -e .
```

### Testing
```bash
# Run all tests
pytest

# Run specific test module
pytest remote_sensing/tests/test_podaac.py

# Run with verbose output
pytest -v
```

### CLI Tools
```bash
# View NetCDF files interactively
rs_view_nc <file.nc> <variable_name>

# Operational workflows
python -m remote_sensing.operations.merged_sst_to_kmz
python -m remote_sensing.operations.merged_ssh_to_kmz
```

### Documentation
```bash
cd docs
pip install -r requirements.txt
sphinx-build -b html . _build/html
```

## Architecture

### Core Class: RS_Healpix (`healpix/rs_healpix.py`)

The central data abstraction representing hierarchical equal-area pixelization maps.

**Key Attributes**:
- `nside`: HEALPix NSIDE parameter (power of 2, determines resolution)
- `npix`: Total number of pixels (12 × nside²)
- `hp`: numpy masked array of HEALPix values
- `counts`: Per-pixel data contribution counts (for quality tracking)
- `time`, `filename`, `variable`: Metadata

**Factory Methods**:
- `from_dataset_file(filename, variable, resol_km)`: Load from NetCDF with automatic quality control
- `from_dataarray(data_array, nside)`: Convert xarray DataArray to HEALPix
- `from_list(rs_healpix_list)`: Average/merge multiple RS_Healpix objects

**Key Operations**:
- `fill_in(other_rs_healpix)`: Interpolate missing values from another HEALPix map
- `plot(vmin, vmax, cmap, projection)`: Visualize on globe using cartopy
- `save_to_nc(filename)`: Export to NetCDF

### Data Pipeline Flow

```
1. Download → 2. Quality Control → 3. HEALPix Mapping → 4. Visualization/Export

PODAAC/EarthAccess     netcdf/sst.py          healpix/rs_healpix.py    plotting/globe.py
    ↓                      ↓                          ↓                        ↓
local NetCDF files    quality masks          RS_Healpix object       matplotlib/cartopy
                      + unit conversion       (gridded data)          or KML/KMZ
```

### Module Organization

**`download/`** - Data acquisition from multiple sources
- `podaac.py`: PO.DAAC archive interface using podaac-data-subscriber
  - `grab_file_list(dataset_id, dt_past)`: Query files with temporal filtering
  - `download_files(file_list)`: Download with checksums
- `earthaccess.py`: NASA EarthData API interface with spatial/temporal filtering
  - `extract_spatial_extent()`: Handle polygons, rectangles, antimeridian crossing
  - `build_df()`: Create pandas DataFrame from granule collections
- `copernicus.py`: Copernicus Marine services
- `earthdata.py`: Authentication utilities

**`netcdf/`** - NetCDF file handling
- `sst.py`: SST-specific loading and quality control
  - `quality_control(dataset, variable, sensor)`: Sensor-specific QC (AMSR2, VIIRS, AHI)
  - `find_variable(dataset)`: Locate SST variable across naming conventions
- `utils.py`: Generic NetCDF utilities
  - `find_coord(dataset)`: Locate lat/lon coordinates (handles naming variations)
  - `gen_mask_for_dataset()`: Create quality masks from flags/thresholds

**`healpix/`** - HEALPix processing
- `rs_healpix.py`: Core RS_Healpix class (318 lines)
- `utils.py`: HEALPix utilities
  - `get_nside_from_angular_size(size_deg)`: Calculate NSIDE from resolution
  - `arrays_to_healpix(lons, lats, values, nside)`: Convert regular grid to HEALPix
  - `masked_in_box(hp_map, lon_range, lat_range)`: Spatial subsetting
- `combine.py`: Multi-map averaging with intelligent mask handling

**`plotting/`** - Visualization
- `globe.py`: Global map plotting with cartopy
  - `plot_lons_lats_vals(lons, lats, vals, projection)`: Core plotting primitive
  - `healpix_map()`: Dedicated HEALPix visualization
- `utils.py`: Cartography helpers (gridlines, fontsize, interactive viewing)

**`process/`** - Data processing
- `swot_ssh_utils.py`: SWOT SSH processing (1375 lines)
  - Bias correction, filtering, geostrophic velocity computation
  - Spectral analysis, along-track interpolation
  - Classes: `SSH_L2`, `unsmoothed`

**`operations/`** - End-to-end workflows
- `merged_sst_to_kmz.py`: Multi-source SST merging (AMSR2 + Himawari-09)
- `merged_ssh_to_kmz.py`: Multi-source SSH merging (AVISO + SWOT)
  - Both use JSON state management for reprocessing
  - Output KMZ files for Google Earth (field deployment)

**`kml.py`** - KML/KMZ generation for Google Earth
- `make_kml(hp_map, output_file)`: Create overlays from HEALPix
- `scatter_to_kml_advanced()`: Point cloud styling

**`io.py`** - Serialization utilities
- `savejson()`/`loadjson()`: JSON with gzip support
- `jsonify()`: Recursive JSON-friendly conversion

**`units.py`** - Unit conversions
- `kelvin_to_celsius()`: Temperature conversion preserving metadata

**`scripts/view_nc.py`** - Interactive NetCDF visualization CLI

## Key Design Patterns

1. **HEALPix as Central Data Structure**: Hierarchical equal-area pixelization enables multi-resolution analysis and natural spherical Earth representation. Masked arrays handle sparse/missing data efficiently.

2. **Flexible NetCDF Loading**: `netcdf/utils.find_coord()` and `netcdf/sst.find_variable()` handle multiple naming conventions across data sources (e.g., "sea_surface_temperature" vs "analysed_sst").

3. **Sensor-Specific Quality Control**: Each sensor (AMSR2, VIIRS, AHI) has dedicated QC thresholds in `netcdf/sst.quality_control()`. When adding new sensors, register them here.

4. **Multi-Source Data Fusion**: `RS_Healpix.from_list()` enables averaging multiple sources with intelligent mask handling (e.g., microwave + infrared SST).

5. **Field Deployment Ready**: JSON checkpointing (`operations/`) allows reprocessing without re-downloading. KMZ export enables offline Google Earth viewing on field devices.

## Important Implementation Notes

### Working with RS_Healpix

**Creating from NetCDF**:
```python
hp_map = RS_Healpix.from_dataset_file(
    'sst_file.nc',
    'sea_surface_temperature',
    resol_km=25  # Determines NSIDE automatically
)
```

**Merging Multiple Sources**:
```python
# Combine AMSR2 (microwave) + Himawari (IR)
merged = RS_Healpix.from_list([hp_amsr2, hp_himawari])

# Fill gaps from lower-priority source
merged.fill_in(hp_backup)
```

**Spatial Subsetting**:
```python
from remote_sensing.healpix.utils import masked_in_box

# Extract region
subset = masked_in_box(hp_map, lon_range=(-180, -120), lat_range=(30, 50))
```

### Quality Control

Quality control happens automatically in `RS_Healpix.from_dataset_file()` via `netcdf/sst.quality_control()`. When modifying:

- Temperature bounds: Typically -2°C to 40°C
- Sensor-specific flags: quality_level, l2p_flags (varies by sensor)
- The `sensor` parameter is inferred from filename/attributes

### Coordinate Handling

The package handles multiple coordinate naming conventions:
- Latitude: "lat", "latitude", "nav_lat"
- Longitude: "lon", "longitude", "nav_lon"

Use `netcdf/utils.find_coord()` when adding new coordinate systems.

### HEALPix Resolution Selection

Resolution is determined by NSIDE (power of 2):
- NSIDE=64: ~55 km/pixel
- NSIDE=128: ~27 km/pixel
- NSIDE=256: ~14 km/pixel
- NSIDE=512: ~7 km/pixel

Use `healpix/utils.get_nside_from_angular_size(resol_deg)` to calculate from desired resolution.

## Testing Strategy

Tests in `remote_sensing/tests/` are integration tests that make real API calls:
- `test_podaac.py`: PODAAC query and download
- Tests use current AMSR2 and Himawari data
- Minimal mocking (tests real data pipeline)

When adding tests, follow existing pattern of testing full workflows rather than isolated units.

## Common Pitfalls

1. **NSIDE Must Be Power of 2**: HEALPix requires NSIDE ∈ {1, 2, 4, 8, 16, 32, 64, 128, 256, 512, ...}

2. **Masked Arrays**: Always check `hp.mask` before operations. Use `numpy.ma` functions, not standard numpy.

3. **Antimeridian Crossing**: When working with Pacific data spanning 180°, use `earthaccess.extract_spatial_extent()` which handles polygon wrapping.

4. **Quality Flags Vary by Sensor**: Don't assume uniform quality flag names. Use sensor-specific logic in `netcdf/sst.quality_control()`.

5. **Coordinate Order**: HEALPix uses colatitude (0 at North Pole, π at South Pole). The package handles conversion internally via healpy.

## Dependencies

**Core**: numpy, scipy, xarray, pandas, healpy, cartopy, matplotlib, h5netcdf/netcdf4

**Data Access**: podaac-data-subscriber, earthaccess, copernicusmarine

**Utilities**: scikit-learn, scikit-image, shapely, simplekml, tqdm

Python 3.11+ required (uses modern type hints and f-strings).
