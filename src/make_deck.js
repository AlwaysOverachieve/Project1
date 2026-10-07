// Builds out/Biotech_MVE_vs_Age.pptx from out/deck/stats.json and the PNGs made by
// make_deck_charts.py.   Run: python3 src/make_deck_charts.py && node src/make_deck.js
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const fa = require("react-icons/fa");
const { applyTheme } = require("./apply_theme.js");

const ROOT = path.resolve(__dirname, "..");
const DECK = path.join(ROOT, "out", "deck");
const OUT = process.env.DECK_OUT || path.join(ROOT, "out", "Biotech_MVE_vs_Age.pptx");
// footer shown at the bottom left of every slide (override with the DECK_FOOTER environment variable)
const FOOTER = process.env.DECK_FOOTER || "Created with Claude - Reviewed by Jacob Willson";
const REPO_URL = "https://github.com/AlwaysOverachieve/Project1";
const S = JSON.parse(fs.readFileSync(path.join(DECK, "stats.json"), "utf8"));

// ---------- theme: deep teal + orange accent (one dominant color, one sharp accent)
const THEME = {
  name: "Biotech Teal",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1B2B34", lt1: "FFFFFF", dk2: "0F4C5C", lt2: "EEF4F5",
    accent1: "1F7A8C", accent2: "E36414", accent3: "8A9BA3", accent4: "5FA8B8", accent5: "9A031E", accent6: "2F6B3C",
    hlink: "1F7A8C", folHlink: "8A9BA3",
  },
};
const HEX = THEME.colors; // hex-only options (chart colors) read from here

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5 in
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "Biotech Industry - MVE vs Age";
pres.author = "Jacob Willson";
const C = pres.SchemeColor;

// ---------- layouts
pres.defineSlideMaster({
  title: "TITLE",
  background: { color: C.text2 },
  objects: [],
  slideNumber: undefined,
});
// placeholders are added through the objects array
pres.defineSlideMaster({
  title: "TITLE_LAYOUT",
  background: { color: C.text2 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 2.35, w: 8.4, h: 1.5, fontFace: "Cambria", fontSize: 44, bold: true, color: C.background1, align: "left", valign: "bottom", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "subtitle", type: "body", x: 0.8, y: 4.05, w: 8.4, h: 1.3, fontSize: 20, color: C.background2, align: "left", valign: "top", margin: 0 }, text: "" } },
    { text: { text: FOOTER, options: { x: 0.6, y: 7.05, w: 8, h: 0.3, fontSize: 10, color: C.background2, margin: 0, valign: "middle" } } },
  ],
});
pres.defineSlideMaster({
  title: "CONTENT_LAYOUT",
  background: { color: C.background1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.35, w: 12.13, h: 1.0, fontFace: "Cambria", fontSize: 30, bold: true, color: C.text2, align: "left", valign: "middle", margin: 0 }, text: "" } },
    { text: { text: FOOTER, options: { x: 0.6, y: 7.05, w: 8, h: 0.3, fontSize: 10, color: C.accent3, margin: 0, valign: "middle" } } },
  ],
  slideNumber: { x: 12.23, y: 7.05, w: 0.5, h: 0.3, fontSize: 10, color: C.accent3, align: "right" },
});

// ---------- helpers
const FONT_BODY = "+mn-lt";
const billions = (v) => `$${(v / 1e9).toFixed(1)}B`;
const f2 = (v) => v.toFixed(2);

async function icon(name, color = "#FFFFFF", size = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(fa[name], { color, size: String(size) }));
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}
const txt = (slide, text, o) => slide.addText(text, { isTextBox: true, margin: 0, ...o });
const bullets = (items, o = {}) =>
  items.map((t, i) => ({
    text: t,
    options: { bullet: { indent: 16 }, breakLine: i < items.length - 1, paraSpaceAfter: 6, ...o },
  }));
function card(slide, x, y, w, h, name, fill = C.background2) {
  slide.addShape(pres.ShapeType.roundRect, { x, y, w, h, fill: { color: fill }, line: { color: fill, width: 0 }, rectRadius: 0.08, objectName: name });
}
function statCard(slide, x, y, w, h, big, label, name) {
  card(slide, x, y, w, h, name);
  txt(slide, big, { x: x + 0.2, y: y + 0.12, w: w - 0.4, h: h * 0.52, fontFace: "Cambria", fontSize: 38, bold: true, color: C.text2, valign: "middle", objectName: name + " value" });
  txt(slide, label, { x: x + 0.2, y: y + h * 0.62, w: w - 0.4, h: h * 0.34, fontSize: 13, color: C.text1, valign: "top", objectName: name + " label" });
}

(async () => {
  // ================= Slide 1: title
  pres.addSection({ title: "Main" });
  let s = pres.addSlide({ masterName: "TITLE_LAYOUT", sectionTitle: "Main" });
  const dots = [[10.4, 1.2, 1.6, "accent1", 30], [11.9, 2.6, 0.9, "accent2", 15], [9.9, 3.6, 0.7, "accent4", 40], [11.2, 4.4, 2.0, "accent1", 55],
    [12.5, 0.8, 0.5, "accent4", 20], [9.3, 5.6, 1.0, "accent2", 45], [11.6, 6.3, 0.6, "accent4", 35], [10.3, 2.4, 0.45, "accent2", 10]];
  dots.forEach(([x, y, d, c, tr], i) =>
    s.addShape(pres.ShapeType.ellipse, { x, y, w: d, h: d, fill: { color: C[c], transparency: tr }, line: { color: C[c], width: 0, transparency: 100 }, objectName: `Dot motif ${i + 1}` }));
  s.addText("Biotech Industry - MVE vs Age", { placeholder: "title" });
  s.addText([
    { text: "Jacob Willson", options: { bold: true, breakLine: true } },
    { text: "October 7, 2026" },
  ], { placeholder: "subtitle" });
  s.addNotes("Title slide. Question: is a biotech firm's market value of equity related to how long it has been a public filer?");

  // ================= Slide 2: business context & question
  s = pres.addSlide({ masterName: "CONTENT_LAYOUT", sectionTitle: "Main" });
  s.addText("Business Context & Question", { placeholder: "title" });
  card(s, 0.6, 1.5, 4.9, 2.55, "Research question card", C.text2);
  txt(s, "RESEARCH QUESTION", { x: 0.85, y: 1.68, w: 4.4, h: 0.3, fontSize: 12, bold: true, color: C.accent4, charSpacing: 2 });
  txt(s, "Is the Market Value of Equity correlated with company age? If so, does it increase or decrease over time for Biotech companies?",
    { x: 0.85, y: 2.05, w: 4.4, h: 1.9, fontSize: 19, color: C.background1, valign: "top" });
  txt(s, "Measurable outcomes", { x: 0.6, y: 4.3, w: 4.9, h: 0.35, fontSize: 16, bold: true, color: C.text2 });
  txt(s, bullets([
    "Rank (Spearman ρ) and linear (Pearson r) correlation of MVE with post-IPO age; H1: ρ > 0",
    "Effect size: change in median MVE across age bands and per decade of age",
    "Direction: does MVE rise, stay flat or fall as firms age?",
  ]), { x: 0.6, y: 4.7, w: 4.9, h: 1.75, fontSize: 14, color: C.text1, valign: "top" });
  txt(s, "Counter-view: patent cliffs and maturing franchises could flatten or lower older firms' value, which is why this is an empirical question.",
    { x: 0.6, y: 6.5, w: 4.9, h: 0.5, fontSize: 11, italic: true, color: C.accent3, valign: "top" });

  txt(s, "Economic rationale: why we expect a positive correlation", { x: 5.95, y: 1.5, w: 6.78, h: 0.35, fontSize: 16, bold: true, color: C.text2 });
  const why = [
    ["FaChartLine", "Industry expansion", "Biotech is an expanding industry, so firms that persist should grow in value alongside it."],
    ["FaFlask", "Pipeline de-risking", "Survivors turn R&D into approved, revenue-generating products; resolved clinical risk lifts expected cash flows and lowers required returns."],
    ["FaBalanceScale", "Accounting: R&D is expensed", "US GAAP expenses most R&D, so book equity understates accumulated know-how; market value capitalizes it as the pipeline matures."],
    ["FaBuilding", "Survival and scale", "Failures delist; long-lived public biotechs have raised more capital and reached commercial scale."],
  ];
  for (let i = 0; i < why.length; i++) {
    const y = 2.0 + i * 1.22;
    s.addShape(pres.ShapeType.ellipse, { x: 5.95, y: y + 0.05, w: 0.62, h: 0.62, fill: { color: C.accent1 }, line: { color: C.accent1, width: 0 }, objectName: `Rationale icon bg ${i + 1}` });
    s.addImage({ data: await icon(why[i][0]), x: 6.12, y: y + 0.22, w: 0.28, h: 0.28, altText: why[i][1], objectName: `Rationale icon ${i + 1}` });
    txt(s, [
      { text: why[i][1], options: { bold: true, fontSize: 15, color: C.text2, breakLine: true } },
      { text: why[i][2], options: { fontSize: 14, color: C.text1 } },
    ], { x: 6.8, y, w: 5.93, h: 1.1, valign: "top" });
  }
  s.addNotes("The 'why': industry expansion is the headline expectation. The accounting angle is that R&D is expensed, so the value created by successful R&D shows up in market value rather than book value. De-risking and survival reinforce this. We state a directional hypothesis (rho > 0) before looking at the data.");

  // ================= Slide 3: data & cleaning
  s = pres.addSlide({ masterName: "CONTENT_LAYOUT", sectionTitle: "Main" });
  s.addText("Data & Cleaning Choices", { placeholder: "title" });
  const cw = 2.9, gap = (12.13 - 4 * cw) / 3;
  [[String(S.n), "company-years after cleaning"], [String(S.firms), "unique biotech firms"], [`${S.fyear_min}–${S.fyear_max}`, "fiscal years covered"], ["≥ $100M", "revenue floor on every row"]]
    .forEach(([big, label], i) => statCard(s, 0.6 + i * (cw + gap), 1.5, cw, 1.3, big, label, `Stat ${i + 1}`));
  txt(s, "The data", { x: 0.6, y: 3.05, w: 5.9, h: 0.35, fontSize: 16, bold: true, color: C.text2 });
  txt(s, bullets([
    "What: annual firm-level financial ratios from the provided file ValuesFSARatios.xlsx (MVE, R&D / revenue, debt / equity, FCF / net income, revenue)",
    "Age: days since the firm's first filed 10-K (post-IPO age)",
    `When: fiscal years ${S.fyear_min}–${S.fyear_max}; 1 to ${S.rows_per_firm_max} years per firm (median ${S.rows_per_firm_median})`,
    "Industry: biotech as provided; the file has no industry code, so membership is taken as given",
  ]), { x: 0.6, y: 3.45, w: 5.9, h: 3.45, fontSize: 16, color: C.text1, valign: "top" });
  txt(s, "Cleaning steps", { x: 6.83, y: 3.05, w: 5.9, h: 0.35, fontSize: 16, bold: true, color: C.text2 });
  txt(s, bullets([
    "Revenue floor: only firm-years with revenue ≥ $100M (applied upstream) so ratios are not distorted by tiny denominators",
    "Missing data: none in the columns used; no imputation, and this analysis dropped no rows. Upstream filters on the full source table: Appendix A1",
    "Outliers: none removed and no winsorizing; 1% / 99% and 5% / 95% tests left the results unchanged (Appendix A2). Log axes handle the skew",
    "Units: MVE converted from $ millions to $; age from days to years",
  ]), { x: 6.83, y: 3.45, w: 5.9, h: 3.45, fontSize: 16, color: C.text1, valign: "top" });
  s.addNotes("Final sample is 833 company-years for 201 firms. The $100M revenue floor was applied in the data file and matters a lot: without it the correlation is much weaker (Appendix A2). We deliberately did not winsorize; the appendix shows why.");

  // ================= Slide 4: key visuals
  s = pres.addSlide({ masterName: "CONTENT_LAYOUT", sectionTitle: "Main" });
  s.addText("Age, not calendar time, is where MVE grows", { placeholder: "title" });
  const iw = 5.95, ih = iw / (6.05 / 4.75);
  s.addImage({ path: path.join(DECK, "lines_annotated.png"), x: 0.6, y: 1.45, w: iw, h: ih, altText: "Line graphs of MVE, R&D/revenue and debt/equity by fiscal year with yearly medians", objectName: "Line charts" });
  s.addImage({ path: path.join(DECK, "dot_annotated.png"), x: 6.78, y: 1.45, w: iw, h: ih, altText: "Dot plot of MVE against years since first 10-K with LOESS trend", objectName: "Dot plot" });
  txt(s, [{ text: "Line graphs: ", options: { bold: true } }, { text: "yearly medians are stable, so MVE, R&D intensity and leverage show no strong time trend." }],
    { x: 0.6, y: 6.2, w: iw, h: 0.7, fontSize: 13, color: C.text1, valign: "top" });
  txt(s, [{ text: "Dot plot: ", options: { bold: true } }, { text: `MVE is flat for ~12 years of filing history, then rises about ${(S.trend25 / S.trend11).toFixed(0)}× by year 25, with huge spread around the trend.` }],
    { x: 6.78, y: 6.2, w: iw, h: 0.7, fontSize: 13, color: C.text1, valign: "top" });
  s.addNotes("Left: each grey line is one company; the orange line is the yearly median. Right: each dot is a company-year; the orange line is a LOESS trend with a bootstrap 95% band (resampling whole companies). The median MVE by calendar year does not trend up, so the age pattern is not just a rising tide.");

  // ================= Slide 5: evidence
  s = pres.addSlide({ masterName: "CONTENT_LAYOUT", sectionTitle: "Main" });
  s.addText(`Older firms are worth ~${S.ratio_20plus.toFixed(0)}× more, but age explains only ~${Math.round(S.fit.r2 * 100)}%`, { placeholder: "title" });
  txt(s, "Size of the correlation", { x: 0.6, y: 1.45, w: 5.7, h: 0.3, fontSize: 16, bold: true, color: C.text2 });
  const sw = 2.75, sh = 1.62;
  [[f2(S.rho), "Spearman ρ (rank correlation)"], [f2(S.pearson_log), "Pearson r, log MVE vs age"],
   [`${Math.round(S.fit.r2 * 100)}%`, "share of log-MVE variation explained (R²)"], [`×${S.fit.per_decade.toFixed(1)}`, `MVE per extra decade of age (95% CI ×${S.fit.ci_lo.toFixed(1)}–${S.fit.ci_hi.toFixed(1)})`]]
    .forEach(([big, label], i) => statCard(s, 0.6 + (i % 2) * (sw + 0.2), 1.85 + Math.floor(i / 2) * (sh + 0.15), sw, sh, big, label, `Evidence stat ${i + 1}`));
  const bl = { "0-5": "0–5", "5-10": "5–10", "10-20": "10–20", "20-30": "20–30", "30+": "30+" };
  s.addChart(pres.charts.BAR, [{
    name: "Median MVE ($B)", labels: S.bands.map((b) => `${bl[b.band]} yrs (n=${b.n})`), values: S.bands.map((b) => +(b.median / 1e9).toFixed(1)),
  }], {
    x: 6.6, y: 1.45, w: 6.13, h: 3.85, barDir: "col", barGapWidthPct: 45,
    chartColors: [HEX.accent3, HEX.accent3, HEX.accent3, HEX.accent2, HEX.accent2],
    showTitle: true, title: "Median MVE by years since first 10-K ($ billions)", titleFontSize: 14, titleColor: HEX.dk1, titleFontFace: FONT_BODY,
    showValue: true, dataLabelFormatCode: "$0.0", dataLabelFontSize: 13, dataLabelFontBold: true, dataLabelColor: HEX.dk1, dataLabelFontFace: FONT_BODY, dataLabelPosition: "outEnd",
    catAxisLabelFontSize: 12, catAxisLabelColor: HEX.dk1, catAxisLabelFontFace: FONT_BODY,
    valAxisLabelFontSize: 12, valAxisLabelColor: HEX.dk1, valAxisLabelFontFace: FONT_BODY, valAxisLabelFormatCode: "$0",
    valGridLine: { color: "D5DDE0", size: 0.75 }, catGridLine: { style: "none" }, showLegend: false,
    valAxisMaxVal: 16, valAxisMajorUnit: 4,
  });
  card(s, 0.6, 5.45, 12.13, 1.45, "Economic significance card", C.background2);
  txt(s, [
    { text: "Economic significance: ", options: { bold: true, color: C.text2 } },
    { text: `firms with 20+ years of filings have a median MVE about ${S.ratio_20plus.toFixed(0)}× that of younger firms (${billions(S.bands[3].median)}–${billions(S.bands[4].median)} vs ${billions(S.bands[1].median)}–${billions(S.bands[2].median)}; 95% CI ${S.ratio_ci[0].toFixed(1)}–${S.ratio_ci[1].toFixed(1)}×, resampling firms). But the ranges overlap heavily: age shifts the typical level, yet on its own it is a weak predictor of any one firm's value.` },
  ], { x: 0.85, y: 5.55, w: 11.65, h: 1.25, fontSize: 15, color: C.text1, valign: "middle" });
  s.addNotes("rho = 0.29 is a moderate positive rank correlation. Under 20 years the median MVE is flat at roughly $1.5-1.7B; after 20 years it jumps. The 95% interval for the ratio of medians comes from resampling whole firms because each firm appears in several years.");

  // ================= Slide 6: conclusion
  s = pres.addSlide({ masterName: "CONTENT_LAYOUT", sectionTitle: "Main" });
  s.addText("Conclusion & Implications", { placeholder: "title" });
  const colW = 3.95, colGap = (12.13 - 3 * colW) / 2;
  const cols = [
    ["FaCheckCircle", "What we found", [
      `Yes: MVE is positively correlated with post-IPO age (ρ = ${f2(S.rho)}), so it rises rather than falls with age`,
      `Not steadily: flat (or slightly down) for ~12 years, then ~${(S.trend25 / S.trend11).toFixed(0)}× higher by year 25`,
      "Median MVE by calendar year does not drift up, so this looks like maturity and de-risking, not just a rising tide",
      `Age explains only ~${Math.round(S.fit.r2 * 100)}% of the variation: a real but modest factor`,
    ]],
    ["FaExclamationTriangle", "Limitations", [
      "Survivorship: failed biotechs delist, so older firms are the winners",
      `The $100M revenue floor excludes pre-revenue biotechs; without it ρ falls to ${f2(S.unfloored.spearman)}`,
      `Firms repeat across years; firm-level ρ is only ${f2(S.robust[1].spearman)}–${f2(S.robust[0].spearman)}`,
      "Correlation, not causation: scale and year effects are not controlled; industry label taken as given",
    ]],
    ["FaSearch", "Further analysis", [
      "Control for revenue, fiscal-year and firm effects to isolate age",
      "Add pre-revenue and delisted biotechs to test selection and survivorship",
      "Test the mechanism directly with pipeline stage or FDA approvals",
      `Compare IPO cohorts: ρ was ${f2(S.robust[3].spearman)} in 2010–16 vs ${f2(S.robust[4].spearman)} in 2017–24`,
    ]],
  ];
  for (let i = 0; i < 3; i++) {
    const x = 0.6 + i * (colW + colGap);
    card(s, x, 1.5, colW, 5.4, `Column card ${i + 1}`);
    s.addShape(pres.ShapeType.ellipse, { x: x + 0.25, y: 1.7, w: 0.55, h: 0.55, fill: { color: i === 1 ? C.accent2 : C.accent1 }, line: { color: C.background1, width: 0 }, objectName: `Column icon bg ${i + 1}` });
    s.addImage({ data: await icon(cols[i][0]), x: x + 0.405, y: 1.855, w: 0.25, h: 0.25, altText: cols[i][1], objectName: `Column icon ${i + 1}` });
    txt(s, cols[i][1], { x: x + 0.95, y: 1.7, w: colW - 1.15, h: 0.55, fontSize: 18, bold: true, color: C.text2, valign: "middle" });
    txt(s, bullets(cols[i][2]), { x: x + 0.25, y: 2.5, w: colW - 0.5, h: 4.25, fontSize: 16, color: C.text1, valign: "top" });
  }
  s.addNotes("Answer to the question: positive, moderate, and non-linear. Limitations matter: survivorship and the revenue floor are the big ones. Next steps are about separating age from scale and from calendar-time effects.");

  // ================= Appendix
  pres.addSection({ title: "Appendix" });
  const HDR = { bold: true, color: C.background1, fill: { color: C.text2 }, fontSize: 13, valign: "middle" };
  const cell = (t, o = {}) => ({ text: String(t), options: { fontSize: 13, color: C.text1, valign: "middle", ...o } });

  // A1: source data and upstream filters
  s = pres.addSlide({ masterName: "CONTENT_LAYOUT", sectionTitle: "Appendix" });
  s.addText("Appendix A1: Source data and upstream filters", { placeholder: "title" });
  const stepW = 3.6, arrowW = 0.45, stepGap = (12.13 - 3 * stepW) / 2;
  const steps = [
    { head: "Original source table", big: "100,000+", sub: "lines of data, all available columns (CompustatData.xlsx)", fill: C.background2, dark: false },
    { head: "Filters applied before this analysis", lines: ["Removed rows with zero total debt", "Removed rows with blank capex", "Kept revenue ≥ $100M"], fill: C.text2, dark: true },
    { head: "Extract provided for this analysis", big: String(S.n), sub: `company-years (${S.firms} firms), simplified to the columns needed`, fill: C.background2, dark: false },
  ];
  steps.forEach((st, i) => {
    const x = 0.6 + i * (stepW + stepGap);
    card(s, x, 1.5, stepW, 2.1, `Step card ${i + 1}`, st.fill);
    txt(s, st.head, { x: x + 0.2, y: 1.62, w: stepW - 0.4, h: 0.4, fontSize: 14, bold: true, color: st.dark ? C.accent4 : C.accent1, valign: "top", objectName: `Step ${i + 1} heading` });
    if (st.big) {
      txt(s, st.big, { x: x + 0.2, y: 2.05, w: stepW - 0.4, h: 0.7, fontFace: "Cambria", fontSize: 36, bold: true, color: C.text2, valign: "middle", objectName: `Step ${i + 1} value` });
      txt(s, st.sub, { x: x + 0.2, y: 2.8, w: stepW - 0.4, h: 0.7, fontSize: 14, color: C.text1, valign: "top", objectName: `Step ${i + 1} label` });
    } else {
      txt(s, bullets(st.lines, { color: C.background1 }), { x: x + 0.2, y: 2.1, w: stepW - 0.4, h: 1.4, fontSize: 15, color: C.background1, valign: "top", objectName: `Step ${i + 1} filters` });
    }
    if (i < 2) s.addShape(pres.ShapeType.rightArrow, { x: x + stepW + (stepGap - arrowW) / 2, y: 2.3, w: arrowW, h: 0.5, fill: { color: C.accent2 }, line: { color: C.accent2, width: 0 }, objectName: `Step arrow ${i + 1}` });
  });
  txt(s, "Why it matters", { x: 0.6, y: 3.9, w: 12.13, h: 0.35, fontSize: 16, bold: true, color: C.text2 });
  txt(s, bullets([
    "Zero total debt removed: debt-free firm-years are excluded, which may tilt the sample toward firms that carry debt",
    "Blank capex removed: only firm-years that report capital expenditure remain, which may leave out some early-stage or sparse filers",
    "These filters were applied before the file reached this analysis, so their effect on the MVE–age correlation has not been measured here; Appendix A2 isolates only the revenue floor (ρ 0.11 → 0.29)",
    "To test them, rebuild the charts from the full table with and without each filter",
  ]), { x: 0.6, y: 4.3, w: 12.13, h: 1.95, fontSize: 15, color: C.text1, valign: "top" });
  txt(s, [
    { text: "Code, data extract and README: ", options: { bold: true, color: C.text2 } },
    { text: REPO_URL, options: { color: C.accent1, underline: { style: "sng" }, hyperlink: { url: REPO_URL, tooltip: "Project repository on GitHub" } } },
    { text: "   |   Full source table: ", options: { bold: true, color: C.text2 } },
    { text: "CompustatData.xlsx (in the repository)" },
  ], { x: 0.6, y: 6.4, w: 12.13, h: 0.5, fontSize: 14, color: C.text1, valign: "middle", objectName: "Repository link" });
  s.addNotes("The data used here is a simplified extract of a table with over 100,000 lines. Before extraction, rows with zero total debt and rows with blank capex were removed, and the $100M revenue floor was applied. We have not measured how the first two filters affect the result.");

  // A2
  s = pres.addSlide({ masterName: "CONTENT_LAYOUT", sectionTitle: "Appendix" });
  s.addText("Appendix A2: Data cleaning choices and their effects", { placeholder: "title" });
  const r2 = (v) => (v == null ? "–" : v.toFixed(2));
  const rowsA1 = [[
    { text: "Version", options: { ...HDR, align: "left" } }, { text: "n", options: { ...HDR, align: "right" } }, { text: "Spearman ρ", options: { ...HDR, align: "right" } },
    { text: "Pearson r", options: { ...HDR, align: "right" } }, { text: "R² (log MVE)", options: { ...HDR, align: "right" } }, { text: "MVE per decade", options: { ...HDR, align: "right" } },
  ]];
  S.versions.forEach((v, i) => rowsA1.push([
    cell(v.label, { bold: i === 0 }), cell(v.n, { align: "right" }), cell(r2(v.spearman), { align: "right" }), cell(r2(v.pearson), { align: "right" }),
    cell(r2(v.r2), { align: "right" }), cell(`×${v.per_decade.toFixed(2)}`, { align: "right" }),
  ]));
  rowsA1.push([cell("Earlier data, no $100M revenue floor"), cell(S.unfloored.n.toLocaleString("en-US"), { align: "right" }), cell(r2(S.unfloored.spearman), { align: "right" }),
    cell(`${r2(S.unfloored.pearson_log)}*`, { align: "right" }), cell("–", { align: "right" }), cell("–", { align: "right" })]);
  s.addTable(rowsA1, { x: 0.6, y: 1.5, w: 12.13, colW: [4.73, 1.2, 1.5, 1.5, 1.6, 1.6], rowH: 0.38, border: { type: "solid", pt: 0.5, color: "D5DDE0" }, fill: { color: "FFFFFF" }, objectName: "Cleaning effects table" });
  txt(s, `* Pearson r on log MVE; this earlier file (${S.unfloored.n.toLocaleString("en-US")} company-years, ${S.unfloored.firms} firms) has no revenue column.`, { x: 0.6, y: 4.28, w: 12.13, h: 0.3, fontSize: 11, italic: true, color: C.accent3 });
  txt(s, bullets([
    "Winsorizing pulls extreme values to the cutoff. It lifts raw Pearson r (0.29 → 0.33–0.35) because a few giant firms stop dominating, but leaves rank correlation and the fitted slope unchanged, so no hidden stronger relationship",
    "Bias from winsorizing: it shrinks the tails toward the middle and understates true dispersion. Rank statistics and log axes handle outliers without changing values, so the final analysis uses unmodified data",
    "The $100M revenue floor is the biggest data choice: it removes small and pre-revenue firms and raises ρ from 0.11 to 0.29. Results describe commercial-stage biotechs",
    "No firms were dropped for missing data in this analysis (no missing values in the columns used); upstream filters are in Appendix A1",
  ]), { x: 0.6, y: 4.7, w: 12.13, h: 2.25, fontSize: 14, color: C.text1, valign: "top" });
  s.addNotes("Why winsorizing was not used: it changes Pearson but not the rank-based result or the slope.");

  // A2
  s = pres.addSlide({ masterName: "CONTENT_LAYOUT", sectionTitle: "Appendix" });
  s.addText("Appendix A3: Robustness checks", { placeholder: "title" });
  const rowsA2 = [[
    { text: "Cut of the data", options: { ...HDR, align: "left" } }, { text: "n", options: { ...HDR, align: "right" } }, { text: "Correlation of MVE with age", options: { ...HDR, align: "right" } },
  ]];
  rowsA2.push([cell("Full sample (Spearman ρ)", { bold: true }), cell(S.n, { align: "right" }), cell(f2(S.rho), { align: "right" })]);
  S.robust.forEach((r) => rowsA2.push([cell(r.label), cell(r.n, { align: "right" }), cell(r.spearman != null ? `ρ = ${f2(r.spearman)}` : `r = ${f2(r.pearson)}`, { align: "right" })]));
  s.addTable(rowsA2, { x: 0.6, y: 1.5, w: 7.2, colW: [4.4, 0.9, 1.9], rowH: 0.4, border: { type: "solid", pt: 0.5, color: "D5DDE0" }, fill: { color: "FFFFFF" }, objectName: "Robustness table" });
  txt(s, "Reading the table", { x: 8.2, y: 1.5, w: 4.53, h: 0.35, fontSize: 16, bold: true, color: C.text2 });
  txt(s, bullets([
    "Positive in every cut, but weaker once each firm counts once (ρ ≈ 0.15–0.18)",
    `Strongest in 2010–16 (ρ = ${f2(S.robust[3].spearman)}) and weaker in 2017–24 (${f2(S.robust[4].spearman)}), a period when many young IPOs entered: ${S.n_by_year[2010]} firms in 2010 vs ${S.n_by_year[2024]} in 2024`,
    `Not driven by the largest firms: dropping MVE above $100B leaves ρ = ${f2(S.robust[5].spearman)}`,
    `Scale matters more than age: revenue has ρ = ${f2(S.other_corr.revt.mve)} with MVE (and ${f2(S.other_corr.revt.age)} with age)`,
  ]), { x: 8.2, y: 1.9, w: 4.53, h: 4.9, fontSize: 14, color: C.text1, valign: "top" });
  s.addNotes("Within-firm only means each firm's average is removed, so it measures whether a firm's MVE rises as it ages; it is positive but small, and it also reflects calendar time.");

  // A3
  s = pres.addSlide({ masterName: "CONTENT_LAYOUT", sectionTitle: "Appendix" });
  s.addText("Appendix A4: Summary statistics and methods", { placeholder: "title" });
  const sm = S.summary, num = (v, d = 0) => v.toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d });
  const rowsA3 = [["Variable", "Min", "Median", "Mean", "Max"].map((t, i) => ({ text: t, options: { ...HDR, align: i ? "right" : "left" } }))];
  [["MVE ($ millions)", sm.mve, 0], ["Age (years since first 10-K)", sm.age, 1], ["Revenue ($ millions)", sm.revt, 0]].forEach(([n, v, d]) =>
    rowsA3.push([cell(n), cell(num(v.min, d), { align: "right" }), cell(num(v["50%"], d), { align: "right" }), cell(num(v.mean, d), { align: "right" }), cell(num(v.max, d), { align: "right" })]));
  s.addTable(rowsA3, { x: 0.6, y: 1.5, w: 7.2, colW: [2.9, 0.9, 1.1, 1.1, 1.2], rowH: 0.42, border: { type: "solid", pt: 0.5, color: "D5DDE0" }, fill: { color: "FFFFFF" }, objectName: "Summary statistics table" });
  txt(s, `n = ${S.n} company-years (${S.firms} firms). MVE is strongly right-skewed (mean about 5× the median), which is why the charts use a log axis.`, { x: 0.6, y: 3.45, w: 7.2, h: 0.7, fontSize: 13, color: C.text1, valign: "top" });
  txt(s, "Method notes", { x: 8.2, y: 1.5, w: 4.53, h: 0.35, fontSize: 16, bold: true, color: C.text2 });
  txt(s, bullets([
    "Trend line: LOESS of log(MVE) on age, span 0.4, drawn over the 1st–99th percentile of age",
    "95% band: 300 resamples of whole firms, refitting each time",
    "Axes: MVE log scale; R&D / revenue linear; debt / equity symmetric-log (it has negative values)",
    "Reproduce: Python and Node scripts, data extract and README at github.com/AlwaysOverachieve/Project1",
  ]), { x: 8.2, y: 1.9, w: 4.53, h: 4.9, fontSize: 14, color: C.text1, valign: "top" });
  s.addNotes("Summary statistics are for the final sample. The mean MVE is far above the median because of a few very large firms.");

  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
})();
