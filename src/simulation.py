"""Join the component models and expose CSV-friendly scenario results."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Mapping

from .greenhouse_load import GreenhouseInputs, heat_loss_intensity, supported_floor_area_m2
from .heat_recovery import HeatRecoveryInputs, evaluate_heat_recovery


def _number(row: Mapping[str, object], key: str) -> float:
    try:
        return float(row[key])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"Scenario field {key!r} must be numeric") from exc


def run_scenario(row: Mapping[str, object]) -> dict[str, object]:
    """Run one scenario mapping and return a flat, CSV-friendly dictionary."""

    heat_inputs = HeatRecoveryInputs(
        it_capacity_mw=_number(row, "it_capacity_mw"),
        it_load_fraction=_number(row, "it_load_fraction"),
        heat_conversion_fraction=_number(row, "heat_conversion_fraction"),
        collection_fraction=_number(row, "collection_fraction"),
        heat_exchanger_effectiveness=_number(row, "heat_exchanger_effectiveness"),
        coolant_outlet_temp_c=_number(row, "coolant_outlet_temp_c"),
        greenhouse_supply_temp_c=_number(row, "greenhouse_supply_temp_c"),
        direct_hx_approach_c=_number(row, "direct_hx_approach_c"),
        distribution_loss_fraction=_number(row, "distribution_loss_fraction"),
        hp_carnot_efficiency=_number(row, "hp_carnot_efficiency"),
        hp_source_approach_c=_number(row, "hp_source_approach_c"),
        hp_sink_approach_c=_number(row, "hp_sink_approach_c"),
        hp_minimum_cop=_number(row, "hp_minimum_cop"),
        hp_maximum_cop=_number(row, "hp_maximum_cop"),
    )
    greenhouse_inputs = GreenhouseInputs(
        indoor_temp_c=_number(row, "greenhouse_indoor_temp_c"),
        envelope_u_value_w_m2k=_number(row, "envelope_u_value_w_m2k"),
        envelope_area_to_floor_area=_number(row, "envelope_area_to_floor_area"),
        air_changes_per_hour=_number(row, "air_changes_per_hour"),
        mean_height_m=_number(row, "greenhouse_mean_height_m"),
        air_density_kg_m3=_number(row, "air_density_kg_m3"),
        air_specific_heat_j_kgk=_number(row, "air_specific_heat_j_kgk"),
        design_margin_fraction=_number(row, "design_margin_fraction"),
    )
    outdoor_temp_c = _number(row, "outdoor_temp_c")

    recovery = evaluate_heat_recovery(heat_inputs)
    greenhouse = heat_loss_intensity(outdoor_temp_c, greenhouse_inputs)
    area_m2 = supported_floor_area_m2(
        recovery.delivered_heat_kw, outdoor_temp_c, greenhouse_inputs
    )

    return {
        "scenario_id": row.get("scenario_id", "unnamed"),
        "description": row.get("description", ""),
        "it_capacity_mw": heat_inputs.it_capacity_mw,
        "it_load_fraction": heat_inputs.it_load_fraction,
        "heat_conversion_fraction": heat_inputs.heat_conversion_fraction,
        "collection_fraction": heat_inputs.collection_fraction,
        "heat_exchanger_effectiveness": heat_inputs.heat_exchanger_effectiveness,
        "operating_it_power_mw": recovery.operating_it_power_kw / 1_000.0,
        "nameplate_theoretical_heat_mw": heat_inputs.it_capacity_mw
        * heat_inputs.heat_conversion_fraction,
        "theoretical_heat_mw": recovery.heat_generated_kw / 1_000.0,
        "collected_heat_mw": recovery.heat_collected_kw / 1_000.0,
        "post_hx_source_heat_mw": recovery.heat_after_exchanger_kw / 1_000.0,
        "coolant_outlet_temp_c": heat_inputs.coolant_outlet_temp_c,
        "greenhouse_supply_temp_c": heat_inputs.greenhouse_supply_temp_c,
        "outdoor_temp_c": outdoor_temp_c,
        "pathway": recovery.pathway,
        "heat_pump_cop": recovery.heating_cop,
        "heat_pump_electric_mw": recovery.heat_pump_electric_kw / 1_000.0,
        "distribution_loss_fraction": heat_inputs.distribution_loss_fraction,
        "distribution_loss_mw": recovery.distribution_loss_kw / 1_000.0,
        "delivered_heat_mw": recovery.delivered_heat_kw / 1_000.0,
        "greenhouse_heat_intensity_w_m2": greenhouse.design_heat_w_m2,
        "greenhouse_indoor_temp_c": greenhouse_inputs.indoor_temp_c,
        "envelope_u_value_w_m2k": greenhouse_inputs.envelope_u_value_w_m2k,
        "envelope_area_to_floor_area": greenhouse_inputs.envelope_area_to_floor_area,
        "air_changes_per_hour": greenhouse_inputs.air_changes_per_hour,
        "greenhouse_mean_height_m": greenhouse_inputs.mean_height_m,
        "supported_area_m2": area_m2,
        "supported_area_hectares": area_m2 / 10_000.0,
        "supported_area_acres": area_m2 / 4_046.8564224,
    }


def read_scenarios(path: str | Path) -> list[dict[str, str]]:
    """Read scenario rows without hiding type conversion in a dataframe."""

    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def run_scenario_file(path: str | Path) -> list[dict[str, object]]:
    """Evaluate every row in a scenario CSV."""

    return [run_scenario(row) for row in read_scenarios(path)]
