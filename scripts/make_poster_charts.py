"""Regenerate the three plain Times New Roman poster figures.

Run from the repository root with pandas and matplotlib installed:
    python scripts/make_poster_charts.py

The outputs in charts/ are 300 dpi PNGs and editable-text SVGs.
"""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".matplotlib-cache"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np
import pandas as pd


OUT = ROOT / "charts"
OUT.mkdir(exist_ok=True)

GREEN = "#005030"
ORANGE = "#c64d1a"
BLACK = "#222222"
GRAY = "#666666"
GRID = "#dddddd"

plt.rcParams.update(
    {
        "font.family": "Times New Roman",
        "font.size": 12,
        "text.color": BLACK,
        "axes.labelcolor": BLACK,
        "xtick.color": BLACK,
        "ytick.color": BLACK,
        "axes.edgecolor": BLACK,
        "svg.fonttype": "none",
        "savefig.facecolor": "white",
    }
)


def save(fig: plt.Figure, name: str) -> None:
    fig.savefig(OUT / f"{name}.png", dpi=300, facecolor="white")
    fig.savefig(OUT / f"{name}.svg", facecolor="white")
    plt.close(fig)


def heat_path(results: pd.DataFrame) -> None:
    baseline = results.loc["baseline_10mw"]
    nodes = [
        ("IT electricity", f"{baseline.operating_it_power_mw:.1f} MW"),
        ("Heat collected", f"{baseline.collected_heat_mw:.1f} MW"),
        ("After exchanger", f"{baseline.post_hx_source_heat_mw:.1f} MW"),
        (
            "After heat pump",
            f"{baseline.post_hx_source_heat_mw + baseline.heat_pump_electric_mw:.1f} MW",
        ),
        ("Delivered heat", f"{baseline.delivered_heat_mw:.2f} MW"),
    ]

    fig, ax = plt.subplots(figsize=(12, 3.65))
    fig.subplots_adjust(left=0.03, right=0.97, top=0.91, bottom=0.08)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.text(0.02, 0.96, "Modeled baseline heat balance", fontsize=19, fontweight="bold", va="top")
    ax.text(0.02, 0.84, "10 MW IT nameplate; 80% operating load", fontsize=12, va="top")

    xs = [0.02, 0.22, 0.42, 0.62, 0.82]
    y, w, h = 0.34, 0.16, 0.28
    for x, (label, value) in zip(xs, nodes):
        ax.add_patch(
            Rectangle((x, y), w, h, facecolor="white", edgecolor=GREEN, linewidth=1.2)
        )
        ax.text(x + w / 2, y + 0.18, label, ha="center", va="center", fontsize=13)
        ax.text(x + w / 2, y + 0.08, value, ha="center", va="center", fontsize=16, fontweight="bold")

    for x in xs[:-1]:
        ax.annotate(
            "",
            xy=(x + 0.198, y + h / 2),
            xytext=(x + w + 0.004, y + h / 2),
            arrowprops={"arrowstyle": "->", "color": BLACK, "linewidth": 1.2},
        )

    ax.text(
        0.02,
        0.22,
        f"Heat pump electricity: {baseline.heat_pump_electric_mw:.2f} MW    "
        f"Distribution loss: {baseline.distribution_loss_mw:.2f} MW",
        fontsize=12,
    )
    ax.text(
        0.02,
        0.10,
        f"At 0°C outdoors, delivered heat meets the modeled peak load of {baseline.supported_area_hectares:.2f} ha of greenhouse.",
        fontsize=12,
    )
    save(fig, "01_heat_path")


def area_by_scenario(results: pd.DataFrame) -> None:
    cases = [
        ("Favorable", "favorable_case_10mw"),
        ("Baseline", "baseline_10mw"),
        ("Cold weather", "cold_weather_10mw"),
        ("Stress test", "stress_case_10mw"),
    ]
    values = [float(results.loc[key, "supported_area_hectares"]) for _, key in cases]
    y = np.arange(len(cases))

    fig, ax = plt.subplots(figsize=(9.2, 4.75))
    fig.subplots_adjust(left=0.23, right=0.94, top=0.81, bottom=0.26)
    ax.barh(
        y,
        values,
        height=0.55,
        color=[GREEN, GREEN, GREEN, ORANGE],
        edgecolor="none",
    )
    ax.invert_yaxis()
    ax.set_yticks(y, [name for name, _ in cases])
    ax.set_xlim(0, 8)
    ax.set_xticks([0, 2, 4, 6, 8])
    ax.set_xlabel("Greenhouse floor area (ha)", labelpad=5)
    ax.tick_params(axis="y", length=0, pad=7)
    ax.grid(axis="x", color=GRID, linewidth=0.7)
    ax.set_axisbelow(True)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_linewidth(0.8)
    for yy, value in zip(y, values):
        ax.text(value + 0.12, yy, f"{value:.2f}", va="center", fontsize=12)

    fig.text(0.04, 0.94, "Estimated peak greenhouse area", fontsize=19, fontweight="bold", va="top")
    fig.text(0.04, 0.08, "10 MW IT nameplate. Baseline: 0°C outdoors; cold case: −10°C.", fontsize=10.5, color=GRAY)
    fig.text(
        0.04,
        0.035,
        "Stress and favorable cases also change IT load, heat capture, and the greenhouse envelope.",
        fontsize=10.5,
        color=GRAY,
    )
    save(fig, "02_area_by_scenario")


def daily_mismatch() -> None:
    hourly = pd.read_csv(ROOT / "results" / "illustrative_day_results.csv")
    storage = pd.read_csv(ROOT / "results" / "storage_summary.csv").iloc[0]
    hours = hourly.hour.to_numpy()
    supply_mw = hourly.available_heat_kw_after_distribution.to_numpy() / 1000
    demand_mw = hourly.greenhouse_demand_kw.to_numpy() / 1000

    fig, ax = plt.subplots(figsize=(9.2, 4.75))
    fig.subplots_adjust(left=0.12, right=0.96, top=0.79, bottom=0.25)
    ax.plot(hours, supply_mw, color=GREEN, linewidth=2.0, label="Available heat")
    ax.plot(hours, demand_mw, color=ORANGE, linewidth=2.0, linestyle="--", label="Greenhouse demand")
    ax.set_xlim(0, 23)
    ax.set_ylim(2, 6.2)
    ax.set_xticks([0, 4, 8, 12, 16, 20, 23])
    ax.set_yticks([2, 3, 4, 5, 6])
    ax.set_xlabel("Hour")
    ax.set_ylabel("Thermal power (MW)")
    ax.grid(axis="y", color=GRID, linewidth=0.7)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["bottom", "left"]].set_linewidth(0.8)
    ax.legend(frameon=False, loc="upper right", fontsize=11)

    fig.text(0.04, 0.94, "Illustrative 24-hour heat balance", fontsize=19, fontweight="bold", va="top")
    fig.text(
        0.04,
        0.08,
        f"Synthetic winter day; {storage.profile_area_m2 / 10000:.2f} ha greenhouse. "
        f"Screening storage: {storage.screening_design_storage_kwh / 1000:.2f} MWh "
        f"({storage.equivalent_water_volume_m3_at_20C_swing:.0f} m³ of water).",
        fontsize=10.5,
        color=GRAY,
    )
    fig.text(0.04, 0.035, "Synthetic temperatures and IT load; storage estimate assumes a full starting tank.", fontsize=10.5, color=GRAY)
    save(fig, "03_daily_mismatch")


if __name__ == "__main__":
    results = pd.read_csv(ROOT / "results" / "scenario_results.csv").set_index("scenario_id")
    heat_path(results)
    area_by_scenario(results)
    daily_mismatch()
