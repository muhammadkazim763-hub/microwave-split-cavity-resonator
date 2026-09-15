"""Reproduce analytical frequency and Q-factor checks from the thesis data."""

from __future__ import annotations

import csv
import math
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUTPUTS = ROOT / "outputs"
C = 299_792_458.0


def load_csv(name: str) -> list[dict[str, str]]:
    with (DATA / name).open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def parse_mode(mode: str) -> tuple[int, int, int]:
    if len(mode) != 3 or not mode.isdigit():
        raise ValueError(f"Expected a three-digit mode label, received {mode!r}")
    return tuple(int(value) for value in mode)  # type: ignore[return-value]


def rectangular_cavity_frequency_ghz(
    x_mm: float, y_mm: float, z_mm: float, mode: str
) -> float:
    m, n, l = parse_mode(mode)
    a, b, d = x_mm / 1000.0, y_mm / 1000.0, z_mm / 1000.0
    frequency_hz = C / 2.0 * math.sqrt((m / a) ** 2 + (n / b) ** 2 + (l / d) ** 2)
    return frequency_hz / 1e9


def analyse_modes() -> list[dict[str, float | str]]:
    designs = {row["resonator"]: row for row in load_csv("cavity_designs.csv")}
    results: list[dict[str, float | str]] = []

    for row in load_csv("resonance_modes.csv"):
        design = designs[row["resonator"]]
        calculated = rectangular_cavity_frequency_ghz(
            float(design["x_mm"]),
            float(design["y_mm"]),
            float(design["z_mm"]),
            row["mode"],
        )
        simulated = float(row["simulated_ghz"])
        deviation = abs(simulated - calculated) / calculated * 100.0
        results.append(
            {
                "resonator": row["resonator"],
                "mode": row["mode"],
                "simulated_ghz": simulated,
                "calculated_ghz": calculated,
                "deviation_percent": deviation,
            }
        )
    return results


def write_frequency_results(results: list[dict[str, float | str]]) -> None:
    path = OUTPUTS / "frequency_validation.csv"
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)


def plot_frequency_comparison(results: list[dict[str, float | str]]) -> None:
    labels = [f'{row["resonator"]} TE{row["mode"]}' for row in results]
    simulated = [float(row["simulated_ghz"]) for row in results]
    calculated = [float(row["calculated_ghz"]) for row in results]
    positions = list(range(len(labels)))
    width = 0.38

    fig, ax = plt.subplots(figsize=(11, 5.8))
    ax.bar([p - width / 2 for p in positions], simulated, width, label="CST simulation")
    ax.bar([p + width / 2 for p in positions], calculated, width, label="Analytical")
    ax.set_ylabel("Resonance frequency (GHz)")
    ax.set_title("Calculated and simulated resonance frequencies")
    ax.set_xticks(positions, labels, rotation=35, ha="right")
    ax.grid(axis="y", alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUTPUTS / "frequency-comparison.png", dpi=180)
    plt.close(fig)


def plot_q_factors() -> None:
    rows = load_csv("q_factors.csv")
    labels = [row["configuration"] for row in rows]
    loaded = [float(row["loaded_q"]) for row in rows]
    unloaded = [float(row["unloaded_q"]) for row in rows]
    positions = list(range(len(labels)))
    width = 0.36

    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.bar([p - width / 2 for p in positions], loaded, width, label="Loaded Q")
    ax.bar([p + width / 2 for p in positions], unloaded, width, label="Unloaded Q")
    ax.set_ylabel("Quality factor")
    ax.set_title("Loaded and unloaded quality-factor comparison")
    ax.set_xticks(positions, labels)
    ax.grid(axis="y", alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUTPUTS / "quality-factor-comparison.png", dpi=180)
    plt.close(fig)


def verify_q_reductions() -> None:
    for row in load_csv("q_factors.csv"):
        loaded = float(row["loaded_q"])
        unloaded = float(row["unloaded_q"])
        calculated = (unloaded - loaded) / unloaded * 100.0
        reported = float(row["reported_reduction_percent"])
        print(
            f'{row["configuration"]}: calculated reduction={calculated:.2f}% '
            f'(thesis={reported:.2f}%)'
        )


def main() -> None:
    OUTPUTS.mkdir(exist_ok=True)
    results = analyse_modes()
    write_frequency_results(results)
    plot_frequency_comparison(results)
    plot_q_factors()
    verify_q_reductions()
    print(f"Results written to {OUTPUTS}")


if __name__ == "__main__":
    main()
