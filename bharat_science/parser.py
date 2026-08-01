"""
CSV Data Parser for rtl_power spectrum recordings.
"""

from dataclasses import dataclass
import datetime
from pathlib import Path
from typing import Union
import numpy as np
import pandas as pd


@dataclass
class ScanData:
    timestamp: datetime.datetime
    start_freq_mhz: float
    stop_freq_mhz: float
    freqs_mhz: np.ndarray
    power_dbm: np.ndarray
    power_watts: np.ndarray


def dbm_to_watts(power_dbm: np.ndarray) -> np.ndarray:
    """
    Convert power from dBm (decibel-milliwatts) to Watts.
    P(W) = (10 ^ (P(dBm) / 10)) / 1000
    """
    return (10.0 ** (power_dbm / 10.0)) / 1000.0


def parse_rtl_power_csv(file_path: Union[str, Path]) -> ScanData:
    """
    Parse an rtl_power CSV file into a ScanData object.
    
    Expected CSV row format:
    col 0: Date (YYYY-MM-DD)
    col 1: Time (HH:MM:SS)
    col 2: Start Freq (Hz)
    col 3: Stop Freq (Hz)
    col 4: Bin Size (Hz)
    col 5: Number of samples
    col 6..N: Power values in dBm per frequency bin
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"CSV file not found: {file_path}")

    df = pd.read_csv(path, header=None)
    if df.empty or df.shape[1] < 7:
        raise ValueError(f"Invalid rtl_power CSV structure in file: {file_path}")

    date_str = str(df.iloc[0, 0]).strip()
    time_str = str(df.iloc[0, 1]).strip()
    timestamp_str = f"{date_str} {time_str}"
    timestamp = datetime.datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')

    start_freq_mhz = float(df.iloc[0, 2]) / 1e6
    stop_freq_mhz = float(df.iloc[0, 3]) / 1e6

    num_bins = df.shape[1] - 6
    freqs_mhz = np.linspace(start_freq_mhz, stop_freq_mhz, num=num_bins)

    power_dbm = df.iloc[0, 6:].values.astype(float)
    power_watts = dbm_to_watts(power_dbm)

    return ScanData(
        timestamp=timestamp,
        start_freq_mhz=start_freq_mhz,
        stop_freq_mhz=stop_freq_mhz,
        freqs_mhz=freqs_mhz,
        power_dbm=power_dbm,
        power_watts=power_watts,
    )
