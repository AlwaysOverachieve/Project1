"""Annotated chart images for the presentation (out/deck/*.png).

Usage: python src/make_deck_charts.py [input.xlsx] [output_dir]
Same data and transformations as make_charts.py (MVE x 1e6, age days -> years,
no winsorizing/outlier removal); the styling follows the deck palette and adds
on-chart annotations. All annotation numbers are computed from the data.
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager as fm
from matplotlib.ticker import FuncFormatter
from statsmodels.nonparametric.smoothers_lowess import lowess

ROOT = Path(__file__).resolve().parent.parent
src = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "ValuesFSARatios.xlsx"
out = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "out" / "deck"
out.mkdir(parents=True, exist_ok=True)

if any("Carlito" in f.name for f in fm.fontManager.ttflist):
    plt.rcParams["font.family"] = "Carlito"  # metric-compatible with Calibri used in the deck

TEAL, ORANGE, GREY, INK = "#1F7A8C", "#E36414", "#8A9BA3", "#1B2B34"
plt.rcParams.update({"text.color": INK, "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK})

d = pd.read_excel(src)
d["age_years"] = d["age_days"] / 365.25
d["mve"] = d["mve"] * 1e6  # source MVE is in $ millions


def money(v, _):
    for unit, suffix in ((1e12, "T"), (1e9, "B"), (1e6, "M"), (1e3, "K")):
        if v >= unit:
            return f"${v / unit:g}{suffix}"
    return f"${v:g}"


mfmt = FuncFormatter(money)
box = dict(boxstyle="round,pad=0.25", fc="white", ec="#C9D3D8", lw=0.8)
arrow = dict(arrowstyle="-", color=INK, lw=0.9)

# ---------------- line graphs: three compact panels with annotations
fig, axs = plt.subplots(3, 1, figsize=(6.05, 4.75), sharex=True,
                        gridspec_kw={"height_ratios": [1.35, 1, 1], "hspace": 0.18})
spec = [("mve", "MVE ($)", "log", mfmt), ("xrd_revt", "R&D / revenue", "linear", None),
        ("debt_equity", "Debt / equity", "symlog", FuncFormatter(lambda v, _: f"{v:,.0f}"))]
med = {c: d.groupby("fyear")[c].median() for c, *_ in spec}
for ax, (c, label, scale, f) in zip(axs, spec):
    for _, g in d.groupby("tic"):
        g = g.sort_values("fyear")
        ax.plot(g.fyear, g[c], color=GREY, alpha=0.2, lw=0.7)
    ax.plot(med[c].index, med[c].values, color=ORANGE, lw=3)
    ax.set_yscale(scale, **({"linthresh": 1} if scale == "symlog" else {}))
    if f is not None:
        ax.yaxis.set_major_formatter(f)
    ax.set_ylabel(label, fontsize=9)
    ax.tick_params(labelsize=8.5)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(alpha=0.2)
axs[2].set_xlabel("Fiscal year", fontsize=9)
axs[2].set_xticks(range(2010, 2025, 2))

m = med["mve"]
axs[0].annotate("Grey = one company\nOrange = yearly median", xy=(2010.3, 2.5e11), fontsize=9,
                va="top", bbox=box)
axs[0].annotate(f"Median ≈ \\${m[2010] / 1e9:.1f}B in 2010 and \\${m[2024] / 1e9:.1f}B in 2024:\nno drift over calendar time",
                xy=(2019.5, m[2019]), xytext=(2014.3, 3.5e7), fontsize=9, bbox=box, arrowprops=arrow)
axs[0].set_ylim(1e7, 6e11)
x = med["xrd_revt"]
axs[1].annotate(f"Median {x[2010]:.2f} → {x[2024]:.2f}", xy=(2016, x[2016]), xytext=(2010.4, 2.2),
                fontsize=9, bbox=box, arrowprops=arrow)
axs[1].set_ylim(0, 4.2)
y = med["debt_equity"]
axs[2].annotate(f"Median peaks at {y.max():.2f} ({y.idxmax()}),\nthen falls to {y[2024]:.2f}", xy=(2020, y[2020]),
                xytext=(2015.3, 12), fontsize=9, bbox=box, arrowprops=arrow)
axs[2].set_ylim(-30, 300)
fig.subplots_adjust(left=0.15, right=0.98, top=0.99, bottom=0.1)
fig.savefig(out / "lines_annotated.png", dpi=220)
plt.close(fig)

# ---------------- dot plot with LOESS trend and annotations
x = d[["age_years", "mve", "tic"]].dropna()
rho = x.age_years.rank().corr(x.mve.rank())
r_log = np.log(x.mve).corr(x.age_years)
LOESS_FRAC, N_BOOT = 0.4, 300
grid = np.linspace(*x.age_years.quantile([0.01, 0.99]), 100)
fit = lambda df: np.interp(grid, *lowess(np.log(df.mve), df.age_years, frac=LOESS_FRAC).T)
rng = np.random.default_rng(0)
groups = {k: v for k, v in x.groupby("tic")}
boots = np.array([fit(pd.concat([groups[k] for k in rng.choice(list(groups), len(groups))]))
                  for _ in range(N_BOOT)])
lo, hi = np.percentile(boots, [2.5, 97.5], axis=0)
trend = np.exp(fit(x))

fig, ax = plt.subplots(figsize=(6.05, 4.75))
ax.scatter(x.age_years, x.mve, s=9, color=TEAL, alpha=0.3, edgecolors="none")
ax.fill_between(grid, np.exp(lo), np.exp(hi), color=ORANGE, alpha=0.2, lw=0)
ax.plot(grid, trend, color=ORANGE, lw=3)
ax.set_yscale("log")
ax.yaxis.set_major_formatter(mfmt)
ax.set_ylim(1e7, 1.2e12)
ax.set_xlabel("Years since first 10-K (post-IPO age)", fontsize=9)
ax.set_ylabel("MVE ($, log scale)", fontsize=9)
ax.tick_params(labelsize=8.5)
ax.spines[["top", "right"]].set_visible(False)
ax.grid(alpha=0.2)
t = lambda a: float(np.interp(a, grid, trend))
ax.annotate(f"Teal dots: {len(x)} company-years\nOrange line: LOESS trend\nShaded: 95% band (bootstrap)", xy=(0.8, 5e11),
            fontsize=9, va="top", bbox=box)
ax.annotate(f"≈\\${t(11) / 1e9:.1f}B at year 11\n(flat for ~12 yrs)", xy=(11, t(11)), xytext=(10.5, 3e7),
            fontsize=9, bbox=box, arrowprops=arrow)
ax.annotate(f"≈\\${t(25) / 1e9:.0f}B at year 25\n({t(25) / t(11):.1f}× year 11)", xy=(25, t(25)), xytext=(23, 3e8),
            fontsize=9, bbox=box, arrowprops=arrow)
ax.annotate(f"Spearman ρ = {rho:.2f}", xy=(0.99, 0.02), xycoords="axes fraction", ha="right", fontsize=9.5,
            fontweight="bold", bbox=box)
fig.subplots_adjust(left=0.15, right=0.98, top=0.99, bottom=0.12)
fig.savefig(out / "dot_annotated.png", dpi=220)
plt.close(fig)
print(f"rho={rho:.3f} r_log={r_log:.3f} trend(11)={t(11):.3g} trend(25)={t(25):.3g}")

# ---------------- numbers used in the slides (written to stats.json)
rank_corr = lambda a, b: float(a.rank().corr(b.rank()))
lm = np.log(d.mve)


def line_fit(age, mve):
    """log(MVE) ~ age: R2 and the multiplicative change per decade (company-clustered 95% CI)."""
    y = np.log(mve)
    X = np.c_[np.ones(len(age)), age]
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    e = y - X @ b
    XtXi = np.linalg.inv(X.T @ X)
    meat, cl = np.zeros((2, 2)), d.loc[age.index, "tic"].values
    for g in np.unique(cl):
        s_ = X[cl == g].T @ e[cl == g]
        meat += np.outer(s_, s_)
    G = len(np.unique(cl))
    se = np.sqrt((XtXi @ meat @ XtXi * G / (G - 1))[1, 1])
    r2 = 1 - (e ** 2).sum() / ((y - y.mean()) ** 2).sum()
    return dict(r2=float(r2), per_decade=float(np.exp(10 * b[1])),
                ci_lo=float(np.exp(10 * (b[1] - 1.96 * se))), ci_hi=float(np.exp(10 * (b[1] + 1.96 * se))))


def wins(s, p):
    lo_, hi_ = s.quantile([p, 1 - p])
    return s.clip(lo_, hi_)


def version(label, age, mve, n=None):
    return dict(label=label, n=int(len(age)), spearman=rank_corr(age, mve), pearson=float(age.corr(mve)),
                pearson_log=float(np.log(mve).corr(age)), **line_fit(age, mve))


bands = pd.cut(d.age_years, [0, 5, 10, 20, 30, 100], labels=["0-5", "5-10", "10-20", "20-30", "30+"])
band_tbl = d.groupby(bands, observed=True).agg(n=("mve", "size"), firms=("tic", "nunique"), median=("mve", "median"),
                                              q1=("mve", lambda s_: s_.quantile(.25)), q3=("mve", lambda s_: s_.quantile(.75)))
# company-bootstrap ratio of median MVE for 20+ vs <20 years
firms = {k: v for k, v in d.groupby("tic")}
ratios = []
for _ in range(1000):
    b_ = pd.concat([firms[k] for k in rng.choice(list(firms), len(firms))])
    ratios.append(b_.loc[b_.age_years >= 20, "mve"].median() / b_.loc[b_.age_years < 20, "mve"].median())
old = d.loc[d.age_years >= 20, "mve"].median() / d.loc[d.age_years < 20, "mve"].median()

latest = d.sort_values("fyear").groupby("tic").tail(1)
firm_med = d.groupby("tic")[["mve", "age_years"]].median()
dm = pd.DataFrame({"lm": lm, "age": d.age_years}) - pd.DataFrame({"lm": lm, "age": d.age_years}).groupby(d.tic).transform("mean")
early, late = d[d.fyear <= 2016], d[d.fyear >= 2017]
# earlier version of the data without the $100M revenue floor (revenue column not available there)
uf = pd.read_excel(ROOT / "data" / "prior_no_revenue_floor.xlsx")
uf_age, uf_mve = uf.age_days / 365.25, uf.mve * 1e6
unfloored = dict(n=int(len(uf)), firms=int(uf.tic.nunique()), spearman=rank_corr(uf_age, uf_mve),
                 pearson_log=float(np.log(uf_mve[uf_mve > 0]).corr(uf_age[uf_mve > 0])))

stats = dict(
    n=int(len(d)), firms=int(d.tic.nunique()), fyear_min=int(d.fyear.min()), fyear_max=int(d.fyear.max()),
    rows_per_firm_median=float(d.groupby("tic").size().median()), rows_per_firm_max=int(d.groupby("tic").size().max()),
    rev_min_m=float(d.revt.min()), rho=rank_corr(d.age_years, d.mve), pearson=float(d.age_years.corr(d.mve)),
    pearson_log=float(lm.corr(d.age_years)), fit=line_fit(d.age_years, d.mve),
    trend11=t(11), trend25=t(25),
    bands=[dict(band=k, **{c: float(v) for c, v in r.items()}) for k, r in band_tbl.iterrows()],
    ratio_20plus=float(old), ratio_ci=[float(np.percentile(ratios, 2.5)), float(np.percentile(ratios, 97.5))],
    summary=dict(mve=(d.mve / 1e6).describe().to_dict(), age=d.age_years.describe().to_dict(), revt=d.revt.describe().to_dict()),
    versions=[version("Final: no winsorizing", d.age_years, d.mve),
              version("MVE winsorized 1% / 99%", d.age_years, wins(d.mve, .01)),
              version("MVE and age winsorized 1% / 99%", wins(d.age_years, .01), wins(d.mve, .01)),
              version("MVE and age winsorized 5% / 95%", wins(d.age_years, .05), wins(d.mve, .05))],
    robust=[dict(label="One observation per firm (latest year)", n=int(len(latest)), spearman=rank_corr(latest.age_years, latest.mve)),
            dict(label="Firm medians (one point per firm)", n=int(len(firm_med)), spearman=rank_corr(firm_med.age_years, firm_med.mve)),
            dict(label="Within-firm only (firm means removed), log MVE", n=int(len(d)), spearman=None, pearson=float(dm.lm.corr(dm.age))),
            dict(label="Fiscal years 2010-2016", n=int(len(early)), spearman=rank_corr(early.age_years, early.mve)),
            dict(label="Fiscal years 2017-2024", n=int(len(late)), spearman=rank_corr(late.age_years, late.mve)),
            dict(label="Excluding MVE above $100B", n=int((d.mve <= 1e11).sum()), spearman=rank_corr(d.age_years[d.mve <= 1e11], d.mve[d.mve <= 1e11]))],
    unfloored=unfloored,
    other_corr={c: dict(age=rank_corr(d[c], d.age_years), mve=rank_corr(d[c], d.mve)) for c in ("revt", "xrd_revt", "debt_equity", "FCF_ni")},
    median_by_year={int(k): float(v) for k, v in d.groupby("fyear").mve.median().items()},
    n_by_year={int(k): int(v) for k, v in d.groupby("fyear").size().items()},
)
(out / "stats.json").write_text(json.dumps(stats, indent=1))
print("wrote", out / "stats.json")
