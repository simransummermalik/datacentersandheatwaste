"""Reproduce Charlotte Dec 2024–Feb 2025 hourly reliability and cost tables.

Run after scripts/prepare_charlotte_weather.py and
scripts/extract_nlr_it_load.py have prepared their compact hourly inputs.
"""

from __future__ import annotations

import csv
from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".matplotlib-cache"))
sys.path.insert(0, str(ROOT))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.greenhouse_load import GreenhouseInputs
from src.heat_recovery import HeatRecoveryInputs
from src.winter_analysis import WinterCase, run_winter_case, scaled_load_fractions
from src.thermal_storage import simulate_storage_dispatch, water_storage_volume_m3


DATA = ROOT / "data"
RESULTS = ROOT / "results"
CHARTS = ROOT / "charts"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise ValueError(f"No rows to write: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def save_chart(fig: plt.Figure, stem: str) -> None:
    CHARTS.mkdir(parents=True, exist_ok=True)
    fig.savefig(CHARTS / f"{stem}.png", dpi=300, facecolor="white")
    fig.savefig(CHARTS / f"{stem}.svg", facecolor="white")
    plt.close(fig)


def storage_sweep(base_rows: list[dict], parameters: dict[str, float]) -> list[dict]:
    """Find the idealized tank needed to eliminate backup for this one winter."""
    available = [float(row["available_heat_kwh"]) for row in base_rows]
    demand = [float(row["greenhouse_demand_kwh"]) for row in base_rows]
    heating_hours = sum(value > 1e-9 for value in demand)

    def dispatch_at(capacity_kwh: float):
        return simulate_storage_dispatch(
            available, demand, capacity_kwh,
            initial_state_of_charge_kwh=0.0,
            charge_efficiency=parameters["storage_charge_efficiency"],
            discharge_efficiency=parameters["storage_discharge_efficiency"],
            standing_loss_fraction_per_hour=parameters["storage_standing_loss_per_hour"],
        )

    upper = 500_000.0
    if dispatch_at(upper).total_backup_kwh > 1e-6:
        raise ValueError("500 MWh does not cover the whole winter; no finite screen was found")
    lower = 0.0
    for _ in range(40):
        midpoint = (lower + upper) / 2
        if dispatch_at(midpoint).total_backup_kwh > 1e-6:
            lower = midpoint
        else:
            upper = midpoint

    capacities = [0, 5_000, parameters["winter_storage_capacity_kwh"], 20_000, 50_000, 100_000, upper, 150_000]
    output: list[dict] = []
    for capacity in capacities:
        simulation = dispatch_at(capacity)
        covered = sum(d > 1e-9 and b <= 1e-6 for d, b in zip(demand, simulation.backup_heat_kwh, strict=True))
        output.append({
            "storage_capacity_mwh": capacity / 1000,
            "idealized_water_volume_m3_at_20c": water_storage_volume_m3(capacity, parameters["storage_delta_t_c"]),
            "heating_hours_without_backup_pct": 100 * covered / heating_hours,
            "backup_heat_mwh": simulation.total_backup_kwh / 1000,
            "initial_soc_mwh": 0,
        })
    return output


def plot_charts(summaries: list[dict], sweep: list[dict], base_rows: list[dict]) -> None:
    plt.rcParams.update(
        {
            "font.family": "Times New Roman",
            "font.size": 12,
            "text.color": "#222222",
            "axes.edgecolor": "#222222",
            "svg.fonttype": "none",
            "savefig.facecolor": "white",
        }
    )
    green, orange, gray = "#005030", "#c64d1a", "#666666"
    cases = {row["case"]: row for row in summaries}
    labels = ["2.7 ha\nno storage", "2.7 ha\n10.5 MWh tank", "2.7 ha\nconstant IT", "3.6 ha\n10.5 MWh tank"]
    selected = [
        cases["measured_2_7ha_no_storage"],
        cases["measured_2_7ha_10_53mwh"],
        cases["constant_2_7ha_10_53mwh"],
        cases["measured_3_6ha_10_53mwh"],
    ]

    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.7))
    fig.subplots_adjust(left=0.08, right=0.98, top=0.78, bottom=0.25, wspace=0.28)
    fig.suptitle("Winter heat reliability | Charlotte, Dec 2024–Feb 2025", fontsize=19, fontweight="bold", y=0.97)
    fig.text(0.5, 0.86, "Measured Colorado IT-load shape paired with observed Charlotte weather; cases are hypothetical", ha="center", fontsize=11)
    x = range(4)
    bars = axes[0].bar(x, [row["heating_hours_without_backup_pct"] for row in selected], width=0.62, color=[gray, green, gray, orange])
    axes[0].set_ylim(0, 105)
    axes[0].set_ylabel("Heating hours without backup (%)")
    axes[0].set_xticks(list(x), labels)
    axes[0].spines[["top", "right"]].set_visible(False)
    axes[0].grid(axis="y", color="#dddddd", linewidth=0.6)
    axes[0].set_axisbelow(True)
    for bar, row in zip(bars, selected):
        axes[0].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.4, f"{row['heating_hours_without_backup_pct']:.1f}%", ha="center", fontsize=11)

    bars = axes[1].bar(x, [row["backup_heat_mwh"] for row in selected], width=0.62, color=[gray, green, gray, orange])
    axes[1].set_ylabel("Backup thermal energy (MWh)")
    axes[1].set_xticks(list(x), labels)
    axes[1].spines[["top", "right"]].set_visible(False)
    axes[1].grid(axis="y", color="#dddddd", linewidth=0.6)
    axes[1].set_axisbelow(True)
    ymax = max(row["backup_heat_mwh"] for row in selected)
    axes[1].set_ylim(0, ymax * 1.18 if ymax else 1)
    for bar, row in zip(bars, selected):
        axes[1].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + ymax * 0.025, f"{row['backup_heat_mwh']:.0f}", ha="center", fontsize=11)
    save_chart(fig, "04_winter_reliability")

    baseline = cases["measured_2_7ha_10_53mwh"]
    cost_labels = ["Electric resistance\nreference", "Heat recovery +\nelectric backup", "Gas boiler\nreference", "Heat recovery +\ngas backup"]
    costs = [
        baseline["electric_resistance_reference_usd"],
        baseline["recovery_plus_electric_backup_usd"],
        baseline["gas_boiler_reference_usd"],
        baseline["recovery_plus_gas_backup_usd"],
    ]
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.subplots_adjust(left=0.11, right=0.96, top=0.76, bottom=0.24)
    fig.suptitle("Winter heating energy cost | 2.7 ha greenhouse", fontsize=19, fontweight="bold", y=0.97)
    fig.text(0.5, 0.86, "Same hourly heat demand in every case; 10.5 MWh storage in recovery cases", ha="center", fontsize=11)
    bars = ax.bar(range(4), [value / 1000 for value in costs], width=0.65, color=[gray, green, gray, green])
    ax.set_ylabel("Modeled winter energy cost (thousand USD)")
    ax.set_xticks(list(range(4)), cost_labels)
    ax.set_ylim(0, max(costs) / 1000 * 1.17)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#dddddd", linewidth=0.6)
    ax.set_axisbelow(True)
    for bar, cost in zip(bars, costs):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(costs) / 1000 * 0.025, f"${cost / 1000:,.0f}k", ha="center", fontsize=11)
    fig.text(0.5, 0.075, "EIA NC 2025 averages: electricity 10.22¢/kWh; gas $12.71/Mcf. Boiler efficiency 85%.", ha="center", fontsize=10)
    fig.text(0.5, 0.035, "Energy cost only; excludes equipment, piping, demand charges, heat purchase, and cooling savings.", ha="center", fontsize=10)
    save_chart(fig, "05_winter_heating_cost")

    fig, ax = plt.subplots(figsize=(10.5, 4.7))
    fig.subplots_adjust(left=0.11, right=0.97, top=0.77, bottom=0.23)
    fig.suptitle("A prolonged compute dip requires much larger storage", fontsize=18, fontweight="bold", y=0.97)
    fig.text(0.5, 0.86, "2.7 ha greenhouse; observed Charlotte winter; measured Colorado IT-load shape", ha="center", fontsize=11)
    xs = [row["storage_capacity_mwh"] for row in sweep]
    ys = [row["backup_heat_mwh"] for row in sweep]
    ax.plot(xs, ys, color=green, linewidth=1.8, marker="o", markersize=5)
    ax.axvline(10.532, color=gray, linestyle="--", linewidth=1)
    ax.text(13, 115, "Poster tank: 10.5 MWh", fontsize=11, color=gray)
    needed = sweep[-2]
    ax.annotate(f"Zero-backup screen: {needed['storage_capacity_mwh']:.1f} MWh\n~{needed['idealized_water_volume_m3_at_20c']:,.0f} m³ of water", xy=(needed["storage_capacity_mwh"], 0), xytext=(82, 70), arrowprops={"arrowstyle": "->", "color": "#222222"}, fontsize=11)
    ax.set_xlim(0, 165)
    ax.set_ylim(0, 165)
    ax.set_xlabel("Usable thermal storage capacity (MWh)")
    ax.set_ylabel("Winter backup heat (MWh)")
    ax.grid(color="#dddddd", linewidth=0.6)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    fig.text(0.5, 0.07, "Initial tank empty; 98% charge/discharge efficiency; 0.1% hourly standing loss; unlimited tank power.", ha="center", fontsize=10)
    save_chart(fig, "06_storage_sizing")

    # Identify the longest continuous backup interval without assuming an
    # outage cause. The source dataset reports IT power, not incident logs.
    episodes: list[list[dict]] = []
    active: list[dict] = []
    for row in base_rows:
        if float(row["backup_heat_kwh"]) > 1e-6:
            active.append(row)
        elif active:
            episodes.append(active)
            active = []
    if active:
        episodes.append(active)
    if not episodes:
        return
    longest = max(episodes, key=len)
    start = datetime.fromisoformat(longest[0]["timestamp_utc"].replace("Z", "+00:00")) - timedelta(hours=12)
    end = datetime.fromisoformat(longest[-1]["timestamp_utc"].replace("Z", "+00:00")) + timedelta(hours=12)
    window = [
        row for row in base_rows
        if start <= datetime.fromisoformat(row["timestamp_utc"].replace("Z", "+00:00")) <= end
    ]
    hours = [datetime.fromisoformat(row["timestamp_utc"].replace("Z", "+00:00")) for row in window]
    fig, ax = plt.subplots(figsize=(11, 4.8))
    fig.subplots_adjust(left=0.10, right=0.97, top=0.78, bottom=0.23)
    fig.suptitle("A multi-day compute dip drives almost all backup heat", fontsize=18, fontweight="bold", y=0.97)
    fig.text(0.5, 0.87, "2.7 ha greenhouse with 10.5 MWh storage | Colorado IT-load proxy + Charlotte weather", ha="center", fontsize=11)
    ax.plot(hours, [float(row["greenhouse_demand_kwh"]) / 1000 for row in window], color=orange, linewidth=1.5, label="Greenhouse demand")
    ax.plot(hours, [float(row["available_heat_kwh"]) / 1000 for row in window], color=green, linewidth=1.5, label="Available recovered heat")
    ax.fill_between(hours, [float(row["available_heat_kwh"]) / 1000 for row in window], [float(row["greenhouse_demand_kwh"]) / 1000 for row in window], where=[float(row["backup_heat_kwh"]) > 1e-6 for row in window], color=orange, alpha=0.15, label="Hours with backup")
    ax.set_ylabel("Thermal power (MW)")
    ax.set_xlabel("Date and time (UTC)")
    ax.grid(color="#dddddd", linewidth=0.6)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, loc="upper right", fontsize=10)
    fig.autofmt_xdate(rotation=0)
    episode_mwh = sum(float(row["backup_heat_kwh"]) for row in longest) / 1000
    winter_mwh = sum(float(row["backup_heat_kwh"]) for row in base_rows) / 1000
    fig.text(0.5, 0.07, f"{len(longest)} consecutive backup hours, {episode_mwh:.0f} MWh: {100 * episode_mwh / winter_mwh:.1f}% of modeled winter backup energy.", ha="center", fontsize=11)
    save_chart(fig, "07_low_compute_event")


def main() -> None:
    parameters = {row["parameter"]: float(row["value"]) for row in read_csv(DATA / "source_data.csv")}
    weather = read_csv(DATA / "weather" / "charlotte_winter_2024_25_hourly.csv")
    measured = read_csv(DATA / "load_profiles" / "nlr_esif_it_power_winter_2024_25_hourly.csv")
    timestamps = [row["timestamp_utc"] for row in weather]
    if len(weather) != 2160 or timestamps != [row["utc_hour"] for row in measured]:
        raise ValueError("Weather and measured IT power must cover the same 2,160 UTC hours")
    start_utc = datetime(2024, 12, 1, 5, tzinfo=timezone.utc)
    if timestamps != [
        (start_utc + timedelta(hours=hour)).strftime("%Y-%m-%dT%H:00:00Z")
        for hour in range(2160)
    ]:
        raise ValueError("Winter inputs must be continuous hourly data in the declared UTC window")
    if any(not row["it_power_kw"] for row in measured):
        raise ValueError("The measured IT profile has missing hours")
    temperatures = [float(row["outdoor_temp_c"]) for row in weather]
    observed_power = [float(row["it_power_kw"]) for row in measured]
    proxy_fractions = scaled_load_fractions(observed_power, parameters["it_capacity_mw"] * 1000, parameters["it_load_fraction"])
    constant_fractions = [parameters["it_load_fraction"]] * len(weather)

    heat = HeatRecoveryInputs(
        it_capacity_mw=parameters["it_capacity_mw"],
        it_load_fraction=parameters["it_load_fraction"],
        heat_conversion_fraction=parameters["heat_conversion_fraction"],
        collection_fraction=parameters["collection_fraction"],
        heat_exchanger_effectiveness=parameters["heat_exchanger_effectiveness"],
        coolant_outlet_temp_c=parameters["coolant_outlet_temp_c"],
        greenhouse_supply_temp_c=parameters["greenhouse_supply_temp_c"],
        direct_hx_approach_c=parameters["direct_hx_approach_c"],
        distribution_loss_fraction=parameters["distribution_loss_fraction"],
        hp_carnot_efficiency=parameters["hp_carnot_efficiency"],
        hp_source_approach_c=parameters["hp_source_approach_c"],
        hp_sink_approach_c=parameters["hp_sink_approach_c"],
        hp_minimum_cop=parameters["hp_minimum_cop"],
        hp_maximum_cop=parameters["hp_maximum_cop"],
    )
    greenhouse = GreenhouseInputs(
        indoor_temp_c=parameters["greenhouse_indoor_temp_c"],
        envelope_u_value_w_m2k=parameters["envelope_u_value_w_m2k"],
        envelope_area_to_floor_area=parameters["envelope_area_to_floor_area"],
        air_changes_per_hour=parameters["air_changes_per_hour"],
        mean_height_m=parameters["greenhouse_mean_height_m"],
        air_density_kg_m3=parameters["air_density_kg_m3"],
        air_specific_heat_j_kgk=parameters["air_specific_heat_j_kgk"],
        design_margin_fraction=parameters["winter_energy_design_margin_fraction"],
    )
    area = parameters["winter_greenhouse_floor_area_m2"]
    cases = [
        WinterCase("measured_2_7ha_no_storage", area, 0),
        WinterCase("measured_2_7ha_10_53mwh", area, parameters["winter_storage_capacity_kwh"]),
        WinterCase("constant_2_7ha_10_53mwh", area, parameters["winter_storage_capacity_kwh"], "constant_80pct"),
        WinterCase("measured_3_6ha_10_53mwh", 35_950, parameters["winter_storage_capacity_kwh"]),
    ]
    hourly: list[dict] = []
    summaries: list[dict] = []
    base_rows: list[dict] = []
    for case in cases:
        profile = constant_fractions if case.it_load_profile == "constant_80pct" else proxy_fractions
        rows, summary = run_winter_case(
            case, timestamps, temperatures, profile, heat, greenhouse,
            charge_efficiency=parameters["storage_charge_efficiency"],
            discharge_efficiency=parameters["storage_discharge_efficiency"],
            standing_loss_fraction_per_hour=parameters["storage_standing_loss_per_hour"],
            electricity_price_per_kwh=parameters["nc_2025_commercial_electricity_usd_per_kwh"],
            gas_price_per_mcf=parameters["nc_2025_commercial_gas_usd_per_mcf"],
            gas_mmbtu_per_mcf=parameters["gas_mmbtu_per_mcf"],
            boiler_efficiency=parameters["reference_gas_boiler_efficiency"],
            pump_electricity_fraction=parameters["pump_electricity_per_delivered_heat_fraction"],
        )
        hourly.extend(rows)
        summaries.append(summary)
        if case.name == "measured_2_7ha_10_53mwh":
            base_rows = rows
    write_csv(RESULTS / "winter_hourly_results.csv", hourly)
    write_csv(RESULTS / "winter_summary.csv", summaries)
    sweep = storage_sweep(base_rows, parameters)
    write_csv(RESULTS / "winter_storage_sweep.csv", sweep)
    plot_charts(summaries, sweep, base_rows)
    for row in summaries:
        print(f"{row['case']}: {row['heating_hours_without_backup_pct']:.2f}% covered heating hours; {row['backup_heat_mwh']:.1f} MWh backup")


if __name__ == "__main__":
    main()
