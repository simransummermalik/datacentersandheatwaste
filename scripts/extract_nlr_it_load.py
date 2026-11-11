"""Extract a measured hourly IT-power proxy from the NLR ESIF HPC dataset.

Source: Clark and Strelka, NLR HPC Facility Power Usage Effectiveness (PUE)
Data, DOI 10.7799/3015212, CC BY 4.0:
https://data.nlr.gov/submissions/300

Download the official zipped CSV resource and run::

    python scripts/extract_nlr_it_load.py /path/to/esif.influx.buildingData.PUE.combined.csv.zip

The output uses the same UTC window as a Charlotte local winter running from
2024-12-01 00:00 through 2025-03-01 00:00 America/New_York. The measured IT
power was recorded at an HPC data center in Golden, Colorado, and is only a
temporal proxy for a hypothetical Charlotte data center. It is not AI-specific.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timedelta, timezone
from io import TextIOWrapper
from math import isfinite
from pathlib import Path
import re
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = (
    ROOT / "data" / "load_profiles" / "nlr_esif_it_power_winter_2024_25_hourly.csv"
)
INNER_CSV = "esif.influx.buildingData.PUE.combined.csv"
FIRST_HOUR_UTC = datetime(2024, 12, 1, 5, tzinfo=timezone.utc)
AFTER_LAST_HOUR_UTC = datetime(2025, 3, 1, 5, tzinfo=timezone.utc)
SOURCE_TIMESTAMP = re.compile(
    r"^(?P<clock>[A-Za-z]{3} [A-Za-z]{3} \d{2} \d{4} \d{2}:\d{2}:\d{2}) "
    r"GMT(?P<offset>[+-]\d{4})"
)


def extract(archive: Path, output: Path) -> None:
    sums_kw: dict[datetime, float] = {}
    observations: dict[datetime, int] = {}
    discarded = 0

    with ZipFile(archive) as compressed:
        with TextIOWrapper(
            compressed.open(INNER_CSV), encoding="utf-8", newline=""
        ) as stream:
            for record in csv.DictReader(stream):
                timestamp = record["ts"]
                # Parsing the 10-year archive in full is unnecessary; include
                # November/March because UTC winter bounds cross local dates.
                local_year, local_month = timestamp[11:15], timestamp[4:7]
                if not (
                    (local_year == "2024" and local_month in ("Nov", "Dec"))
                    or (local_year == "2025" and local_month in ("Jan", "Feb", "Mar"))
                ):
                    continue

                match = SOURCE_TIMESTAMP.match(timestamp)
                if match is None:
                    discarded += 1
                    continue
                instant = datetime.strptime(
                    f"{match['clock']} {match['offset']}",
                    "%a %b %d %Y %H:%M:%S %z",
                ).astimezone(timezone.utc)
                if not FIRST_HOUR_UTC <= instant < AFTER_LAST_HOUR_UTC:
                    continue

                try:
                    power_kw = float(record["it_power_kw"])
                except (TypeError, ValueError):
                    discarded += 1
                    continue
                if not isfinite(power_kw) or power_kw <= 0:
                    discarded += 1
                    continue

                hour = instant.replace(minute=0, second=0, microsecond=0)
                sums_kw[hour] = sums_kw.get(hour, 0.0) + power_kw
                observations[hour] = observations.get(hour, 0) + 1

    output.parent.mkdir(parents=True, exist_ok=True)
    missing_hours = 0
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(("utc_hour", "it_power_kw", "observation_count"))
        hour = FIRST_HOUR_UTC
        while hour < AFTER_LAST_HOUR_UTC:
            count = observations.get(hour, 0)
            if count:
                mean_kw = f"{sums_kw[hour] / count:.6f}"
            else:
                mean_kw = ""
                missing_hours += 1
            writer.writerow((hour.strftime("%Y-%m-%dT%H:00:00Z"), mean_kw, count))
            hour += timedelta(hours=1)

    print(f"Wrote {output}")
    print(f"Hours: {len(observations)} observed, {missing_hours} missing")
    print(f"Observations per observed hour: {min(observations.values())}–{max(observations.values())}")
    print(f"Discarded invalid records in the selected window: {discarded}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help="Official zipped CSV resource")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    extract(args.archive, args.output)
