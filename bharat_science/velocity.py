"""
Velocity Conversion & VLSR Correction Module.

Derivation & Equations:
1. Radial Velocity v (km/s):
   v = c * (1 - (f / f0))
   where f0 = 1420.4057511 MHz (neutral hydrogen 21cm line rest frequency)
   c = 299792.458 km/s (speed of light)

2. Local Standard of Rest (LSR) Correction:
   - Barycentric/Helicentric correction `corr` obtained via PyAstronomy.pyasl.helcorr
     (or calculated via standard orbital mechanics).
   - Solar apex velocity correction v_rs:
     v_sun = 20.5 km/s
     apex RA = 270.2 deg, DEC = 28.7 deg
     v_rs = v_sun * (cos(dec_sun)*cos(dec_obs)*cos(ra_sun - ra_obs) + sin(dec_sun)*sin(dec_obs))
   - v_lsr_total = corr + v_rs
   - v_corrected = v + v_lsr_total
"""

import datetime
import math
from typing import Tuple, Union
import numpy as np

try:
    from PyAstronomy import pyasl
    HAS_PYASTRONOMY = True
except ImportError:
    HAS_PYASTRONOMY = False


REST_FREQ_MHZ = 1420.4057511  # H-I line frequency in MHz
SPEED_OF_LIGHT_KMS = 299792.458  # Speed of light in km/s


def freq_to_velocity(freqs_mhz: np.ndarray, f0: float = REST_FREQ_MHZ, c: float = SPEED_OF_LIGHT_KMS) -> np.ndarray:
    """
    Convert frequency array (MHz) to uncorrected radial velocity (km/s).
    v = c * (1 - (f / f0))
    """
    return c * (1.0 - (freqs_mhz / f0))


def parse_sexa_coords(coords_str: str) -> Tuple[float, float]:
    """
    Parse sexagesimal RA DEC string (e.g. '19 41 53.4 +50 31 31' or '19:41:53.4 +50:31:31') into degrees.
    """
    if HAS_PYASTRONOMY:
        return pyasl.coordsSexaToDeg(coords_str)
    
    # Custom parser fallback for "HH MM SS DD MM SS"
    parts = coords_str.strip().split()
    if len(parts) != 6:
        raise ValueError(f"Invalid sexagesimal string format: '{coords_str}'. Expected 'RA_h RA_m RA_s DEC_d DEC_m DEC_s'")
    
    ra_h, ra_m, ra_s = float(parts[0]), float(parts[1]), float(parts[2])
    ra_deg = (ra_h + ra_m / 60.0 + ra_s / 3600.0) * 15.0

    dec_sign = -1.0 if parts[3].startswith('-') else 1.0
    dec_d = abs(float(parts[3]))
    dec_m, dec_s = float(parts[4]), float(parts[5])
    dec_deg = dec_sign * (dec_d + dec_m / 60.0 + dec_s / 3600.0)

    return ra_deg, dec_deg


def calculate_solar_apex_velocity(ra_deg: float, dec_deg: float, v_sun: float = 20.5, apex_ra_deg: float = 270.2, apex_dec_deg: float = 28.7) -> float:
    """
    Calculate peculiar solar motion velocity relative to LSR (km/s).
    """
    sun_ra = math.radians(apex_ra_deg)
    sun_dec = math.radians(apex_dec_deg)
    obs_ra = math.radians(ra_deg)
    obs_dec = math.radians(dec_deg)

    a = math.cos(sun_dec) * math.cos(obs_dec)
    b = (math.cos(sun_ra) * math.cos(obs_ra)) + (math.sin(sun_ra) * math.sin(obs_ra))
    c = math.sin(sun_dec) * math.sin(obs_dec)

    return v_sun * ((a * b) + c)


def calculate_vlsr_correction(
    longitude: float,
    latitude: float,
    altitude: float,
    ra_deg: float,
    dec_deg: float,
    obs_datetime: datetime.datetime,
) -> float:
    """
    Calculate the total LSR velocity correction in km/s (Barycentric + Solar Apex).
    v_lsr = helcorr + v_solar_apex
    """
    if not HAS_PYASTRONOMY:
        raise RuntimeError("PyAstronomy is required to compute barycentric helcorr.")

    jd = pyasl.jdcnv(obs_datetime)
    corr, _ = pyasl.helcorr(longitude, latitude, altitude, ra_deg, dec_deg, jd, debug=False)
    v_rs = calculate_solar_apex_velocity(ra_deg, dec_deg)

    return corr + v_rs


def apply_vlsr_correction(velocity: np.ndarray, vlsr_corr: float) -> np.ndarray:
    """
    Apply VLSR correction to velocity array.
    v_corrected = v + vlsr_corr
    """
    return velocity + vlsr_corr
