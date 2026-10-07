# FSA ratio charts

Line graphs (per-company grey lines + median) of MVE, R&D/revenue and debt/equity, and a dot plot of MVE vs R&D/revenue.

## Reproduce

```
pip install -r requirements.txt
python src/make_charts.py            # data/ValuesFSARatios.xlsx -> out/
```

Optional arguments: `python src/make_charts.py <input.xlsx> <output_dir>`.

## Notes

- `data/ValuesFSARatios.xlsx` is the input. Its figures are in $ millions; MVE is converted to dollars for display. The R&D/revenue and debt/equity ratios are unitless and plotted as-is.
- No outliers are removed. Log (MVE) and symmetric-log (ratios) axes handle extreme values. Median is over all companies each year.
- Dot plot omits 3 rows with MVE = 0 (can't be drawn on a log axis). Correlations are printed to the console.
