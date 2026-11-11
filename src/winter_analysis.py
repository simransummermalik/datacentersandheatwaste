"""Hourly winter reliability and operating-energy accounting.

The source and weather series are paired by UTC hour for a *hypothetical*
Charlotte installation. The measured source load is a cross-site temporal proxy.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from math import isclose
from typing import Sequence

from .greenhouse_load import GreenhouseInputs, heating_demand_kw
from .heat_recovery import HeatRecoveryInputs, evaluate_heat_recovery
from .thermal_storage import simulate_storage_dispatch


@dataclass(frozen=True)
class WinterCase:
    name: str
    floor_area_m2: float
    storage_capacity_kwh: float
    it_load_profile: str = "measured_proxy"


def scaled_load_fractions(
    measured_it_kw: Sequence[float], nameplate_kw: float, target_mean_fraction: float
) -> list[float]:
    """Preserve measured temporal variation while setting an explicit mean load."""
    if not measured_it_kw or nameplate_kw <= 0 or not 0 < target_mean_fraction <= 1:
        raise ValueError("Profile, nameplate, and target mean must be positive")
    if any(power <= 0 for power in measured_it_kw):
        raise ValueError("Measured IT power must be positive in every hour")
    observed_mean = sum(measured_it_kw) / len(measured_it_kw)
    fractions = [power / observed_mean * target_mean_fraction for power in measured_it_kw]
    if max(fractions) > 1.0 + 1e-9:
        raise ValueError("Scaling exceeds nameplate IT capacity; choose a lower mean")
    assert isclose(sum(fractions) / len(fractions), target_mean_fraction, rel_tol=1e-12)
    return fractions


def run_winter_case(
    case: WinterCase,
    timestamps_utc: Sequence[str],
    outdoor_temp_c: Sequence[float],
    it_load_fractions: Sequence[float],
    heat_inputs: HeatRecoveryInputs,
    greenhouse_inputs: GreenhouseInputs,
    charge_efficiency: float,
    discharge_efficiency: float,
    standing_loss_fraction_per_hour: float,
    electricity_price_per_kwh: float,
    gas_price_per_mcf: float,
    gas_mmbtu_per_mcf: float,
    boiler_efficiency: float,
    pump_electricity_fraction: float,
) -> tuple[list[dict[str, float | str | int]], dict[str, float | str | int]]:
    """Dispatch hourly recovered heat and compare equal-demand heating costs.

    The compressor and circulation energy is counted only for heat actually
    sent to the load or charged into storage. This assumes a modulating heat
    pump at the modeled COP. Storage begins empty, avoiding free initial heat.
    """
    count = len(timestamps_utc)
    if count == 0 or not (len(outdoor_temp_c) == len(it_load_fractions) == count):
        raise ValueError("Hourly arrays must be nonempty and aligned")
    if not 0 < boiler_efficiency <= 1 or not 0 <= pump_electricity_fraction < 1:
        raise ValueError("Invalid boiler efficiency or pump electricity fraction")
    if min(electricity_price_per_kwh, gas_price_per_mcf, gas_mmbtu_per_mcf) <= 0:
        raise ValueError("Prices and gas heat content must be positive")

    # 1 MMBtu = 293.071070172 kWh, a thermochemical unit conversion.
    gas_price_per_fuel_kwh = gas_price_per_mcf / (gas_mmbtu_per_mcf * 293.071070172)
    available_kw: list[float] = []
    demand_kw: list[float] = []
    compressor_ratio: list[float] = []
    for temperature, load_fraction in zip(outdoor_temp_c, it_load_fractions, strict=True):
        recovery = evaluate_heat_recovery(replace(heat_inputs, it_load_fraction=load_fraction))
        available_kw.append(recovery.delivered_heat_kw)
        demand_kw.append(heating_demand_kw(case.floor_area_m2, temperature, greenhouse_inputs))
        compressor_ratio.append(
            recovery.heat_pump_electric_kw / recovery.delivered_heat_kw
            if recovery.delivered_heat_kw > 0 else 0.0
        )

    dispatch = simulate_storage_dispatch(
        available_kw,
        demand_kw,
        capacity_kwh=case.storage_capacity_kwh,
        initial_state_of_charge_kwh=0.0,
        charge_efficiency=charge_efficiency,
        discharge_efficiency=discharge_efficiency,
        standing_loss_fraction_per_hour=standing_loss_fraction_per_hour,
    )

    rows: list[dict[str, float | str | int]] = []
    for index, timestamp in enumerate(timestamps_utc):
        # The heat pump must make heat sent directly to load plus heat entering
        # the tank before charging loss. It need not run for curtailed heat.
        hp_delivered_kwh = (
            dispatch.direct_to_load_kwh[index]
            + dispatch.charged_kwh[index] / charge_efficiency
        )
        compressor_kwh = hp_delivered_kwh * compressor_ratio[index]
        pump_kwh = hp_delivered_kwh * pump_electricity_fraction
        rows.append(
            {
                "case": case.name,
                "timestamp_utc": timestamp,
                "outdoor_temp_c": outdoor_temp_c[index],
                "it_load_fraction": it_load_fractions[index],
                "it_power_kw": heat_inputs.it_capacity_mw * 1000 * it_load_fractions[index],
                "greenhouse_demand_kwh": demand_kw[index],
                "available_heat_kwh": available_kw[index],
                "direct_heat_kwh": dispatch.direct_to_load_kwh[index],
                "stored_heat_to_load_kwh": dispatch.discharged_to_load_kwh[index],
                "storage_charge_kwh": dispatch.charged_kwh[index],
                "storage_soc_kwh": dispatch.state_of_charge_kwh[index],
                "backup_heat_kwh": dispatch.backup_heat_kwh[index],
                "curtailed_heat_kwh": dispatch.curtailed_heat_kwh[index],
                "compressor_electricity_kwh": compressor_kwh,
                "pump_electricity_kwh": pump_kwh,
                "heating_hour": int(demand_kw[index] > 1e-9),
                "covered_without_backup": int(demand_kw[index] > 1e-9 and dispatch.backup_heat_kwh[index] <= 1e-6),
            }
        )

    def total(field: str) -> float:
        return sum(float(row[field]) for row in rows)

    heating_hours = int(total("heating_hour"))
    covered_hours = int(total("covered_without_backup"))
    winter_hours_without_backup = sum(float(row["backup_heat_kwh"]) <= 1e-6 for row in rows)
    demand = total("greenhouse_demand_kwh")
    backup = total("backup_heat_kwh")
    hp_electricity = total("compressor_electricity_kwh")
    pump_electricity = total("pump_electricity_kwh")
    gas_reference = demand / boiler_efficiency * gas_price_per_fuel_kwh
    electric_reference = demand * electricity_price_per_kwh
    recovered_plus_gas = (
        (hp_electricity + pump_electricity) * electricity_price_per_kwh
        + backup / boiler_efficiency * gas_price_per_fuel_kwh
    )
    recovered_plus_electric = (
        (hp_electricity + pump_electricity + backup) * electricity_price_per_kwh
    )
    assert isclose(
        demand,
        total("direct_heat_kwh") + total("stored_heat_to_load_kwh") + backup,
        rel_tol=1e-10,
    )
    summary: dict[str, float | str | int] = {
        "case": case.name,
        "floor_area_m2": case.floor_area_m2,
        "storage_capacity_mwh": case.storage_capacity_kwh / 1000,
        "it_load_profile": case.it_load_profile,
        "winter_hours": count,
        "heating_hours": heating_hours,
        "covered_heating_hours": covered_hours,
        "heating_hours_without_backup_pct": 100 * covered_hours / heating_hours,
        "winter_hours_without_backup": winter_hours_without_backup,
        "winter_hours_without_backup_pct": 100 * winter_hours_without_backup / count,
        "greenhouse_demand_mwh": demand / 1000,
        "recovered_heat_to_load_mwh": (demand - backup) / 1000,
        "backup_heat_mwh": backup / 1000,
        "backup_energy_share_pct": 100 * backup / demand,
        "compressor_electricity_mwh": hp_electricity / 1000,
        "pump_electricity_mwh": pump_electricity / 1000,
        "thermal_storage_charge_mwh": total("storage_charge_kwh") / 1000,
        "thermal_storage_discharge_mwh": total("stored_heat_to_load_kwh") / 1000,
        "thermal_storage_end_soc_mwh": dispatch.state_of_charge_kwh[-1] / 1000,
        "curtailed_heat_mwh": total("curtailed_heat_kwh") / 1000,
        "electric_resistance_reference_usd": electric_reference,
        "gas_boiler_reference_usd": gas_reference,
        "recovery_plus_electric_backup_usd": recovered_plus_electric,
        "recovery_plus_gas_backup_usd": recovered_plus_gas,
        "electric_reference_savings_pct": 100 * (1 - recovered_plus_electric / electric_reference),
        "gas_reference_savings_pct": 100 * (1 - recovered_plus_gas / gas_reference),
    }
    return rows, summary
