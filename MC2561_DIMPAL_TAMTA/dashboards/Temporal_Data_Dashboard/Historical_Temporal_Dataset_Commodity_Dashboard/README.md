# GeoTime Analytics – Commodity Temporal Dashboard (main page)

Power BI-style Streamlit dashboard for `data/commodity-prices.csv`
(18 commodities, 2000-01-03 → 2026-11-20, ~116k daily OHLCV records). Everything is calculated from the file – no data is invented.

## Pages (top navigation bar)
| Page | What it covers |
|---|---|
| **Dashboard** | 4 KPIs · line trend + commodity panel · donut · ribbon · waterfall · volume · price & volume · OHLC candlestick · market movers |
| **Price Trends** | Line / Area / Candlestick / OHLC with moving averages, open-vs-close, monthly & yearly averages, High–Low band, 20/50/200 rolling trend |
| **Comparison** | Multi-commodity prices (log toggle), normalised index, average price, highest/lowest, return correlation heatmap, ranking |
| **Volume** | Daily / monthly / yearly volume, commodity-wise volume, price-vs-volume, rolling average + unusual-volume days |
| **Volatility & Risk** | Daily returns, rolling volatility (window slider, annualise), return histogram vs normal, drawdown, volatility by commodity, box plot, daily range, VaR / max drawdown |
| **Seasonality** | Monthly average, year × month heatmap (return or average), quarterly, yearly, day-of-week return, monthly volume |
| **Statistics & Data** | Descriptive stats, price correlation, price box plot, outliers (|z| slider), validation checks + data gaps, searchable table, CSV and Excel export |

Global slicers (commodity, date range, interval, metric, focus) and the corner buttons (theme · calendar filters Year/Month/Quarter · data-quality notes · CSV download · reset) work on every page.

## Behaviour notes
* Nothing selected at start → placeholder image and empty states (donut, ribbon, movers and the comparison/statistics pages use the whole market).
* One commodity → real photo (Wikipedia, fetched at run time). 2+ commodities → compact list, indexed line chart, and the **Focus commodity** drives single-commodity charts.
* Returns, rolling windows and drawdowns are computed per commodity (never across commodities); rolling windows use full history, then are clipped to the date range.
* Missing volume is a gap, never 0. Suspicious rows are counted (ℹ button and Statistics → Data quality), not silently removed; only repeated (date, symbol) rows are de-duplicated (last kept).
* Daily returns across zero/negative prices (WTI, April 2020) are left blank because a % return is undefined there.
* Outliers are flagged for investigation, not classified as errors. Seasonality charts describe history, not predictable behaviour.

## Run on Windows
```bat
cd GeoTime_Commodity_Dashboard
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```
Internet is only needed for the commodity photos; without it a placeholder is shown.

## Structure
```
app.py                 main dashboard
pages/1…6_*.py         the six detail pages
modules/shell.py       header, navigation, slicers, calendar filters, filtering
modules/data.py        load, derived fields, quality report, resampling, summaries
modules/charts.py      main-dashboard figures
modules/pagecharts.py  detail-page figures
modules/stats.py       statistics, outliers, validation, gaps, Excel export
modules/ui.py · images.py · theme.py
data/commodity-prices.csv
```
