"""Does winsorizing improve the MVE vs post-IPO age relationship?

Usage: python src/mve_age_winsorization_check.py [input.xlsx]
Compares correlations and a log-MVE ~ age line fit (cluster-robust by company)
on raw data vs winsorized MVE/age.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
src = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "ValuesFSARatios.xlsx"
d = pd.read_excel(src)
d["age"] = d["age_days"] / 365.25
cl = d["tic"].values


def wins(s, p=0.01):
    lo, hi = s.quantile([p, 1 - p])
    return s.clip(lo, hi)


def report(age, mve, label):
    lm = np.log(mve)
    X = np.c_[np.ones(len(age)), age]
    b = np.linalg.lstsq(X, lm, rcond=None)[0]
    e = lm - X @ b
    XtXi = np.linalg.inv(X.T @ X)
    meat = np.zeros((2, 2))
    for g in np.unique(cl):
        s = X[cl == g].T @ e[cl == g]
        meat += np.outer(s, s)
    G = len(np.unique(cl))
    se = np.sqrt((XtXi @ meat @ XtXi * G / (G - 1))[1, 1])
    r2 = 1 - (e ** 2).sum() / ((lm - lm.mean()) ** 2).sum()
    lo, hi = np.exp(10 * (b[1] - 1.96 * se)), np.exp(10 * (b[1] + 1.96 * se))
    print(f"{label:28s} Pearson(MVE,age)={mve.corr(age):.3f}  Pearson(logMVE,age)={lm.corr(age):.3f}  "
          f"Spearman={mve.rank().corr(age.rank()):.3f}  R2(logMVE)={r2:.3f}  "
          f"x{np.exp(10 * b[1]):.2f}/decade (x{lo:.2f}-x{hi:.2f})")


report(d.age, d.mve, "raw")
report(d.age, wins(d.mve), "MVE winsorized 1/99")
report(wins(d.age), wins(d.mve), "MVE & age winsorized 1/99")
report(wins(d.age, 0.05), wins(d.mve, 0.05), "MVE & age winsorized 5/95")
