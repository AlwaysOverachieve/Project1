"""Build the FSA ratio charts.

Usage: python src/make_charts.py [input.xlsx] [output_dir]
Defaults: data/ValuesFSARatios.xlsx -> out/

Outputs:
  lines_mve_xrd_de.png  - per-company lines (grey, low opacity) + median line
                          for MVE, R&D/revenue and debt/equity
  dot_mve_vs_age.png    - MVE vs years since first 10-K (post-IPO age) scatter
                          with a LOESS trend and bootstrap 95% band
                          (prints Spearman/Pearson correlations)
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter
from statsmodels.nonparametric.smoothers_lowess import lowess

ROOT = Path(__file__).resolve().parent.parent
src = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "ValuesFSARatios.xlsx"
out = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "out"
out.mkdir(parents=True, exist_ok=True)

d = pd.read_excel(src)
d["age_years"] = d["age_days"] / 365.25  # age_days = days since the firm's first filed 10-K
d["mve"] = d["mve"] * 1e6  # source MVE is in $ millions; ratios are unitless (no change)


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
    ("xrd_revt", "R&D / revenue", "linear", None),
    ("debt_equity", "Debt / equity", "symlog", 1),
]

# --- line graphs: one grey line per company, median across companies in red
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
    if scale != "linear":
        ax.yaxis.set_major_formatter(mfmt if c == "mve" else fmt)
    ax.set_title(f"{label} by company ({scale} scale)", loc="left")
    ax.set_xlabel("Fiscal year")
    ax.set_ylabel(label)
    ax.legend(loc="upper left")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(alpha=0.2)
fig.tight_layout()
fig.savefig(out / "lines_mve_xrd_de.png", dpi=150)

# --- dot plot: MVE vs post-IPO age, with LOESS trend
x = d[["age_years", "mve"]].dropna()
spearman = x.age_years.rank().corr(x.mve.rank())
pearson = x.age_years.corr(x.mve)

# LOESS trend of log(MVE) on age, with a 95% band from a company-level bootstrap
LOESS_FRAC, N_BOOT = 0.4, 300
grid = np.linspace(*x.age_years.quantile([0.01, 0.99]), 100)
fit = lambda df: np.interp(grid, *lowess(np.log(df.mve), df.age_years, frac=LOESS_FRAC).T)
rng = np.random.default_rng(0)
groups = {k: v for k, v in x.groupby(d.loc[x.index, "tic"])}
boots = np.array([fit(pd.concat([groups[k] for k in rng.choice(list(groups), len(groups))]))
                  for _ in range(N_BOOT)])
lo, hi = np.percentile(boots, [2.5, 97.5], axis=0)

fig, ax = plt.subplots(figsize=(9, 7))
ax.scatter(x.age_years, x.mve, s=10, color="#4C78A8", alpha=0.35, edgecolors="none")
ax.fill_between(grid, np.exp(lo), np.exp(hi), color="#D62728", alpha=0.18, lw=0,
                label="95% band (bootstrap by company)")
ax.plot(grid, np.exp(fit(x)), color="#D62728", lw=2.5, label=f"LOESS trend (span {LOESS_FRAC})")
ax.legend(loc="upper left")
ax.set_yscale("log")
ax.xaxis.set_major_formatter(fmt)
ax.yaxis.set_major_formatter(mfmt)
ax.set_xlabel("Years since first 10-K (post-IPO age)")
ax.set_ylabel("MVE ($) (log)")
ax.set_title(f"MVE ($) vs Years since first 10-K (n={len(x)}; Spearman ρ={spearman:.2f})", loc="left")
ax.spines[["top", "right"]].set_visible(False)
ax.grid(alpha=0.2)
fig.tight_layout()
fig.savefig(out / "dot_mve_vs_age.png", dpi=150)
print(f"MVE vs age: n={len(x)}  Spearman={spearman:.3f}  Pearson={pearson:.3f}")
