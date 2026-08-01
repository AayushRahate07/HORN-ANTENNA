# HORN-ANTENNA

# BHARAT H-I Analysis

A browser-based workstation for processing and visualizing 21 cm neutral hydrogen (H I) radio astronomy observations.

This project implements the complete H I analysis pipeline including receiver temperature calibration, brightness temperature estimation, Doppler velocity calculation, VLSR correction, and interactive spectral visualization.

---

## Features

- Multiple source observation support
- Ground / Sky / Source calibration
- Receiver temperature (Y-factor) calibration
- Brightness temperature estimation
- Velocity & VLSR correction
- Interactive Plotly visualizations
- CSV export
- FastAPI backend
- Single-page responsive web interface

---

## Tech Stack

### Backend
- Python 3.11+
- FastAPI
- Uvicorn
- NumPy
- Pandas
- Astropy

### Frontend
- HTML
- CSS
- JavaScript
- Plotly.js

---

## Project Structure

```
bharat-hi-analysis/
│
├── app/
│   ├── main.py
│   ├── bharat_science/
│   ├── static/
│   └── templates/
│
├── requirements.txt
└── README.md
```

---

# Installation

Clone the repository.

```bash
git clone https://github.com/<your-username>/bharat-hi-analysis.git
cd bharat-hi-analysis
```

Create a virtual environment.

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies.

```bash
pip install -r requirements.txt
```

---

# Running the Application

Navigate to the application directory.

```bash
cd app
```

Launch the FastAPI server.

```bash
python -m uvicorn main:app --reload
```

Open your browser.

```
http://127.0.0.1:8000
```

---

# Observation Workflow

1. Upload a Ground calibration scan.
2. Upload a Sky calibration scan.
3. Upload one or more Source scans.
4. Enter:
   - Sky Temperature
   - Ground Temperature
   - Observatory Latitude
   - Observatory Longitude
   - Observatory Altitude
   - Source Right Ascension / Declination
5. Click **PROCESS OBSERVATION**.
6. Explore:
   - Velocity Spectrum
   - Temperature Calibration
   - Power Spectrum
7. Export calibrated observations as CSV.

---

# Input Files

Accepted format:

```
CSV
```

Current workflow expects:

- 1 Ground scan
- 1 Sky scan
- 1..N Source scans

All selected source observations are calibrated using the same Ground/Sky reference pair.

---

# Outputs

The application generates:

- Receiver Temperature (Tr)
- Source Temperature (Ts)
- Brightness Temperature (Tb)
- Raw Radial Velocity
- VLSR Corrected Velocity
- Interactive Spectral Plots
- Calibrated CSV files

---

# Roadmap

- Live RTL-SDR acquisition
- Observation session management
- FITS support
- Peak detection
- Automatic H I line fitting
- Observation database
- Multi-session comparison dashboard

---

# License

MIT License

---

## Acknowledgements

The scientific workflow is based on the BHARAT Horn Antenna H I analysis methodology developed by Ashish Mhase. This project is an independent browser-based implementation focused on improving accessibility, modularity, and user experience while reproducing the underlying analysis pipeline.
