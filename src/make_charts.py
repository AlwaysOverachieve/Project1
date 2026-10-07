"""Build the FSA ratio charts.

Usage: python src/make_charts.py [input.xlsx] [output_dir]
Defaults: data/ValuesFSARatios.xlsx -> out/

Outputs:
  lines_mve_xrd_de.png  - per-company lines (grey, low opacity) + median line
                          for MVE, R&D/revenue and debt/equity
  dot_mve_vs_age.png    - MVE vs years since first 10-K (post-IPO age) scatter
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

# Optional winsorizing of MVE, R&D/revenue and debt/equity at the pooled 1st/99th
# percentile (values beyond the cutoffs are set to the cutoffs). Off by default.
WINSORIZE = False
LOWER, UPPER = 0.01, 0.99
TAG = ", winsorized 1%/99%" if WINSORIZE else ""
if WINSORIZE:
    for col in ("mve", "xrd_revt", "debt_equity"):
        lo, hi = d[col].quantile([LOWER, UPPER])
        n_lo, n_hi = (d[col] < lo).sum(), (d[col] > hi).sum()
        d[col] = d[col].clip(lo, hi)
        print(f"winsorized {col}: [{lo:.6g}, {hi:.6g}]  ({n_lo} raised, {n_hi} lowered)")

d["age_years"] = d["age_days"] / 365.25  # age_days = days since the firm's first filed 10-K
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
    ("xrd_revt", "R&D / revenue", "linear", None),
    ("debt_equity", "Debt / equity", "symlog", 1),
]

# --- line graphs (log/symlog scales handle the wide spread)
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
    ax.set_title(f"{label} by company ({scale} scale{TAG})", loc="left")
    ax.set_xlabel("Fiscal year")
    ax.set_ylabel(label)
    ax.legend(loc="upper left")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(alpha=0.2)
fig.tight_layout()
fig.savefig(out / "lines_mve_xrd_de.png", dpi=150)

# --- dot plot: MVE vs post-IPO age
def dot_plot(ycol, ylabel, xcol, xlabel, xscale, xfmt, fname, yscale="symlog", yfmt=None, loess=False):
    x = d[[xcol, ycol]].dropna()
    if xscale == "log":
        x = x[x[xcol] > 0]  # zeros can't be drawn on a log axis
    spearman = x[xcol].rank().corr(x[ycol].rank())
    pearson = x[xcol].corr(x[ycol])
    fig, ax = plt.subplots(figsize=(9, 7))
    ax.scatter(x[xcol], x[ycol], s=10, color="#4C78A8", alpha=0.35, edgecolors="none")
    if loess:
        # LOESS trend of log(y) on x with a 95% band from a company-level bootstrap
        LOESS_FRAC, N_BOOT = 0.4, 300
        grid = np.linspace(*x[xcol].quantile([0.01, 0.99]), 100)
        fit = lambda df: np.interp(grid, *lowess(np.log(df[ycol]), df[xcol], frac=LOESS_FRAC).T)
        rng = np.random.default_rng(0)
        firms = d.loc[x.index, "tic"]
        groups = {k: v for k, v in x.groupby(firms)}
        boots = np.array([fit(pd.concat([groups[k] for k in rng.choice(list(groups), len(groups))]))
                          for _ in range(N_BOOT)])
        lo, hi = np.percentile(boots, [2.5, 97.5], axis=0)
        ax.fill_between(grid, np.exp(lo), np.exp(hi), color="#D62728", alpha=0.18, lw=0,
                        label="95% band (bootstrap by company)")
        ax.plot(grid, np.exp(fit(x)), color="#D62728", lw=2.5, label=f"LOESS trend (span {LOESS_FRAC})")
        ax.legend(loc="upper left")
    ax.set_xscale(xscale, **({"linthresh": 1} if xscale == "symlog" else {}))
    ax.set_yscale(yscale, **({"linthresh": 1} if yscale == "symlog" else {}))
    ax.xaxis.set_major_formatter(xfmt if xfmt is not None else fmt)
    ax.yaxis.set_major_formatter(yfmt if yfmt is not None else fmt)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(f"{ylabel} ({yscale})" if yscale != "linear" else ylabel)
    ax.set_title(f"{ylabel} vs {xlabel.split(' (')[0]}{TAG} "
                 f"(n={len(x)}; Spearman ρ={spearman:.2f})", loc="left")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(out / fname, dpi=150)
    plt.close(fig)
    print(f"{ycol} vs {xcol}: n={len(x)}  Spearman={spearman:.3f}  Pearson={pearson:.3f}")


dot_plot("mve", "MVE ($)", "age_years", "Years since first 10-K (post-IPO age)", "linear", None, "dot_mve_vs_age.png", yscale="log", yfmt=mfmt, loess=True)
