# Charlotte winter reliability screen

## Research question and scenario

For a specified **27,000 m² (2.70 ha) double-poly greenhouse**, what fraction
of the hours in which heating is required can recovered data-center heat meet
without backup? The window is December 1, 2024 through February 28, 2025 in
Charlotte local time: 2,160 consecutive hours. The indoor setpoint is 18 °C.
This is a *hypothetical* colocated system, evaluated with observed Charlotte
weather and a measured but **cross-site** compute-load shape.

The compute series comes from the [`it_power_kw` field in NLR's ESIF HPC data
center dataset](https://data.nlr.gov/submissions/300), recorded in Golden,
Colorado. It is an HPC site, **not an AI facility or a Charlotte facility**.
Each measured hourly IT-power value is divided by that series' mean and scaled
to a hypothetical 10 MW nameplate plant at 80% mean load. This preserves the
observed variation without claiming that the Colorado and Charlotte systems
actually operated together. The scaled profile averages 8.00 MW and ranges
from 1.32 to 9.64 MW; no point exceeds 10 MW nameplate. The constant 8 MW case
is an explicit sensitivity check.

Charlotte outdoor temperature comes from [NOAA Global Hourly](https://www.ncei.noaa.gov/products/land-based-station/integrated-surface-database),
Charlotte Douglas airport station 72314013881. Of 2,160 hours, 2,155 have
quality-coded observations and five short missing hours are interpolated. Raw
files, source URLs, quality rules, and checksums are in
[`data/weather/`](../data/weather/README.md); the compute-series provenance is
in [`data/load_profiles/`](../data/load_profiles/README.md).

The heat-recovery assumptions are the repository's 35 °C coolant, 40 °C
greenhouse supply, 75% collection, 75% heat-exchanger effectiveness, 8%
distribution loss, and a capped COP of 6. The greenhouse sensible load uses a
3.98 W/m²-K envelope, 1.5 envelope/floor ratio, 0.75 ACH, and 4 m mean height.
Hourly energy demand omits the 10% *design sizing margin* used in the earlier
peak-area calculation. Solar gains, growing-stage schedules, night curtains,
evapotranspiration, intentional ventilation, and ground loss are omitted.
These choices are in [`data/source_data.csv`](../data/source_data.csv).

## What counts as reliability

An hour is a **heating hour** when modeled greenhouse demand is greater than
zero. It is covered **without backup** only if the residual backup heat after
direct use and storage discharge is zero within a 1 Wh numerical tolerance.
Storage begins **empty**, charges from surplus delivered heat at 98%
efficiency, discharges at 98%, loses 0.1% of state of charge per hour, and has
no charge/discharge power limit. The 10.532 MWh case carries forward the
earlier *synthetic-day* poster tank size; it is not a winter optimum. All energy
quantities below are over this single 90-day winter.

| IT-load case and greenhouse | Storage | Heating hours without backup | Backup heat | Winter compressor electricity |
|---|---:|---:|---:|---:|
| Measured proxy, 2.70 ha | 0 MWh | 94.55% (1,942/2,054) | 149.9 MWh | 818.7 MWh |
| **Measured proxy, 2.70 ha** | **10.532 MWh** | **96.54% (1,983/2,054)** | **127.8 MWh** | **828.8 MWh** |
| Constant 80% IT load, 2.70 ha | 10.532 MWh | 100.00% (2,054/2,054) | 0 MWh | 852.0 MWh |
| Measured proxy, 3.595 ha | 10.532 MWh | 94.55% (1,942/2,054) | 235.1 MWh | 1,090.0 MWh |

For the primary 2.70 ha case, total modeled winter greenhouse heat demand is
**4,668.9 MWh**. Recovered heat meets 4,541.0 MWh of that demand; the backup
energy share is **2.74%**. The heating-hour coverage percentage is a separate,
stricter reliability measure: even a small deficit makes an hour count as
requiring backup.
Across **all 2,160 winter hours**, including 106 hours with no heating demand,
**2,089 hours (96.71%)** need no backup. The heating-hour denominator is more
useful for a grower, so it is the headline reliability result.

The strongest result is about **duration**. A single 66-hour backup episode
from December 21 00:00 to December 23 17:00 UTC accounts for **125.2 MWh,
97.9%** of the season's 127.8 MWh backup heat. The measured IT-power proxy is
low during this interval; the dataset does not identify why. A flat 80% load
would miss this failure mode entirely. Storage smooths short gaps, but a 10.5
MWh tank cannot bridge this multi-day episode. Under the same idealized,
unlimited-power storage model, the minimum capacity that removes all backup
for *this exact winter and profile* is about **148.7 MWh**, equivalent to about
**6,414 m³** of water at a 20 °C usable temperature swing. That is a model
screen, not a tank design or a reliability guarantee for other winters.
All 66 source-profile hours in that episode contain 60 measured IT-power
observations, so the drop is not caused by missing hourly values in the compact
series.

## Heating electricity and cost comparison

No actual greenhouse's existing heater or utility contract has been provided.
The comparisons therefore use two **reference options**, both meeting exactly
the same 4,668.9 MWh greenhouse heat demand: electric resistance at 100%
conversion and a gas boiler at an assumed 85% seasonal delivered-heat
efficiency. Backup in a recovery case uses the named reference option.

| Heating option, 2.70 ha | Compressor electricity | Circulation proxy electricity | Backup heat | Modeled 90-day energy cost |
|---|---:|---:|---:|---:|
| Electric resistance only | 0 | 0 | 4,668.9 MWh | $477,159 |
| Heat recovery + electric backup | 828.8 MWh | 91.5 MWh | 127.8 MWh | $107,113 |
| Gas boiler only | 0 | 0 | 4,668.9 MWh | $229,714 |
| Heat recovery + gas backup | 828.8 MWh | 91.5 MWh | 127.8 MWh | $100,339 |

Prices are the [EIA 2025 North Carolina commercial average electricity price,
10.22¢/kWh](https://www.eia.gov/electricity/annual/table.php?t=epa_02_10.html)
and [commercial natural gas price,
$12.71/Mcf](https://www.eia.gov/dnav/ng/hist/n3020nc3a.htm). The gas calculation
uses [EIA's 2025 average 1.037 MMBtu/Mcf heat
content](https://www.eia.gov/tools/faqs/faq.php?id=45&t=5) and the stated 85%
boiler efficiency. The 2% circulation electricity assumption is applied to
heat-pump output sent to the load or charged into storage. The heat pump is
assumed to modulate at the modeled COP; actual part-load performance is
unknown. Electricity for backup is 1 kWh per kWh of thermal deficit in the
resistance case. Gas backup requires deficit/0.85 fuel kWh in the boiler case.
The dispatch greedily fills the tank whenever there is surplus heat, and the
10.532 MWh tank ends the winter full. The energy-cost totals include the
electricity used to leave that heat in storage; they do not credit a later use.

These are **energy-only operating comparisons**, not bills or savings claims
for a real facility. They omit equipment and tank capital cost, piping,
maintenance, electricity demand charges and time-of-use rates, contract price
for recovered heat, gas fixed charges, and any avoided data-center cooling
cost. The 2025 EIA annual-average prices are a common benchmark, not prices
observed during each hour of the 2024–25 winter.

## Figures and reproduction

Plain Times New Roman poster figures are in [`charts/`](../charts/):
[`04_winter_reliability.png`](../charts/04_winter_reliability.png),
[`05_winter_heating_cost.png`](../charts/05_winter_heating_cost.png),
[`06_storage_sizing.png`](../charts/06_storage_sizing.png), and
[`07_low_compute_event.png`](../charts/07_low_compute_event.png). Each has an
editable-text SVG companion. Reproducible hourly and summary tables are
[`results/winter_hourly_results.csv`](../results/winter_hourly_results.csv),
[`results/winter_summary.csv`](../results/winter_summary.csv), and
[`results/winter_storage_sweep.csv`](../results/winter_storage_sweep.csv).

From the repository root after installing `requirements.txt`:

```bash
python scripts/prepare_charlotte_weather.py
python scripts/run_winter_analysis.py
```

The compact compute series is committed as a CSV. To recreate it from the
official zipped raw resource, follow
[`data/load_profiles/README.md`](../data/load_profiles/README.md) and run
`python scripts/extract_nlr_it_load.py /path/to/source.zip` before the winter
analysis. The raw 97 MB compute archive is not retained here.

**Poster-ready finding:** “An 8 MW average compute load appears sufficient for
this 2.7 ha greenhouse, but the measured IT-load shape paired with Charlotte
weather leaves 71 heating hours requiring backup even with 10.5 MWh of thermal
storage. One 66-hour low-load interval causes 97.9% of backup energy. The
design problem is prolonged heat availability even when seasonal heat is
ample.”
