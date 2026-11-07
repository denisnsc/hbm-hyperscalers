# HBM & Hyperscalers Portfolio Terminal — Design & Architecture Decisions

Brief reference log of all product, data, and UI decisions for future sessions.

## 1. Architecture & Delivery
- **Self-Contained Static HTML + Python Refresh Pipeline**:
  - `portfolio_config.json`: Persistent, editable configuration of tracked companies and segments.
  - `fetch_portfolio_data.py`: Fetches live & 5-year historical data from Yahoo Finance (`yfinance >= 1.8.0`), saves to `portfolio_data.json`.
  - `build_dashboard.py`: Injects `portfolio_data.json` into the self-contained HTML template and writes `dashboard.html` and `index.html`.
  - `update_dashboard.py`: One-command updater (`python update_dashboard.py`) and CLI tool to add tickers (`--add TICKER ...`).
  - **All scripts live in the project root** (`d:\Antigravity\HBM & Hyperscalers\`), never in `scratch/`.
- **GitHub Pages & Sharing**:
  - Generates `index.html` with OpenGraph meta tags for rich Telegram link previews.
  - `.github/workflows/update_pages.yml`: Automated weekday refresh after US market close (`22:15 UTC`).
  - `deploy_github_pages.py`: GitHub REST API uploader (no local `git` installation required).

## 2. Portfolio Universe & Categorization
- **Market Cap Filter**: Strictly include only companies with **Market Cap $\ge$ \$150B USD** (`min_market_cap_usd_bn: 150`). Smaller holdings (`MRVL`, `VRT`, `SMCI`, `CAMT`, `ONTO`, `AMKR`, `CRWV`) were removed.
- **Core Screenshot Holdings (`is_core: true`, marked with gold star `★`)**:
  - `000660.KS` (SK Hynix), `005930.KS` (Samsung Electronics), `MU` (Micron), `ORCL`, `AVGO`, `META`, `GOOGL`, `NVDA`, `AMZN`, `MSFT`.
- **Extended Peers (`is_core: false`, $\ge$ \$150B)**:
  - `TSM`, `AMD`, `INTC`, `ARM`, `ASML`, `ANET`, `DELL`, `LRCX`, `AAPL`, `BABA`.
- **3 Filterable Sectors**:
  1. `HBM Memory` (Teal `#00bfa5`)
  2. `Hyperscalers` (Royal Blue `#1e88e5`)
  3. `AI Semis & Infra` (Vibrant Orange `#fb8c00`)

## 3. Data & Metric Definitions
- **Currency & Price Basis**:
  - Use **daily closing prices** converted into **USD** via historical daily FX series (`KRW=X`, `TWD=X`, `EUR=X`, `CNY=X`) before calculating returns and drawdowns.
  - Display USD price alongside native currency price (`₩` for Korean tickers).
- **Peak Drawdown**:
  - Primary drawdown metric is **Loss Since 52-Week Peak (%)** using USD-adjusted daily closing prices (`drawdown_52w_pct`), with **Loss Since 5-Year Peak (%)** (`drawdown_5y_pct`) also available.
- **Valuation Multiples**:
  - `Trailing P/E` (computed as `marketCap / netIncomeToCommon` when Yahoo omits `trailingPE` on KRX stocks; negative P/E stocks placed at bottom when ranking by P/E), `Forward P/E`, `Current Year P/E`, `PEG Ratio`, and `Market Cap ($B)`.
- **Horizon Returns**:
  - `YTD`, `1Y`, `2Y`, `3Y`, and `5Y` USD total price returns.
- **Time-Series Granularity**:
  - **Last 1 Year**: Daily (`1D`) trading closes (~252 points).
  - **Years 2–5**: Weekly (`1W-FRI`) closes.

## 4. UI / UX & Visual Design
- **Visual Style**:
  - Inspired by **Google Finance & Yahoo Finance** with vibrant, high-contrast financial colors (no "Claudism" purple-gradient clichés or emoji clutter).
  - **Light Mode is the default** (`data-theme="light"`), with a `☀ Light` / `☾ Dark` switch in the top header.
  - Explicit, 100% opaque CSS surface variables (`--bg-elevated`, `--bg-surface`) so standalone Chrome rendering has solid backgrounds on all pop-ups, tooltips, and modals.
- **Decluttered Header**:
  - Removed the top holdings quote ribbon and quick-ranking button row to keep the top area clean.
- **View Modes**:
  - `Overview (3 Views)`: Shows Ranked Bars + Valuation Scatter Matrix + Full Heatmap Table (excludes the large Interactive Chart to keep the overview lightweight).
  - Single-view tabs (`Ranked Bars`, `Scatter Matrix`, `Full Table`, `Interactive Chart`) render only the selected view at full width.
- **Interactive Time-Series Charts (Main Tab & Holding Card Modal)**:
  - Google Finance-style hover crosshair scrubbing across dates (`1M`, `3M`, `6M`, `YTD`, `1Y`, `2Y`, `3Y`, `5Y`).
  - Supports all Ranked Bar metrics (`% Change`, `Share Price`, `Market Cap`, `Trailing P/E`, `Forward P/E`, `Current Year P/E`, `PEG`, `52W Peak Loss`, `5Y Peak Loss`, `YTD`/`1Y`/`2Y`/`3Y`/`5Y` returns) and multi-holding comparison on the same graph.
- **Holding Card Modal**:
  - Direct external buttons for **Google Finance ↗** and **Yahoo Finance ↗**.
  - **Earnings & FCF Bar Chart**: Quarterly & Annual **Revenue (\$B)**, **Net Income (\$B)**, and **Free Cash Flow (\$B)** bars. Annual bars include **2026 TTM** (Trailing 12 Months) for calendar-year companies whose FY2026 hasn't closed yet.
  - **Capital Return & Dilution Bar Chart**: Switchable between:
    1. **Buybacks + Divs (\$B)** (Combined side-by-side Purple Buybacks & Green Dividends on the same graph, hiding `$0.0B` zero labels so zero-dividend years never clutter the baseline)
    2. **Dilution (YoY % change in diluted shares)** (Green `<0%` net share count reduction vs. Red `>0%` net dilution, including `FY2022` through `2026 YTD`)
    3. **Div / Share (\$)** (Annual dividend rate `$/sh`, Yield %, and Payout Ratio %)
