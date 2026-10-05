"""Execute the scenario model and write tables/figures used by the README.

Run from the repository root with ``python scripts/generate_results.py``.  All
inputs are kept in ``data/``; this script only assembles model outputs and plots.
"""

from __future__ import annotations

import csv
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".matplotlib-cache"))
sys.path.insert(0, str(ROOT))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.greenhouse_load import GreenhouseInputs, heating_demand_kw
from src.heat_recovery import HeatRecoveryInputs, evaluate_heat_recovery
from src.simulation import read_scenarios, run_scenario
from src.thermal_storage import (
    minimum_cyclic_storage_capacity_kwh,
    simulate_storage_dispatch,
    water_storage_volume_m3,
)


RESULTS = ROOT / "results"
FIGURES = ROOT / "figures"
RESULTS.mkdir(exist_ok=True)
FIGURES.mkdir(exist_ok=True)


def _savefig(name: str) -> None:
    plt.tight_layout()
    plt.savefig(FIGURES / name, dpi=180, bbox_inches="tight")
    plt.close()


def read_parameter_catalog() -> dict[str, float]:
    """Read numeric baseline constants from the auditable parameter CSV."""

    with (ROOT / "data" / "source_data.csv").open(newline="", encoding="utf-8") as handle:
        return {row["parameter"]: float(row["value"]) for row in csv.DictReader(handle)}


def main() -> None:
    catalog = read_parameter_catalog()
    scenario_rows = read_scenarios(ROOT / "data" / "scenarios.csv")
    scenario_results = pd.DataFrame([run_scenario(row) for row in scenario_rows])
    scenario_results.to_csv(RESULTS / "scenario_results.csv", index=False)

    # A full-factorial screening of load, source temperature, weather, and the
    # fraction of IT heat entering the recovery loop.
    baseline = next(row for row in scenario_rows if row["scenario_id"] == "baseline_10mw")
    sensitivity_rows: list[dict[str, object]] = []
    for load_mw in (1.0, 10.0, 50.0):
        for source_temp_c in (25.0, 35.0, 45.0, 55.0):
            for outdoor_temp_c in (-10.0, 0.0, 10.0):
                for collection_fraction in (0.40, 0.60, 0.75, 0.90):
                    row = dict(baseline)
                    row.update(
                        {
                            "scenario_id": (
                                f"load_{load_mw:g}mw_source_{source_temp_c:g}c_"
                                f"outdoor_{outdoor_temp_c:g}c_collection_{collection_fraction:.2f}"
                            ),
                            "description": "Factorial sensitivity screening",
                            "it_capacity_mw": load_mw,
                            "coolant_outlet_temp_c": source_temp_c,
                            "outdoor_temp_c": outdoor_temp_c,
                            "collection_fraction": collection_fraction,
                        }
                    )
                    sensitivity_rows.append(run_scenario(row))
    pd.DataFrame(sensitivity_rows).to_csv(
        RESULTS / "sensitivity_results.csv", index=False
    )

    # Ideal source-heat scale and baseline usable delivery.
    baseline_loads = scenario_results[scenario_results.scenario_id.str.startswith("baseline_")].copy()
    baseline_loads["ideal_nameplate_heat_mw"] = baseline_loads["it_capacity_mw"]
    baseline_loads[
        [
            "it_capacity_mw",
            "ideal_nameplate_heat_mw",
            "nameplate_theoretical_heat_mw",
            "operating_it_power_mw",
            "post_hx_source_heat_mw",
            "delivered_heat_mw",
            "supported_area_m2",
        ]
    ].to_csv(RESULTS / "baseline_scale.csv", index=False)

    # Illustrative one-day mismatch.  Temperatures and load fractions are
    # deliberately synthetic, marked in the input CSV, and not a weather claim.
    profile = pd.read_csv(ROOT / "data" / "illustrative_day.csv")
    profile_row = dict(baseline)
    baseline_area = float(
        scenario_results.loc[
            scenario_results.scenario_id == "baseline_10mw", "supported_area_m2"
        ].iloc[0]
    )
    profile_area_m2 = 0.75 * baseline_area
    available_kw: list[float] = []
    demand_kw: list[float] = []
    profile_outputs: list[dict[str, object]] = []
    for record in profile.to_dict("records"):
        row = dict(profile_row)
        row["it_load_fraction"] = record["it_load_fraction"]
        row["outdoor_temp_c"] = record["outdoor_temp_c"]
        recovery = evaluate_heat_recovery(
            HeatRecoveryInputs(
                it_capacity_mw=float(row["it_capacity_mw"]),
                it_load_fraction=float(row["it_load_fraction"]),
                heat_conversion_fraction=float(row["heat_conversion_fraction"]),
                collection_fraction=float(row["collection_fraction"]),
                heat_exchanger_effectiveness=float(row["heat_exchanger_effectiveness"]),
                coolant_outlet_temp_c=float(row["coolant_outlet_temp_c"]),
                greenhouse_supply_temp_c=float(row["greenhouse_supply_temp_c"]),
                direct_hx_approach_c=float(row["direct_hx_approach_c"]),
                distribution_loss_fraction=float(row["distribution_loss_fraction"]),
                hp_carnot_efficiency=float(row["hp_carnot_efficiency"]),
                hp_source_approach_c=float(row["hp_source_approach_c"]),
                hp_sink_approach_c=float(row["hp_sink_approach_c"]),
                hp_minimum_cop=float(row["hp_minimum_cop"]),
                hp_maximum_cop=float(row["hp_maximum_cop"]),
            )
        )
        greenhouse = GreenhouseInputs(
            indoor_temp_c=float(row["greenhouse_indoor_temp_c"]),
            envelope_u_value_w_m2k=float(row["envelope_u_value_w_m2k"]),
            envelope_area_to_floor_area=float(row["envelope_area_to_floor_area"]),
            air_changes_per_hour=float(row["air_changes_per_hour"]),
            mean_height_m=float(row["greenhouse_mean_height_m"]),
            air_density_kg_m3=float(row["air_density_kg_m3"]),
            air_specific_heat_j_kgk=float(row["air_specific_heat_j_kgk"]),
            design_margin_fraction=float(row["design_margin_fraction"]),
        )
        demand = heating_demand_kw(
            profile_area_m2, float(record["outdoor_temp_c"]), greenhouse
        )
        available = recovery.delivered_heat_kw
        available_kw.append(available)
        demand_kw.append(demand)
        profile_outputs.append(
            {
                "hour": int(record["hour"]),
                "outdoor_temp_c": float(record["outdoor_temp_c"]),
                "it_load_fraction": float(record["it_load_fraction"]),
                "available_heat_kw_after_distribution": available,
                "greenhouse_demand_kw": demand,
                "profile_area_m2": profile_area_m2,
                "pathway": "heat_pump",
            }
        )

    profile_results = pd.DataFrame(profile_outputs)
    profile_results.to_csv(RESULTS / "illustrative_day_results.csv", index=False)

    ideal_storage_kwh = minimum_cyclic_storage_capacity_kwh(available_kw, demand_kw)
    design_storage_kwh = ideal_storage_kwh * 1.20 if np.isfinite(ideal_storage_kwh) else np.inf
    dispatch = simulate_storage_dispatch(
        available_kw,
        demand_kw,
        capacity_kwh=design_storage_kwh,
        initial_state_of_charge_kwh=design_storage_kwh,
        charge_efficiency=catalog["storage_charge_efficiency"],
        discharge_efficiency=catalog["storage_discharge_efficiency"],
        standing_loss_fraction_per_hour=catalog["storage_standing_loss_per_hour"],
    )
    storage_volume = water_storage_volume_m3(
        design_storage_kwh,
        catalog["storage_delta_t_c"],
        water_density_kg_m3=catalog["water_density_kg_m3"],
        water_specific_heat_kj_kgk=catalog["water_specific_heat_kj_kgk"],
    )
    storage_summary = pd.DataFrame(
        [
            {
                "profile_area_m2": profile_area_m2,
                "ideal_lossless_storage_kwh": ideal_storage_kwh,
                "screening_design_storage_kwh": design_storage_kwh,
                "equivalent_water_volume_m3_at_20C_swing": storage_volume,
                "backup_heat_kwh_with_design_store": dispatch.total_backup_kwh,
                "curtailed_heat_kwh": dispatch.total_curtailed_kwh,
                "standing_loss_kwh": dispatch.total_standing_loss_kwh,
            }
        ]
    )
    storage_summary.to_csv(RESULTS / "storage_summary.csv", index=False)
    pd.DataFrame(
        {
            "hour": profile["hour"],
            "state_of_charge_kwh": dispatch.state_of_charge_kwh,
            "direct_to_load_kwh": dispatch.direct_to_load_kwh,
            "charged_kwh": dispatch.charged_kwh,
            "discharged_to_load_kwh": dispatch.discharged_to_load_kwh,
            "backup_heat_kwh": dispatch.backup_heat_kwh,
            "curtailed_heat_kwh": dispatch.curtailed_heat_kwh,
            "standing_loss_kwh": dispatch.standing_loss_kwh,
        }
    ).to_csv(RESULTS / "storage_dispatch.csv", index=False)

    make_figures(scenario_results, sensitivity_rows, profile_results, dispatch)


def make_figures(
    scenario_results: pd.DataFrame,
    sensitivity_rows: list[dict[str, object]],
    profile_results: pd.DataFrame,
    dispatch: object,
) -> None:
    """Create small, reproducible PNGs for the README and notebooks."""

    plt.rcParams.update({"font.size": 10, "axes.grid": True, "grid.alpha": 0.25})

    scale = scenario_results[scenario_results.scenario_id.str.startswith("baseline_")].sort_values(
        "it_capacity_mw"
    )
    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.plot(scale.it_capacity_mw, scale.nameplate_theoretical_heat_mw, "o-", label="Nameplate IT → heat (ideal)")
    ax.plot(scale.it_capacity_mw, scale.post_hx_source_heat_mw, "o-", label="After collection + HX")
    ax.plot(scale.it_capacity_mw, scale.delivered_heat_mw, "o-", label="Delivered after HP/distribution")
    ax.set(xlabel="Data-center IT capacity (MW)", ylabel="Thermal power (MW)", title="Baseline heat flow scales with IT load")
    ax.legend(frameon=False)
    _savefig("heat_flow_vs_it_load.png")

    sens = pd.DataFrame(sensitivity_rows)
    area = sens[
        (sens.it_capacity_mw == 10.0)
        & (sens.coolant_outlet_temp_c == 35.0)
        & (sens.collection_fraction == 0.75)
    ].sort_values("outdoor_temp_c")
    fig, ax = plt.subplots(figsize=(7, 4.2))
    for capacity in (1.0, 10.0, 50.0):
        subset = sens[
            (sens.it_capacity_mw == capacity)
            & (sens.coolant_outlet_temp_c == 35.0)
            & (sens.collection_fraction == 0.75)
        ].sort_values("outdoor_temp_c")
        ax.plot(subset.outdoor_temp_c, subset.supported_area_m2 / 10_000, "o-", label=f"{capacity:g} MW IT")
    ax.set(xlabel="Outdoor temperature (°C)", ylabel="Peak-supported area (hectares)", title="Cold weather reduces peak-supported greenhouse area")
    ax.legend(frameon=False)
    _savefig("supported_area_vs_outdoor_temperature.png")

    temp = pd.concat(
        [
            scenario_results[
                scenario_results.scenario_id.isin(["baseline_10mw"])
            ],
            scenario_results[
                scenario_results.scenario_id.str.contains("coolant_")
            ],
        ],
        ignore_index=True,
    )
    temp = temp.sort_values("coolant_outlet_temp_c")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 3.8))
    colors = ["#c44e52" if p == "heat_pump" else "#4c72b0" for p in temp.pathway]
    ax1.bar(temp.coolant_outlet_temp_c.astype(str), temp.delivered_heat_mw, color=colors)
    ax1.set(xlabel="Coolant outlet (°C)", ylabel="Delivered heat (MW)", title="Pathway changes at the direct-use threshold")
    ax1.tick_params(axis="x", rotation=30)
    hp = temp.heat_pump_electric_mw.fillna(0)
    ax2.bar(temp.coolant_outlet_temp_c.astype(str), hp, color=colors)
    ax2.set(xlabel="Coolant outlet (°C)", ylabel="Heat-pump electricity (MW)", title="Low-temperature recovery has an electrical cost")
    ax2.tick_params(axis="x", rotation=30)
    _savefig("direct_vs_heat_pump.png")

    efficiency = sens[
        (sens.it_capacity_mw == 10.0)
        & (sens.coolant_outlet_temp_c == 35.0)
        & (sens.outdoor_temp_c == 0.0)
    ].sort_values("collection_fraction")
    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.plot(efficiency.collection_fraction, efficiency.supported_area_m2 / 10_000, "o-")
    ax.set(xlabel="IT heat collection fraction (scenario)", ylabel="Peak-supported area (hectares)", title="Sensitivity to the fraction entering the recovery loop")
    _savefig("sensitivity_collection_fraction.png")

    base = scenario_results[scenario_results.scenario_id == "baseline_10mw"].iloc[0]
    labels = ["IT heat\ngenerated", "Collected", "After HX", "Delivered"]
    values = [
        base.theoretical_heat_mw,
        base.collected_heat_mw,
        base.post_hx_source_heat_mw,
        base.delivered_heat_mw,
    ]
    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.bar(labels, values, color=["#8172b2", "#64b5cd", "#55a868", "#c44e52"])
    ax.set(ylabel="Thermal power (MW)", title="Baseline 10 MW energy-flow checkpoints")
    ax.text(0.99, 0.96, f"HP electricity: {base.heat_pump_electric_mw:.2f} MW\nDistribution loss: {base.distribution_loss_mw:.2f} MW", transform=ax.transAxes, ha="right", va="top", bbox={"facecolor": "white", "alpha": 0.8, "edgecolor": "none"})
    _savefig("energy_flow_checkpoints.png")

    hours = profile_results.hour
    fig, ax = plt.subplots(figsize=(8, 4.4))
    ax.plot(hours, profile_results.available_heat_kw_after_distribution / 1_000, "o-", label="Available heat after distribution")
    ax.plot(hours, profile_results.greenhouse_demand_kw / 1_000, "o-", label="Greenhouse demand")
    ax.fill_between(hours, profile_results.greenhouse_demand_kw / 1_000, profile_results.available_heat_kw_after_distribution / 1_000, where=(profile_results.available_heat_kw_after_distribution >= profile_results.greenhouse_demand_kw), alpha=0.18, label="Surplus")
    ax.fill_between(hours, profile_results.greenhouse_demand_kw / 1_000, profile_results.available_heat_kw_after_distribution / 1_000, where=(profile_results.available_heat_kw_after_distribution < profile_results.greenhouse_demand_kw), alpha=0.18, label="Deficit")
    ax.set(xlabel="Hour in illustrative winter day", ylabel="Thermal power (MW)", title="Synthetic mismatch profile: storage can shift surplus")
    ax.legend(frameon=False, ncol=2)
    _savefig("illustrative_day_supply_demand.png")

    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.plot(hours, dispatch.state_of_charge_kwh, "o-", color="#4c72b0")
    ax.set(xlabel="Hour in illustrative winter day", ylabel="Stored heat (kWh)", title="Illustrative storage state of charge")
    _savefig("illustrative_day_storage.png")


if __name__ == "__main__":
    main()
