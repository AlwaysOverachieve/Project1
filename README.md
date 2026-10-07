# FSA ratio charts

Line graphs (per-company grey lines + median) of MVE, R&D/revenue and debt/equity, and dot plots of debt/equity vs MVE and debt/equity vs R&D/revenue.

## Reproduce

```
pip install -r requirements.txt
python src/make_charts.py            # data/ValuesFSARatios.xlsx -> out/
```

Optional arguments: `python src/make_charts.py <input.xlsx> <output_dir>`.

## Notes

- `data/ValuesFSARatios.xlsx` is the input (835 company-years, 201 companies, revenue ≥ $100M; includes a `revt` revenue column in $ millions, not used by the charts). Its figures are in $ millions; MVE is converted to dollars for display. The R&D/revenue and debt/equity ratios are unitless and plotted as-is.
- MVE, R&D/revenue and debt/equity are winsorized at the pooled 1st/99th percentile (values beyond the cutoffs are set to the cutoffs; no rows dropped). Cutoffs are printed when the script runs. The median and correlations use the winsorized data. MVE uses a log axis, debt/equity a symmetric-log axis, and R&D/revenue a linear axis.
- Correlations (Spearman and Pearson) are printed to the console and the Spearman value is in each dot plot's title.
