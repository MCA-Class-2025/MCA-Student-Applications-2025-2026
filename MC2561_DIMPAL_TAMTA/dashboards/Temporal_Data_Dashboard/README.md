<h1>Commodity Market<br>Temporal Analysis</h1>

<p align="center">
  An interactive 7-page Streamlit dashboard that shows <b>how 18 commodity prices have moved since 2000</b>,
  <b>how much was traded</b>, and <b>which markets are the most volatile, seasonal or risky</b>.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/Streamlit-dashboard-ff4b4b" alt="Streamlit">
  <img src="https://img.shields.io/badge/Plotly-interactive%20charts-3f4f75" alt="Plotly">
  <img src="https://img.shields.io/badge/Data-daily%20OHLCV-0b5394" alt="Daily OHLCV data">
</p>

<!-- IMAGE 1 (MAIN IMAGE): full screenshot of page 1 "Dashboard". Save as docs/images/01_dashboard.png -->
<p align="center">
  <img src="docs/images/01_dashboard.png" alt="Dashboard page" width="100%">
</p>

<p align="center"><i>Page 1 – Dashboard: KPIs, price trend, commodity panel, ribbon, waterfall, volume, candlestick and market movers in one screen.</i></p>

---

## Contents

- [What is this project?](#what-is-this-project)
- [Highlights](#highlights)
- [Pages, one by one](#pages-one-by-one)
- [Quick start](#quick-start)
- [How the data is handled](#how-the-data-is-handled)
- [Calculations used](#calculations-used)
- [Themes](#themes)
- [Project structure](#project-structure)
- [Known limitations](#known-limitations)
- [Data source](#data-source)

---

## What is this project?

The dataset holds **116,401 daily records for 18 commodities** (metals, energy and agricultural products) from
**3 January 2000 to 20 November 2026**. Each record has open, high, low, close and volume.

This dashboard turns that raw table into a clear story that anyone can follow:

1. **How** did prices move over time? (trends, comparison, indexed growth)
2. **How much** was traded? (volume, price vs volume)
3. **How risky** is each market? (volatility, drawdown, daily range)
4. **Are there patterns?** (seasonality by month, quarter and weekday)
5. **What can I download?** (filtered CSV, statistics table, Excel export)

## Highlights

- **7 linked pages** with one shared set of filters (commodity, date range, interval, price metric, year, month, quarter).
- **Nothing selected means all data** - the dashboard never looks empty; it shows all 18 commodities and a Market Index.
- **Power BI-style ribbon chart** - stacked columns with ribbons flowing between periods, ordered by value.
- **Waterfall, candlestick and price-volume charts** with clear labels, legends and axis units.
- **Real commodity photos** for the selected commodity (fetched from Wikipedia).
- **8 colour themes** that change the background, card style, font and chart colours.
- **Data quality is visible** - suspicious rows are counted in the Info panel, never silently removed.
- **One-click exports** - filtered CSV from the header, Excel export on the Statistics page.

---

## Pages, one by one

### 1 · Dashboard

The one-page summary of the whole market. It answers *"what is in this dataset?"* in about ten seconds.

| Visual | What it tells you |
|---|---|
| **KPI tiles** | Total records, commodities, date coverage, latest close (or average change when nothing is selected) |
| **Historical Price Trend** | Price line with dots at each data point and the Peak, Low and Latest marked. Several commodities are indexed to 100 |
| **Commodity panel** | Photo, latest close, change over the range, period high and low |
| **Commodity Composition** | Donut showing each commodity's share of records |
| **Performance Ranking** | Ribbon chart: price index (start of range = 100) per period, biggest on top, ribbons show how ranks change |
| **Price Change Analysis** | Waterfall: how each period's change adds up, with Start and End bars and a +/- label on every step |
| **Trading Activity** | Volume bars for the selected commodity (or total volume for every commodity) |
| **Price & Volume Analysis** | Price line drawn over volume bars |
| **OHLC Candlestick** | Body = open to close, thin line = high to low (blue = up, amber = down) |
| **Market Movers** | % change over the range for all commodities |

### 2 · Price Trends

<!-- IMAGE 2: full screenshot of page 2. Save as docs/images/02_price_trends.png -->
<p align="center">
  <img src="docs/images/02_price_trends.png" alt="Price Trends page" width="100%">
</p>

Shows **how the price of one commodity moved**.

- Chart type: **Line, Area, Candlestick or OHLC**, with optional moving averages.
- **Open vs close**, monthly and yearly average price.
- **High-Low band** and 20 / 50 / 200-day rolling trend.

### 3 · Commodity Comparison

<!-- IMAGE 3: full screenshot of page 3. Save as docs/images/03_comparison.png -->
<p align="center">
  <img src="docs/images/03_comparison.png" alt="Commodity Comparison page" width="100%">
</p>

Compares commodities side by side: *which one grew most, and which ones move together?*

- Multi-commodity price chart (log-scale option) and **normalised index** (all start at 100).
- Average price, highest and lowest price, performance ranking.
- **Return correlation heat map.**

### 4 · Trading Volume

<!-- IMAGE 4: full screenshot of page 4. Save as docs/images/04_volume.png -->
<p align="center">
  <img src="docs/images/04_volume.png" alt="Trading Volume page" width="100%">
</p>

Shows **how much was traded**.

- Daily, monthly and yearly volume, and volume by commodity.
- **Price vs volume** scatter, rolling average volume.
- **Unusual-volume days** flagged for a closer look.

### 5 · Volatility & Risk

<!-- IMAGE 5: full screenshot of page 5. Save as docs/images/05_volatility_risk.png -->
<p align="center">
  <img src="docs/images/05_volatility_risk.png" alt="Volatility and Risk page" width="100%">
</p>

Shows **how risky** each market has been.

- Daily returns and **rolling volatility** (window slider, optional annualising).
- **Return histogram** compared with a normal curve.
- **Drawdown**, volatility by commodity, box plot and daily price range.
- Risk numbers such as **VaR** and **maximum drawdown**.

### 6 · Seasonality

<!-- IMAGE 6: full screenshot of page 6. Save as docs/images/06_seasonality.png -->
<p align="center">
  <img src="docs/images/06_seasonality.png" alt="Seasonality page" width="100%">
</p>

Looks for **repeating patterns** through the year.

- Monthly average, quarterly and yearly charts.
- **Year x month heat map** (return or average price).
- **Day-of-week returns** and monthly volume.

### 7 · Statistics & Data

<!-- IMAGE 7: full screenshot of page 7. Save as docs/images/07_statistics.png -->
<p align="center">
  <img src="docs/images/07_statistics.png" alt="Statistics and Data page" width="100%">
</p>

The numbers behind every chart.

- Descriptive statistics, price correlation and box plot.
- **Outliers** (z-score slider) and validation checks with data gaps.
- Searchable table with **CSV and Excel export**.

---

## Quick start

```bash
# 1. get the code
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>

# 2. create a virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 3. install the requirements
pip install -r requirements.txt

# 4. start the dashboard
streamlit run app.py
```

Streamlit opens the dashboard in your browser (normally <http://localhost:8501>).
The data file is already included in `data/`, so no extra download is needed.

**Header controls:** **Theme** (8 themes), **Filters** (date range, year, month, quarter), **Info** (data quality),
**Export** (filtered CSV) and **Reset** (clear all filters).

## How the data is handled

- The raw CSV in `data/` is **never modified**; all cleaning happens in memory.
- 13 repeated date + symbol rows are removed (the last one is kept). Nothing else is deleted.
- **7,417 rows have no volume** (6.4 %). They are shown as **gaps, never as 0**.
- **21 rows have High below Low** and **6,497 rows have Close outside the High-Low range**. They are counted in the
  Info panel and **kept as in the source**.
- **One negative close** exists (WTI crude oil, 19 April 2020, a real negative-price event). It is kept, and the
  daily returns around it are left blank because a % return is undefined across zero or negative prices.
- Returns, rolling windows and drawdowns are calculated **per commodity**, never across commodities.
- Prices are shown **as reported**; units and currency are not stated in the file.

## Calculations used

Implemented with pandas, NumPy and Plotly:

- **Daily return** (% change of close) and **change** per period
- **Indexed price** (each commodity = 100 at the start of the range)
- **Rolling mean and rolling volatility**, optionally annualised
- **Drawdown** and **maximum drawdown**; **Value at Risk (VaR)**
- **Correlation** of returns and of prices
- **Z-score outliers**
- **Resampling** to weekly, monthly, quarterly and yearly OHLCV (open = first, high = max, low = min, close = last, volume = sum)

## Themes

<!-- IMAGE 8: theme 1 (for example Light Navy). Save as docs/images/theme_light_navy.png -->
<p align="center">
  <img src="docs/images/theme_light_navy.png" alt="Light Navy theme" width="100%">
</p>

<!-- IMAGE 9: theme 2 (for example Deep Teal). Save as docs/images/theme_deep_teal.png -->
<p align="center">
  <img src="docs/images/theme_deep_teal.png" alt="Deep Teal theme" width="100%">
</p>

<!-- IMAGE 10: theme 3 (for example Forest Mint). Save as docs/images/theme_forest_mint.png -->
<p align="center">
  <img src="docs/images/theme_forest_mint.png" alt="Forest Mint theme" width="100%">
</p>

Choose a theme from the header (**Theme** button). A theme changes the page background, card style, font and every
chart colour, so the charts always match the background.

| Theme | Style | Font | Accent |
|---|---|---|---|
| **Light Navy** | Light, clean and professional (default) | Inter | Blue |
| **Dark Navy** | Dark blue, high contrast | Inter | Sky blue |
| **Deep Teal** | Dark green-blue, rounded cards | Poppins | Teal |
| **Charcoal Gold** | Dark grey with sharp corners | IBM Plex Sans | Gold |
| **Sunrise Sand** | Light, warm, very rounded cards | Poppins | Orange |
| **Forest Mint** | Light, fresh green | Nunito | Green |
| **Royal Purple** | Dark purple, rounded cards | Montserrat | Violet |
| **Slate Mono** | Light grey, minimal and compact | IBM Plex Sans | Slate |

- Every theme has its own colour set, built so that bars, lines and candles stay clearly visible on that background.
- The up/down candle colours (blue / amber) are different from the waterfall rise/fall colours (green / red), so the two charts are easy to tell apart.
- Filters stay active when you move between pages.

## Project structure

```text
.
├── app.py                      # main dashboard page
├── requirements.txt
├── .streamlit/config.toml
├── pages/                      # the 6 detail pages
├── modules/
│   ├── shell.py                # header, navigation, filters, data filtering
│   ├── data.py                 # loading, derived fields, quality report, resampling
│   ├── charts.py               # main-dashboard charts
│   ├── pagecharts.py           # detail-page charts
│   ├── stats.py                # statistics, outliers, validation, Excel export
│   ├── ui.py                   # CSS and small HTML pieces (KPI cards, titles, panels)
│   ├── theme.py                # the 8 colour themes
│   └── images.py               # commodity photos from Wikipedia
├── data/commodity-prices.csv
└── docs/images/                # screenshots used in this README
```

## Known limitations

- **Units and currency** are not stated in the file, so prices are shown as reported.
- **Volumes are contract-specific** and not comparable across commodities. Compare a commodity with itself over time.
- The **ribbon chart** shows the selected commodities (up to 8), or the top 6 performers when fewer than 2 are
  selected, for the last 6 periods. The **waterfall** shows the last 14 periods.
- The **candlestick** needs one commodity to be selected.
- **Seasonality charts describe history**, not predictable behaviour. Outliers are flagged for a closer look, not treated as errors.
- Photos and theme fonts need an internet connection. Offline, the app shows a placeholder image and a default font.

## Data source

Daily commodity price file `commodity-prices.csv` (open, high, low, close, volume).
The file does not state where it was originally downloaded from; add your source link here.
