"""Build the FSA ratio charts.

Usage: python src/make_charts.py [input.xlsx] [output_dir]
Defaults: data/ValuesFSARatios.xlsx -> out/

Outputs:
  lines_mve_xrd_de.png  - per-company lines (grey, low opacity) + median line
                          for MVE, R&D/revenue and debt/equity
  dot_mve_vs_xrd.png    - MVE vs R&D/revenue scatter; prints correlations
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter

ROOT = Path(__file__).resolve().parent.parent
src = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "ValuesFSARatios.xlsx"
out = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "out"
out.mkdir(parents=True, exist_ok=True)

d = pd.read_excel(src)

# Winsorize MVE, R&D/revenue and debt/equity at the 1st/99th percentile
# (pooled over all company-years); values beyond the cutoffs are set to the cutoffs.
LOWER, UPPER = 0.01, 0.99
for col in ("mve", "xrd_revt", "debt_equity"):
    lo, hi = d[col].quantile([LOWER, UPPER])
    n_lo, n_hi = (d[col] < lo).sum(), (d[col] > hi).sum()
    d[col] = d[col].clip(lo, hi)
    print(f"winsorized {col}: [{lo:.6g}, {hi:.6g}]  ({n_lo} raised, {n_hi} lowered)")

d["mve"] = d["mve"] * 1e6  # source MVE is in $ millions; ratios are unitless


def money(v, _):
    for unit, suffix in ((1e12, "T"), (1e9, "B"), (1e6, "M"), (1e3, "K")):
        if v >= unit:
            return f"${v / unit:g}{suffix}"
    return f"${v:g}"


mfmt = FuncFormatter(money)
fmt = FuncFormatter(lambda v, _: f"{v:,.0f}" if abs(v) >= 1 or v == 0 else f"{v:g}")

# (column, label, axis scale, symlog linthresh)
METRICS = [
    ("mve", "Market value of equity (MVE, $)", "log", None),
    ("xrd_revt", "R&D / revenue", "symlog", 1),
    ("debt_equity", "Debt / equity", "symlog", 1),
]

# --- line graphs (winsorized data; log/symlog scales still handle the wide spread)
fig, axs = plt.subplots(3, 1, figsize=(11, 13))
for ax, (c, label, scale, linthresh) in zip(axs, METRICS):
    for _, g in d.groupby("tic"):
        g = g.sort_values("fyear").dropna(subset=[c])
        if c == "mve":
            g = g[g[c] > 0]  # zeros can't be drawn on a log axis
        ax.plot(g.fyear, g[c], color="grey", alpha=0.15, lw=0.8)
    med = d.groupby("fyear")[c].median()  # median over all companies
    ax.plot(med.index, med.values, color="#D62728", lw=3, label="Median (all companies)")
    ax.set_yscale(scale, **({"linthresh": linthresh} if linthresh else {}))
    ax.yaxis.set_major_formatter(mfmt if c == "mve" else fmt)
    ax.set_title(f"{label} by company ({scale} scale, winsorized 1%/99%)", loc="left")
    ax.set_xlabel("Fiscal year")
    ax.set_ylabel(label)
    ax.legend(loc="upper left")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(alpha=0.2)
fig.tight_layout()
fig.savefig(out / "lines_mve_xrd_de.png", dpi=150)

# --- dot plot: MVE vs R&D/revenue
x = d[["mve", "xrd_revt"]].dropna()
xp = x[x.mve > 0]
spearman = x.mve.rank().corr(x.xrd_revt.rank())
pearson_raw = x.mve.corr(x.xrd_revt)
pearson_log = np.log(xp.mve).corr(xp.xrd_revt)

fig, ax = plt.subplots(figsize=(9, 7))
ax.scatter(xp.mve, xp.xrd_revt, s=10, color="#4C78A8", alpha=0.35, edgecolors="none")
ax.set_xscale("log")
ax.set_yscale("symlog", linthresh=1)
ax.set_ylim(bottom=0)  # winsorized R&D/revenue is all positive
ax.xaxis.set_major_formatter(mfmt)
ax.yaxis.set_major_formatter(fmt)
ax.set_xlabel("MVE ($, log)")
ax.set_ylabel("R&D / revenue (symlog)")
ax.set_title(f"MVE vs R&D/revenue, winsorized 1%/99% (n={len(xp)} company-years; Spearman ρ={spearman:.2f})", loc="left")
ax.spines[["top", "right"]].set_visible(False)
ax.grid(alpha=0.2)
fig.tight_layout()
fig.savefig(out / "dot_mve_vs_xrd.png", dpi=150)

print(f"rows with MVE and R&D/revenue: {len(x)} ({(x.mve <= 0).sum()} with MVE = 0 omitted from dot plot)")
print(f"Spearman (rank):            {spearman:.3f}")
print(f"Pearson (raw):              {pearson_raw:.3f}")
print(f"Pearson (log MVE vs ratio): {pearson_log:.3f}")
