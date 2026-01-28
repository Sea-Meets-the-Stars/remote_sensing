"""
Tests for MODIS Aqua L2 ocean color functionality.

These are integration tests that require:
1. EarthData login credentials
2. Internet connection to OB.DAAC
3. Sufficient disk space for downloading test files
"""

import pytest
import numpy as np
import os

from remote_sensing.download import earthaccess as ea
from remote_sensing.netcdf import oc


@pytest.fixture(scope="module")
def earthdata_login():
    """Login to EarthData (required for all tests)."""
    import earthaccess
    try:
        earthaccess.login()
        return True
    except Exception as e:
        pytest.skip(f"EarthData login failed: {e}")


def test_query_modis_oc_standard(earthdata_login):
    """Test querying MODIS L2 OC standard processing."""
    granules = ea.query_modis_oc(
        time_range=('2024-01-15', '2024-01-16'),
        bbox=(127, 18, 134, 23),  # Japan region
        nrt=False,
        verbose=True
    )

    assert granules is not None
    assert len(granules) > 0
    print(f"Found {len(granules)} standard MODIS L2 OC granules")


def test_query_modis_oc_nrt(earthdata_login):
    """Test querying MODIS L2 OC near-real-time."""
    granules = ea.query_modis_oc(
        time_range=('2024-01-15', '2024-01-16'),
        bbox=(127, 18, 134, 23),
        cloud_cover=(0, 50),
        nrt=True,
        verbose=True
    )

    assert granules is not None
    print(f"Found {len(granules)} NRT MODIS L2 OC granules")


def test_query_with_cloud_filter(earthdata_login):
    """Test querying with cloud cover filter."""
    # Low cloud cover
    granules_clear = ea.query_modis_oc(
        time_range=('2024-01-15', '2024-01-16'),
        bbox=(127, 18, 134, 23),
        cloud_cover=(0, 20),
        verbose=True
    )

    # High cloud cover allowed
    granules_all = ea.query_modis_oc(
        time_range=('2024-01-15', '2024-01-16'),
        bbox=(127, 18, 134, 23),
        cloud_cover=(0, 100),
        verbose=True
    )

    # Clear sky should have fewer granules than all sky
    assert len(granules_clear) <= len(granules_all)
    print(f"Clear: {len(granules_clear)}, All: {len(granules_all)}")


@pytest.mark.skip(reason="Requires download - enable manually")
def test_download_modis_oc(earthdata_login, tmp_path):
    """Test downloading MODIS L2 OC file (skipped by default)."""
    # Query one granule
    granules = ea.query_modis_oc(
        time_range=('2024-01-15', '2024-01-15T01:00:00'),
        bbox=(127, 18, 134, 23),
        verbose=True
    )

    if len(granules) == 0:
        pytest.skip("No granules found for test period")

    # Download only first granule
    files = ea.download_modis_oc(
        granules[:1],
        download_dir=str(tmp_path),
        verbose=True
    )

    assert len(files) == 1
    assert os.path.exists(files[0])
    assert files[0].endswith('.nc')

    # Try to load it
    rrs_dict, l2_flags, lat, lon, time = oc.load(files[0], verbose=True)

    assert rrs_dict is not None
    assert l2_flags is not None
    assert lat is not None
    assert lon is not None
    assert time is not None

    print(f"Downloaded and loaded: {os.path.basename(files[0])}")
    print(f"  Rrs bands: {list(rrs_dict.keys())} nm")
    print(f"  Shape: {lat.shape}")
    print(f"  Time: {time}")


def test_rrs_variables():
    """Test Rrs variable naming."""
    wavelengths = oc.get_wavelength_array()

    assert len(wavelengths) == 10
    assert wavelengths[0] == 412
    assert wavelengths[-1] == 678

    # Check variable naming
    expected_vars = [f'Rrs_{wl}' for wl in wavelengths]
    assert expected_vars[0] == 'Rrs_412'
    assert expected_vars[-1] == 'Rrs_678'


def test_l2_flags():
    """Test L2 flag definitions and checking."""
    # Create dummy flags
    l2_flags = np.zeros((100, 100), dtype=np.uint32)

    # Set ATMFAIL flag (bit 0)
    l2_flags[10, 10] = 1 << 0

    # Set LAND flag (bit 1)
    l2_flags[20, 20] = 1 << 1

    # Set both ATMFAIL and LAND
    l2_flags[30, 30] = (1 << 0) | (1 << 1)

    # Check flags
    atmfail_mask = oc.check_flag(l2_flags, 'ATMFAIL')
    assert atmfail_mask[10, 10] == True
    assert atmfail_mask[20, 20] == False
    assert atmfail_mask[30, 30] == True

    land_mask = oc.check_flag(l2_flags, 'LAND')
    assert land_mask[10, 10] == False
    assert land_mask[20, 20] == True
    assert land_mask[30, 30] == True


def test_quality_mask():
    """Test quality mask creation."""
    # Create dummy flags with various issues
    l2_flags = np.zeros((100, 100), dtype=np.uint32)

    # Set ATMFAIL in one region
    l2_flags[:10, :] = 1 << oc.L2_FLAGS['ATMFAIL']

    # Set LAND in another region
    l2_flags[20:30, :] = 1 << oc.L2_FLAGS['LAND']

    # Set CLDICE in another region
    l2_flags[40:50, :] = 1 << oc.L2_FLAGS['CLDICE']

    # Create quality mask
    mask = oc.create_quality_mask(l2_flags, verbose=True)

    # Check that flagged regions are masked
    assert np.all(mask[:10, :] == True)  # ATMFAIL region
    assert np.all(mask[20:30, :] == True)  # LAND region
    assert np.all(mask[40:50, :] == True)  # CLDICE region

    # Check that clean region is not masked
    assert np.all(mask[60:70, :] == False)


def test_extract_spectrum():
    """Test extracting Rrs spectrum at a pixel."""
    # Create dummy Rrs data
    wavelengths = oc.get_wavelength_array()
    rrs_dict = {}

    for wl in wavelengths:
        # Create synthetic spectrum (higher Rrs at shorter wavelengths)
        rrs_dict[wl] = np.ones((100, 100)) * (600.0 / wl) * 0.01

    # Extract spectrum at a pixel
    wl_out, rrs_out = oc.extract_rrs_spectrum(rrs_dict, 50, 50)

    assert len(wl_out) == 10
    assert len(rrs_out) == 10
    assert np.all(wl_out == wavelengths)

    # Check that spectrum decreases with wavelength (as designed)
    assert rrs_out[0] > rrs_out[-1]


def test_conservative_vs_permissive_masking():
    """Test different masking strategies."""
    # Create flags with PRODWARN (bit 2) set everywhere
    l2_flags = np.ones((100, 100), dtype=np.uint32) * (1 << oc.L2_FLAGS['PRODWARN'])

    # Conservative masking (includes PRODWARN implicitly via DEFAULT_MASK_FLAGS)
    # Actually, PRODWARN is not in DEFAULT_MASK_FLAGS, so let's test with ATMFAIL
    l2_flags = np.ones((100, 100), dtype=np.uint32) * (1 << oc.L2_FLAGS['ATMFAIL'])

    conservative_mask = oc.create_quality_mask(l2_flags)

    # Permissive masking (only critical flags)
    permissive_mask = oc.create_quality_mask(
        l2_flags,
        mask_flags=['ATMFAIL', 'LAND', 'CLDICE']
    )

    # Both should mask ATMFAIL
    assert np.all(conservative_mask == True)
    assert np.all(permissive_mask == True)

    # Now test with PRODWARN (not in permissive list)
    l2_flags = np.ones((100, 100), dtype=np.uint32) * (1 << oc.L2_FLAGS['HISOLZEN'])

    conservative_mask = oc.create_quality_mask(l2_flags)
    permissive_mask = oc.create_quality_mask(
        l2_flags,
        mask_flags=['ATMFAIL', 'LAND', 'CLDICE']
    )

    # Conservative should mask HISOLZEN, permissive should not
    assert np.sum(conservative_mask) > np.sum(permissive_mask)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
