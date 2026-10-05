from math import isclose, isinf

from src.greenhouse_load import GreenhouseInputs, heat_loss_intensity, supported_floor_area_m2
from src.heat_pump import upgrade_source_heat
from src.heat_recovery import HeatRecoveryInputs, evaluate_heat_recovery
from src.thermal_storage import minimum_cyclic_storage_capacity_kwh, water_storage_volume_m3


def baseline_inputs(**overrides):
    values = dict(
        it_capacity_mw=10,
        it_load_fraction=0.8,
        heat_conversion_fraction=1.0,
        collection_fraction=0.75,
        heat_exchanger_effectiveness=0.75,
        coolant_outlet_temp_c=35,
        greenhouse_supply_temp_c=40,
        direct_hx_approach_c=5,
        distribution_loss_fraction=0.08,
    )
    values.update(overrides)
    return HeatRecoveryInputs(**values)


def test_baseline_heat_flow_is_auditable():
    result = evaluate_heat_recovery(baseline_inputs())
    assert isclose(result.heat_generated_kw, 8_000.0)
    assert isclose(result.heat_collected_kw, 6_000.0)
    assert isclose(result.heat_after_exchanger_kw, 4_500.0)
    assert result.pathway == "heat_pump"
    assert isclose(result.heating_cop, 6.0)
    assert isclose(result.heat_pump_electric_kw, 900.0)
    assert isclose(result.delivered_heat_kw, 4_968.0)


def test_direct_exchange_threshold_is_explicit():
    assert evaluate_heat_recovery(baseline_inputs(coolant_outlet_temp_c=45)).pathway == "direct"
    assert evaluate_heat_recovery(baseline_inputs(coolant_outlet_temp_c=44.99)).pathway == "heat_pump"


def test_heat_pump_energy_balance():
    result = upgrade_source_heat(4_500, 35, 40)
    assert isclose(result.condenser_heat_kw, result.source_heat_kw + result.compressor_power_kw)
    assert isclose(result.condenser_heat_kw / result.compressor_power_kw, result.heating_cop)


def test_greenhouse_load_components_and_area():
    inputs = GreenhouseInputs(
        indoor_temp_c=18,
        envelope_u_value_w_m2k=3.98,
        envelope_area_to_floor_area=1.5,
        air_changes_per_hour=0.75,
        mean_height_m=4,
        design_margin_fraction=0.1,
    )
    breakdown = heat_loss_intensity(0, inputs)
    assert breakdown.transmission_w_m2 > breakdown.infiltration_w_m2
    assert isclose(breakdown.design_heat_w_m2, 138.191196, rel_tol=1e-6)
    assert isclose(supported_floor_area_m2(4_968, 0, inputs), 35_950.191791, rel_tol=1e-6)


def test_storage_reports_infinite_when_average_energy_is_short():
    assert isinf(minimum_cyclic_storage_capacity_kwh([1, 1], [2, 2]))
    assert isclose(minimum_cyclic_storage_capacity_kwh([0, 10], [5, 5]), 5.0)


def test_water_volume_conversion():
    assert isclose(water_storage_volume_m3(23.18, 20), 1.0, rel_tol=0.01)

