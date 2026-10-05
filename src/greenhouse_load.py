"""Transparent steady-state greenhouse space-heating calculations."""

from __future__ import annotations

from dataclasses import dataclass
from math import inf


@dataclass(frozen=True)
class GreenhouseInputs:
    """Envelope and infiltration inputs normalized by greenhouse floor area."""

    indoor_temp_c: float
    envelope_u_value_w_m2k: float
    envelope_area_to_floor_area: float
    air_changes_per_hour: float
    mean_height_m: float
    air_density_kg_m3: float = 1.204
    air_specific_heat_j_kgk: float = 1_006.0
    design_margin_fraction: float = 0.10


@dataclass(frozen=True)
class GreenhouseLoadBreakdown:
    """Heat-loss intensities per square metre of greenhouse floor."""

    delta_t_k: float
    transmission_w_m2: float
    infiltration_w_m2: float
    subtotal_w_m2: float
    design_heat_w_m2: float


def heat_loss_intensity(
    outdoor_temp_c: float, inputs: GreenhouseInputs
) -> GreenhouseLoadBreakdown:
    """Return design heating intensity from transmission plus infiltration.

    Solar gains, crop evapotranspiration, ground exchange, thermal screens, and
    equipment gains are intentionally excluded.  This makes the result a
    screening load, not a crop-production energy simulation.
    """

    nonnegative = {
        "envelope_u_value_w_m2k": inputs.envelope_u_value_w_m2k,
        "envelope_area_to_floor_area": inputs.envelope_area_to_floor_area,
        "air_changes_per_hour": inputs.air_changes_per_hour,
        "mean_height_m": inputs.mean_height_m,
        "air_density_kg_m3": inputs.air_density_kg_m3,
        "air_specific_heat_j_kgk": inputs.air_specific_heat_j_kgk,
        "design_margin_fraction": inputs.design_margin_fraction,
    }
    if any(value < 0.0 for value in nonnegative.values()):
        raise ValueError("Greenhouse heat-loss inputs cannot be negative")

    delta_t_k = max(inputs.indoor_temp_c - outdoor_temp_c, 0.0)
    transmission_coefficient = (
        inputs.envelope_u_value_w_m2k * inputs.envelope_area_to_floor_area
    )
    infiltration_coefficient = (
        inputs.air_density_kg_m3
        * inputs.air_specific_heat_j_kgk
        * inputs.air_changes_per_hour
        * inputs.mean_height_m
        / 3_600.0
    )
    transmission_w_m2 = transmission_coefficient * delta_t_k
    infiltration_w_m2 = infiltration_coefficient * delta_t_k
    subtotal_w_m2 = transmission_w_m2 + infiltration_w_m2
    design_heat_w_m2 = subtotal_w_m2 * (1.0 + inputs.design_margin_fraction)
    return GreenhouseLoadBreakdown(
        delta_t_k=delta_t_k,
        transmission_w_m2=transmission_w_m2,
        infiltration_w_m2=infiltration_w_m2,
        subtotal_w_m2=subtotal_w_m2,
        design_heat_w_m2=design_heat_w_m2,
    )


def heating_demand_kw(
    floor_area_m2: float, outdoor_temp_c: float, inputs: GreenhouseInputs
) -> float:
    """Calculate instantaneous sensible space-heating demand in kW."""

    if floor_area_m2 < 0.0:
        raise ValueError("floor_area_m2 cannot be negative")
    intensity = heat_loss_intensity(outdoor_temp_c, inputs).design_heat_w_m2
    return floor_area_m2 * intensity / 1_000.0


def supported_floor_area_m2(
    available_heat_kw: float, outdoor_temp_c: float, inputs: GreenhouseInputs
) -> float:
    """Return floor area whose modeled peak load equals available heat."""

    if available_heat_kw < 0.0:
        raise ValueError("available_heat_kw cannot be negative")
    intensity = heat_loss_intensity(outdoor_temp_c, inputs).design_heat_w_m2
    if intensity == 0.0:
        return inf
    return available_heat_kw * 1_000.0 / intensity

