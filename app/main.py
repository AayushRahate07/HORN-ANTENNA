"""
FastAPI Scientific Server for BHARAT Radio Astronomy Pipeline.
"""

import tempfile
from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
import pandas as pd
import numpy as np

from bharat_science.pipeline import process_observation

app = FastAPI(title="BHARAT Science Engine", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check():
    return {"status": "ok", "engine": "BHARAT Science Pipeline v0.1.0"}


@app.post("/api/process")
async def process_scans(
    ground_file: UploadFile = File(...),
    sky_file: UploadFile = File(...),
    source_files: List[UploadFile] = File(...),

    sky_temp_k: float = Form(5.0),
    ground_temp_k: float = Form(300.0),

    observatory_lat: Optional[float] = Form(28.6139),
    observatory_lon: Optional[float] = Form(77.2090),
    observatory_alt: Optional[float] = Form(216.0),

    source_coords_str: Optional[str] = Form(
        "19 41 53.4 +50 31 31"
    ),
):

    with tempfile.TemporaryDirectory() as tmpdir:

        tmp_path = Path(tmpdir)

        ground_path = tmp_path / "ground.csv"
        sky_path = tmp_path / "sky.csv"

        # Shared calibration scans
        with open(ground_path, "wb") as f:
            f.write(await ground_file.read())

        with open(sky_path, "wb") as f:
            f.write(await sky_file.read())

        observations = []

        # Process each source independently
        for index, source_file in enumerate(source_files):

            source_path = tmp_path / f"source_{index}.csv"

            with open(source_path, "wb") as f:
                f.write(await source_file.read())

            try:

                df = process_observation(
                    ground_csv=ground_path,
                    sky_csv=sky_path,
                    source_csv=source_path,

                    sky_temp_k=sky_temp_k,
                    ground_temp_k=ground_temp_k,

                    observatory_lat=observatory_lat,
                    observatory_lon=observatory_lon,
                    observatory_alt=observatory_alt,

                    source_coords_str=source_coords_str,
                )

            except Exception as e:

                raise HTTPException(
                    status_code=400,
                    detail=f"{source_file.filename}: {str(e)}"
                )

            df_clean = (
                df
                .replace([np.inf, -np.inf], np.nan)
                .fillna(0.0)
            )

            observations.append({

                "name":
                    source_file.filename,

                "channels":
                    len(df_clean),

                "freq_mhz":
                    df_clean["Frequency_MHz"].tolist(),

                "power_ground_watts":
                    df_clean["Ground_Watts"].tolist(),

                "power_sky_watts":
                    df_clean["Sky_Watts"].tolist(),

                "power_source_watts":
                    df_clean["Source_Watts"].tolist(),

                "tr_original_k":
                    df_clean["Tr_Original_K"].tolist(),

                "tr_corrected_k":
                    df_clean["Tr_Corrected_K"].tolist(),

                "ts_k":
                    df_clean["Ts_K"].tolist(),

                "brightness_temp_k":
                    df_clean["Brightness_Temp_K"].tolist(),

                "velocity_raw_kms":
                    df_clean["Velocity_km_s"].tolist(),

                "velocity_corrected_kms":
                    df_clean["Velocity_Corrected_km_s"].tolist(),
            })

        return {
            "observation_count": len(observations),
            "observations": observations,
        }

# Serve static web frontend
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/", response_class=HTMLResponse)
    def read_root():
        return FileResponse(static_dir / "index.html")
