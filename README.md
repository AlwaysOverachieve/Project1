# FSA ratio charts

Line graphs (per-company grey lines + median) of MVE, R&D/revenue and debt/equity, and dot plots of debt/equity vs MVE, debt/equity vs R&D/revenue, FCF/net income vs R&D/revenue, FCF/net income vs debt/equity, and MVE vs company age.

## Reproduce

```
pip install -r requirements.txt
python src/make_charts.py            # data/ValuesFSARatios.xlsx -> out/
```

Optional arguments: `python src/make_charts.py <input.xlsx> <output_dir>`.

## Notes

- `data/ValuesFSARatios.xlsx` is the input (833 company-years, 201 companies, revenue ≥ $100M; includes a `revt` revenue column in $ millions, not used by the charts; `FCF_ni` is free cash flow / net income). Its figures are in $ millions; MVE is converted to dollars for display. The R&D/revenue and debt/equity ratios are unitless and plotted as-is.
- No winsorizing or outlier removal by default. To winsorize MVE, R&D/revenue and debt/equity at the pooled 1st/99th percentile, set `WINSORIZE = True` in `src/make_charts.py` (cutoffs are printed; titles are tagged). MVE uses a log axis, debt/equity a symmetric-log axis, and R&D/revenue a linear axis.
- Correlations (Spearman and Pearson) are printed to the console and the Spearman value is in each dot plot's title.
