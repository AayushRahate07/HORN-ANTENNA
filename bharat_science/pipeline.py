"""
Top-level Pipeline Orchestrator for BHARAT Radio Astronomy Processing.
"""

import datetime
from pathlib import Path
from typing import Optional, Tuple, Union
import pandas as pd

from .parser import parse_rtl_power_csv, ScanData
from .calibration import (
    calculate_receiver_temperature,
    apply_tr_linear_correction,
    calculate_source_temperature,
    calculate_brightness_temperature,
)
from .velocity import (
    freq_to_velocity,
    parse_sexa_coords,
    calculate_vlsr_correction,
    apply_vlsr_correction,
)


def process_observation(
    ground_csv: Union[str, Path],
    sky_csv: Union[str, Path],
    source_csv: Union[str, Path],
    sky_temp_k: float = 5.0,
    ground_temp_k: float = 300.0,
    tr_baseline_points: Optional[Tuple[Tuple[float, float], Tuple[float, float]]] = None,
    observatory_lat: Optional[float] = None,
    observatory_lon: Optional[float] = None,
    observatory_alt: Optional[float] = None,
    source_coords_str: Optional[str] = None,
    override_datetime: Optional[datetime.datetime] = None,
) -> pd.DataFrame:
    """
    Run the end-to-end science pipeline on Ground, Sky, and Source scans.
    """
    ground = parse_rtl_power_csv(ground_csv)
    sky = parse_rtl_power_csv(sky_csv)
    source = parse_rtl_power_csv(source_csv)

    # Validate channel length parity across inputs
    if not (len(ground.freqs_mhz) == len(sky.freqs_mhz) == len(source.freqs_mhz)):
        raise ValueError("Frequency array lengths do not match between Ground, Sky, and Source scans.")

    freqs_mhz = ground.freqs_mhz

    # 1. Receiver Temperature Tr
    tr_original = calculate_receiver_temperature(
        power_ground_watts=ground.power_watts,
        power_sky_watts=sky.power_watts,
        sky_temp_k=sky_temp_k,
        ground_temp_k=ground_temp_k,
    )

    if tr_baseline_points is not None:
        p1, p2 = tr_baseline_points
        tr_corrected = apply_tr_linear_correction(freqs_mhz, tr_original, p1, p2)
    else:
        tr_corrected = tr_original.copy()

    # 2. Source Temperature Ts
    ts = calculate_source_temperature(
        power_ground_watts=ground.power_watts,
        power_source_watts=source.power_watts,
        tr=tr_corrected,
        sky_temp_k=sky_temp_k,
        ground_temp_k=ground_temp_k,
    )

    # 3. Brightness Temperature T_BT
    t_bt, _ = calculate_brightness_temperature(ts)

    # 4. Raw Radial Velocity
    velocity_raw = freq_to_velocity(freqs_mhz)

    # 5. VLSR Correction
    vlsr_corr = 0.0
    if (
        observatory_lat is not None
        and observatory_lon is not None
        and observatory_alt is not None
        and source_coords_str is not None
    ):
        obs_dt = override_datetime if override_datetime is not None else source.timestamp
        ra_deg, dec_deg = parse_sexa_coords(source_coords_str)
        vlsr_corr = calculate_vlsr_correction(
            longitude=observatory_lon,
            latitude=observatory_lat,
            altitude=observatory_alt,
            ra_deg=ra_deg,
            dec_deg=dec_deg,
            obs_datetime=obs_dt,
        )

    velocity_corrected = apply_vlsr_correction(velocity_raw, vlsr_corr)

    df_out = pd.DataFrame({
        "Frequency_MHz": freqs_mhz,
        "Ground_Watts": ground.power_watts,
        "Sky_Watts": sky.power_watts,
        "Source_Watts": source.power_watts,
        "Tr_Original_K": tr_original,
        "Tr_Corrected_K": tr_corrected,
        "Ts_K": ts,
        "Brightness_Temp_K": t_bt,
        "Velocity_km_s": velocity_raw,
        "Velocity_Corrected_km_s": velocity_corrected,
    })

    return df_out
