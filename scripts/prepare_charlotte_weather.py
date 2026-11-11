"""Extract the observed 2024–25 Charlotte winter from NOAA Global Hourly.

The two source CSVs are NOAA station 72314013881 (Charlotte Douglas airport).
Download links are documented in docs/winter_reliability.md. This script keeps
quality-coded observations, averages multiple observations within an hour, and
interpolates only short gaps of at most four hours. It writes exactly 2,160
hourly values for December 2024 through February 2025, Eastern Standard Time.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
WEATHER = ROOT / "data" / "weather"
RAW_FILES = [
    WEATHER / "charlotte_douglas_noaa_2024.csv",
    WEATHER / "charlotte_douglas_noaa_2025.csv",
]
OUTPUT = WEATHER / "charlotte_winter_2024_25_hourly.csv"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def longest_gap(mask: pd.Series) -> int:
    current = longest = 0
    for missing in mask:
        current = current + 1 if missing else 0
        longest = max(longest, current)
    return longest


def main() -> None:
    for path in RAW_FILES:
        if not path.exists():
            raise FileNotFoundError(f"Download the NOAA source file first: {path}")

    raw = pd.concat(
        [
            pd.read_csv(path, usecols=["STATION", "DATE", "TMP"], dtype=str)
            for path in RAW_FILES
        ],
        ignore_index=True,
    )
    if set(raw.STATION.dropna()) != {"72314013881"}:
        raise ValueError("Source files are not solely Charlotte Douglas station 72314013881")
    raw["timestamp_utc"] = pd.to_datetime(raw.DATE, utc=True, errors="coerce")
    parts = raw.TMP.str.extract(r"^(?P<tenths>[+-]\d{4}),(?P<quality>[0-9A-Z])$")
    raw["temperature_c"] = pd.to_numeric(parts.tenths, errors="coerce") / 10.0
    raw["quality"] = parts.quality

    # NOAA ISD quality 1/5 means passed all checks; 0/4 passed gross limits.
    valid = raw[
        raw.timestamp_utc.notna()
        & raw.quality.isin(["0", "1", "4", "5"])
        & raw.temperature_c.notna()
        & (raw.temperature_c < 99.9)
    ]
    hourly = (
        valid.set_index("timestamp_utc")
        .sort_index()
        .temperature_c.resample("h")
        .agg(["mean", "count"])
    )

    # All of this winter is EST, so 00:00 local on December 1 is 05:00 UTC.
    expected_utc = pd.date_range(
        "2024-12-01 05:00:00+00:00", periods=2160, freq="h"
    )
    hourly = hourly.reindex(expected_utc)
    missing = hourly["mean"].isna()
    maximum_gap = longest_gap(missing)
    if maximum_gap > 4:
        raise ValueError(f"Weather has a gap longer than 4 hours: {maximum_gap}")
    hourly["temperature_c"] = hourly["mean"].interpolate(
        method="time", limit=4, limit_direction="both"
    )
    if hourly.temperature_c.isna().any():
        raise ValueError("Weather still contains missing hours after interpolation")

    output = pd.DataFrame(
        {
            "timestamp_utc": expected_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "timestamp_local": expected_utc.tz_convert("America/New_York").strftime(
                "%Y-%m-%dT%H:%M:%S%z"
            ),
            "outdoor_temp_c": hourly.temperature_c.to_numpy(),
            "observation_count": hourly["count"].fillna(0).astype(int).to_numpy(),
            "interpolated": missing.to_numpy(),
        }
    )
    output.to_csv(OUTPUT, index=False, float_format="%.3f")

    metadata = {
        "station": "NOAA 72314013881 Charlotte Douglas airport",
        "winter_local": "2024-12-01 00:00 through 2025-03-01 00:00 America/New_York",
        "hours": len(output),
        "hours_with_quality_coded_observations": int((~missing).sum()),
        "interpolated_hours": int(missing.sum()),
        "longest_interpolated_gap_hours": maximum_gap,
        "quality_codes_accepted": ["0", "1", "4", "5"],
        "hourly_reduction": "mean of valid observations within each UTC hour",
        "raw_source_sha256": {path.name: sha256(path) for path in RAW_FILES},
    }
    (WEATHER / "charlotte_winter_2024_25_metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
