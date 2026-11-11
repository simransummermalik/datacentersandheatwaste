# Observed Charlotte winter weather

`charlotte_winter_2024_25_hourly.csv` contains 2,160 hourly outdoor-air
temperatures for December 1, 2024 through February 28, 2025 in Charlotte local
time (Eastern Standard Time). Its source is [NOAA Global Hourly / Integrated
Surface Database](https://www.ncei.noaa.gov/products/land-based-station/integrated-surface-database),
Charlotte Douglas airport station **72314013881**. The exact original yearly
CSV resources are:

- [2024](https://noaa-global-hourly-pds.s3.amazonaws.com/2024/72314013881.csv)
- [2025](https://noaa-global-hourly-pds.s3.amazonaws.com/2025/72314013881.csv)

The two original files are retained here. Run
`python scripts/prepare_charlotte_weather.py` to regenerate the compact hourly
series and `charlotte_winter_2024_25_metadata.json`. The script accepts NOAA
temperature quality codes 0, 1, 4, and 5; averages valid observations in each
UTC hour; and interpolates gaps of at most four hours. **2,155 hours have NOAA
observations; five are interpolated**, with a longest four-hour gap. The
metadata file records source SHA-256 checksums. Airport temperature is a proxy
for a prospective greenhouse site; no onsite weather measurement is available.

The hourly weather is paired by UTC timestamp with a measured *Colorado* HPC
IT-power profile in the analysis. That pairing is a hypothetical temporal
scenario, not an observed colocated system.
