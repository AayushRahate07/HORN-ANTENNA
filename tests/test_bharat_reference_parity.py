"""
Strict Parity Regression Suite.
Compares bharat_science package outputs directly against BHARAT (GUI.py) reference logic step-by-step
on real MilkyWay2 observation CSVs across all intermediate & final physical quantities.
"""

import datetime
import math
import unittest
import numpy as np
import pandas as pd
from PyAstronomy import pyasl

from bharat_science.pipeline import process_observation
from bharat_science.parser import parse_rtl_power_csv


class TestBharatReferenceParity(unittest.TestCase):

    def setUp(self):
        self.ground_path = "readings/MilkyWay2/btm1.csv"
        self.sky_path = "readings/MilkyWay2/up1.csv"
        self.source_path = "readings/MilkyWay2/center1.csv"
        self.sky_temp = 5.0
        self.ground_temp = 300.0
        self.lat = 28.6139
        self.lon = 77.2090
        self.alt = 216.0
        self.source_coords = "19 41 53.4 +50 31 31"

    def test_direct_bharat_reference_parity(self):
        # -------------------------------------------------------------
        # 1. Compute Reference Quantities directly via GUI.py formulas
        # -------------------------------------------------------------
        df_g = pd.read_csv(self.ground_path, header=None)
        df_k = pd.read_csv(self.sky_path, header=None)
        df_s = pd.read_csv(self.source_path, header=None)

        # Frequencies (GUI.py lines 90-92)
        x_start = df_g.iloc[0, 2] / 1e6
        x_stop = df_g.iloc[0, 3] / 1e6
        ref_freqs = np.linspace(x_start, x_stop, num=len(df_g.columns) - 6)

        # Power dBm -> Watts (GUI.py lines 93 & 131)
        y_g_dbm = df_g.iloc[0, 6:].values.astype(float)
        y_k_dbm = df_k.iloc[0, 6:].values.astype(float)
        y_s_dbm = df_s.iloc[0, 6:].values.astype(float)

        ref_power_g = (10 ** (y_g_dbm / 10)) / 1000
        ref_power_k = (10 ** (y_k_dbm / 10)) / 1000
        ref_power_s = (10 ** (y_s_dbm / 10)) / 1000

        # Receiver Temperature Tr (GUI.py lines 173-175)
        p1 = ref_power_g / ref_power_k
        with np.errstate(divide='ignore', invalid='ignore'):
            ref_tr = (self.sky_temp * p1 - self.ground_temp) / (1 - p1)

        # Source Temperature Ts (GUI.py lines 207-210)
        p2 = ref_power_g / ref_power_s
        with np.errstate(divide='ignore', invalid='ignore'):
            ref_ts = ((self.ground_temp + ref_tr) / p2) - ref_tr - self.sky_temp

        # Brightness Temperature T_BT (GUI.py lines 265-266)
        with np.errstate(divide='ignore', invalid='ignore'):
            ref_offset = (np.nanmean(ref_ts[:10]) + np.nanmean(ref_ts[-10:])) / 2
            ref_t_bt = ref_ts - ref_offset

        # Frequency -> Velocity (GUI.py lines 358-362)
        f0 = 1420.4057511
        c = 299792.458
        ref_v_raw = c * (1 - (ref_freqs / f0))

        # VLSR Correction (GUI.py lines 305-340 & 380-391)
        obs_ra_2000, obs_dec_2000 = pyasl.coordsSexaToDeg(self.source_coords)
        source_date_time_str = df_s.iloc[0, 0] + " " + df_s.iloc[0, 1]
        source_date_time = datetime.datetime.strptime(source_date_time_str, '%Y-%m-%d %H:%M:%S')
        jd = pyasl.jdcnv(source_date_time)
        corr, _ = pyasl.helcorr(self.lon, self.lat, self.alt, obs_ra_2000, obs_dec_2000, jd, debug=False)

        v_sun = 20.5
        sun_ra = math.radians(270.2)
        sun_dec = math.radians(28.7)
        obs_dec = math.radians(obs_dec_2000)
        obs_ra = math.radians(obs_ra_2000)

        a = math.cos(sun_dec) * math.cos(obs_dec)
        b = (math.cos(sun_ra) * math.cos(obs_ra)) + (math.sin(sun_ra) * math.sin(obs_ra))
        c_val = math.sin(sun_dec) * math.sin(obs_dec)
        v_rs = v_sun * ((a * b) + c_val)
        v_lsr = corr + v_rs
        ref_vlsr_return = -v_lsr
        ref_v_corrected = ref_v_raw - ref_vlsr_return

        # -------------------------------------------------------------
        # 2. Run Pipeline from package
        # -------------------------------------------------------------
        df_pkg = process_observation(
            ground_csv=self.ground_path,
            sky_csv=self.sky_path,
            source_csv=self.source_path,
            sky_temp_k=self.sky_temp,
            ground_temp_k=self.ground_temp,
            observatory_lat=self.lat,
            observatory_lon=self.lon,
            observatory_alt=self.alt,
            source_coords_str=self.source_coords,
        )

        # -------------------------------------------------------------
        # 3. Assert Strict Numerical Parity across ALL quantities
        # -------------------------------------------------------------
        np.testing.assert_allclose(df_pkg["Frequency_MHz"].values, ref_freqs, rtol=1e-12, atol=1e-12)
        np.testing.assert_allclose(df_pkg["Ground_Watts"].values, ref_power_g, rtol=1e-12, atol=1e-15)
        np.testing.assert_allclose(df_pkg["Sky_Watts"].values, ref_power_k, rtol=1e-12, atol=1e-15)
        np.testing.assert_allclose(df_pkg["Source_Watts"].values, ref_power_s, rtol=1e-12, atol=1e-15)
        np.testing.assert_allclose(df_pkg["Tr_Original_K"].values, ref_tr, rtol=1e-12, atol=1e-12)
        np.testing.assert_allclose(df_pkg["Ts_K"].values, ref_ts, rtol=1e-12, atol=1e-12)
        np.testing.assert_allclose(df_pkg["Brightness_Temp_K"].values, ref_t_bt, rtol=1e-12, atol=1e-12)
        np.testing.assert_allclose(df_pkg["Velocity_km_s"].values, ref_v_raw, rtol=1e-12, atol=1e-12)
        np.testing.assert_allclose(df_pkg["Velocity_Corrected_km_s"].values, ref_v_corrected, rtol=1e-12, atol=1e-12)


if __name__ == "__main__":
    unittest.main()
