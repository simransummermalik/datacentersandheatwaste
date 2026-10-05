"""Short-horizon sensible-heat storage and dispatch utilities."""

from __future__ import annotations

from dataclasses import dataclass
from math import inf
from typing import Sequence


@dataclass(frozen=True)
class StorageDispatch:
    """One storage-dispatch simulation."""

    state_of_charge_kwh: list[float]
    direct_to_load_kwh: list[float]
    charged_kwh: list[float]
    discharged_to_load_kwh: list[float]
    backup_heat_kwh: list[float]
    curtailed_heat_kwh: list[float]
    standing_loss_kwh: list[float]

    @property
    def total_backup_kwh(self) -> float:
        return sum(self.backup_heat_kwh)

    @property
    def total_curtailed_kwh(self) -> float:
        return sum(self.curtailed_heat_kwh)

    @property
    def total_standing_loss_kwh(self) -> float:
        return sum(self.standing_loss_kwh)


def minimum_cyclic_storage_capacity_kwh(
    supply_kw: Sequence[float],
    demand_kw: Sequence[float],
    timestep_hours: float = 1.0,
) -> float:
    """Return ideal storage needed to time-shift one repeating profile.

    The calculation assumes lossless storage with unlimited charge/discharge
    power.  If average supply is lower than average demand, no finite store can
    close the energy deficit and ``math.inf`` is returned.
    """

    if len(supply_kw) != len(demand_kw) or not supply_kw:
        raise ValueError("supply_kw and demand_kw must be non-empty and equal length")
    if timestep_hours <= 0.0:
        raise ValueError("timestep_hours must be positive")

    deficits = [
        (float(demand) - float(supply)) * timestep_hours
        for supply, demand in zip(supply_kw, demand_kw, strict=True)
    ]
    if sum(deficits) > 1e-9:
        return inf

    # Maximum circular subarray sum: the largest energy drawdown between two
    # opportunities to refill the tank.
    maximum_drawdown = 0.0
    count = len(deficits)
    for start in range(count):
        running = 0.0
        for width in range(count):
            running += deficits[(start + width) % count]
            maximum_drawdown = max(maximum_drawdown, running)
    return maximum_drawdown


def simulate_storage_dispatch(
    supply_kw: Sequence[float],
    demand_kw: Sequence[float],
    capacity_kwh: float,
    timestep_hours: float = 1.0,
    initial_state_of_charge_kwh: float | None = None,
    charge_efficiency: float = 0.98,
    discharge_efficiency: float = 0.98,
    standing_loss_fraction_per_hour: float = 0.001,
) -> StorageDispatch:
    """Dispatch supply to demand, then charge/discharge a bounded heat store."""

    if len(supply_kw) != len(demand_kw) or not supply_kw:
        raise ValueError("supply_kw and demand_kw must be non-empty and equal length")
    if capacity_kwh < 0.0 or timestep_hours <= 0.0:
        raise ValueError("capacity must be nonnegative and timestep positive")
    for name, value in (
        ("charge_efficiency", charge_efficiency),
        ("discharge_efficiency", discharge_efficiency),
    ):
        if not 0.0 < value <= 1.0:
            raise ValueError(f"{name} must be in (0, 1]")
    if not 0.0 <= standing_loss_fraction_per_hour < 1.0:
        raise ValueError("standing loss fraction must be in [0, 1)")

    state = capacity_kwh if initial_state_of_charge_kwh is None else float(
        initial_state_of_charge_kwh
    )
    if not 0.0 <= state <= capacity_kwh:
        raise ValueError("initial state of charge must lie within storage capacity")

    states: list[float] = []
    direct: list[float] = []
    charged: list[float] = []
    discharged: list[float] = []
    backup: list[float] = []
    curtailed: list[float] = []
    losses: list[float] = []

    interval_loss_fraction = 1.0 - (
        1.0 - standing_loss_fraction_per_hour
    ) ** timestep_hours

    for supply_power, demand_power in zip(supply_kw, demand_kw, strict=True):
        supply_energy = max(float(supply_power), 0.0) * timestep_hours
        demand_energy = max(float(demand_power), 0.0) * timestep_hours

        standing_loss = state * interval_loss_fraction
        state -= standing_loss

        direct_energy = min(supply_energy, demand_energy)
        surplus = supply_energy - direct_energy
        deficit = demand_energy - direct_energy

        room = capacity_kwh - state
        energy_into_store = min(surplus * charge_efficiency, room)
        source_energy_charged = energy_into_store / charge_efficiency
        state += energy_into_store
        curtailed_energy = surplus - source_energy_charged

        deliverable = state * discharge_efficiency
        discharged_to_load = min(deficit, deliverable)
        state -= discharged_to_load / discharge_efficiency
        backup_energy = deficit - discharged_to_load

        states.append(state)
        direct.append(direct_energy)
        charged.append(energy_into_store)
        discharged.append(discharged_to_load)
        backup.append(backup_energy)
        curtailed.append(max(curtailed_energy, 0.0))
        losses.append(standing_loss)

    return StorageDispatch(
        state_of_charge_kwh=states,
        direct_to_load_kwh=direct,
        charged_kwh=charged,
        discharged_to_load_kwh=discharged,
        backup_heat_kwh=backup,
        curtailed_heat_kwh=curtailed,
        standing_loss_kwh=losses,
    )


def water_storage_volume_m3(
    usable_capacity_kwh: float,
    storage_delta_t_c: float,
    water_density_kg_m3: float = 997.0,
    water_specific_heat_kj_kgk: float = 4.186,
) -> float:
    """Convert usable sensible-heat capacity to an ideal water volume."""

    if usable_capacity_kwh < 0.0:
        raise ValueError("usable_capacity_kwh cannot be negative")
    if storage_delta_t_c <= 0.0:
        raise ValueError("storage_delta_t_c must be positive")
    energy_per_m3_kwh = (
        water_density_kg_m3
        * water_specific_heat_kj_kgk
        * storage_delta_t_c
        / 3_600.0
    )
    return usable_capacity_kwh / energy_per_m3_kwh

