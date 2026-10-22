# U.S. Semiconductor Market Intelligence

**Live dashboard:** [Open the interactive Streamlit dashboard](https://us-semiconductor-market-intelligence-vzkc2ijowqqttrdxoztrhc.streamlit.app/)

An analysis of U.S. trade in semiconductor devices (HS 8541) and integrated circuits (HS 8542), compared with U.S. semiconductor manufacturing output. It covers January 2025 through August 2026.

**Research question:** How did U.S. imports and exports of semiconductors change from Jan–Aug 2025 to Jan–Aug 2026? Which countries were the leading trade partners? How did trade compare with domestic production?

## Key findings

- **Imports grew faster than exports.** Integrated-circuit imports rose **39.1%** ($26.30B → $36.58B) while integrated-circuit exports rose **6.0%** ($35.04B → $37.14B).
- **The trade balance flipped.** Across both product categories, the U.S. went from a **$2.70B surplus** (Jan–Aug 2025) to a **$1.27B deficit** (Jan–Aug 2026). August 2026 had the largest monthly deficit, at $1.21B.
- **Production grew, but imports grew faster.** The average Federal Reserve production index rose **11.3%** (163.4 → 181.9). Imports grew more than that over the same months.
- **Supply is concentrated.** Taiwan supplied about one-third of U.S. integrated-circuit imports in August 2026. The top four partners (Taiwan, Ireland, South Korea and Israel) supplied about two-thirds. China was the largest buyer of U.S. integrated-circuit exports.
- **Integrated circuits make up most of the trade:** about 77% of average monthly imports in the two categories studied.

## What's in this repository

| File | Description |
|---|---|
| `app.py` | Interactive Streamlit + Plotly dashboard. It has month and product filters, KPI cards with month-over-month change, trade trends, the monthly trade balance, a Jan–Aug comparison, the production trend, and the top 10 import and export partners. |
| `US_Semiconductor_Analysis.ipynb` | Jupyter notebook with the data cleaning, validation, statistical summaries and charts |
| `US_Semiconductor_Market_Intelligence_Report.docx` | Written report with a literature review, methods, results and limitations |
| `data/us_semiconductor_trade_2025_2026.csv` | Monthly U.S. Census trade records by partner country and HS code (10,980 rows) |
| `data/us_semiconductor_production_index.csv` | FRED series IPG3344S, the industrial production index for NAICS 3344 (2017 = 100) |
| `requirements.txt` | Python packages for the dashboard |

## Methods

- **Data collection:** I used the U.S. Census International Trade API to retrieve monthly semiconductor trade records (HS 8541 and HS 8542) and downloaded the production index from FRED. I saved the results as CSV files in the `data` folder, so the notebook and dashboard run without direct API access and anyone can reproduce the analysis on the same data.
- **Data cleaning:** The Census files include regional and group totals (for example Asia, ASEAN and CAFTA-DR) plus an all-countries total. Keeping them would double-count trade. I kept only individual-country rows, meaning four-digit country codes that don't start with 0, and only positive trade values. That left 7,061 records.
- **Validation:** I summed the cleaned country rows for each month, product and trade flow, then compared them with Census's official totals. The largest difference was **$0**.
- **Analysis:** I calculated monthly totals, a same-period comparison (Jan–Aug vs. Jan–Aug), surplus and deficit months, partner rankings, and growth indexed to January 2025 = 100.
- **Tools:** Python, pandas, matplotlib, seaborn, Plotly Express and Streamlit.

### Time periods used

- **Year-over-year comparisons** (percent changes, trade balance shift, production change) use **January–August 2025 vs. January–August 2026**, so both periods cover the same 8 months. September–December 2025 are left out of these comparisons because the 2026 data ends in August.
- **Trend charts and summary statistics** use all 20 months (Jan 2025–Aug 2026) to show month-to-month movement.
- **Partner rankings** use the latest month, August 2026.

## Run the dashboard locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Data sources

- U.S. Census Bureau, [International Trade Data](https://www.census.gov/data/developers/data-sets/international-trade.html): monthly imports and exports by partner country and HS code.
- Board of Governors of the Federal Reserve System, [FRED series IPG3344S](https://fred.stlouisfed.org/series/IPG3344S): industrial production for semiconductor and other electronic components.

## Limitations

HS 8541 and HS 8542 don't cover every semiconductor-related product, such as manufacturing equipment or chips inside finished electronics. The production index covers the broader NAICS 3344 industry, not chip output alone. The 20-month window shows recent patterns, not long-term trends, and the comparisons show association, not cause.

---
Victoria Reyna · B.A. Multidisciplinary Studies, Applied Data Science · The University of Texas at San Antonio · [LinkedIn](https://www.linkedin.com/in/victoria-reyna21)
