"""
Thermal cycle analysis for alumina-based thermal barrier ceramic coatings.

Reads the temperature-time profiles recorded during oxy-acetylene torch testing
(one accelerated thermal cycle per sample, pyrometer readings at 10 s intervals)
and produces:

  1. overlaid heating/cooling curves for all eight coating compositions
  2. post-peak cooling rate ranked against thermal-cycle survival

Run:
    pip install -r requirements.txt
    python src/analyse_thermal_cycles.py
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
FIGS = ROOT / "figures"
FIGS.mkdir(exist_ok=True)

profiles = pd.read_csv(DATA / "thermal_cycle_profiles.csv")
compositions = pd.read_csv(DATA / "sample_compositions.csv")
samples = [c for c in profiles.columns if c != "time_s"]

# ---------------------------------------------------------------- figure 1
fig, ax = plt.subplots(figsize=(9, 5.5))
for sample in samples:
    survived = compositions.loc[
        compositions["sample"] == sample, "survived_thermal_cycle"
    ].iloc[0]
    ax.plot(
        profiles["time_s"],
        profiles[sample],
        marker="o",
        markersize=4,
        linewidth=2.2 if survived == "yes" else 1.2,
        alpha=1.0 if survived == "yes" else 0.65,
        label=f"{sample} (no cracking)" if survived == "yes" else sample,
    )
ax.axvline(60, color="grey", linestyle="--", linewidth=1)
ax.annotate(
    "flame cut off",
    xy=(60, 1108),
    xytext=(62, 1108),
    fontsize=9,
    color="grey",
)
ax.set_xlabel("Time (s)")
ax.set_ylabel("Surface temperature (deg C)")
ax.set_title("Accelerated thermal cycle: oxy-acetylene torch test")
ax.legend(ncol=2, fontsize=9)
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(FIGS / "01_thermal_cycle_profiles.png", dpi=150)
plt.close(fig)

# ---------------------------------------------------------------- figure 2
peak = profiles.loc[profiles["time_s"] == 60].iloc[0]
final = profiles.loc[profiles["time_s"] == 80].iloc[0]

summary = pd.DataFrame(
    {
        "sample": samples,
        "peak_C": [peak[s] for s in samples],
        "temp_at_80s_C": [final[s] for s in samples],
    }
)
summary["drop_C"] = summary["peak_C"] - summary["temp_at_80s_C"]
summary["cooling_rate_C_per_s"] = summary["drop_C"] / 20.0
summary = summary.merge(
    compositions[["sample", "survived_thermal_cycle"]], on="sample"
).sort_values("cooling_rate_C_per_s")

fig, ax = plt.subplots(figsize=(9, 5))
colours = [
    "#2a7f4f" if s == "yes" else "#b03a2e"
    for s in summary["survived_thermal_cycle"]
]
ax.bar(summary["sample"], summary["cooling_rate_C_per_s"], color=colours)
ax.set_ylabel("Post-peak cooling rate, 60-80 s (deg C/s)")
ax.set_xlabel("Coating composition")
ax.set_title("Cooling rate after flame cut-off (green = survived the cycle)")
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
fig.savefig(FIGS / "02_cooling_rate_vs_survival.png", dpi=150)
plt.close(fig)

summary.to_csv(DATA / "cooling_rate_summary.csv", index=False)

print(summary.to_string(index=False))
print("\nFigures written to", FIGS)
