# FSA ratio charts

This repository turns `data/ValuesFSARatios.xlsx` into two charts:

| Chart | What it shows |
|---|---|
| `out/lines_mve_xrd_de.png` | Three stacked line graphs (MVE, R&D/revenue, debt/equity) by fiscal year. Each company is a thin grey line; the median across companies is a solid red line. |
| `out/dot_mve_vs_age.png` | A dot plot of MVE against years since the firm's first 10-K (post-IPO age), with a LOESS trend line and a 95% bootstrap band. |

## Presentation

`out/Biotech_MVE_vs_Age.pptx` (6 main slides + 3 appendix slides) is built from the same data:

```
pip install -r requirements.txt
npm install                           # pptxgenjs, react-icons, sharp
npm run deck                          # = python3 src/make_deck_charts.py && node src/make_deck.js
```

- `src/make_deck_charts.py` makes the annotated chart images in `out/deck/` and `out/deck/stats.json`. Every number in the slides (correlations, medians by age band, robustness checks) is computed there from `data/ValuesFSARatios.xlsx`. It applies the same transformations as `make_charts.py`, with no winsorizing or outlier removal.
- `data/prior_no_revenue_floor.xlsx` is the earlier version of the data without the $100M revenue floor (3,448 company-years). It is used only for the appendix comparison of the revenue floor's effect.
- `src/make_deck.js` lays out the slides. `src/apply_theme.js` writes the theme colors into the file.

## Reproduce the two charts

```
pip install -r requirements.txt
python src/make_charts.py            # data/ValuesFSARatios.xlsx -> out/
```

Optional arguments: `python src/make_charts.py <input.xlsx> <output_dir>`. All logic is in `src/make_charts.py`. The script prints the Spearman and Pearson correlation for the dot plot, and the LOESS bootstrap uses a fixed random seed so reruns give the same image.

## Source data

`data/ValuesFSARatios.xlsx` is the file you supplied (sheet `Values FSA Ratios`).

- 833 company-years, 201 companies (`tic`), fiscal years 2010–2024. Companies have between 1 and 15 years each (median 3).
- Revenue is at least $100M in every row (this floor was applied in your file, not in the code).
- No missing values and no duplicate company-year rows.
- Columns used by the charts:

| Column | Meaning | Used for |
|---|---|---|
| `tic` | Company ticker | Grouping rows into one line per company |
| `fyear` | Fiscal year | X-axis of the line graphs |
| `mve` | Market value of equity, in $ millions | Line graph and dot plot |
| `xrd_revt` | R&D / revenue | Line graph |
| `debt_equity` | Debt / equity | Line graph |
| `age_days` | Days since the firm's first filed 10-K (post-IPO age) | Dot plot x-axis |

- Columns in the file that the charts do not use: `firm_id`, `name`, `fiscal_year_end_month`, `revt` (revenue, $ millions), `FCF_ni` (free cash flow / net income).

## Changes made to the data

Only two transformations are applied to the values, and neither removes or alters any observation's relative position:

1. **MVE × 1,000,000.** The source MVE is in $ millions (1.1 means $1,100,000), so it is converted to dollars. This lets the axes read `$100M`, `$1B`, `$100B` and so on.
2. **`age_days` ÷ 365.25.** Days since the first 10-K are converted to years for the dot plot's x-axis.

The ratios (`xrd_revt`, `debt_equity`) are unitless, so the millions cancel and their values are plotted exactly as given.

**What is not done:**

- **No winsorizing and no outlier removal.** All 833 rows are plotted. I tested winsorizing at the 1st/99th percentile while developing the charts. It raised the raw Pearson correlation of MVE and age from about 0.29 to about 0.34, but left the rank correlation (0.29), the log-scale R² (about 0.11) and the fitted slope unchanged. It did not reveal a stronger relationship, so the final charts use the unmodified values.
- **No rows dropped.** The dot plot uses n = 833. MVE is above zero in every row, so the log-scale plot excludes nothing.
- **No imputation or smoothing of the data itself.** The LOESS curve is an overlay that is drawn on top of the unchanged points.

## How each chart is built

### `lines_mve_xrd_de.png`

1. Read the sheet, convert MVE to dollars.
2. For each of the three metrics, draw one line per company (grouped by `tic`, sorted by fiscal year) in grey with 15% opacity. A company with a single year has no line, because there is nothing to connect. Companies with gaps in their years get a line joined across the gap.
3. For each fiscal year, compute the median of the metric over all companies in that year, and draw it as a solid red line.
4. Axis scales are chosen only to make the very wide ranges readable. These change how the data is displayed, not the data:
   - MVE: log scale.
   - R&D/revenue: linear scale.
   - Debt/equity: symmetric-log scale (linear within ±1, logarithmic beyond). This is used because debt/equity has negative values (companies with negative book equity) and extreme values up to about 880.

### `dot_mve_vs_age.png`

1. Read the sheet, convert MVE to dollars and age to years.
2. Plot one dot per company-year: x = years since first 10-K, y = MVE on a log axis.
3. Compute and print the Spearman rank correlation (0.29, shown in the title) and the Pearson correlation of the raw values (0.29).
4. Fit the trend line with LOESS (`statsmodels` `lowess`) of log(MVE) on age, with a span of 0.4. The curve is drawn between the 1st and 99th percentile of age (about 2 to 36 years), because the data is too thin beyond that for a stable fit.
5. Draw the 95% band by bootstrapping: resample the 201 companies with replacement 300 times (keeping each company's rows together, because a company appears in several years), refit the LOESS each time, and take the 2.5th and 97.5th percentiles of the fitted curves at each age.

## Reading the results with care

- Rows are company-years, so the dots are not independent. The company-level bootstrap accounts for this in the band, but the correlation numbers and the dot cloud itself do not.
- Age explains only about 11% of the variation in log MVE (R² of a straight-line fit). The LOESS line shows the typical level at each age, not a prediction for an individual company.
- The right-hand end of the LOESS curve (beyond roughly 30 years) is based on few companies, which is why the band widens there.
