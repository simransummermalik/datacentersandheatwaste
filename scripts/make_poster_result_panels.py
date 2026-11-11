"""Make compact, plain research-poster panels from the winter results.

These panels have no built-in section titles so they can sit under the poster's
existing headers. Run after scripts/run_winter_analysis.py.
"""

from __future__ import annotations

import csv
from datetime import datetime
import os
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".matplotlib-cache"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt


RESULTS = ROOT / "results"
CHARTS = ROOT / "charts"
GREEN = "#005030"
INK = "#202020"
MUTED = "#555555"

plt.rcParams.update(
    {
        "font.family": "Times New Roman",
        "font.size": 11,
        "text.color": INK,
        "axes.labelcolor": INK,
        "xtick.color": INK,
        "ytick.color": INK,
        "axes.edgecolor": INK,
        "svg.fonttype": "none",
        "savefig.facecolor": "white",
    }
)


def read_rows(name: str) -> list[dict[str, str]]:
    with (RESULTS / name).open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def save(fig: plt.Figure, name: str) -> None:
    CHARTS.mkdir(exist_ok=True)
    fig.savefig(CHARTS / f"{name}.png", dpi=300, facecolor="white")
    fig.savefig(CHARTS / f"{name}.svg", facecolor="white")
    plt.close(fig)


def rule(ax: plt.Axes, y: float, weight: float = 0.8) -> None:
    ax.plot([0.03, 0.97], [y, y], color=INK, linewidth=weight, transform=ax.transAxes)


def reliability_table(summary: dict[str, dict[str, str]]) -> None:
    fig, ax = plt.subplots(figsize=(7.2, 2.55))
    fig.subplots_adjust(left=0.02, right=0.98, top=0.98, bottom=0.02)
    ax.axis("off")
    ax.text(0.04, 0.88, "2.7 ha greenhouse · 2,054 heating hours", fontsize=13, fontweight="bold", transform=ax.transAxes)
    rule(ax, 0.80, 1.0)
    ax.text(0.04, 0.71, "Compute-load case", fontweight="bold", transform=ax.transAxes)
    ax.text(0.68, 0.71, "Hours covered", ha="right", fontweight="bold", transform=ax.transAxes)
    ax.text(0.96, 0.71, "Backup heat", ha="right", fontweight="bold", transform=ax.transAxes)
    rule(ax, 0.65, 0.55)
    cases = [
        ("Measured shape; no tank", "measured_2_7ha_no_storage"),
        ("Measured shape; 10.5 MWh tank", "measured_2_7ha_10_53mwh"),
        ("Flat 8 MW; 10.5 MWh tank", "constant_2_7ha_10_53mwh"),
    ]
    for y, (label, key) in zip([0.54, 0.40, 0.26], cases):
        row = summary[key]
        ax.text(0.04, y, label, transform=ax.transAxes)
        ax.text(0.68, y, f"{float(row['heating_hours_without_backup_pct']):.1f}%", ha="right", fontweight="bold" if key == "measured_2_7ha_10_53mwh" else "normal", transform=ax.transAxes)
        ax.text(0.96, y, f"{float(row['backup_heat_mwh']):.0f} MWh", ha="right", transform=ax.transAxes)
    rule(ax, 0.19, 1.0)
    ax.text(0.04, 0.09, "Measured shape: NLR Colorado HPC; weather: NOAA Charlotte. Hypothetical pairing.", fontsize=9.5, color=MUTED, transform=ax.transAxes)
    save(fig, "poster_reliability_table")


def cost_table(summary: dict[str, dict[str, str]]) -> None:
    row = summary["measured_2_7ha_10_53mwh"]
    fig, ax = plt.subplots(figsize=(6.1, 2.35))
    fig.subplots_adjust(left=0.02, right=0.98, top=0.98, bottom=0.02)
    ax.axis("off")
    ax.text(0.04, 0.88, "90-day heating energy cost · 2.7 ha greenhouse", fontsize=12.5, fontweight="bold", transform=ax.transAxes)
    rule(ax, 0.79, 1)
    ax.text(0.04, 0.68, "Reference heater", fontweight="bold", transform=ax.transAxes)
    ax.text(0.67, 0.68, "Heater alone", ha="right", fontweight="bold", transform=ax.transAxes)
    ax.text(0.96, 0.68, "Recovery + backup", ha="right", fontweight="bold", transform=ax.transAxes)
    rule(ax, 0.62, 0.55)
    ax.text(0.04, 0.49, "Electric resistance", transform=ax.transAxes)
    ax.text(0.67, 0.49, f"${float(row['electric_resistance_reference_usd']) / 1000:,.0f}k", ha="right", transform=ax.transAxes)
    ax.text(0.96, 0.49, f"${float(row['recovery_plus_electric_backup_usd']) / 1000:,.0f}k", ha="right", transform=ax.transAxes)
    ax.text(0.04, 0.34, "Gas boiler (85% efficient)", transform=ax.transAxes)
    ax.text(0.67, 0.34, f"${float(row['gas_boiler_reference_usd']) / 1000:,.0f}k", ha="right", transform=ax.transAxes)
    ax.text(0.96, 0.34, f"${float(row['recovery_plus_gas_backup_usd']) / 1000:,.0f}k", ha="right", transform=ax.transAxes)
    rule(ax, 0.25, 1)
    ax.text(0.04, 0.14, "EIA NC 2025 averages; energy only. Excludes capital and heat purchase.", fontsize=9.5, color=MUTED, transform=ax.transAxes)
    save(fig, "poster_cost_table")


def cost_sidebar(summary: dict[str, dict[str, str]]) -> None:
    row = summary["measured_2_7ha_10_53mwh"]
    fig, ax = plt.subplots(figsize=(3.4, 3.9))
    fig.subplots_adjust(left=0.03, right=0.97, top=0.98, bottom=0.02)
    ax.axis("off")
    ax.text(0.05, 0.93, "Electric resistance", fontsize=14, fontweight="bold", transform=ax.transAxes)
    rule(ax, 0.88)
    ax.text(0.06, 0.79, "Heater alone", transform=ax.transAxes)
    ax.text(0.95, 0.79, f"${float(row['electric_resistance_reference_usd']) / 1000:,.0f}k", ha="right", transform=ax.transAxes)
    ax.text(0.06, 0.69, "Recovery + backup", transform=ax.transAxes)
    ax.text(0.95, 0.69, f"${float(row['recovery_plus_electric_backup_usd']) / 1000:,.0f}k", ha="right", fontweight="bold", transform=ax.transAxes)
    ax.text(0.05, 0.56, "Gas boiler (85%)", fontsize=14, fontweight="bold", transform=ax.transAxes)
    rule(ax, 0.51)
    ax.text(0.06, 0.42, "Boiler alone", transform=ax.transAxes)
    ax.text(0.95, 0.42, f"${float(row['gas_boiler_reference_usd']) / 1000:,.0f}k", ha="right", transform=ax.transAxes)
    ax.text(0.06, 0.32, "Recovery + backup", transform=ax.transAxes)
    ax.text(0.95, 0.32, f"${float(row['recovery_plus_gas_backup_usd']) / 1000:,.0f}k", ha="right", fontweight="bold", transform=ax.transAxes)
    rule(ax, 0.23)
    ax.text(0.05, 0.16, "Reference heaters; energy only.", fontsize=10, color=MUTED, transform=ax.transAxes)
    ax.text(0.05, 0.10, "EIA NC 2025 average prices.", fontsize=10, color=MUTED, transform=ax.transAxes)
    ax.text(0.05, 0.04, "Excludes equipment and piping.", fontsize=10, color=MUTED, transform=ax.transAxes)
    save(fig, "poster_cost_sidebar")


def low_load_event(hourly: list[dict[str, str]]) -> None:
    winter = [row for row in hourly if row["case"] == "measured_2_7ha_10_53mwh"]
    local = ZoneInfo("America/New_York")
    window = [
        row for row in winter
        if "2024-12-20T12:00:00Z" <= row["timestamp_utc"] <= "2024-12-24T06:00:00Z"
    ]
    timestamps = [datetime.fromisoformat(row["timestamp_utc"].replace("Z", "+00:00")).astimezone(local) for row in window]
    supply = [float(row["available_heat_kwh"]) / 1000 for row in window]
    demand = [float(row["greenhouse_demand_kwh"]) / 1000 for row in window]
    fig, ax = plt.subplots(figsize=(7.2, 3.7))
    fig.subplots_adjust(left=0.12, right=0.97, top=0.96, bottom=0.23)
    ax.plot(timestamps, demand, color=INK, linewidth=1.7, label="Greenhouse demand")
    ax.plot(timestamps, supply, color=GREEN, linewidth=1.7, label="Available recovered heat")
    ax.set_ylim(0, 5)
    ax.set_ylabel("Thermal power (MW)")
    ax.set_xlabel("December 2024, Charlotte local time")
    ax.xaxis.set_major_locator(mdates.DayLocator(tz=local))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d", tz=local))
    ax.spines[["top", "right"]].set_visible(False)
    ax.yaxis.grid(True, color="#dddddd", linewidth=0.5)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, loc="upper left", fontsize=10)
    save(fig, "poster_low_load_event")


def main() -> None:
    summary = {row["case"]: row for row in read_rows("winter_summary.csv")}
    reliability_table(summary)
    cost_table(summary)
    cost_sidebar(summary)
    low_load_event(read_rows("winter_hourly_results.csv"))


if __name__ == "__main__":
    main()
