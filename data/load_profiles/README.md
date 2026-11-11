# Measured IT-power proxy

`nlr_esif_it_power_winter_2024_25_hourly.csv` is an hourly mean of the measured
`it_power_kw` field from [Clark and Strelka, *NLR HPC Facility Power Usage
Effectiveness (PUE) Data*](https://data.nlr.gov/submissions/300), DOI
[10.7799/3015212](https://doi.org/10.7799/3015212). The source is licensed
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The source facility
is the Energy Systems Integration Facility HPC data center in Golden, Colorado.
It is a measured temporal proxy, not an AI workload or a Charlotte data-center
measurement.

The official resource used is the [zipped power-metrics
CSV](https://data.nlr.gov/system/files/300/1757105566-esif.influx.buildingData.PUE.combined.csv.zip).
Its SHA-256 checksum at retrieval on 2026-11-10 was
`59e6c0537956b77fb071c6f8211efc3fa4522ca10e5e3d95679aa937627262b1`.
The 97 MB source archive is not committed. To regenerate this compact file,
download the source archive and run `python scripts/extract_nlr_it_load.py
/path/to/source.zip` from the repository root.

The source timestamp includes its Mountain Standard Time offset. The extractor
converts each observation to UTC, averages valid IT-power observations within
each hour, and writes every hour in the Charlotte local winter window from
2024-12-01 00:00 through 2025-03-01 00:00 America/New_York. Its corresponding
UTC window is 2024-12-01 05:00 through 2025-03-01 05:00, with an exclusive end.
The CSV has 2,160 hourly rows, all with measured values; there are no missing
hours or invalid IT-power observations in this window. Observation counts range
from 54 to 60 per hour, with a median of 60. The mean of the hourly means is
2,338.53 kW, and the range is 385.36 to 2,818.30 kW. The low-load hours are
retained as measured; they should not be silently smoothed away.

Any scaling from this facility's measured IT power to a hypothetical 10 MW
Charlotte facility is a scenario assumption and must be reported separately.
