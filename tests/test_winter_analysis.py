from math import isclose

import pytest

from src.greenhouse_load import GreenhouseInputs
from src.heat_recovery import HeatRecoveryInputs
from src.winter_analysis import WinterCase, run_winter_case, scaled_load_fractions


HEAT = HeatRecoveryInputs(
    it_capacity_mw=10,
    it_load_fraction=0.8,
    heat_conversion_fraction=1,
    collection_fraction=0.75,
    heat_exchanger_effectiveness=0.75,
    coolant_outlet_temp_c=35,
    greenhouse_supply_temp_c=40,
    direct_hx_approach_c=5,
    distribution_loss_fraction=0.08,
)
GREENHOUSE = GreenhouseInputs(
    indoor_temp_c=18,
    envelope_u_value_w_m2k=3.98,
    envelope_area_to_floor_area=1.5,
    air_changes_per_hour=0.75,
    mean_height_m=4,
    design_margin_fraction=0,
)


def run(loads, capacity):
    return run_winter_case(
        WinterCase("small_test", 27_000, capacity),
        ["a", "b", "c"],
        [0, 0, 20],
        loads,
        HEAT,
        GREENHOUSE,
        charge_efficiency=0.98,
        discharge_efficiency=0.98,
        standing_loss_fraction_per_hour=0.001,
        electricity_price_per_kwh=0.1022,
        gas_price_per_mcf=12.71,
        gas_mmbtu_per_mcf=1.037,
        boiler_efficiency=0.85,
        pump_electricity_fraction=0.02,
    )


def test_measured_shape_scaling_keeps_mean_and_rejects_nameplate_overflow():
    # Use a profile whose 80% normalized peak remains within nameplate.
    fractions = scaled_load_fractions([8, 9, 10], 10, 0.8)
    assert sum(fractions) / 3 == pytest.approx(0.8)
    assert fractions[2] / fractions[0] == pytest.approx(10 / 8)
    with pytest.raises(ValueError, match="exceeds nameplate"):
        scaled_load_fractions([1, 2, 3], 10, 0.8)


def test_empty_store_cannot_supply_first_low_load_hour_and_dispatch_conserves_heat():
    rows, summary = run([0.1, 0.8, 0.8], 10_532)
    assert rows[0]["backup_heat_kwh"] > 0
    assert rows[0]["storage_soc_kwh"] == pytest.approx(0)
    for row in rows:
        assert row["greenhouse_demand_kwh"] == pytest.approx(
            row["direct_heat_kwh"] + row["stored_heat_to_load_kwh"] + row["backup_heat_kwh"]
        )
    assert summary["heating_hours"] == 2
    assert summary["covered_heating_hours"] == 1
    assert summary["winter_hours_without_backup"] == 2
    assert summary["winter_hours_without_backup_pct"] == pytest.approx(200 / 3)


def test_storage_reduces_backup_but_uses_extra_compressor_electricity():
    without_rows, without = run([0.8, 0.1, 0.8], 0)
    rows, with_store = run([0.8, 0.1, 0.8], 10_532)
    assert with_store["backup_heat_mwh"] < without["backup_heat_mwh"]
    assert with_store["compressor_electricity_mwh"] > without["compressor_electricity_mwh"]
    assert without_rows[2]["compressor_electricity_kwh"] == pytest.approx(0)
    assert rows[2]["compressor_electricity_kwh"] > 0  # Charges the tank despite no load.
    assert isclose(
        with_store["gas_boiler_reference_usd"],
        with_store["greenhouse_demand_mwh"] * 1000 / 0.85 * 12.71 / (1.037 * 293.071070172),
    )
