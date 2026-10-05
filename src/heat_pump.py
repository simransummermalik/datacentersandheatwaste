"""Heat-pump screening calculations.

This is an energy-balance model, not equipment-selection software.  It estimates
an achievable heating COP as a fraction of the Carnot limit and applies explicit
bounds so that a small modeled temperature lift does not imply an implausibly
large COP.
"""

from __future__ import annotations

from dataclasses import dataclass


KELVIN_OFFSET = 273.15


@dataclass(frozen=True)
class HeatPumpResult:
    """Calculated heat-pump temperatures, COP, and energy flows."""

    evaporating_temp_c: float
    condensing_temp_c: float
    carnot_cop: float
    heating_cop: float
    source_heat_kw: float
    compressor_power_kw: float
    condenser_heat_kw: float


def estimate_heating_cop(
    source_fluid_temp_c: float,
    sink_supply_temp_c: float,
    carnot_efficiency: float = 0.45,
    source_approach_c: float = 5.0,
    sink_approach_c: float = 5.0,
    minimum_cop: float = 1.5,
    maximum_cop: float = 6.0,
) -> tuple[float, float, float, float]:
    """Return ``(COP, Carnot COP, evaporating C, condensing C)``.

    ``source_approach_c`` and ``sink_approach_c`` represent temperature gaps
    across the evaporator and condenser.  The result is intended for scenario
    screening.  A real design needs manufacturer maps at the actual part load,
    flow, and entering/leaving temperatures.
    """

    if not 0.0 < carnot_efficiency <= 1.0:
        raise ValueError("carnot_efficiency must be in (0, 1]")
    if minimum_cop <= 1.0 or maximum_cop < minimum_cop:
        raise ValueError("COP limits must satisfy 1 < minimum <= maximum")
    if source_approach_c < 0.0 or sink_approach_c < 0.0:
        raise ValueError("approach temperatures cannot be negative")

    evaporating_temp_c = source_fluid_temp_c - source_approach_c
    condensing_temp_c = sink_supply_temp_c + sink_approach_c
    temperature_lift_k = condensing_temp_c - evaporating_temp_c
    if temperature_lift_k <= 0.0:
        raise ValueError(
            "The heat-pump condenser must be warmer than the evaporator; "
            "use direct exchange when the source is already hot enough."
        )

    carnot_cop = (condensing_temp_c + KELVIN_OFFSET) / temperature_lift_k
    estimated_cop = carnot_efficiency * carnot_cop
    heating_cop = min(max(estimated_cop, minimum_cop), maximum_cop)
    return heating_cop, carnot_cop, evaporating_temp_c, condensing_temp_c


def upgrade_source_heat(
    source_heat_kw: float,
    source_fluid_temp_c: float,
    sink_supply_temp_c: float,
    carnot_efficiency: float = 0.45,
    source_approach_c: float = 5.0,
    sink_approach_c: float = 5.0,
    minimum_cop: float = 1.5,
    maximum_cop: float = 6.0,
) -> HeatPumpResult:
    """Upgrade recovered source heat and keep compressor energy explicit.

    Heating COP is ``Q_condenser / W_compressor``.  With recovered heat entering
    the evaporator, ``Q_condenser = Q_source * COP / (COP - 1)``.
    """

    if source_heat_kw < 0.0:
        raise ValueError("source_heat_kw cannot be negative")

    cop, carnot_cop, evaporating_c, condensing_c = estimate_heating_cop(
        source_fluid_temp_c=source_fluid_temp_c,
        sink_supply_temp_c=sink_supply_temp_c,
        carnot_efficiency=carnot_efficiency,
        source_approach_c=source_approach_c,
        sink_approach_c=sink_approach_c,
        minimum_cop=minimum_cop,
        maximum_cop=maximum_cop,
    )
    compressor_power_kw = source_heat_kw / (cop - 1.0)
    condenser_heat_kw = source_heat_kw + compressor_power_kw
    return HeatPumpResult(
        evaporating_temp_c=evaporating_c,
        condensing_temp_c=condensing_c,
        carnot_cop=carnot_cop,
        heating_cop=cop,
        source_heat_kw=source_heat_kw,
        compressor_power_kw=compressor_power_kw,
        condenser_heat_kw=condenser_heat_kw,
    )

