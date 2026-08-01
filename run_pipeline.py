"""
Standalone runner for the BHARAT Science Pipeline.

Usage:
    python run_pipeline.py --ground readings/NGC6881/test1.csv --sky readings/NGC6881/test2.csv --source readings/NGC6881/test3.csv --out processed_output.csv
"""

import argparse
from pathlib import Path
from bharat_science.pipeline import process_observation


def main():
    parser = argparse.ArgumentParser(description="BHARAT Science Pipeline CSV Processor")
    parser.add_argument("--ground", required=True, help="Path to Ground scan CSV file")
    parser.add_argument("--sky", required=True, help="Path to Sky scan CSV file")
    parser.add_argument("--source", required=True, help="Path to Source scan CSV file")
    parser.add_argument("--sky-temp", type=float, default=5.0, help="Sky temperature in K (default: 5.0)")
    parser.add_argument("--ground-temp", type=float, default=300.0, help="Ground temperature in K (default: 300.0)")
    parser.add_argument("--lat", type=float, default=28.6139, help="Observatory latitude in degrees")
    parser.add_argument("--lon", type=float, default=77.2090, help="Observatory longitude in degrees")
    parser.add_argument("--alt", type=float, default=216.0, help="Observatory altitude in meters")
    parser.add_argument("--source-coords", type=str, default="19 41 53.4 +50 31 31", help="Source coordinates (RA DEC sexagesimal)")
    parser.add_argument("--out", type=str, default="processed_output.csv", help="Output CSV path")

    args = parser.parse_args()

    print("Processing observation...")
    df = process_observation(
        ground_csv=args.ground,
        sky_csv=args.sky,
        source_csv=args.source,
        sky_temp_k=args.sky_temp,
        ground_temp_k=args.ground_temp,
        observatory_lat=args.lat,
        observatory_lon=args.lon,
        observatory_alt=args.alt,
        source_coords_str=args.source_coords,
    )

    output_path = Path(args.out)
    df.to_csv(output_path, index=False)
    print(f"Successfully processed {len(df)} frequency channels!")
    print(f"Results saved to: {output_path.resolve()}")
    print("\nPreview of processed data (first 5 rows):")
    print(df.head())


if __name__ == "__main__":
    main()
