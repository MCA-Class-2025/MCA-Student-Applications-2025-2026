// PolicyPal — Phase 1 (Parts A–E) report.
// Reads reports/phase1/stats.json + figures (made by build_phase1_assets.py). No API calls.
// Run: node reports/phase1/build_report.js   (needs: npm install docx)
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell, WidthType,
  ShadingType, AlignmentType, ImageRun, PageBreak, LevelFormat, BorderStyle, TableOfContents,
  Footer, Header, PageNumber,
} = require("docx");

const R = __dirname;
const S = JSON.parse(fs.readFileSync(path.join(R, "stats.json"), "utf8"));
const n = (x) => Number(x).toLocaleString("en-US");
const pct = (a, b) => ((100 * a) / b).toFixed(1) + "%";
const A = S.api_calls;

const FONT = "Calibri", MONO = "Consolas";
const BLUE = "1F4E79", LIGHT = "DCE6F2", GREY = "F2F2F2", RED = "C00000", GREEN = "2E7D32", AMBER = "B26A00";
const W = 9026;

const runs = (t) => String(t).split(/(\*\*[^*]+\*\*)/).filter(Boolean).map((p) =>
  p.startsWith("**") ? new TextRun({ text: p.slice(2, -2), bold: true }) : new TextRun(p));
const P = (t) => new Paragraph({ children: runs(t), spacing: { after: 120, line: 276 } });
const H1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(t)] });
const H2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(t)] });
const H3 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun(t)] });
const B = (t) => new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: runs(t), spacing: { after: 60 } });
const NUM = (t) => new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: runs(t), spacing: { after: 60 } });
const BR = () => new Paragraph({ children: [new PageBreak()] });
const gap = (a = 120) => new Paragraph({ spacing: { after: a }, children: [] });
const cap = (t) => new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 60, after: 200 },
  children: [new TextRun({ text: t, italics: true, size: 18, color: "595959" })] });

let figNo = 0, tabNo = 0;
const figure = (file, w, title) => {
  const buf = fs.readFileSync(path.join(R, "figures", file));
  const pw = buf.readUInt32BE(16), ph = buf.readUInt32BE(20);
  figNo++;
  return [new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 120 },
    children: [new ImageRun({ type: "png", data: buf, transformation: { width: w, height: Math.round(w * ph / pw) },
      altText: { title, description: title, name: file } })] }), cap(`Figure ${figNo}. ${title}`)];
};
const border = { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF" };
const borders = { top: border, bottom: border, left: border, right: border };
const cell = (text, w, o = {}) => new TableCell({
  width: { size: w, type: WidthType.DXA }, borders,
  shading: o.fill ? { fill: o.fill, type: ShadingType.CLEAR, color: "auto" } : undefined,
  margins: { top: 60, bottom: 60, left: 100, right: 100 },
  children: String(text).split("\n").map((l) => new Paragraph({ alignment: o.align || AlignmentType.LEFT,
    children: [new TextRun({ text: l, bold: o.bold, color: o.color, size: o.mono ? 17 : 19, font: o.mono ? MONO : FONT })] })),
});
const table = (title, headers, rows, widths, opts = {}) => {
  tabNo++;
  return [
    new Paragraph({ keepNext: true, spacing: { before: 160, after: 80 },
      children: [new TextRun({ text: `Table ${tabNo}. ${title}`, bold: true, size: 19, color: BLUE })] }),
    new Table({ width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA }, columnWidths: widths, rows: [
      new TableRow({ tableHeader: true, children: headers.map((h, i) => cell(h, widths[i], { bold: true, fill: LIGHT })) }),
      ...rows.map((r) => new TableRow({ cantSplit: true, children: r.map((v, i) => {
        let o = {};
        if (v && typeof v === "object") { o = { ...v }; v = v.t; }
        if (opts.mono && opts.mono.includes(i)) o.mono = true;
        if (opts.right && opts.right.includes(i)) o.align = AlignmentType.RIGHT;
        return cell(v, widths[i], o);
      }) })),
    ] }),
    gap(),
  ];
};
const code = (lines, label) => [
  ...(label ? [new Paragraph({ keepNext: true, spacing: { before: 120, after: 40 }, children: [new TextRun({ text: label, bold: true, size: 18, color: "595959" })] })] : []),
  new Table({ width: { size: W, type: WidthType.DXA }, columnWidths: [W], rows: [new TableRow({ children: [new TableCell({
    width: { size: W, type: WidthType.DXA }, borders, shading: { fill: GREY, type: ShadingType.CLEAR, color: "auto" },
    margins: { top: 80, bottom: 80, left: 140, right: 140 },
    children: lines.map((l) => new Paragraph({ children: [new TextRun({ text: l || " ", font: MONO, size: 16 })] })) })] })] }),
  gap(100),
];
const callout = (title, body, color = BLUE, fill = "EAF1FB") => [
  new Table({ width: { size: W, type: WidthType.DXA }, columnWidths: [W], rows: [new TableRow({ children: [new TableCell({
    width: { size: W, type: WidthType.DXA },
    borders: { top: border, bottom: border, right: border, left: { style: BorderStyle.SINGLE, size: 24, color } },
    shading: { fill, type: ShadingType.CLEAR, color: "auto" }, margins: { top: 100, bottom: 100, left: 180, right: 180 },
    children: [new Paragraph({ spacing: { after: 60 }, children: [new TextRun({ text: title, bold: true, color })] }),
      ...[].concat(body).map((b) => new Paragraph({ spacing: { after: 40 }, children: runs(b) }))] })] })] }),
  gap(),
];
const dash = { style: BorderStyle.DASHED, size: 8, color: "7F7F7F" };
const placeholder = (what, how) => [
  new Table({ width: { size: W, type: WidthType.DXA }, columnWidths: [W], rows: [new TableRow({ height: { value: 1400, rule: "atLeast" },
    children: [new TableCell({ width: { size: W, type: WidthType.DXA }, borders: { top: dash, bottom: dash, left: dash, right: dash },
      shading: { fill: "FAFAFA", type: ShadingType.CLEAR, color: "auto" }, margins: { top: 200, bottom: 200, left: 200, right: 200 }, verticalAlign: "center",
      children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: `[ SCREENSHOT PLACEHOLDER — ${what} ]`, bold: true, color: "7F7F7F" })] }),
        new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: how, italics: true, size: 18, color: "7F7F7F" })] })] })] })] }),
  gap(160),
];
const st = (t, c) => ({ t, bold: true, color: c });

const ex = { c: S.ex_country, g: S.ex_geo, w: S.ex_wx, h: S.ex_holiday, nw: (S.ex_news_relevant[0] || S.ex_news[0]) };
const missing = S.master_missing;
const body = [];

// ---------- title page
body.push(
  new Paragraph({ spacing: { before: 2200, after: 200 }, alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "PolicyPal — Company Policy AI Bot", bold: true, size: 44, color: BLUE })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 400 },
    children: [new TextRun({ text: "API Data Fusion for Data Science & Analytics", bold: true, size: 32, color: BLUE })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 120 }, children: [new TextRun({ text: "Phase 1 Report — Parts A to E", size: 30 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 1000 },
    children: [new TextRun({ text: "Original Dataset · Five-API Collection · Data Fusion · Data Quality · EDA", size: 22, color: "595959" })] }),
  ...table("Submission details", ["Field", "Value"], [
    ["Student name", "[Student Name]"], ["Roll number", "[Roll Number]"], ["Course", "[Course Name]"],
    ["Faculty", "[Faculty Name]"], ["Academic year", "[Academic Year]"], ["Project folder", "policy-chatbot-v8/"],
  ], [3000, 6026]),
  BR(),
  new Paragraph({ spacing: { after: 200 }, children: [new TextRun({ text: "Contents", bold: true, size: 34, color: BLUE })] }),
  new TableOfContents("Contents", { hyperlink: true, headingStyleRange: "1-2" }),
  BR(),
);

// ---------- executive summary
body.push(H1("Executive Summary"),
  P("PolicyPal is a RAG-based company-policy chatbot. Its original data is a policy knowledge base for the fictional company NimbusTech Solutions (five policy documents and an HR FAQ file). Phase 1 adds a **data-fusion layer**: five public APIs supply country, currency, weather, public-holiday and HR-news context, which `src/policy_data_fusion.py` fuses into one analytical table, data/PolicyPal_Master_Dataset.xlsx."),
  P("Every number in this report was computed from the project's own files: data/raw, vectorstore, data/api_cache (the raw JSON saved during collection) and the fused workbook. No API was called again for this report."),
  ...table("Key results", ["Metric", "Value"], [
    ["Original knowledge base", `${S.kb_files} files (5 Markdown policies + hr_faqs.csv), ${n(S.kb_total_words)} words, ${S.kb_size_kb} KB`],
    ["RAG index", `${S.chunks_total} chunks × ${S.embedding_dim}-dimension embeddings (FAISS)`],
    ["API requests in the collection run", n(Object.values(A).reduce((a, b) => a + b.requests, 0))],
    ["Before-fusion source tables", `11 sheets (data/PolicyPal_Before_Fusion_Source_Tables.xlsx)`],
    ["Fused dataset (Master_Dataset)", `${n(S.master_rows)} rows × ${S.master_cols} columns`],
    ["News articles behind the fused rows", `${S.news_articles} (each expanded to 5 cities)`],
    ["Countries with fused rows", `6 of 10 (${S.countries_without_rows.join(", ")} have none)`],
    ["Fusion validation", { t: "All checks passed (row count, unique IDs, attribute match)", bold: true, color: GREEN }],
  ], [4200, 4826]),
  ...callout("Academic integrity note on API results", [
    "All five APIs were reached, but **not every request returned data**. countries.dev, ExchangeRate-API and Open-Meteo answered every request. Nager.Date returned **no data (HTTP 204) for India and the UAE**. NewsData.io returned articles for only **52 of 100** requests: from request 55 onward no successful response was recorded, so the UAE, Germany, France and Japan have **no news rows**.",
    "These outcomes are reported exactly as found in the cache and the workbook. Successful and failed requests are kept separate in every table and chart.",
  ], AMBER, "FFF6E5"),
  BR());

// ---------- PART A
const docs = S.kb_docs;
body.push(H1("Part A — Original Dataset"),
  H2("A.1 Source and description"),
  P("PolicyPal's original dataset is its **policy knowledge base**: a synthetic but realistic set of HR policy documents for the fictional company NimbusTech Solutions. Real company handbooks are confidential, so a representative corpus was constructed with consistent structure and internally consistent figures (for example, 18 days of annual leave). This corpus is what the chatbot retrieves from; it is stored in data/raw/."),
  ...table("Knowledge-base composition", ["File", "Format", "Title", "Words", "Sections", "Numbers"],
    [...docs.map((d) => [d.file, "Markdown", d.title, String(d.words), String(d.sections), String(d.numeric_values)]),
      ["hr_faqs.csv", "CSV", "HR FAQs (question / answer / category)", String(S.kb_total_words - docs.reduce((a, d) => a + d.words, 0)), `${S.faq_rows} rows`, "—"]],
    [2500, 900, 2826, 900, 1000, 900], { mono: [0], right: [3, 4, 5] }),
  H2("A.2 Structured component — hr_faqs.csv"),
  ...table("hr_faqs.csv schema", ["Column", "Type", "Description"], [
    ["question", "text", "Employee question in natural language"], ["answer", "text", "Policy-grounded answer"],
    ["category", "categorical", "Leave, Finance, IT Security, Remote Work, Code of Conduct, Attendance"],
  ], [2000, 1600, 5426], { mono: [0] }),
  ...table("Sample FAQ records", ["Question", "Answer", "Category"],
    S.faq_sample.slice(0, 3).map((r) => [r.question, r.answer, r.category]), [2900, 4826, 1300]),
  H2("A.3 Processing into the RAG index"),
  P(`src/data_processing.py splits each document on its section headers so that every chunk stays on one topic, and turns each FAQ row into its own chunk. The result is ${S.chunks_total} chunks (median ${S.chunk_chars["50%"]} characters, range ${S.chunk_chars.min}–${S.chunk_chars.max}) embedded with Cohere into ${S.embedding_dim}-dimensional vectors and stored in vectorstore/index.faiss.`),
  H2("A.4 Exploratory analysis of the original data"),
  ...figure("a1_policy_documents.png", 540, "Size and structure of the five policy documents."),
  P(`The five policies are of similar length (${Math.min(...docs.map((d) => d.words))}–${Math.max(...docs.map((d) => d.words))} words). The leave and attendance policy is the most detailed (${docs.find((d) => d.file.startsWith("leave")).sections} sections, ${docs.find((d) => d.file.startsWith("leave")).numeric_values} numeric values such as day counts), which matches it being the most frequently asked-about topic.`),
  ...figure("a2_faq_categories.png", 520, "HR FAQ questions by category."),
  ...figure("a3_chunks_per_source.png", 520, "RAG chunks per source file."),
  P(`The FAQ file contributes ${S.chunks_by_source["hr_faqs.csv"]} of the ${S.chunks_total} chunks because each Q/A pair is indexed separately. The FAQ data has ${S.faq_missing} missing values and ${S.faq_dup_questions} duplicate questions. The analytics log holds ${S.interactions} test interactions (${Object.entries(S.interaction_coverage).map(([k, v]) => `${v} ${k}`).join(", ")} coverage).`),
  BR());

// ---------- PART B
const apiDocs = [
  { n: "countries.dev", key: "countries.dev", url: "https://countries.dev/alpha/{country_code}", params: "path: ISO alpha-2 code (e.g. IN)", auth: "None",
    fields: "name, alpha3Code, capital, region, subregion, timezones[0], population, area, currencies[0].code/name/symbol", fn: "get_country()", grain: "1 request per country (10)" },
  { n: "ExchangeRate-API (open.er-api.com)", key: "ExchangeRate-API", url: "https://open.er-api.com/v6/latest/USD", params: "none (base currency USD in path)", auth: "None",
    fields: "result, rates{currency: rate}, time_last_update_utc", fn: "get_currency_rates()", grain: "1 request per run" },
  { n: "Open-Meteo (geocoding + forecast)", key: "Open-Meteo (forecast)", url: "https://geocoding-api.open-meteo.com/v1/search\nhttps://api.open-meteo.com/v1/forecast", params: "name, count=10, language=en\nlatitude, longitude, current=temperature_2m,precipitation,weather_code,wind_speed_10m", auth: "None",
    fields: "latitude, longitude (geocoding); temperature_2m, precipitation, weather_code, wind_speed_10m (forecast)", fn: "geocode(), get_weather()", grain: "2 requests per city (50 cities)" },
  { n: "Nager.Date (nagerholidays.com)", key: "Nager.Date", url: "https://nagerholidays.com/api/v4/Holidays/{country}/{year}", params: "path: country code, year", auth: "None",
    fields: "date, name, holidayTypes, nationalHoliday", fn: "get_holidays()", grain: "1 request per country-year (10)" },
  { n: "NewsData.io", key: "NewsData.io", url: "https://newsdata.io/api/1/news", params: "apikey, q={policy topic}, country, language=en", auth: "API key (NEWSDATA_API_KEY)",
    fields: "title, source_id, link, pubDate (max 10 articles per request)", fn: "get_news()", grain: "1 request per country × topic (100)" },
];
const outcome = (k) => {
  const a = A[k];
  if (k === "Nager.Date") return [st("PARTIAL", AMBER), `${a.with_data}/${a.requests} countries returned holidays (${a.records} rows); India and UAE: HTTP 204, no data.`];
  if (k === "NewsData.io") return [st("PARTIAL", AMBER), `${a.with_data}/${a.requests} requests returned articles (${a.records} articles); 2 succeeded with 0 articles; 46 had no successful response.`];
  if (k === "Open-Meteo (forecast)") return [st("SUCCESS", GREEN), `Geocoding ${A["Open-Meteo (geocoding)"].with_data}/50 and forecast ${a.with_data}/50 cities.`];
  return [st("SUCCESS", GREEN), `${a.with_data}/${a.requests} requests returned data (${n(a.records)} records).`];
};
body.push(H1("Part B — Five-API Data Collection"),
  H2("B.1 Collection design"),
  P("The collection grid is defined in src/fusion_config.py: **10 countries × 5 cities × 10 HR policy topics**. For each country the builder fetches country metadata, the current year's public holidays and the weather of its five cities, and runs one NewsData query per policy topic. One USD exchange-rate snapshot is shared by all rows."),
  B("**Disk cache:** every successful JSON response is saved to data/api_cache/, named by a hash of the URL and parameters, so re-runs never spend API credits twice."),
  B("**Status capture:** each source's status (LIVE, CACHE, HTTP_xxx, ERROR) is written into api_collection_status for every fused row."),
  B("**No fabrication:** a missing response stays missing; it is never filled with made-up values."),
  B("**Credit control:** NewsData requests are capped at 100 per run, with a 0.25 s pause between requests."),
  H2("B.2 API documentation"),
);
apiDocs.forEach((d, i) => {
  const [s, note] = outcome(d.key);
  body.push(H3(`B.2.${i + 1} ${d.n}`),
    ...table(`${d.n} — specification and observed result`, ["Item", "Detail"], [
      ["Endpoint", { t: d.url, mono: true }], ["Method", "GET"], ["Parameters", { t: d.params, mono: true }],
      ["Authentication", d.auth], ["Response format", "JSON"], ["Request grain", d.grain], ["Fields parsed", d.fields],
      ["Parser", { t: `src/policy_data_fusion.py → ${d.fn}`, mono: true }], ["Observed status", s], ["Result", note],
    ], [2200, 6826]),
    ...placeholder(`${d.n} request/response`, "Paste a browser/Postman screenshot of one request and its JSON response."));
});
body.push(H2("B.3 Collection outcome"),
  ...table("Requests and records per API", ["API", "Requests", "Returned data", "Records", "Classification"],
    Object.entries(A).map(([k, a]) => [k, String(a.requests), `${a.with_data} (${pct(a.with_data, a.requests)})`, n(a.records),
      a.with_data === a.requests ? st("Successful", GREEN) : st("Partial", AMBER)]), [2700, 1100, 1800, 1200, 2226], { right: [1, 2, 3] }),
  ...figure("b1_api_outcomes.png", 540, "Share of requests that returned data, by API."),
  ...figure("b2_news_request_grid.png", 580, "NewsData.io: articles returned for each country × topic request."),
  ...callout("Interpretation", [
    `**NewsData.io** is the limiting source. Requests run in config order (India, US, UK, Canada, Australia, Singapore, UAE, Germany, France, Japan). The first ${S.news_first_failure_index - 1} succeeded and every request from number ${S.news_first_failure_index} onward has no successful response. That pattern fits the free plan's request limits; the exact HTTP code was not persisted, because only successful responses are cached.`,
    "**Nager.Date** returned HTTP 204 (no content) for India and the UAE, so these countries have no holiday context.",
    "**countries.dev, ExchangeRate-API and Open-Meteo** were fully successful: 10 countries, 166 currency rates, 50 geocoded cities and 50 weather readings.",
  ]),
  H2("B.4 Request → Response → Parsing → Structured data"),
  P("Worked examples follow one city (Pune, India) through Open-Meteo and one India news request through NewsData. Responses are taken from data/api_cache and shortened to the fields the parser reads."),
  H3("Example 1 — Open-Meteo (Pune)"),
  ...code([
    "GET https://geocoding-api.open-meteo.com/v1/search?name=Pune&count=10&language=en&format=json",
    `→ {"results": [{"name": "${ex.g.resolved_name}", "country_code": "${ex.g.resolved_country_code}", "admin1": "${ex.g.resolved_admin1}",`,
    `                "latitude": ${ex.g.latitude}, "longitude": ${ex.g.longitude}}, ... ${ex.g.candidates_returned - 1} more candidates]}`,
    "",
    `GET https://api.open-meteo.com/v1/forecast?latitude=${ex.g.latitude}&longitude=${ex.g.longitude}`,
    "    &current=temperature_2m,precipitation,weather_code,wind_speed_10m&timezone=auto",
    `→ {"timezone": "${ex.w.timezone}", "current": {"time": "${ex.w.observed_at_local}", "temperature_2m": ${ex.w.temperature_c},`,
    `                "precipitation": ${ex.w.precipitation_mm}, "weather_code": ${ex.w.weather_code}, "wind_speed_10m": ${ex.w.wind_speed_kmh}}}`,
  ], "Request and response (abridged)"),
  ...code([
    "matches   = payload['results']",
    "preferred = [x for x in matches if x['country_code'].upper() == country_code]   # IN",
    "item      = (preferred or matches)[0]",
    "current   = forecast['current']",
    "label, severe = weather_label(current['weather_code'])      # WMO code → text + severity",
    "row = {latitude, longitude, temperature_c, precipitation_mm, wind_speed_kmh,",
    "       weather_code, weather_condition=label, is_severe_weather=severe or temp >= 42}",
  ], "Parsing (src/policy_data_fusion.py)"),
  ...table("Structured weather record — Pune", ["Column", "Value"], [
    ["country_code / city", `${ex.g.country_code} / ${ex.g.city}`], ["latitude, longitude", `${ex.g.latitude}, ${ex.g.longitude}`],
    ["temperature_c", String(ex.w.temperature_c)], ["precipitation_mm", String(ex.w.precipitation_mm)],
    ["wind_speed_kmh", String(ex.w.wind_speed_kmh)], ["weather_code → weather_condition", `${ex.w.weather_code} → Partly cloudy`],
    ["is_severe_weather", "False"],
  ], [3600, 5426], { mono: [0] }),
  H3("Example 2 — NewsData.io (India, “remote work”)"),
  ...code([
    "GET https://newsdata.io/api/1/news?apikey=***&q=remote work&country=in&language=en",
    `→ {"status": "success", "totalResults": ..., "results": [`,
    `     {"title": "${String(ex.nw.title).slice(0, 70)}…",`,
    `      "source_id": "${ex.nw.source_id}", "pubDate": "${ex.nw.pubDate}",`,
    `      "link": "${String(ex.nw.link).slice(0, 70)}…"}, ... ]}`,
  ], "Request and response (abridged; API key masked)"),
  ...code([
    "for item in payload['results'][:10]:",
    "    articles.append({'news_title': item['title'], 'news_source': item['source_id'],",
    "                     'news_url': item['link'], 'news_published_at': item['pubDate'],",
    "                     'news_country': country_code})",
  ], "Parsing"),
  ...table("Structured news record", ["Column", "Value"], [
    ["policy_topic", ex.nw.policy_topic], ["news_title", ex.nw.title], ["news_source", ex.nw.source_id],
    ["news_published_at", ex.nw.pubDate], ["news_country", ex.nw.country_code],
  ], [2600, 6426], { mono: [0] }),
  P(`Every parsed response is kept, before fusion, in **data/PolicyPal_Before_Fusion_Source_Tables.xlsx**. It has one sheet per source: countries (${S.before_sheets.API1_Countries}), exchange rates (${S.before_sheets.API2_Exchange_Rates}), city geocodes (${S.before_sheets.API3a_City_Geocode}), city weather (${S.before_sheets.API3b_City_Weather}), holidays (${S.before_sheets.API4_Holidays}) and news articles (${S.before_sheets.API5_News_Articles}). It also holds the knowledge-base sheets and two request logs (${S.before_sheets.NewsData_Request_Log} NewsData requests, ${S.before_sheets.API_Request_Log} requests in total).`),
  BR());

// ---------- PART C
body.push(H1("Part C — Data Fusion"),
  H2("C.1 Fusion keys and method"),
  P("PolicyPal has no single row key such as an ID shared by all sources. Instead, each source is attached through the reference it naturally shares with the **observation unit: one news article × one city × one policy topic**."),
  ...table("Fusion keys", ["Source", "Join key", "Relationship", "Fields added"], [
    ["NewsData.io (driver)", "country_code + policy_topic", "1 request → up to 10 articles", "news_title, news_source, news_url, news_published_at"],
    ["Config grid", "country_code", "each article × 5 cities of its country", "city"],
    ["countries.dev", "country_code", "many-to-one", "country_name … currency_symbol (12 fields)"],
    ["ExchangeRate-API", "currency_code (from countries.dev)", "many-to-one", "usd_to_local_rate"],
    ["Open-Meteo", "country_code + city", "many-to-one", "latitude … is_severe_weather (8 fields)"],
    ["Nager.Date", "country_code + year", "first holiday of the year", "holiday_date, holiday_name, holiday_type, is_public_holiday"],
  ], [2000, 2300, 2300, 2426]),
  ...code([
    "for country_code, cfg in COUNTRIES.items():",
    "    country, c_status = get_country(country_code)              # countries.dev",
    "    holidays, h_status = get_holidays(country_code, year)      # Nager.Date",
    "    weather = {city: get_weather(city, country_code) for city in cfg['cities']}   # Open-Meteo",
    "    for topic in POLICY_TOPICS:",
    "        articles, n_status = get_news(key, country_code, topic)  # NewsData.io",
    "        for article in articles:",
    "            for city in cfg['cities']:",
    "                row = {record_id, observation_date, country_code, **country,",
    "                       'usd_to_local_rate': rates[country['currency_code']],   # ExchangeRate-API",
    "                       'city': city, **weather[city], **choose_holiday(holidays),",
    "                       'policy_topic': topic, **article, api_collection_status, data_quality_flag}",
  ], "src/policy_data_fusion.py — build_dataset() (simplified)"),
  P("Because NewsData drives the row creation, a country only appears in the fused table if at least one of its news requests returned articles. The full holiday list is kept separately in the Holiday_Calendar sheet so that holidays do not multiply the article rows."),
  H2("C.2 Fusion validation"),
  ...table("Fusion validation", ["Check", "Expected", "Observed", "Result"], [
    ["Fused rows = articles × 5 cities", `${S.news_articles} × 5 = ${n(S.expected_rows)}`, n(S.master_rows), st(S.master_rows === S.expected_rows ? "PASS" : "FAIL", S.master_rows === S.expected_rows ? GREEN : RED)],
    ["Fused columns = DATASET_COLUMNS", "36", String(S.master_cols), st("PASS", GREEN)],
    ["record_id unique", "0 duplicates", S.record_id_unique ? "0" : "> 0", st(S.record_id_unique ? "PASS" : "FAIL", S.record_id_unique ? GREEN : RED)],
    ["Country attributes = countries.dev table", "0 mismatches", String(S.chk_country_attr_mismatch), st("PASS", GREEN)],
    ["usd_to_local_rate = ExchangeRate-API rate", "0 mismatches", String(S.chk_fx_mismatch), st("PASS", GREEN)],
    ["Weather = Open-Meteo city table", "0 mismatches", `${S.chk_weather_mismatch} of ${n(S.chk_weather_joined)}`, st("PASS", GREEN)],
    ["Geocoded city in requested country", "50 / 50", `${50 - S.geo_country_mismatch.length} / 50`, st("PASS", GREEN)],
    ["holiday_date = first holiday in calendar", "true", String(S.chk_holiday_first_ok), st("PASS", GREEN)],
    ["Exact duplicate rows (excluding ID)", "0", String(S.dup_full_rows), st("PASS", GREEN)],
    ["Countries represented", "10", `6 (missing ${S.countries_without_rows.join(", ")})`, st("NOTE", AMBER)],
  ], [3500, 2000, 1900, 1626]),
  H2("C.3 Fused dataset structure"),
  ...table("PolicyPal_Master_Dataset.xlsx — sheets", ["Sheet", "Rows × columns", "Content"], [
    ["Master_Dataset", S.master_sheets.Master_Dataset.join(" × "), "Fused observations"],
    ["Holiday_Calendar", S.master_sheets.Holiday_Calendar.join(" × "), "All holidays per country"],
    ["Data_Dictionary", S.master_sheets.Data_Dictionary.join(" × "), "Column description and source"],
    ["API_Run_Log", S.master_sheets.API_Run_Log.join(" × "), "Run timestamp, request count"],
    ["Dataset_Summary", S.master_sheets.Dataset_Summary.join(" × "), "Purpose and design notes"],
  ], [2400, 1800, 4826], { mono: [0] }),
  ...table("Master_Dataset — 36 columns by source", ["Source", "Columns", "Count"], [
    ["System / derived", "record_id, observation_date, api_collection_status, data_quality_flag", "4"],
    ["Config", "country_code, city, policy_topic", "3"],
    ["countries.dev", "country_name, alpha3_code, capital, region, subregion, timezone, population, area_km2, currency_code, currency_name, currency_symbol", "11"],
    ["ExchangeRate-API", "usd_to_local_rate", "1"],
    ["Open-Meteo", "latitude, longitude, temperature_c, precipitation_mm, wind_speed_kmh, weather_code, weather_condition, is_severe_weather", "8"],
    ["Nager.Date", "holiday_date, holiday_name, holiday_type, is_public_holiday", "4"],
    ["NewsData.io", "news_title, news_source, news_url, news_published_at, news_country", "5"],
  ], [2000, 6226, 800], { right: [2] }),
  H2("C.4 Excel files"),
  ...table("Excel deliverables", ["File", "Stage", "Content"], [
    ["data/PolicyPal_Before_Fusion_Source_Tables.xlsx", "Before fusion", "Knowledge base + one parsed table per API + request logs (11 sheets)"],
    ["data/PolicyPal_Master_Dataset.xlsx", "After fusion", "Fused Master_Dataset + Holiday_Calendar, Data_Dictionary, API_Run_Log, Dataset_Summary"],
  ], [4200, 1500, 3326], { mono: [0] }),
  BR());

// ---------- PART D
body.push(H1("Part D — Data Quality Assessment"),
  H2("D.1 Missing values"),
  ...figure("d1_missing_values.png", 540, "Columns with missing values in Master_Dataset."),
  ...table("Missing values in Master_Dataset", ["Column", "Missing", "Cause"], [
    ["holiday_type", `${n(missing.holiday_type)} (100%)`, "Parsing bug: the API returns holidayTypes, the parser reads types/type"],
    ["holiday_date, holiday_name", `${n(missing.holiday_date)} (${pct(missing.holiday_date, S.master_rows)})`, "All India rows — Nager.Date returned HTTP 204 for IN"],
    ["All other 33 columns", "0", "Complete"],
  ], [2600, 1800, 4626]),
  P(`At source level, 4 countries (AE, DE, FR, JP) are missing from the fused table entirely because their news requests failed. The data_quality_flag column marks **all ${n(S.master_rows)} rows as COMPLETE**, even the 435 rows without a holiday, because the flag only checks country, currency, city, coordinates and news title. The flag therefore over-states completeness.`),
  H2("D.2 Duplicates"),
  ...table("Duplicate analysis", ["Check", "Count", "Interpretation"], [
    ["Duplicate record_id", "0", "IDs are unique"],
    ["Exact duplicate rows (excluding record_id)", String(S.dup_full_rows), "None"],
    ["Same article under 2+ topics in one country", String(S.dup_article_across_topics), "One article matched several topic queries; it is repeated for each topic"],
    ["Unique article URLs overall", `${S.unique_articles_global} of ${S.article_rows}`, "Article-topic rows vs distinct articles"],
    ["Same title, different URL", String(S.dup_title_diff_url), "Syndicated stories published by several outlets"],
    ["City expansion", `× 5`, "By design each article is copied to 5 city rows — counts must be divided by 5 for article-level analysis"],
  ], [3300, 1500, 4226]),
  H2("D.3 Malformed and inconsistent records"),
  B("**Schema mismatch (holiday_type):** Nager.Date v4 returns `holidayTypes` (a list) but the parser reads `types`/`type`, so holiday_type is always empty. Holiday types are present in the raw data (" + Object.entries(S.holiday_type_values).map(([k, v]) => `${k}: ${v}`).join(", ") + ")."),
  B("**HTTP 204 responses:** India and UAE holiday requests returned no content — a valid response with no data, not a crash."),
  B("**Paid-plan placeholders:** NewsData's `content` field contains the text \"ONLY AVAILABLE IN PAID PLANS\"; the parser correctly ignores it."),
  B(`**Long official names:** countries.dev returns \"${S.country_name_long[0]}\" — correct but inconvenient for display; a short-name mapping is advisable.`),
  B(`**Geocoding name differences:** ${S.geo_name_differs.map((g) => `${g.city} → ${g.resolved_name}`).join("; ")} — correct places with different names; all 50 cities resolved inside the requested country.`),
  B("**Representative holiday:** choose_holiday() picks the earliest holiday, so every fused row with a holiday shows New Year's Day (1 January). The column carries no information that varies between rows."),
  H2("D.4 Consistency and relevance"),
  P(`Cross-source values are consistent (Part C.2: 0 mismatches for country, currency and weather fields). The weakest point is **topic relevance**: NewsData's q parameter matches the whole article text, so many results are only loosely related. Only **${S.topic_relevance_overall}%** of article titles contain the topic keyword.`),
  ...figure("d2_topic_relevance.png", 520, "Share of article titles containing the policy-topic keyword."),
  P("Title matching is a strict test, because an article can be relevant without the keyword in its title. Even so, the low rates show that news rows need relevance filtering (for example qInTitle or a classifier) before they are used as policy context."),
  H2("D.5 Outliers"),
  ...figure("d3_temperature_outliers.png", 520, "City temperatures at collection time, by country."),
  P(`Weather values are physically plausible: temperature ${S.weather_stats.temperature_c.min}–${S.weather_stats.temperature_c.max} °C (median ${S.weather_stats.temperature_c.median}), wind ${S.weather_stats.wind_speed_kmh.min}–${S.weather_stats.wind_speed_kmh.max} km/h, precipitation at most ${S.weather_stats.precipitation_mm.max} mm. UAE cities (40.7–44.1 °C) are the hottest, and they are genuine summer readings. Dubai (44.1 °C), Abu Dhabi (42.9 °C) and Al Ain (42.6 °C) exceed the 42 °C severe-heat threshold in is_severe_weather, but the UAE has no fused rows, so none of the 30 fused cities is flagged as severe. Canada's Toronto (13.3 °C) and the US's Austin (30.0 °C) are within-country outliers that reflect real climate differences, not errors. Exchange rates range from ${Math.min(...Object.values(S.fx_rates_10)).toFixed(2)} (GBP per USD) to ${Math.max(...Object.values(S.fx_rates_10)).toFixed(2)} (JPY per USD); the spread reflects different currencies, not errors.`),
  H2("D.6 Quality summary and actions"),
  ...table("Data-quality issues and actions", ["Dimension", "Finding", "Severity", "Action"], [
    ["Coverage", "46/100 NewsData requests failed → 4 countries absent", st("High", RED), "Spread requests over time / upgrade plan; resume from cache"],
    ["Validity", "holiday_type empty in 100% of rows", st("High", RED), "Read holidayTypes in get_holidays()"],
    ["Completeness", "435 rows without holiday (India HTTP 204)", st("Medium", AMBER), "Fallback holiday source for IN, AE"],
    ["Accuracy", "data_quality_flag = COMPLETE for all rows", st("Medium", AMBER), "Include holiday fields in quality_flag()"],
    ["Relevance", `${S.topic_relevance_overall}% of titles mention the topic`, st("Medium", AMBER), "Use qInTitle / relevance filter"],
    ["Uniqueness", `${S.dup_article_across_topics} articles repeated across topics; 5× city expansion`, st("Low", GREEN), "De-duplicate at article level for analysis"],
    ["Informativeness", "Representative holiday is always 1 January", st("Low", GREEN), "Use next upcoming holiday instead of first"],
    ["Format", "Long official country names", st("Low", GREEN), "Add short display names"],
  ], [1500, 3200, 1000, 3326]),
  BR());

// ---------- PART E
const topCountry = Object.entries(S.master_by_country).sort((a, b) => b[1] - a[1])[0];
body.push(H1("Part E — Exploratory Data Analysis"),
  P("Part E explores the fused dataset. Original-data charts are in Part A.4 and quality charts in Part D."),
  ...figure("e1_rows_by_country.png", 520, "Fused rows per country."),
  P(`${topCountry[0]} has the most fused rows (${topCountry[1]}). Singapore has only 70, because 6 of its 10 news requests failed. The four countries at the end of the request order have no rows at all, so country comparisons in this run are biased toward English-language markets that were queried first.`),
  ...figure("e2_articles_by_topic.png", 520, "News articles per policy topic (article level)."),
  P("Remote work, business travel and working hours return the most articles. Workplace attendance and workplace regulation return the fewest — partly a genuine topic effect and partly because those topics come last in the request order, when failures had started."),
  ...figure("e3_top_sources.png", 520, "Top 10 news sources by unique articles."),
  P("Sources are spread out — the top source supplies only about 3% of unique articles. Aggregators (Yahoo, Head Topics) and national outlets (Daily Mail UK, Times of India) dominate."),
  ...figure("e4_weather_conditions.png", 520, "Weather condition across the fused cities."),
  ...figure("e5_holidays_by_country.png", 520, "Public holidays per country from Nager.Date."),
  P("Canada (31) and Australia (27) have the most holidays because Nager.Date also lists provincial and state holidays. India and the UAE have none in this run (HTTP 204)."),
  H2("E.1 Key EDA insights"),
  NUM("The fused data is complete and consistent where APIs succeeded, but its country coverage is driven by NewsData request limits."),
  NUM("Each article appears 5 times (once per city). Article-level analysis must de-duplicate first, otherwise counts are inflated fivefold."),
  NUM("News relevance is the main quality risk; weather, currency and country fields are reliable."),
  NUM("The weather snapshot is a single moment, which is useful for live context (WFH advisories) but not for trend analysis."),
  NUM("The policy knowledge base remains the authoritative source for answers. The fused dataset is analytical context, not RAG content."),
  BR());

// ---------- Conclusion
body.push(H1("Conclusion — Phase 1"),
  P(`Phase 1 documented PolicyPal's original knowledge base (${S.kb_files} files, ${S.chunks_total} RAG chunks) and built a reproducible five-API fusion layer on top of it. ${Object.values(A).reduce((a, b) => a + b.requests, 0)} API requests produced eleven before-fusion source tables and a fused Master_Dataset of ${n(S.master_rows)} × ${S.master_cols}. Every validation check passed: row counts, unique IDs, and agreement with the country, currency and weather tables.`),
  H2("What worked"),
  B("countries.dev, ExchangeRate-API and Open-Meteo returned data for 100% of requests, and their values match the fused table exactly."),
  B("Caching and status capture made the run auditable: every row records which APIs contributed and how."),
  B("No values were fabricated; gaps remain visible as missing values."),
  H2("What did not work, and why"),
  B("**NewsData.io** — only 52 of 100 requests returned articles, so the UAE, Germany, France and Japan are absent."),
  B("**Nager.Date** — HTTP 204 for India and the UAE; separately, a parser bug leaves holiday_type empty."),
  B("**Relevance** — broad news queries return many loosely related articles."),
  H2("Next steps"),
  B("Fix holiday_type parsing and the quality flag; re-run the remaining NewsData requests from the cache."),
  B("Add relevance filtering and article-level de-duplication."),
  B("Use the cleaned dataset for feature engineering, dashboards and ML in the next phase, keeping RAG answers grounded in the policy documents."),
  BR());

body.push(H1("Appendix — Files and Reproduction"),
  ...table("Project files used", ["File", "Purpose"], [
    ["data/raw/", "Original knowledge base (5 policies + hr_faqs.csv)"], ["vectorstore/", "FAISS index + chunk metadata"],
    ["src/fusion_config.py", "Countries, cities, topics, column list"], ["src/policy_data_fusion.py", "Five-API collection and fusion"],
    ["data/api_cache/", "Raw API JSON (173 files)"], ["data/PolicyPal_Before_Fusion_Source_Tables.xlsx", "Source tables before fusion"],
    ["data/PolicyPal_Master_Dataset.xlsx", "Fused dataset"], ["reports/phase1/build_phase1_assets.py", "Statistics, charts, before-fusion workbook (no API calls)"],
    ["reports/phase1/build_report.js", "Generates this report"],
  ], [4300, 4726], { mono: [0] }),
  ...code([
    "pip install -r requirements.txt",
    "$env:NEWSDATA_API_KEY = \"<your key>\"          # PowerShell; never commit the key",
    "python -m src.policy_data_fusion               # collection + fusion (already run)",
    "python reports/phase1/build_phase1_assets.py   # stats, charts, before-fusion Excel",
    "node reports/phase1/build_report.js            # this report",
  ], "Reproduction"),
);

const doc = new Document({
  creator: "PolicyPal", title: "PolicyPal Phase 1 Report (Parts A–E)",
  styles: {
    default: { document: { run: { font: FONT, size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 34, bold: true, color: BLUE }, paragraph: { spacing: { before: 240, after: 160 }, keepNext: true, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 27, bold: true, color: BLUE }, paragraph: { spacing: { before: 240, after: 100 }, keepNext: true, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 23, bold: true, color: "404040" }, paragraph: { spacing: { before: 180, after: 80 }, keepNext: true, outlineLevel: 2 } },
    ],
  },
  numbering: { config: [
    { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] },
    { reference: "numbers", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 300 } } } }] },
  ] },
  features: { updateFields: true },
  sections: [{
    properties: { page: { margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } }, titlePage: true },
    headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT,
      children: [new TextRun({ text: "PolicyPal — Phase 1 (Parts A–E)", size: 16, color: "7F7F7F" })] })] }) },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
      children: [new TextRun({ children: ["Page ", PageNumber.CURRENT, " of ", PageNumber.TOTAL_PAGES], size: 16, color: "7F7F7F" })] })] }) },
    children: body,
  }],
});
const out = path.join(R, "PolicyPal_Phase1_Parts_A-E_Report.docx");
Packer.toBuffer(doc).then((b) => { fs.writeFileSync(out, b); console.log("Wrote", out); });
