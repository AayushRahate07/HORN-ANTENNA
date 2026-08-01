"""
Pytest Suite to verify numerical parity against BHARAT reference calculations.
"""

import math
import datetime
import numpy as np
import pandas as pd
import pytest

from bharat_science.parser import parse_rtl_power_csv, dbm_to_watts
from bharat_science.calibration import (
    calculate_receiver_temperature,
    apply_tr_linear_correction,
    calculate_source_temperature,
    calculate_brightness_temperature,
)
from bharat_science.velocity import (
    freq_to_velocity,
    parse_sexa_coords,
    calculate_solar_apex_velocity,
    calculate_vlsr_correction,
    apply_vlsr_correction,
)
from bharat_science.pipeline import process_observation


def test_dbm_to_watts_parity():
    dbm_input = np.array([-46.09, 0.0, 10.0, -100.0])
    # Reference formula from GUI.py: (10 ** (y_data / 10)) / 1000
    expected_watts = (10.0 ** (dbm_input / 10.0)) / 1000.0
    actual_watts = dbm_to_watts(dbm_input)
    np.testing.assert_allclose(actual_watts, expected_watts, rtol=1e-12, atol=1e-15)


def test_receiver_temp_parity():
    ground_watts = np.array([1e-7, 1.2e-7, 0.9e-7])
    sky_watts = np.array([5e-8, 6e-8, 4.5e-8])
    sky_temp = 5.0
    ground_temp = 300.0

    # Reference formula from GUI.py line 174-175:
    # p1 = ground_data / sky_data
    # Tr_original = (sky_temp * p1 - ground_temp) / (1 - p1)
    p1 = ground_watts / sky_watts
    expected_tr = (sky_temp * p1 - ground_temp) / (1.0 - p1)

    actual_tr = calculate_receiver_temperature(ground_watts, sky_watts, sky_temp, ground_temp)
    np.testing.assert_allclose(actual_tr, expected_tr, rtol=1e-12, atol=1e-12)


def test_source_temp_parity():
    ground_watts = np.array([1e-7, 1.2e-7, 0.9e-7])
    source_watts = np.array([8e-8, 9e-8, 7.5e-8])
    tr = np.array([200.0, 210.0, 195.0])
    sky_temp = 5.0
    ground_temp = 300.0

    # Reference formula from GUI.py line 208-210:
    # p2 = ground_data / source_data
    # Ts = ((ground_temp + Tr) / p2) - Tr - sky_temp
    p2 = ground_watts / source_watts
    expected_ts = ((ground_temp + tr) / p2) - tr - sky_temp

    actual_ts = calculate_source_temperature(ground_watts, source_watts, tr, sky_temp, ground_temp)
    np.testing.assert_allclose(actual_ts, expected_ts, rtol=1e-12, atol=1e-12)


def test_brightness_temp_parity():
    # Construct synthetic Ts vector of 50 elements
    ts = np.linspace(10, 50, 50) + np.sin(np.linspace(0, 3.14, 50)) * 5
    
    # Reference formula from GUI.py line 265-266:
    # offset = (Ts[:10].mean() + Ts[-10:].mean()) / 2
    # brightness_temp = Ts - offset
    expected_offset = (ts[:10].mean() + ts[-10:].mean()) / 2.0
    expected_t_bt = ts - expected_offset

    actual_t_bt, actual_offset = calculate_brightness_temperature(ts)
    assert actual_offset == pytest.approx(expected_offset, rel=1e-12)
    np.testing.assert_allclose(actual_t_bt, expected_t_bt, rtol=1e-12, atol=1e-12)


def test_radial_velocity_parity():
    freqs_mhz = np.array([1419.405751, 1420.4057511, 1421.405751])
    f0 = 1420.4057511
    c = 299792.458

    # Reference formula from GUI.py line 362:
    # v = c * (1 - (f / f0))
    expected_v = c * (1.0 - (freqs_mhz / f0))

    actual_v = freq_to_velocity(freqs_mhz, f0, c)
    np.testing.assert_allclose(actual_v, expected_v, rtol=1e-12, atol=1e-12)


def test_solar_apex_velocity_parity():
    obs_ra_2000 = 295.4725  # degrees
    obs_dec_2000 = 50.5253  # degrees

    # Reference formula from GUI.py line 326-336:
    v_sun = 20.5
    sun_ra = math.radians(270.2)
    sun_dec = math.radians(28.7)
    obs_dec = math.radians(obs_dec_2000)
    obs_ra = math.radians(obs_ra_2000)

    a = math.cos(sun_dec) * math.cos(obs_dec)
    b = (math.cos(sun_ra) * math.cos(obs_ra)) + (math.sin(sun_ra) * math.sin(obs_ra))
    c = math.sin(sun_dec) * math.sin(obs_dec)
    expected_v_rs = v_sun * ((a * b) + c)

    actual_v_rs = calculate_solar_apex_velocity(obs_ra_2000, obs_dec_2000)
    assert actual_v_rs == pytest.approx(expected_v_rs, rel=1e-12)


def test_full_pipeline_with_real_files():
    ground_path = "readings/NGC6881/test1.csv"
    sky_path = "readings/NGC6881/test2.csv"
    source_path = "readings/NGC6881/test3.csv"

    df = process_observation(
        ground_csv=ground_path,
        sky_csv=sky_path,
        source_csv=source_path,
        sky_temp_k=5.0,
        ground_temp_k=300.0,
        observatory_lat=28.6139,
        observatory_lon=77.2090,
        observatory_alt=216.0,
        source_coords_str="19 41 53.4 +50 31 31",
    )

    assert not df.empty
    assert len(df) == 256  # 256 channels in sample test1.csv
    assert "Brightness_Temp_K" in df.columns
    assert "Velocity_Corrected_km_s" in df.columns
    assert not df["Brightness_Temp_K"].isna().any()
    assert not df["Velocity_Corrected_km_s"].isna().any()
