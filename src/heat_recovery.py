"""Steady-state energy balance from IT electrical load to delivered heat."""

from __future__ import annotations

from dataclasses import dataclass

from .heat_pump import upgrade_source_heat


def _fraction(name: str, value: float) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between 0 and 1")


@dataclass(frozen=True)
class HeatRecoveryInputs:
    """Inputs for one steady-state data-center heat-recovery scenario."""

    it_capacity_mw: float
    it_load_fraction: float
    heat_conversion_fraction: float
    collection_fraction: float
    heat_exchanger_effectiveness: float
    coolant_outlet_temp_c: float
    greenhouse_supply_temp_c: float
    direct_hx_approach_c: float
    distribution_loss_fraction: float
    hp_carnot_efficiency: float = 0.45
    hp_source_approach_c: float = 5.0
    hp_sink_approach_c: float = 5.0
    hp_minimum_cop: float = 1.5
    hp_maximum_cop: float = 6.0


@dataclass(frozen=True)
class HeatRecoveryResult:
    """Energy-flow result; all power fields are thermal unless noted."""

    operating_it_power_kw: float
    heat_generated_kw: float
    heat_collected_kw: float
    heat_after_exchanger_kw: float
    pathway: str
    direct_exchange_feasible: bool
    heating_cop: float | None
    heat_pump_electric_kw: float
    heat_before_distribution_kw: float
    distribution_loss_kw: float
    delivered_heat_kw: float


def evaluate_heat_recovery(inputs: HeatRecoveryInputs) -> HeatRecoveryResult:
    """Evaluate heat collection, temperature lift, and distribution losses.

    ``collection_fraction`` is the fraction of server heat entering the selected
    recovery loop.  ``heat_exchanger_effectiveness`` is then applied once to
    that collected stream.  It must not be interpreted as a second published
    plant-wide recovery fraction.
    """

    if inputs.it_capacity_mw < 0.0:
        raise ValueError("it_capacity_mw cannot be negative")
    for name in (
        "it_load_fraction",
        "heat_conversion_fraction",
        "collection_fraction",
        "heat_exchanger_effectiveness",
        "distribution_loss_fraction",
    ):
        _fraction(name, getattr(inputs, name))
    if inputs.direct_hx_approach_c < 0.0:
        raise ValueError("direct_hx_approach_c cannot be negative")

    operating_it_power_kw = inputs.it_capacity_mw * 1_000.0 * inputs.it_load_fraction
    heat_generated_kw = operating_it_power_kw * inputs.heat_conversion_fraction
    heat_collected_kw = heat_generated_kw * inputs.collection_fraction
    heat_after_exchanger_kw = heat_collected_kw * inputs.heat_exchanger_effectiveness

    direct_exchange_feasible = (
        inputs.coolant_outlet_temp_c
        >= inputs.greenhouse_supply_temp_c + inputs.direct_hx_approach_c
    )

    if direct_exchange_feasible:
        pathway = "direct"
        heating_cop = None
        heat_pump_electric_kw = 0.0
        heat_before_distribution_kw = heat_after_exchanger_kw
    else:
        pathway = "heat_pump"
        upgraded = upgrade_source_heat(
            source_heat_kw=heat_after_exchanger_kw,
            source_fluid_temp_c=inputs.coolant_outlet_temp_c,
            sink_supply_temp_c=inputs.greenhouse_supply_temp_c,
            carnot_efficiency=inputs.hp_carnot_efficiency,
            source_approach_c=inputs.hp_source_approach_c,
            sink_approach_c=inputs.hp_sink_approach_c,
            minimum_cop=inputs.hp_minimum_cop,
            maximum_cop=inputs.hp_maximum_cop,
        )
        heating_cop = upgraded.heating_cop
        heat_pump_electric_kw = upgraded.compressor_power_kw
        heat_before_distribution_kw = upgraded.condenser_heat_kw

    distribution_loss_kw = (
        heat_before_distribution_kw * inputs.distribution_loss_fraction
    )
    delivered_heat_kw = heat_before_distribution_kw - distribution_loss_kw

    return HeatRecoveryResult(
        operating_it_power_kw=operating_it_power_kw,
        heat_generated_kw=heat_generated_kw,
        heat_collected_kw=heat_collected_kw,
        heat_after_exchanger_kw=heat_after_exchanger_kw,
        pathway=pathway,
        direct_exchange_feasible=direct_exchange_feasible,
        heating_cop=heating_cop,
        heat_pump_electric_kw=heat_pump_electric_kw,
        heat_before_distribution_kw=heat_before_distribution_kw,
        distribution_loss_kw=distribution_loss_kw,
        delivered_heat_kw=delivered_heat_kw,
    )

