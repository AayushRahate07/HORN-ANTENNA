"""
Temperature Calibration Module for Radio Astronomy processing.

Derivation & Equations:
1. Power Ratio P1 = P_ground / P_sky (in Watts)
   Receiver Temperature Tr = (T_sky * P1 - T_ground) / (1 - P1)

2. Optional Baseline Correction for Tr:
   Piecewise linear replacement between (x1, y1) and (x2, y2) over [x_min, x_max].

3. Power Ratio P2 = P_ground / P_source (in Watts)
   Source Temperature Ts = ((T_ground + Tr) / P2) - Tr - T_sky

4. Brightness Temperature T_BT:
   offset = (mean(Ts[:10]) + mean(Ts[-10:])) / 2
   T_BT = Ts - offset
"""

from typing import Optional, Tuple
import numpy as np


def calculate_receiver_temperature(
    power_ground_watts: np.ndarray,
    power_sky_watts: np.ndarray,
    sky_temp_k: float = 5.0,
    ground_temp_k: float = 300.0,
) -> np.ndarray:
    """
    Calculate the uncorrected receiver temperature (Tr) in Kelvin.
    """
    with np.errstate(divide='ignore', invalid='ignore'):
        p1 = power_ground_watts / power_sky_watts
        tr = (sky_temp_k * p1 - ground_temp_k) / (1.0 - p1)
    return tr


def apply_tr_linear_correction(
    freqs_mhz: np.ndarray,
    tr: np.ndarray,
    point1: Tuple[float, float],
    point2: Tuple[float, float],
) -> np.ndarray:
    """
    Apply a manual linear interpolation baseline correction to Tr between point1 and point2.
    """
    x1, y1 = point1
    x2, y2 = point2

    if x1 == x2:
        raise ValueError("point1 and point2 cannot have the same frequency (x-coordinate).")

    m = (y2 - y1) / (x2 - x1)
    b = y1 - m * x1

    x_min = min(x1, x2)
    x_max = max(x1, x2)

    tr_corrected = tr.copy()
    mask = (freqs_mhz >= x_min) & (freqs_mhz <= x_max)
    tr_corrected[mask] = m * freqs_mhz[mask] + b

    return tr_corrected


def calculate_source_temperature(
    power_ground_watts: np.ndarray,
    power_source_watts: np.ndarray,
    tr: np.ndarray,
    sky_temp_k: float = 5.0,
    ground_temp_k: float = 300.0,
) -> np.ndarray:
    """
    Calculate the source temperature (Ts) in Kelvin.
    """
    with np.errstate(divide='ignore', invalid='ignore'):
        p2 = power_ground_watts / power_source_watts
        ts = ((ground_temp_k + tr) / p2) - tr - sky_temp_k
    return ts


def calculate_brightness_temperature(ts: np.ndarray) -> Tuple[np.ndarray, float]:
    """
    Calculate brightness temperature (T_BT) by subtracting baseline offset.
    Returns (t_bt, baseline_offset).
    """
    if len(ts) < 20:
        raise ValueError("Source temperature array must have at least 20 bins to compute baseline offset.")

    with np.errstate(divide='ignore', invalid='ignore'):
        offset = (np.nanmean(ts[:10]) + np.nanmean(ts[-10:])) / 2.0
        t_bt = ts - offset
    return t_bt, offset
