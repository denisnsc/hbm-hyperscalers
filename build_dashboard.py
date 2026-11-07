"""
Generates the self-contained interactive HTML visualization from portfolio_data.json.
Features:
  - Fixed View Switcher (All Views excludes Interactive Chart; Ranked Bars & Scatter Matrix show single view)
  - Daily (1D) granularity for the last 1 year, Weekly (1W) for years 2-5
  - Unified metrics across Ranked Bars and Interactive Graphs (including Market Cap)
  - Holding Card includes Earnings (Quarterly/Annual Revenue & Net Income bars),
    Dividends (Annual/Recent bars + Yield/Rate), and direct links to Google Finance & Yahoo Finance
  - Gold star (★) marking all holdings from the user's screenshot
"""

import json
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
DATA_PATH = PROJECT_DIR / "portfolio_data.json"
LOCAL_HTML_PATH = PROJECT_DIR / "dashboard.html"
INDEX_HTML_PATH = PROJECT_DIR / "index.html"

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>HBM & Hyperscalers — Market Valuation & Performance Terminal</title>
  <meta property="og:title" content="HBM & Hyperscalers — Market Valuation & Performance Terminal" />
  <meta property="og:description" content="Interactive portfolio visualization of HBM Memory, Hyperscalers & AI Infrastructure leaders (Mkt Cap >= $150B): P/E, Forward P/E, 52W Peak Drawdown, and YTD to 5Y USD Returns." />
  <meta property="og:type" content="website" />
  <meta name="twitter:card" content="summary_large_image" />
  <script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
  <style>
    /* ==========================================================================
       GOOGLE FINANCE & YAHOO FINANCE INSPIRED THEME SYSTEM (LIGHT DEFAULT)
       100% solid opaque surfaces for Chrome pop-ups, tooltips, and modals
       ========================================================================== */
    html[data-theme="light"] {
      --bg-canvas: #f3f6fa;
      --bg-surface: #ffffff;
      --bg-elevated: #ffffff;
      --bg-subtle: #edf2f7;
      --bg-hover: #f1f5f9;
      --border-color: #dde3ec;
      --border-strong: #c4cddb;
      --text-main: #0f172a;
      --text-secondary: #475569;
      --text-muted: #64748b;
      --accent-blue: #1a73e8;
      --accent-blue-bg: #e8f0fe;
      --accent-blue-border: #aecbfa;
      --gain-fg: #087f5b;
      --gain-bg: #e3fcef;
      --gain-bar: #0ca678;
      --loss-fg: #c92a2a;
      --loss-bg: #ffe3e3;
      --loss-bar: #f03e3e;
      --star-gold: #f59f00;
      /* Vibrant Segment Accents */
      --seg-hbm-fg: #00796b;
      --seg-hbm-bg: #e0f2f1;
      --seg-hbm-bar: #00bfa5;
      --seg-hyp-fg: #1565c0;
      --seg-hyp-bg: #e3f2fd;
      --seg-hyp-bar: #1e88e5;
      --seg-semi-fg: #e65100;
      --seg-semi-bg: #fff3e0;
      --seg-semi-bar: #fb8c00;
      --shadow-card: 0 1px 3px rgba(15, 23, 42, 0.06), 0 1px 2px rgba(15, 23, 42, 0.04);
      --shadow-popup: 0 20px 38px -6px rgba(15, 23, 42, 0.22), 0 8px 16px -4px rgba(15, 23, 42, 0.12);
      --modal-backdrop: rgba(15, 23, 42, 0.55);
      --grid-line: #e2e8f0;
    }

    html[data-theme="dark"] {
      --bg-canvas: #0a0e17;
      --bg-surface: #121824;
      --bg-elevated: #1a2234;
      --bg-subtle: #182030;
      --bg-hover: #1e293b;
      --border-color: #243044;
      --border-strong: #334155;
      --text-main: #f8fafc;
      --text-secondary: #cbd5e1;
      --text-muted: #94a3b8;
      --accent-blue: #38bdf8;
      --accent-blue-bg: rgba(56, 189, 248, 0.15);
      --accent-blue-border: rgba(56, 189, 248, 0.45);
      --gain-fg: #2dd4bf;
      --gain-bg: rgba(20, 184, 166, 0.16);
      --gain-bar: #10b981;
      --loss-fg: #fb7185;
      --loss-bg: rgba(244, 63, 94, 0.18);
      --loss-bar: #f43f5e;
      --star-gold: #fcc419;
      /* Vibrant Segment Accents */
      --seg-hbm-fg: #2dd4bf;
      --seg-hbm-bg: rgba(45, 212, 191, 0.14);
      --seg-hbm-bar: #14b8a6;
      --seg-hyp-fg: #60a5fa;
      --seg-hyp-bg: rgba(96, 165, 250, 0.15);
      --seg-hyp-bar: #3b82f6;
      --seg-semi-fg: #fb923c;
      --seg-semi-bg: rgba(251, 146, 60, 0.15);
      --seg-semi-bar: #f97316;
      --shadow-card: 0 2px 6px rgba(0, 0, 0, 0.35);
      --shadow-popup: 0 24px 48px -8px rgba(0, 0, 0, 0.7), 0 0 0 1px rgba(255, 255, 255, 0.08);
      --modal-backdrop: rgba(2, 6, 23, 0.78);
      --grid-line: #1e293b;
    }

    * { box-sizing: border-box; }
    body {
      margin: 0;
      background-color: var(--bg-canvas);
      color: var(--text-main);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      font-size: 13px;
      line-height: 1.45;
      transition: background-color 0.15s ease, color 0.15s ease;
    }

    .tabular-nums { font-variant-numeric: tabular-nums; }
    .core-star {
      color: var(--star-gold);
      font-size: 13px;
      line-height: 1;
      display: inline-block;
    }

    /* Surfaces & Cards */
    .gf-card {
      background-color: var(--bg-surface);
      border: 1px solid var(--border-color);
      border-radius: 10px;
      box-shadow: var(--shadow-card);
    }

    /* Pills & Buttons */
    .gf-pill {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      padding: 5px 11px;
      border-radius: 9999px;
      font-size: 12px;
      font-weight: 600;
      background-color: var(--bg-surface);
      color: var(--text-secondary);
      border: 1px solid var(--border-color);
      cursor: pointer;
      text-decoration: none;
      transition: all 0.12s ease;
      white-space: nowrap;
    }
    .gf-pill:hover {
      border-color: var(--accent-blue);
      color: var(--accent-blue);
    }
    .gf-pill.active {
      background-color: var(--accent-blue-bg);
      color: var(--accent-blue);
      border-color: var(--accent-blue-border);
    }

    /* Segmented Control */
    .gf-seg-group {
      display: inline-flex;
      background-color: var(--bg-subtle);
      border: 1px solid var(--border-color);
      border-radius: 8px;
      padding: 2px;
      gap: 2px;
    }
    .gf-seg-btn {
      padding: 5px 11px;
      border-radius: 6px;
      font-size: 12px;
      font-weight: 600;
      color: var(--text-secondary);
      background: transparent;
      border: none;
      cursor: pointer;
      transition: all 0.12s ease;
      white-space: nowrap;
    }
    .gf-seg-btn:hover { color: var(--text-main); }
    .gf-seg-btn.active {
      background-color: var(--bg-surface);
      color: var(--accent-blue);
      box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08);
    }

    /* Segment Badges */
    .badge-hbm {
      background-color: var(--seg-hbm-bg);
      color: var(--seg-hbm-fg);
      padding: 2px 8px;
      border-radius: 4px;
      font-weight: 600;
      font-size: 12px;
    }
    .badge-hyp {
      background-color: var(--seg-hyp-bg);
      color: var(--seg-hyp-fg);
      padding: 2px 8px;
      border-radius: 4px;
      font-weight: 600;
      font-size: 12px;
    }
    .badge-semi {
      background-color: var(--seg-semi-bg);
      color: var(--seg-semi-fg);
      padding: 2px 8px;
      border-radius: 4px;
      font-weight: 600;
      font-size: 12px;
    }

    /* Return Pills */
    .ret-pill-pos {
      display: inline-block;
      padding: 2px 7px;
      border-radius: 5px;
      background-color: var(--gain-bg);
      color: var(--gain-fg);
      font-weight: 600;
    }
    .ret-pill-neg {
      display: inline-block;
      padding: 2px 7px;
      border-radius: 5px;
      background-color: var(--loss-bg);
      color: var(--loss-fg);
      font-weight: 600;
    }

    /* Inputs & Selects */
    .gf-input, .gf-select {
      background-color: var(--bg-surface);
      color: var(--text-main);
      border: 1px solid var(--border-color);
      border-radius: 7px;
      padding: 6px 10px;
      font-size: 12px;
      font-weight: 600;
      outline: none;
    }
    .gf-input:focus, .gf-select:focus {
      border-color: var(--accent-blue);
    }

    /* Table */
    .gf-table {
      width: 100%;
      border-collapse: collapse;
    }
    .gf-table th {
      padding: 10px 8px;
      font-size: 12px;
      font-weight: 600;
      color: var(--text-muted);
      border-bottom: 2px solid var(--border-color);
      cursor: pointer;
      user-select: none;
      white-space: nowrap;
    }
    .gf-table th:hover { color: var(--accent-blue); }
    .gf-table td {
      padding: 10px 8px;
      border-bottom: 1px solid var(--border-color);
      font-size: 12px;
    }
    .gf-row {
      cursor: pointer;
      transition: background-color 0.1s ease;
    }
    .gf-row:hover {
      background-color: var(--bg-hover);
    }

    .bar-fill {
      transition: width 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    }

    /* Opaque Popups (Tooltips & Detail Modal) */
    .gf-tooltip {
      position: absolute;
      pointer-events: none;
      z-index: 40;
      background-color: var(--bg-elevated) !important;
      color: var(--text-main) !important;
      border: 1px solid var(--border-strong);
      border-radius: 10px;
      box-shadow: var(--shadow-popup);
      padding: 12px;
      width: 265px;
    }

    .gf-modal-backdrop {
      position: fixed;
      inset: 0;
      z-index: 100;
      background-color: var(--modal-backdrop);
      backdrop-filter: blur(3px);
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 16px;
    }
    .gf-modal-box {
      background-color: var(--bg-elevated) !important;
      color: var(--text-main) !important;
      border: 1px solid var(--border-strong);
      border-radius: 12px;
      box-shadow: var(--shadow-popup);
      max-width: 1020px;
      width: 100%;
      max-height: 92vh;
      overflow-y: auto;
      padding: 22px;
    }
    .hidden { display: none !important; }

    ::-webkit-scrollbar { width: 7px; height: 7px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: var(--border-strong); border-radius: 4px; }
  </style>
</head>
<body>

  <!-- Top Navigation Header -->
  <header style="background-color: var(--bg-surface); border-bottom: 1px solid var(--border-color);">
    <div class="max-w-[1600px] mx-auto px-4 md:px-6 py-3.5">
      <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
        <div class="flex items-center gap-3">
          <div style="width: 10px; height: 28px; border-radius: 3px; background: linear-gradient(180deg, #1a73e8 0%, #00bfa5 100%);"></div>
          <div>
            <div class="flex flex-wrap items-center gap-2.5">
              <span class="text-lg md:text-xl font-bold tracking-tight" style="color: var(--text-main);">
                HBM &amp; Hyperscalers Market Terminal
              </span>
              <span class="px-2 py-0.5 rounded text-xs font-semibold" style="background-color: var(--accent-blue-bg); color: var(--accent-blue);">
                Mkt Cap &ge; $150B · USD Daily Closes
              </span>
            </div>
            <p class="text-xs mt-0.5" style="color: var(--text-muted);">
              Real-time Yahoo Finance valuation multiples, 52-week peak drawdown, and interactive multi-holding comparison (<span class="core-star">★</span> = Screenshot Holding)
            </p>
          </div>
        </div>

        <!-- Right Controls: As-Of Date + Light/Dark Switch -->
        <div class="flex flex-wrap items-center gap-2.5">
          <div class="px-3 py-1.5 rounded-lg text-xs" style="background-color: var(--bg-subtle); border: 1px solid var(--border-color); color: var(--text-secondary);">
            Market Close: <strong class="tabular-nums" style="color: var(--text-main);" id="as-of-label">—</strong>
          </div>

          <div class="gf-seg-group" role="group" aria-label="Theme Switcher">
            <button onclick="setTheme('light')" id="theme-btn-light" class="gf-seg-btn active">
              ☀ Light
            </button>
            <button onclick="setTheme('dark')" id="theme-btn-dark" class="gf-seg-btn">
              ☾ Dark
            </button>
          </div>
        </div>
      </div>
    </div>
  </header>

  <!-- Main Content Container -->
  <main class="max-w-[1600px] mx-auto px-4 md:px-6 py-5 space-y-5">

    <!-- Filter Bar -->
    <div class="gf-card p-3.5">
      <div class="flex flex-col xl:flex-row xl:items-center justify-between gap-3">
        <div class="flex flex-wrap items-center gap-2.5">
          <!-- Universe Scope -->
          <div class="gf-seg-group">
            <button onclick="setScope('all')" id="scope-all" class="gf-seg-btn active">
              All Holdings &ge;$150B (<span id="count-all">20</span>)
            </button>
            <button onclick="setScope('core')" id="scope-core" class="gf-seg-btn">
              <span class="core-star">★</span> Screenshot Holdings (<span id="count-core">10</span>)
            </button>
          </div>

          <!-- Segment Filter -->
          <div class="gf-seg-group">
            <button onclick="setSegment('ALL')" id="seg-ALL" class="gf-seg-btn active">All Sectors</button>
            <button onclick="setSegment('HBM Memory')" id="seg-HBM Memory" class="gf-seg-btn">HBM Memory</button>
            <button onclick="setSegment('Hyperscalers')" id="seg-Hyperscalers" class="gf-seg-btn">Hyperscalers</button>
            <button onclick="setSegment('AI Semis & Infra')" id="seg-AI Semis & Infra" class="gf-seg-btn">AI Semis &amp; Infra</button>
          </div>
        </div>

        <div class="flex flex-wrap items-center gap-2.5">
          <!-- Layout View Switcher (All Views excludes Interactive Chart so it stays fast and clean) -->
          <div class="gf-seg-group">
            <button onclick="setViewMode('all')" id="view-all" class="gf-seg-btn active">Overview (3 Views)</button>
            <button onclick="setViewMode('bars')" id="view-bars" class="gf-seg-btn">Ranked Bars</button>
            <button onclick="setViewMode('scatter')" id="view-scatter" class="gf-seg-btn">Scatter Matrix</button>
            <button onclick="setViewMode('table')" id="view-table" class="gf-seg-btn">Full Table</button>
            <button onclick="setViewMode('compare')" id="view-compare" class="gf-seg-btn">Interactive Chart</button>
          </div>

          <input
            type="text"
            id="search-input"
            oninput="onSearchInput(this.value)"
            placeholder="Search symbol or company..."
            class="gf-input w-48"
          />
        </div>
      </div>
    </div>

    <!-- Summary Benchmark Cards -->
    <div class="grid grid-cols-2 lg:grid-cols-5 gap-3" id="kpi-strip"></div>

    <!-- DEDICATED INTERACTIVE MULTI-HOLDING TIME-SERIES CHART (Shown when 'Interactive Chart' tab is selected) -->
    <div id="panel-compare" class="gf-card p-5 space-y-4 hidden">
      <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-3 pb-3" style="border-bottom: 1px solid var(--border-color);">
        <div>
          <div class="flex flex-wrap items-center gap-2.5">
            <h2 class="text-base font-bold" style="color: var(--text-main);">
              Interactive Historical Comparison Chart
            </h2>
            <span id="ts-hover-date" class="px-2 py-0.5 rounded text-xs font-bold tabular-nums" style="background-color: var(--bg-subtle); color: var(--text-secondary);">
              Daily granularity (1Y) · Hover over chart to inspect dates
            </span>
          </div>
          <p class="text-xs mt-0.5" style="color: var(--text-muted);">
            Switch across any valuation, market cap, peak drawdown, or return metric and overlay multiple holdings
          </p>
        </div>

        <!-- Metric Dropdown (All Ranked Bar Metrics + Market Cap + % Change) & Time Range Controls -->
        <div class="flex flex-wrap items-center gap-2.5">
          <div class="flex items-center gap-1.5">
            <span class="text-xs font-bold" style="color: var(--text-secondary);">Metric:</span>
            <select id="ts-metric-select" onchange="setTsMetric(this.value)" class="gf-select">
              <optgroup label="Relative &amp; Price">
                <option value="pct_window" selected>% Change (Selected Timeframe)</option>
                <option value="price_usd">Share Price (USD $)</option>
                <option value="market_cap_usd_bn">Market Cap ($B)</option>
              </optgroup>
              <optgroup label="Valuation Ratios">
                <option value="trailing_pe">Trailing P/E (TTM)</option>
                <option value="forward_pe">Forward P/E (Est)</option>
                <option value="current_yr_pe">Current Year P/E</option>
                <option value="peg_ratio">PEG Ratio</option>
              </optgroup>
              <optgroup label="Loss From Peak (USD Close)">
                <option value="drawdown_52w_pct">Loss Since 52-Week Peak (%)</option>
                <option value="drawdown_5y_pct">Loss Since 5-Year Peak (%)</option>
              </optgroup>
              <optgroup label="Horizon Gains / Losses (USD)">
                <option value="return_ytd">YTD Gain / Loss (%)</option>
                <option value="return_1y">1-Year Gain / Loss (%)</option>
                <option value="return_2y">2-Year Gain / Loss (%)</option>
                <option value="return_3y">3-Year Gain / Loss (%)</option>
                <option value="return_5y">5-Year Gain / Loss (%)</option>
              </optgroup>
            </select>
          </div>

          <!-- Horizon Selector (1M to 5Y) -->
          <div class="gf-seg-group">
            <button onclick="setTsRange('1M')" id="tsr-1M" class="gf-seg-btn">1M</button>
            <button onclick="setTsRange('3M')" id="tsr-3M" class="gf-seg-btn">3M</button>
            <button onclick="setTsRange('6M')" id="tsr-6M" class="gf-seg-btn">6M</button>
            <button onclick="setTsRange('YTD')" id="tsr-YTD" class="gf-seg-btn">YTD</button>
            <button onclick="setTsRange('1Y')" id="tsr-1Y" class="gf-seg-btn active">1Y</button>
            <button onclick="setTsRange('2Y')" id="tsr-2Y" class="gf-seg-btn">2Y</button>
            <button onclick="setTsRange('3Y')" id="tsr-3Y" class="gf-seg-btn">3Y</button>
            <button onclick="setTsRange('5Y')" id="tsr-5Y" class="gf-seg-btn">5Y</button>
          </div>
        </div>
      </div>

      <!-- Live Legend / Readout Bar for Selected Holdings -->
      <div id="ts-legend-bar" class="flex flex-wrap items-center gap-2.5 text-xs tabular-nums min-h-[28px]"></div>

      <!-- Interactive SVG Chart Area -->
      <div class="relative w-full select-none" id="ts-chart-wrapper">
        <svg id="ts-chart-svg" viewBox="0 0 1120 370" class="w-full h-auto overflow-visible cursor-crosshair"
             onmousemove="onTsChartMouseMove(event)"
             onmouseleave="onTsChartMouseLeave()"></svg>
        <div id="ts-floating-tooltip" class="gf-tooltip hidden"></div>
      </div>

      <!-- Compare Holdings Selector Bar -->
      <div class="pt-3 space-y-2.5" style="border-top: 1px solid var(--border-color);">
        <div class="flex flex-wrap items-center justify-between gap-2">
          <div class="flex flex-wrap items-center gap-1.5 text-xs">
            <span class="font-bold mr-1" style="color: var(--text-secondary);">Compare Presets:</span>
            <button onclick="setCompareGroup(['000660.KS','005930.KS','MU'])" class="gf-pill">HBM Memory Trio (SK Hynix, Samsung, Micron)</button>
            <button onclick="setCompareGroup(['MSFT','AMZN','GOOGL','META','ORCL'])" class="gf-pill">Hyperscalers (MSFT, AMZN, GOOGL, META, ORCL)</button>
            <button onclick="setCompareGroup(['NVDA','AVGO','AMD','TSM','INTC'])" class="gf-pill">AI Chips (NVDA, AVGO, AMD, TSM, INTC)</button>
            <button onclick="setCompareGroup(['000660.KS','MU','NVDA','AVGO','GOOGL'])" class="gf-pill">Top 5 Core Leaders</button>
          </div>
          <span class="text-xs" style="color: var(--text-muted);">Click any ticker below to add/remove from graph (max 8):</span>
        </div>

        <div id="compare-chips-container" class="flex flex-wrap items-center gap-1.5"></div>
      </div>
    </div>

    <!-- Charts Grid: Ranked Bar Chart + Valuation vs Performance Scatter -->
    <div id="charts-grid" class="grid grid-cols-1 xl:grid-cols-12 gap-5">

      <!-- Left Panel: Dynamic Ranked Bar Chart -->
      <div id="panel-bars" class="xl:col-span-7 gf-card p-5 flex flex-col">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3" style="border-bottom: 1px solid var(--border-color);">
          <div>
            <div class="flex items-center gap-2">
              <h2 class="text-base font-bold" style="color: var(--text-main);">Holdings Ranking</h2>
              <span id="active-metric-badge" class="px-2.5 py-0.5 text-xs font-bold rounded" style="background-color: var(--accent-blue-bg); color: var(--accent-blue);">
                Forward P/E
              </span>
            </div>
            <p class="text-xs mt-0.5" style="color: var(--text-muted);">
              Click any holding to open its card with interactive chart, earnings &amp; dividend bars (<span class="core-star">★</span> = Screenshot Holding)
            </p>
          </div>

          <div class="flex items-center gap-2">
            <select id="metric-select" onchange="setMetric(this.value)" class="gf-select">
              <optgroup label="Valuation Ratios">
                <option value="trailing_pe">Trailing P/E (TTM)</option>
                <option value="forward_pe" selected>Forward P/E (Est)</option>
                <option value="current_yr_pe">Current Year P/E</option>
                <option value="peg_ratio">PEG Ratio</option>
              </optgroup>
              <optgroup label="Market Size &amp; Price">
                <option value="market_cap_usd_bn">Market Cap ($B)</option>
                <option value="price_usd">Share Price (USD $)</option>
              </optgroup>
              <optgroup label="Loss From Peak (USD Close)">
                <option value="drawdown_52w_pct">Loss Since 52-Week Peak (%)</option>
                <option value="drawdown_5y_pct">Loss Since 5-Year Peak (%)</option>
              </optgroup>
              <optgroup label="Horizon Gains / Losses (USD)">
                <option value="return_ytd">YTD Return (%)</option>
                <option value="return_1y">1-Year Return (%)</option>
                <option value="return_2y">2-Year Return (%)</option>
                <option value="return_3y">3-Year Return (%)</option>
                <option value="return_5y">5-Year Return (%)</option>
              </optgroup>
            </select>
            <button onclick="toggleSortDir()" id="sort-dir-btn" class="gf-pill">
              ↑ Low to High
            </button>
          </div>
        </div>

        <div id="ranked-bars-container" class="mt-3 space-y-1.5 max-h-[540px] overflow-y-auto pr-1"></div>
      </div>

      <!-- Right Panel: Valuation vs Drawdown/Return Scatter Plot -->
      <div id="panel-scatter" class="xl:col-span-5 gf-card p-5 flex flex-col justify-between">
        <div>
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3" style="border-bottom: 1px solid var(--border-color);">
            <div>
              <h2 class="text-base font-bold" style="color: var(--text-main);">Valuation vs. Return / Drawdown</h2>
              <p class="text-xs mt-0.5" style="color: var(--text-muted);">Dashed lines show cohort median · click any point to open holding card</p>
            </div>
            <div class="flex flex-wrap items-center gap-1.5 text-xs">
              <span style="color: var(--text-muted); font-weight: 600;">X:</span>
              <select id="scatter-x" onchange="renderScatter()" class="gf-select">
                <option value="forward_pe" selected>Forward P/E</option>
                <option value="trailing_pe">Trailing P/E</option>
                <option value="market_cap_usd_bn">Market Cap ($B)</option>
                <option value="drawdown_52w_pct">52W Peak Loss %</option>
                <option value="return_ytd">YTD Return %</option>
              </select>
              <span style="color: var(--text-muted); font-weight: 600;">Y:</span>
              <select id="scatter-y" onchange="renderScatter()" class="gf-select">
                <option value="drawdown_52w_pct" selected>52W Peak Loss %</option>
                <option value="return_ytd">YTD Return %</option>
                <option value="return_1y">1Y Return %</option>
                <option value="return_3y">3Y Return %</option>
                <option value="return_5y">5Y Return %</option>
                <option value="forward_pe">Forward P/E</option>
              </select>
            </div>
          </div>

          <div class="relative mt-3 w-full" id="scatter-wrapper">
            <svg id="scatter-svg" viewBox="0 0 560 420" class="w-full h-auto overflow-visible select-none"></svg>
            <div id="scatter-tooltip" class="gf-tooltip hidden"></div>
          </div>
        </div>

        <div class="mt-3 pt-3 flex flex-wrap items-center justify-between gap-2 text-xs" style="border-top: 1px solid var(--border-color); color: var(--text-secondary);">
          <div class="flex items-center gap-3 font-medium">
            <span class="inline-flex items-center gap-1.5"><span style="width:10px;height:10px;border-radius:50%;background:var(--seg-hbm-bar);display:inline-block;"></span>HBM Memory</span>
            <span class="inline-flex items-center gap-1.5"><span style="width:10px;height:10px;border-radius:50%;background:var(--seg-hyp-bar);display:inline-block;"></span>Hyperscalers</span>
            <span class="inline-flex items-center gap-1.5"><span style="width:10px;height:10px;border-radius:50%;background:var(--seg-semi-bar);display:inline-block;"></span>AI Semis &amp; Infra</span>
          </div>
          <span style="color: var(--text-muted);"><span class="core-star">★</span> = Screenshot Holding</span>
        </div>
      </div>

    </div>

    <!-- Bottom Panel: Full Financial Comparison Table -->
    <div id="panel-table" class="gf-card p-5">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3" style="border-bottom: 1px solid var(--border-color);">
        <div>
          <h2 class="text-base font-bold" style="color: var(--text-main);">
            Multi-Horizon Valuation &amp; Return Screener
          </h2>
          <p class="text-xs mt-0.5" style="color: var(--text-muted);">
            Click any column header to sort. Click any row to open the holding card with interactive graph, earnings &amp; dividends.
          </p>
        </div>
        <div class="flex items-center gap-2 text-xs">
          <label class="inline-flex items-center gap-1.5 cursor-pointer font-medium" style="color: var(--text-secondary);">
            <input type="checkbox" id="positive-pe-only" onchange="togglePositivePeOnly(this.checked)" checked />
            <span>Keep negative P/E (unprofitable TTM) at bottom when ranking by P/E</span>
          </label>
        </div>
      </div>

      <div class="overflow-x-auto mt-2">
        <table class="gf-table tabular-nums">
          <thead>
            <tr>
              <th class="text-left w-10">#</th>
              <th class="text-left" onclick="sortTableBy('display_symbol')">Symbol / Company <span id="sort-ind-display_symbol"></span></th>
              <th class="text-left" onclick="sortTableBy('segment')">Sector <span id="sort-ind-segment"></span></th>
              <th class="text-right" onclick="sortTableBy('price_usd')">Last Price <span id="sort-ind-price_usd"></span></th>
              <th class="text-right" onclick="sortTableBy('market_cap_usd_bn')">Mkt Cap <span id="sort-ind-market_cap_usd_bn"></span></th>
              <th class="text-right" onclick="sortTableBy('trailing_pe')">P/E (TTM) <span id="sort-ind-trailing_pe"></span></th>
              <th class="text-right" onclick="sortTableBy('forward_pe')">Fwd P/E <span id="sort-ind-forward_pe"></span></th>
              <th class="text-right" onclick="sortTableBy('drawdown_52w_pct')">Loss From 52W Peak <span id="sort-ind-drawdown_52w_pct"></span></th>
              <th class="text-right" onclick="sortTableBy('return_ytd')">YTD <span id="sort-ind-return_ytd"></span></th>
              <th class="text-right" onclick="sortTableBy('return_1y')">1Y <span id="sort-ind-return_1y"></span></th>
              <th class="text-right" onclick="sortTableBy('return_2y')">2Y <span id="sort-ind-return_2y"></span></th>
              <th class="text-right" onclick="sortTableBy('return_3y')">3Y <span id="sort-ind-return_3y"></span></th>
              <th class="text-right" onclick="sortTableBy('return_5y')">5Y <span id="sort-ind-return_5y"></span></th>
            </tr>
          </thead>
          <tbody id="heatmap-tbody"></tbody>
        </table>
      </div>
    </div>
  </main>

  <!-- ==========================================================================
       HOLDING'S CARD MODAL:
       - Direct links to Google Finance & Yahoo Finance
       - Interactive Time-Series Graph (All Metrics + Peer Overlay + 1Y Daily Granularity)
       - Earnings Bar Chart (Quarterly / Annual Revenue & Net Income)
       - Dividends Bar Chart (Annual / Recent Payments + Yield & Rate)
       ========================================================================== -->
  <div id="detail-modal" class="gf-modal-backdrop hidden" onclick="if(event.target===this)closeModal()">
    <div class="gf-modal-box space-y-4">
      <!-- Top Header with Google Finance & Yahoo Finance External Links -->
      <div class="flex flex-col sm:flex-row sm:items-start justify-between gap-3 pb-3" style="border-bottom: 1px solid var(--border-color);">
        <div>
          <div class="flex flex-wrap items-center gap-2">
            <h3 class="text-lg font-bold" style="color: var(--text-main);" id="modal-title">Company</h3>
            <span id="modal-core-badge"></span>
            <span id="modal-seg-badge">Sector</span>
          </div>
          <p class="text-xs mt-1" style="color: var(--text-secondary);" id="modal-subtitle"></p>
        </div>

        <div class="flex flex-wrap items-center gap-2 shrink-0">
          <a id="modal-gf-link" href="#" target="_blank" rel="noopener noreferrer" class="gf-pill" title="Open in Google Finance">
            <span>Google Finance</span>
            <span>↗</span>
          </a>
          <a id="modal-yf-link" href="#" target="_blank" rel="noopener noreferrer" class="gf-pill" title="Open in Yahoo Finance">
            <span>Yahoo Finance</span>
            <span>↗</span>
          </a>
          <button onclick="closeModal()" class="gf-pill">
            ✕ Close
          </button>
        </div>
      </div>

      <!-- 8 Key Metrics Strip -->
      <div id="modal-metrics-grid" class="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2 text-xs"></div>

      <!-- Interactive Modal Time-Series Graph -->
      <div class="space-y-2 pt-1">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div class="flex flex-wrap items-center gap-2">
            <span class="text-xs font-bold" style="color: var(--text-secondary);">Graph Metric:</span>
            <select id="modal-metric-select" onchange="setModalMetric(this.value)" class="gf-select">
              <optgroup label="Price &amp; Market Size">
                <option value="price_usd" selected>Share Price (USD $)</option>
                <option value="pct_window">% Change (Selected Timeframe)</option>
                <option value="market_cap_usd_bn">Market Cap ($B)</option>
              </optgroup>
              <optgroup label="Valuation Ratios">
                <option value="trailing_pe">Trailing P/E (TTM)</option>
                <option value="forward_pe">Forward P/E (Est)</option>
                <option value="current_yr_pe">Current Year P/E</option>
                <option value="peg_ratio">PEG Ratio</option>
              </optgroup>
              <optgroup label="Loss From Peak (USD Close)">
                <option value="drawdown_52w_pct">Loss Since 52-Week Peak (%)</option>
                <option value="drawdown_5y_pct">Loss Since 5-Year Peak (%)</option>
              </optgroup>
              <optgroup label="Horizon Gains / Losses (USD)">
                <option value="return_ytd">YTD Gain / Loss (%)</option>
                <option value="return_1y">1-Year Gain / Loss (%)</option>
                <option value="return_2y">2-Year Gain / Loss (%)</option>
                <option value="return_3y">3-Year Gain / Loss (%)</option>
                <option value="return_5y">5-Year Gain / Loss (%)</option>
              </optgroup>
            </select>
          </div>

          <div class="gf-seg-group">
            <button onclick="setModalRange('1M')" id="mr-1M" class="gf-seg-btn">1M</button>
            <button onclick="setModalRange('3M')" id="mr-3M" class="gf-seg-btn">3M</button>
            <button onclick="setModalRange('6M')" id="mr-6M" class="gf-seg-btn">6M</button>
            <button onclick="setModalRange('YTD')" id="mr-YTD" class="gf-seg-btn">YTD</button>
            <button onclick="setModalRange('1Y')" id="mr-1Y" class="gf-seg-btn active">1Y</button>
            <button onclick="setModalRange('2Y')" id="mr-2Y" class="gf-seg-btn">2Y</button>
            <button onclick="setModalRange('3Y')" id="mr-3Y" class="gf-seg-btn">3Y</button>
            <button onclick="setModalRange('5Y')" id="mr-5Y" class="gf-seg-btn">5Y</button>
          </div>
        </div>

        <!-- Modal Live Hover Readout -->
        <div id="modal-chart-legend" class="flex flex-wrap items-center justify-between gap-2 text-xs tabular-nums min-h-[22px] px-1"></div>

        <!-- Interactive SVG inside Modal -->
        <div class="relative select-none" id="modal-chart-wrapper" style="background-color: var(--bg-canvas); border: 1px solid var(--border-color); border-radius: 8px; padding: 10px;">
          <svg id="modal-chart-svg" viewBox="0 0 920 250" class="w-full h-auto overflow-visible cursor-crosshair"
               onmousemove="onModalChartMouseMove(event)"
               onmouseleave="onModalChartMouseLeave()"></svg>
        </div>

        <!-- Compare with Peers inside Modal -->
        <div class="pt-1">
          <div class="text-xs font-bold mb-1.5" style="color: var(--text-secondary);">
            + Compare on this graph (click to overlay):
          </div>
          <div id="modal-compare-chips" class="flex flex-wrap items-center gap-1.5"></div>
        </div>
      </div>

      <!-- EARNINGS & DIVIDENDS BAR CHARTS GRID -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-3" style="border-top: 1px solid var(--border-color);">
        <!-- Left Card: Earnings (Revenue, Net Income & Free Cash Flow Bars) -->
        <div class="p-3.5 rounded-lg space-y-2.5" style="background-color: var(--bg-canvas); border: 1px solid var(--border-color);">
          <div class="flex items-center justify-between gap-2">
            <div>
              <div class="text-xs font-bold" style="color: var(--text-main);">Earnings &amp; FCF: Revenue, Net Income &amp; Free Cash Flow ($B)</div>
              <div class="flex flex-wrap items-center gap-3 text-xs mt-0.5" style="color: var(--text-muted);">
                <span class="inline-flex items-center gap-1"><span style="width:8px;height:8px;border-radius:2px;background:#1a73e8;display:inline-block;"></span>Revenue ($B)</span>
                <span class="inline-flex items-center gap-1"><span style="width:8px;height:8px;border-radius:2px;background:#00bfa5;display:inline-block;"></span>Net Income ($B)</span>
                <span class="inline-flex items-center gap-1"><span style="width:8px;height:8px;border-radius:2px;background:#f59f00;display:inline-block;"></span>Free Cash Flow ($B)</span>
              </div>
            </div>
            <div class="gf-seg-group">
              <button onclick="setEarningsMode('quarterly')" id="earn-btn-quarterly" class="gf-seg-btn active">Quarterly</button>
              <button onclick="setEarningsMode('annual')" id="earn-btn-annual" class="gf-seg-btn">Annual</button>
            </div>
          </div>
          <svg id="modal-earnings-svg" viewBox="0 0 440 185" class="w-full h-auto overflow-visible"></svg>
        </div>

        <!-- Right Card: Capital Return (Buybacks & Dividends) + Dilution Bar Chart -->
        <div class="p-3.5 rounded-lg space-y-2.5" style="background-color: var(--bg-canvas); border: 1px solid var(--border-color);">
          <div class="flex flex-wrap items-center justify-between gap-2">
            <div>
              <div class="text-xs font-bold" style="color: var(--text-main);" id="modal-div-title">Capital Return &amp; Share Dilution</div>
              <div id="modal-div-summary" class="text-xs mt-0.5 tabular-nums" style="color: var(--text-secondary);"></div>
            </div>
            <div class="gf-seg-group">
              <button onclick="setDividendMode('buybacks')" id="div-btn-buybacks" class="gf-seg-btn active">Buybacks + Divs ($B)</button>
              <button onclick="setDividendMode('dilution')" id="div-btn-dilution" class="gf-seg-btn">Dilution (YoY %)</button>
              <button onclick="setDividendMode('dividends')" id="div-btn-dividends" class="gf-seg-btn">Div / Share ($)</button>
            </div>
          </div>
          <svg id="modal-dividends-svg" viewBox="0 0 420 175" class="w-full h-auto overflow-visible"></svg>
        </div>
      </div>
    </div>
  </div>

  <script>
    const PORTFOLIO_DATA = __PORTFOLIO_JSON_PLACEHOLDER__;

    const LINE_PALETTE = [
      "#1a73e8", // Google Royal Blue
      "#00bfa5", // Vivid Teal
      "#fb8c00", // Vibrant Orange
      "#e11d48", // Crimson Rose
      "#7c3aed", // Royal Violet
      "#0284c7", // Ocean Cyan
      "#16a34a", // Emerald Green
      "#d97706"  // Amber Gold
    ];

    const METRIC_META = {
      pct_window:       { label: "% Change (Selected Window)", short: "% Change", unit: "%", defaultDir: "desc", isReturn: true },
      trailing_pe:      { label: "Trailing P/E (TTM)", short: "P/E (TTM)", unit: "x", defaultDir: "asc", isValuation: true },
      forward_pe:       { label: "Forward P/E (Est)", short: "Forward P/E", unit: "x", defaultDir: "asc", isValuation: true },
      current_yr_pe:    { label: "Current Year P/E", short: "CY P/E", unit: "x", defaultDir: "asc", isValuation: true },
      peg_ratio:        { label: "PEG Ratio", short: "PEG", unit: "x", defaultDir: "asc", isValuation: true },
      market_cap_usd_bn:{ label: "Market Cap ($B)", short: "Mkt Cap", unit: "B", defaultDir: "desc" },
      price_usd:        { label: "Share Price (USD $)", short: "Price", unit: "$", defaultDir: "desc" },
      drawdown_52w_pct: { label: "Loss Since 52-Week Peak", short: "52W Peak Loss", unit: "%", defaultDir: "asc", isDrawdown: true },
      drawdown_5y_pct:  { label: "Loss Since 5-Year Peak", short: "5Y Peak Loss", unit: "%", defaultDir: "asc", isDrawdown: true },
      return_ytd:       { label: "YTD Gain / Loss", short: "YTD Return", unit: "%", defaultDir: "desc", isReturn: true, autoRange: "YTD" },
      return_1y:        { label: "1-Year Gain / Loss", short: "1Y Return", unit: "%", defaultDir: "desc", isReturn: true, autoRange: "1Y" },
      return_2y:        { label: "2-Year Gain / Loss", short: "2Y Return", unit: "%", defaultDir: "desc", isReturn: true, autoRange: "2Y" },
      return_3y:        { label: "3-Year Gain / Loss", short: "3Y Return", unit: "%", defaultDir: "desc", isReturn: true, autoRange: "3Y" },
      return_5y:        { label: "5-Year Gain / Loss", short: "5Y Return", unit: "%", defaultDir: "desc", isReturn: true, autoRange: "5Y" },
      display_symbol:   { label: "Symbol", short: "Symbol", unit: "", defaultDir: "asc" },
      segment:          { label: "Sector", short: "Sector", unit: "", defaultDir: "asc" }
    };

    const SEGMENT_BADGE = {
      "HBM Memory": "badge-hbm",
      "Hyperscalers": "badge-hyp",
      "AI Semis & Infra": "badge-semi"
    };

    function getSegmentBarColor(seg) {
      if (seg === "HBM Memory") return "var(--seg-hbm-bar)";
      if (seg === "Hyperscalers") return "var(--seg-hyp-bar)";
      return "var(--seg-semi-bar)";
    }

    let state = {
      theme: "light",
      scope: "all",
      segment: "ALL",
      viewMode: "all",       // 'all' (3 overview panels) | 'bars' | 'scatter' | 'table' | 'compare'
      search: "",
      activeMetric: "forward_pe",
      sortDir: "asc",
      positivePeOnly: true,
      // Main Interactive Time-Series Chart State
      tsMetric: "pct_window",
      tsRange: "1Y",
      compareTickers: ["000660.KS", "005930.KS", "MU", "NVDA"],
      tsPlotCache: null,
      // Modal Interactive Chart State
      modalPrimaryTicker: null,
      modalCompareTickers: [],
      modalMetric: "price_usd",
      modalRange: "1Y",
      modalPlotCache: null,
      earningsMode: "quarterly", // 'quarterly' | 'annual'
      dividendMode: "buybacks"   // 'buybacks' | 'dilution' | 'dividends'
    };

    function starHtml(isCore) {
      return isCore ? `<span class="core-star" title="Screenshot Holding">★</span>` : "";
    }

    function setTheme(theme) {
      state.theme = theme;
      document.documentElement.setAttribute("data-theme", theme);
      document.getElementById("theme-btn-light").classList.toggle("active", theme === "light");
      document.getElementById("theme-btn-dark").classList.toggle("active", theme === "dark");
      try { localStorage.setItem("hbm_dashboard_theme", theme); } catch(e) {}
      renderAll();
      if (!document.getElementById("detail-modal").classList.contains("hidden")) {
        renderModalChart();
        renderModalEarningsAndDividends();
      }
    }

    function formatCurrencyNative(val, curr) {
      if (val === null || val === undefined) return "—";
      if (curr === "KRW") return "₩" + Number(val).toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 0 });
      return "$" + Number(val).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }

    function formatUsd(val) {
      if (val === null || val === undefined) return "—";
      return "$" + Number(val).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }

    function formatMetric(val, metricKey) {
      if (val === null || val === undefined || isNaN(val)) return "N/A";
      const meta = METRIC_META[metricKey] || {};
      if (meta.unit === "$") return formatUsd(val);
      if (meta.unit === "x") {
        if (val < 0) return `Neg (${val.toFixed(1)}x)`;
        return val.toFixed(1) + "x";
      }
      if (meta.unit === "%") {
        const sign = val > 0 ? "+" : "";
        return sign + val.toFixed(1) + "%";
      }
      if (meta.unit === "B") {
        if (val >= 1000) return "$" + (val / 1000).toFixed(2) + "T";
        return "$" + val.toFixed(0) + "B";
      }
      return String(val);
    }

    function formatReturnPill(val) {
      if (val === null || val === undefined) return `<span style="color:var(--text-muted)">N/A</span>`;
      const sign = val > 0 ? "+" : "";
      const cls = val >= 0 ? "ret-pill-pos" : "ret-pill-neg";
      return `<span class="${cls}">${sign}${val.toFixed(1)}%</span>`;
    }

    function getFilteredHoldings() {
      return PORTFOLIO_DATA.holdings.filter(h => {
        if (state.scope === "core" && !h.is_core) return false;
        if (state.segment !== "ALL" && h.segment !== state.segment) return false;
        if (state.search) {
          const q = state.search.toLowerCase();
          const match =
            h.display_symbol.toLowerCase().includes(q) ||
            h.ticker.toLowerCase().includes(q) ||
            h.name.toLowerCase().includes(q) ||
            (h.sub_role && h.sub_role.toLowerCase().includes(q));
          if (!match) return false;
        }
        return true;
      });
    }

    function compareHoldings(a, b, metric, dir) {
      const va = a[metric];
      const vb = b[metric];
      const meta = METRIC_META[metric] || {};

      const aNull = (va === null || va === undefined);
      const bNull = (vb === null || vb === undefined);
      if (aNull && bNull) return a.display_symbol.localeCompare(b.display_symbol);
      if (aNull) return 1;
      if (bNull) return -1;

      if (meta.isValuation && state.positivePeOnly) {
        const aNeg = va <= 0;
        const bNeg = vb <= 0;
        if (aNeg && !bNeg) return 1;
        if (!aNeg && bNeg) return -1;
      }

      if (typeof va === "string" && typeof vb === "string") {
        return dir === "asc" ? va.localeCompare(vb) : vb.localeCompare(va);
      }
      return dir === "asc" ? (va - vb) : (vb - va);
    }

    function median(arr) {
      if (!arr.length) return null;
      const s = [...arr].sort((a, b) => a - b);
      const mid = Math.floor(s.length / 2);
      return s.length % 2 !== 0 ? s[mid] : (s[mid - 1] + s[mid]) / 2;
    }

    /* ==========================================================================
       GOOGLE FINANCE STYLE INTERACTIVE MULTI-SERIES ENGINE
       Supports ALL Ranked Bar Metrics + Market Cap + Daily 1Y Granularity
       ========================================================================== */
    function getStartDateForRange(latestDateStr, rangeKey) {
      const d = new Date(latestDateStr + "T00:00:00Z");
      if (rangeKey === "1M") d.setUTCMonth(d.getUTCMonth() - 1);
      else if (rangeKey === "3M") d.setUTCMonth(d.getUTCMonth() - 3);
      else if (rangeKey === "6M") d.setUTCMonth(d.getUTCMonth() - 6);
      else if (rangeKey === "YTD") return `${d.getUTCFullYear()}-01-01`;
      else if (rangeKey === "1Y") d.setUTCFullYear(d.getUTCFullYear() - 1);
      else if (rangeKey === "2Y") d.setUTCFullYear(d.getUTCFullYear() - 2);
      else if (rangeKey === "3Y") d.setUTCFullYear(d.getUTCFullYear() - 3);
      else d.setUTCFullYear(d.getUTCFullYear() - 5);
      return d.toISOString().slice(0, 10);
    }

    function extractMetricValueAtPoint(h, pt, basePrice, metricKey) {
      if (metricKey === "price_usd") return pt.p;
      if (metricKey === "market_cap_usd_bn") return pt.mc;
      if (metricKey === "trailing_pe") return pt.pe;
      if (metricKey === "forward_pe") {
        if (!h.forward_pe || h.forward_pe <= 0) return null;
        if (pt.pe && h.trailing_pe && h.trailing_pe > 0) {
          return pt.pe * (h.forward_pe / h.trailing_pe);
        }
        return h.price_usd > 0 ? h.forward_pe * (pt.p / h.price_usd) : null;
      }
      if (metricKey === "current_yr_pe") {
        if (!h.current_yr_pe || h.current_yr_pe <= 0) return null;
        if (pt.pe && h.trailing_pe && h.trailing_pe > 0) {
          return pt.pe * (h.current_yr_pe / h.trailing_pe);
        }
        return h.price_usd > 0 ? h.current_yr_pe * (pt.p / h.price_usd) : null;
      }
      if (metricKey === "peg_ratio") {
        if (!h.peg_ratio || h.peg_ratio <= 0) return null;
        if (pt.pe && h.trailing_pe && h.trailing_pe > 0) {
          return pt.pe * (h.peg_ratio / h.trailing_pe);
        }
        return h.price_usd > 0 ? h.peg_ratio * (pt.p / h.price_usd) : null;
      }
      if (metricKey === "drawdown_52w_pct") {
        return pt.dd52 !== undefined && pt.dd52 !== null ? pt.dd52 : pt.dd;
      }
      if (metricKey === "drawdown_5y_pct") {
        return pt.dd;
      }
      // pct_window or return_ytd / return_1y / return_2y / return_3y / return_5y
      return basePrice > 0 ? ((pt.p - basePrice) / basePrice) * 100.0 : null;
    }

    function buildInteractiveTimeSeriesPlot(svgEl, tickers, metricKey, rangeKey, W, H) {
      const pad = { top: 22, right: 68, bottom: 32, left: 16 };
      const plotW = W - pad.left - pad.right;
      const plotH = H - pad.top - pad.bottom;

      const holdings = tickers
        .map(t => PORTFOLIO_DATA.holdings.find(h => h.ticker === t))
        .filter(Boolean);

      if (!holdings.length) {
        svgEl.innerHTML = `<text x="${W/2}" y="${H/2}" text-anchor="middle" fill="var(--text-muted)" font-size="13">Select at least one holding below to plot</text>`;
        return null;
      }

      const latestGlobal = holdings.map(h => h.as_of_date).sort().pop() || "2026-11-06";
      const cutoffDate = getStartDateForRange(latestGlobal, rangeKey);

      const seriesList = [];
      let allDatesSet = new Set();

      holdings.forEach((h, idx) => {
        const allHist = h.chart_history || [];
        const raw = allHist.filter(pt => pt.d >= cutoffDate);
        if (!raw.length) return;

        // Base price is the last point on or before cutoffDate (or first point in raw)
        const priorPts = allHist.filter(pt => pt.d < cutoffDate);
        const basePrice = priorPts.length > 0 ? priorPts[priorPts.length - 1].p : raw[0].p;

        const pts = [];
        raw.forEach(pt => {
          const val = extractMetricValueAtPoint(h, pt, basePrice, metricKey);
          if (val !== null && val !== undefined && !isNaN(val)) {
            pts.push({ d: pt.d, v: val, raw: pt });
            allDatesSet.add(pt.d);
          }
        });
        if (pts.length > 1) {
          seriesList.push({
            holding: h,
            color: LINE_PALETTE[idx % LINE_PALETTE.length],
            pts: pts,
            byDate: Object.fromEntries(pts.map(p => [p.d, p]))
          });
        }
      });

      if (!seriesList.length) {
        svgEl.innerHTML = `<text x="${W/2}" y="${H/2}" text-anchor="middle" fill="var(--text-muted)" font-size="13">No historical data available for this metric in the selected timeframe</text>`;
        return null;
      }

      const sortedDates = Array.from(allDatesSet).sort();
      const allVals = seriesList.flatMap(s => s.pts.map(p => p.v));
      let yMin = Math.min(...allVals);
      let yMax = Math.max(...allVals);
      const ySpan = (yMax - yMin) || 1;
      yMin -= ySpan * 0.08;
      yMax += ySpan * 0.08;

      const dateToX = dStr => {
        const idx = sortedDates.indexOf(dStr);
        if (sortedDates.length <= 1) return pad.left + plotW / 2;
        return pad.left + (idx / (sortedDates.length - 1)) * plotW;
      };
      const yScale = v => pad.top + plotH - ((v - yMin) / (yMax - yMin)) * plotH;

      let html = `<defs>`;
      seriesList.forEach((s, i) => {
        html += `
          <linearGradient id="tsGrad-${svgEl.id}-${i}" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="${s.color}" stop-opacity="${seriesList.length === 1 ? '0.24' : '0.0'}"/>
            <stop offset="100%" stop-color="${s.color}" stop-opacity="0.0"/>
          </linearGradient>
        `;
      });
      html += `</defs>`;

      for (let i = 0; i <= 4; i++) {
        const yv = yMin + (i / 4) * (yMax - yMin);
        const yp = yScale(yv);
        html += `<line x1="${pad.left}" y1="${yp.toFixed(1)}" x2="${pad.left + plotW}" y2="${yp.toFixed(1)}" stroke="var(--grid-line)" stroke-width="1" />`;
        html += `<text x="${pad.left + plotW + 8}" y="${(yp + 4).toFixed(1)}" text-anchor="start" fill="var(--text-muted)" font-size="12" class="tabular-nums">${formatMetric(yv, metricKey)}</text>`;
      }

      const meta = METRIC_META[metricKey] || {};
      if ((meta.isReturn || meta.isDrawdown) && yMin <= 0 && yMax >= 0) {
        const yZero = yScale(0);
        html += `<line x1="${pad.left}" y1="${yZero.toFixed(1)}" x2="${pad.left + plotW}" y2="${yZero.toFixed(1)}" stroke="var(--border-strong)" stroke-dasharray="4,3" stroke-width="1.2" />`;
      }

      const labelCount = Math.min(6, sortedDates.length);
      for (let i = 0; i < labelCount; i++) {
        const dIdx = Math.floor((i / Math.max(1, labelCount - 1)) * (sortedDates.length - 1));
        const dStr = sortedDates[dIdx];
        const xp = pad.left + (dIdx / Math.max(1, sortedDates.length - 1)) * plotW;
        const anchor = i === 0 ? "start" : (i === labelCount - 1 ? "end" : "middle");
        html += `<text x="${xp.toFixed(1)}" y="${H - 8}" text-anchor="${anchor}" fill="var(--text-muted)" font-size="12" class="tabular-nums">${dStr}</text>`;
      }

      seriesList.forEach((s, i) => {
        const coords = s.pts.map(p => ({ x: dateToX(p.d), y: yScale(p.v), d: p.d, v: p.v, raw: p.raw }));
        s.coords = coords;
        const polyPts = coords.map(c => `${c.x.toFixed(1)},${c.y.toFixed(1)}`).join(" ");
        if (seriesList.length === 1) {
          const areaPts = `${coords[0].x.toFixed(1)},${(pad.top + plotH).toFixed(1)} ${polyPts} ${coords[coords.length - 1].x.toFixed(1)},${(pad.top + plotH).toFixed(1)}`;
          html += `<polygon fill="url(#tsGrad-${svgEl.id}-${i})" points="${areaPts}" />`;
        }
        html += `<polyline fill="none" stroke="${s.color}" stroke-width="${seriesList.length === 1 ? '2.4' : '2.0'}" stroke-linecap="round" stroke-linejoin="round" points="${polyPts}" />`;
      });

      html += `<g id="${svgEl.id}-hover-layer" class="hidden">`;
      html += `<line id="${svgEl.id}-crosshair" x1="0" y1="${pad.top}" x2="0" y2="${pad.top + plotH}" stroke="var(--text-muted)" stroke-dasharray="3,3" stroke-width="1.2" />`;
      seriesList.forEach((s, i) => {
        html += `<circle id="${svgEl.id}-dot-${i}" cx="0" cy="0" r="5" fill="${s.color}" stroke="var(--bg-surface)" stroke-width="2" class="hidden" />`;
      });
      html += `</g>`;

      svgEl.innerHTML = html;

      return {
        W, H, pad, plotW, plotH,
        sortedDates,
        seriesList,
        metricKey,
        yScale,
        dateToX
      };
    }

    function renderMainComparisonChart() {
      const svgEl = document.getElementById("ts-chart-svg");
      document.getElementById("ts-metric-select").value = state.tsMetric;
      state.tsPlotCache = buildInteractiveTimeSeriesPlot(
        svgEl,
        state.compareTickers,
        state.tsMetric,
        state.tsRange,
        1120,
        370
      );
      updateMainTsLegend(null);
      renderCompareChips();
    }

    function updateMainTsLegend(dateStr) {
      const bar = document.getElementById("ts-legend-bar");
      const dateBadge = document.getElementById("ts-hover-date");
      const cache = state.tsPlotCache;
      if (!cache || !cache.seriesList.length) {
        bar.innerHTML = "";
        return;
      }

      const targetDate = dateStr || cache.sortedDates[cache.sortedDates.length - 1];
      dateBadge.textContent = dateStr
        ? `Date: ${targetDate} (${cache.sortedDates.length} pts)`
        : `Latest (${targetDate}) · ${cache.sortedDates.length} pts in window`;

      bar.innerHTML = cache.seriesList.map(s => {
        const h = s.holding;
        let pt = s.byDate[targetDate];
        if (!pt) {
          for (let i = s.pts.length - 1; i >= 0; i--) {
            if (s.pts[i].d <= targetDate) { pt = s.pts[i]; break; }
          }
        }
        const valStr = pt ? formatMetric(pt.v, state.tsMetric) : "—";
        return `
          <div class="inline-flex items-center gap-2 px-2.5 py-1 rounded-md" style="background-color: var(--bg-subtle); border: 1px solid var(--border-color);">
            <span style="width:10px;height:10px;border-radius:50%;background:${s.color};display:inline-block;"></span>
            <span class="font-bold" style="color: var(--text-main);">${h.display_symbol}</span>
            ${starHtml(h.is_core)}
            <span class="font-bold" style="color: ${s.color};">${valStr}</span>
            ${state.compareTickers.length > 1 ? `<button onclick="toggleCompareTicker('${h.ticker}')" title="Remove from chart" class="ml-1 hover:opacity-75" style="color:var(--text-muted);">✕</button>` : ''}
          </div>
        `;
      }).join("");
    }

    function onTsChartMouseMove(evt) {
      const cache = state.tsPlotCache;
      if (!cache || !cache.sortedDates.length) return;
      const svg = document.getElementById("ts-chart-svg");
      const rect = svg.getBoundingClientRect();
      const relX = ((evt.clientX - rect.left) / rect.width) * cache.W;
      const clampedX = Math.max(cache.pad.left, Math.min(cache.pad.left + cache.plotW, relX));
      const ratio = (clampedX - cache.pad.left) / (cache.plotW || 1);
      const dIdx = Math.round(ratio * (cache.sortedDates.length - 1));
      const dStr = cache.sortedDates[dIdx];
      const snapX = cache.dateToX(dStr);

      const layer = document.getElementById("ts-chart-svg-hover-layer");
      const line = document.getElementById("ts-chart-svg-crosshair");
      if (layer && line) {
        layer.classList.remove("hidden");
        line.setAttribute("x1", snapX.toFixed(1));
        line.setAttribute("x2", snapX.toFixed(1));
      }

      const activeRows = [];
      cache.seriesList.forEach((s, i) => {
        const dot = document.getElementById(`ts-chart-svg-dot-${i}`);
        let pt = s.byDate[dStr];
        if (!pt) {
          for (let j = s.pts.length - 1; j >= 0; j--) {
            if (s.pts[j].d <= dStr) { pt = s.pts[j]; break; }
          }
        }
        if (dot && pt) {
          dot.setAttribute("cx", snapX.toFixed(1));
          dot.setAttribute("cy", cache.yScale(pt.v).toFixed(1));
          dot.classList.remove("hidden");
          activeRows.push({ s, pt });
        } else if (dot) {
          dot.classList.add("hidden");
        }
      });

      updateMainTsLegend(dStr);

      const tip = document.getElementById("ts-floating-tooltip");
      const wrapRect = document.getElementById("ts-chart-wrapper").getBoundingClientRect();
      activeRows.sort((a, b) => b.pt.v - a.pt.v);
      const mLabel = (METRIC_META[state.tsMetric] || {}).label || state.tsMetric;
      tip.innerHTML = `
        <div class="font-bold text-xs pb-1.5 mb-1.5" style="border-bottom: 1px solid var(--border-color); color: var(--text-main);">
          ${dStr} · ${mLabel}
        </div>
        <div class="space-y-1 text-xs tabular-nums">
          ${activeRows.map(({ s, pt }) => `
            <div class="flex items-center justify-between gap-2">
              <span class="inline-flex items-center gap-1.5 truncate">
                <span style="width:8px;height:8px;border-radius:50%;background:${s.color};display:inline-block;"></span>
                <strong style="color:var(--text-main);">${s.holding.display_symbol}</strong>
                ${starHtml(s.holding.is_core)}
              </span>
              <span class="font-bold" style="color:${s.color};">${formatMetric(pt.v, state.tsMetric)}</span>
            </div>
          `).join("")}
        </div>
      `;
      tip.classList.remove("hidden");
      const leftPos = (evt.clientX - wrapRect.left > wrapRect.width - 280)
        ? Math.max(8, evt.clientX - wrapRect.left - 275)
        : evt.clientX - wrapRect.left + 16;
      const topPos = Math.max(8, Math.min(wrapRect.height - 150, evt.clientY - wrapRect.top - 20));
      tip.style.left = leftPos + "px";
      tip.style.top = topPos + "px";
    }

    function onTsChartMouseLeave() {
      const layer = document.getElementById("ts-chart-svg-hover-layer");
      if (layer) layer.classList.add("hidden");
      document.getElementById("ts-floating-tooltip").classList.add("hidden");
      updateMainTsLegend(null);
    }

    function renderCompareChips() {
      const container = document.getElementById("compare-chips-container");
      const allHoldings = [...PORTFOLIO_DATA.holdings].sort((a, b) => (b.is_core - a.is_core) || a.display_symbol.localeCompare(b.display_symbol));
      container.innerHTML = allHoldings.map(h => {
        const activeIdx = state.compareTickers.indexOf(h.ticker);
        const isActive = activeIdx !== -1;
        const dotColor = isActive ? LINE_PALETTE[activeIdx % LINE_PALETTE.length] : "var(--border-strong)";
        return `
          <button onclick="toggleCompareTicker('${h.ticker}')" class="gf-pill ${isActive ? 'active' : ''}">
            <span style="width:8px;height:8px;border-radius:50%;background:${dotColor};display:inline-block;"></span>
            <span>${h.display_symbol}</span>
            ${starHtml(h.is_core)}
          </button>
        `;
      }).join("");
    }

    function toggleCompareTicker(ticker) {
      const idx = state.compareTickers.indexOf(ticker);
      if (idx !== -1) {
        if (state.compareTickers.length > 1) {
          state.compareTickers.splice(idx, 1);
        }
      } else {
        if (state.compareTickers.length >= 8) {
          state.compareTickers.shift();
        }
        state.compareTickers.push(ticker);
      }
      renderMainComparisonChart();
    }

    function setCompareGroup(tickers) {
      state.compareTickers = [...tickers];
      renderMainComparisonChart();
    }

    function setTsMetric(m) {
      state.tsMetric = m;
      const meta = METRIC_META[m];
      if (meta && meta.autoRange) {
        setTsRange(meta.autoRange);
        return;
      }
      renderMainComparisonChart();
    }

    function setTsRange(r) {
      state.tsRange = r;
      ["1M", "3M", "6M", "YTD", "1Y", "2Y", "3Y", "5Y"].forEach(k => {
        const el = document.getElementById("tsr-" + k);
        if (el) el.classList.toggle("active", k === r);
      });
      renderMainComparisonChart();
    }

    function renderKpiStrip(items) {
      const strip = document.getElementById("kpi-strip");
      const validPe = items.filter(d => d.trailing_pe !== null && d.trailing_pe > 0);
      const validFpe = items.filter(d => d.forward_pe !== null && d.forward_pe > 0);
      const validDd = items.filter(d => d.drawdown_52w_pct !== null);
      const validYtd = items.filter(d => d.return_ytd !== null);
      const valid1y = items.filter(d => d.return_1y !== null);

      const cheapestPe = [...validPe].sort((a, b) => a.trailing_pe - b.trailing_pe)[0];
      const cheapestFpe = [...validFpe].sort((a, b) => a.forward_pe - b.forward_pe)[0];
      const deepestDd = [...validDd].sort((a, b) => a.drawdown_52w_pct - b.drawdown_52w_pct)[0];
      const bestYtd = [...validYtd].sort((a, b) => b.return_ytd - a.return_ytd)[0];
      const best1y = [...valid1y].sort((a, b) => b.return_1y - a.return_1y)[0];

      const medPe = median(validPe.map(d => d.trailing_pe));
      const medFpe = median(validFpe.map(d => d.forward_pe));
      const medDd = median(validDd.map(d => d.drawdown_52w_pct));
      const medYtd = median(validYtd.map(d => d.return_ytd));
      const med1y = median(valid1y.map(d => d.return_1y));

      const cards = [
        {
          title: "Median P/E (TTM)",
          val: medPe !== null ? medPe.toFixed(1) + "x" : "—",
          color: "var(--text-main)",
          sub: cheapestPe ? `Cheapest: ${cheapestPe.display_symbol} (${cheapestPe.trailing_pe.toFixed(1)}x)` : "—",
          action: "applyPreset('trailing_pe','asc')"
        },
        {
          title: "Median Forward P/E",
          val: medFpe !== null ? medFpe.toFixed(1) + "x" : "—",
          color: "var(--accent-blue)",
          sub: cheapestFpe ? `Cheapest: ${cheapestFpe.display_symbol} (${cheapestFpe.forward_pe.toFixed(1)}x)` : "—",
          action: "applyPreset('forward_pe','asc')"
        },
        {
          title: "Median Loss From 52W Peak",
          val: medDd !== null ? medDd.toFixed(1) + "%" : "—",
          color: "var(--loss-fg)",
          sub: deepestDd ? `Biggest Drop: ${deepestDd.display_symbol} (${deepestDd.drawdown_52w_pct.toFixed(1)}%)` : "—",
          action: "applyPreset('drawdown_52w_pct','asc')"
        },
        {
          title: "Median YTD Return",
          val: medYtd !== null ? (medYtd > 0 ? "+" : "") + medYtd.toFixed(1) + "%" : "—",
          color: medYtd >= 0 ? "var(--gain-fg)" : "var(--loss-fg)",
          sub: bestYtd ? `Top YTD: ${bestYtd.display_symbol} (+${bestYtd.return_ytd.toFixed(1)}%)` : "—",
          action: "applyPreset('return_ytd','desc')"
        },
        {
          title: "Median 1-Year Return",
          val: med1y !== null ? (med1y > 0 ? "+" : "") + med1y.toFixed(1) + "%" : "—",
          color: med1y >= 0 ? "var(--gain-fg)" : "var(--loss-fg)",
          sub: best1y ? `Top 1Y: ${best1y.display_symbol} (+${best1y.return_1y.toFixed(1)}%)` : "—",
          action: "applyPreset('return_1y','desc')"
        }
      ];

      strip.innerHTML = cards.map(c => `
        <div onclick="${c.action}" class="gf-card p-3.5 cursor-pointer transition hover:border-[var(--accent-blue)]">
          <div class="text-xs font-semibold" style="color: var(--text-muted);">${c.title}</div>
          <div class="text-xl font-bold tabular-nums mt-1" style="color: ${c.color};">${c.val}</div>
          <div class="text-xs mt-1 truncate font-medium" style="color: var(--text-secondary);">${c.sub}</div>
        </div>
      `).join("");
    }

    function renderRankedBars(items) {
      const container = document.getElementById("ranked-bars-container");
      const metric = state.activeMetric;
      const meta = METRIC_META[metric] || { label: metric, short: metric, unit: "" };

      document.getElementById("active-metric-badge").textContent = meta.label;
      if (document.querySelector(`#metric-select option[value="${metric}"]`)) {
        document.getElementById("metric-select").value = metric;
      }
      document.getElementById("sort-dir-btn").textContent =
        state.sortDir === "asc" ? "↑ Low to High" : "↓ High to Low";

      const sorted = [...items].sort((a, b) => compareHoldings(a, b, metric, state.sortDir));

      const validVals = sorted
        .map(d => d[metric])
        .filter(v => v !== null && v !== undefined && !(meta.isValuation && state.positivePeOnly && v <= 0));

      const maxAbs = validVals.length ? Math.max(...validVals.map(v => Math.abs(v)), 1) : 100;

      container.innerHTML = sorted.map((h, idx) => {
        const val = h[metric];
        const isNegPe = meta.isValuation && val !== null && val <= 0;
        let pctWidth = 0;
        if (val !== null && val !== undefined && !isNegPe) {
          pctWidth = Math.min(100, Math.max(4, (Math.abs(val) / maxAbs) * 100));
        }

        let barColor = getSegmentBarColor(h.segment);
        let valStyle = "color: var(--text-main);";
        if (meta.isDrawdown) {
          barColor = "var(--loss-bar)";
          valStyle = "color: var(--loss-fg);";
        } else if (meta.isReturn && val !== null) {
          barColor = val >= 0 ? "var(--gain-bar)" : "var(--loss-bar)";
          valStyle = val >= 0 ? "color: var(--gain-fg);" : "color: var(--loss-fg);";
        }

        const nativeNote = h.currency !== "USD"
          ? `<span style="color: var(--text-muted);">(${formatCurrencyNative(h.price_native, h.currency)})</span>`
          : "";

        return `
          <div onclick="openModal('${h.ticker}')" class="gf-row rounded-lg p-2" style="border: 1px solid transparent;">
            <div class="flex items-center justify-between gap-2 text-xs mb-1.5">
              <div class="flex items-center gap-2 min-w-0">
                <span class="w-6 text-right font-bold tabular-nums" style="color: var(--text-muted);">${idx + 1}</span>
                <span class="font-bold text-sm" style="color: var(--text-main);">${h.display_symbol}</span>
                ${starHtml(h.is_core)}
                <span class="truncate font-medium" style="color: var(--text-secondary);">${h.name}</span>
                <span class="${SEGMENT_BADGE[h.segment] || ''}">${h.segment}</span>
              </div>
              <div class="flex items-center gap-3 shrink-0 tabular-nums">
                <span class="hidden sm:inline font-medium" style="color: var(--text-secondary);">${formatUsd(h.price_usd)} ${nativeNote}</span>
                <span class="font-bold text-right min-w-[76px] text-sm" style="${valStyle}">
                  ${formatMetric(val, metric)}
                </span>
              </div>
            </div>
            <div class="w-full h-2.5 rounded-full overflow-hidden ml-6" style="width: calc(100% - 1.5rem); background-color: var(--bg-subtle);">
              <div class="h-full rounded-full bar-fill" style="width: ${pctWidth.toFixed(1)}%; background-color: ${barColor};"></div>
            </div>
          </div>
        `;
      }).join("");
    }

    function renderScatter() {
      const items = getFilteredHoldings();
      const xKey = document.getElementById("scatter-x").value;
      const yKey = document.getElementById("scatter-y").value;
      const xMeta = METRIC_META[xKey] || { short: xKey, unit: "" };
      const yMeta = METRIC_META[yKey] || { short: yKey, unit: "" };

      const svg = document.getElementById("scatter-svg");
      const W = 560, H = 420;
      const pad = { top: 28, right: 36, bottom: 46, left: 58 };
      const plotW = W - pad.left - pad.right;
      const plotH = H - pad.top - pad.bottom;

      const pts = items.filter(d => {
        const xv = d[xKey], yv = d[yKey];
        if (xv === null || xv === undefined || yv === null || yv === undefined) return false;
        if (xMeta.isValuation && xv <= 0) return false;
        if (yMeta.isValuation && yv <= 0) return false;
        return true;
      });

      if (!pts.length) {
        svg.innerHTML = `<text x="${W/2}" y="${H/2}" text-anchor="middle" fill="var(--text-muted)" font-size="13">No data points for selected axes</text>`;
        return;
      }

      const xVals = pts.map(d => d[xKey]);
      const yVals = pts.map(d => d[yKey]);
      let xMin = Math.min(...xVals), xMax = Math.max(...xVals);
      let yMin = Math.min(...yVals), yMax = Math.max(...yVals);

      const xSpan = (xMax - xMin) || 10;
      const ySpan = (yMax - yMin) || 10;
      xMin -= xSpan * 0.08;
      xMax += xSpan * 0.12;
      yMin -= ySpan * 0.10;
      yMax += ySpan * 0.10;

      const xScale = v => pad.left + ((v - xMin) / (xMax - xMin)) * plotW;
      const yScale = v => pad.top + plotH - ((v - yMin) / (yMax - yMin)) * plotH;

      const xMed = median(xVals);
      const yMed = median(yVals);

      let html = "";

      for (let i = 0; i <= 4; i++) {
        const xv = xMin + (i / 4) * (xMax - xMin);
        const xp = xScale(xv);
        html += `<line x1="${xp}" y1="${pad.top}" x2="${xp}" y2="${pad.top + plotH}" stroke="var(--grid-line)" stroke-width="1" />`;
        html += `<text x="${xp}" y="${pad.top + plotH + 18}" text-anchor="middle" fill="var(--text-muted)" font-size="12">${xv.toFixed(0)}${xMeta.unit}</text>`;

        const yv = yMin + (i / 4) * (yMax - yMin);
        const yp = yScale(yv);
        html += `<line x1="${pad.left}" y1="${yp}" x2="${pad.left + plotW}" y2="${yp}" stroke="var(--grid-line)" stroke-width="1" />`;
        html += `<text x="${pad.left - 8}" y="${yp + 4}" text-anchor="end" fill="var(--text-muted)" font-size="12">${yv.toFixed(0)}${yMeta.unit}</text>`;
      }

      if (xMed !== null) {
        const xm = xScale(xMed);
        html += `<line x1="${xm}" y1="${pad.top}" x2="${xm}" y2="${pad.top + plotH}" stroke="var(--accent-blue)" stroke-dasharray="5,4" stroke-width="1.5" />`;
        html += `<text x="${xm + 5}" y="${pad.top + 13}" fill="var(--accent-blue)" font-size="12" font-weight="600">Med ${xMed.toFixed(1)}${xMeta.unit}</text>`;
      }
      if (yMed !== null) {
        const ym = yScale(yMed);
        html += `<line x1="${pad.left}" y1="${ym}" x2="${pad.left + plotW}" y2="${ym}" stroke="var(--accent-blue)" stroke-dasharray="5,4" stroke-width="1.5" />`;
        html += `<text x="${pad.left + 6}" y="${ym - 6}" fill="var(--accent-blue)" font-size="12" font-weight="600">Med ${yMed.toFixed(1)}${yMeta.unit}</text>`;
      }

      html += `<text x="${pad.left + plotW / 2}" y="${H - 6}" text-anchor="middle" fill="var(--text-secondary)" font-size="12" font-weight="700">${xMeta.label}</text>`;
      html += `<text x="14" y="${pad.top + plotH / 2}" text-anchor="middle" fill="var(--text-secondary)" font-size="12" font-weight="700" transform="rotate(-90 14 ${pad.top + plotH / 2})">${yMeta.label}</text>`;

      pts.forEach(d => {
        const cx = xScale(d[xKey]);
        const cy = yScale(d[yKey]);
        const color = getSegmentBarColor(d.segment);
        const r = d.is_core ? 7.5 : 6;
        const stroke = d.is_core ? "var(--star-gold)" : "var(--bg-surface)";
        const strokeW = d.is_core ? 2.4 : 1.5;

        html += `
          <g class="cursor-pointer"
             onmouseenter="showScatterTooltip(event, '${d.ticker}')"
             onmouseleave="hideScatterTooltip()"
             onclick="openModal('${d.ticker}')">
            <circle cx="${cx.toFixed(1)}" cy="${cy.toFixed(1)}" r="${r}" fill="${color}" stroke="${stroke}" stroke-width="${strokeW}" />
            <text x="${(cx + r + 4).toFixed(1)}" y="${(cy + 4).toFixed(1)}" fill="var(--text-main)" font-size="12" font-weight="700">${d.display_symbol}${d.is_core ? ' ★' : ''}</text>
          </g>
        `;
      });

      svg.innerHTML = html;
    }

    function showScatterTooltip(evt, ticker) {
      const h = PORTFOLIO_DATA.holdings.find(x => x.ticker === ticker);
      if (!h) return;
      const tip = document.getElementById("scatter-tooltip");
      const wrap = document.getElementById("scatter-wrapper").getBoundingClientRect();
      tip.innerHTML = `
        <div class="flex items-center justify-between gap-2 pb-1.5" style="border-bottom: 1px solid var(--border-color);">
          <span class="font-bold text-sm" style="color: var(--text-main);">${h.display_symbol} ${starHtml(h.is_core)} · ${h.name}</span>
        </div>
        <div class="text-xs mt-1 mb-2" style="color: var(--text-muted);">${h.sub_role}</div>
        <div class="grid grid-cols-2 gap-y-1 text-xs tabular-nums">
          <span style="color: var(--text-secondary);">Price (USD):</span><span class="text-right font-bold">${formatUsd(h.price_usd)}</span>
          <span style="color: var(--text-secondary);">Mkt Cap:</span><span class="text-right font-bold">${formatMetric(h.market_cap_usd_bn, 'market_cap_usd_bn')}</span>
          <span style="color: var(--text-secondary);">P/E (TTM):</span><span class="text-right font-bold">${formatMetric(h.trailing_pe, 'trailing_pe')}</span>
          <span style="color: var(--text-secondary);">Forward P/E:</span><span class="text-right font-bold" style="color: var(--accent-blue);">${formatMetric(h.forward_pe, 'forward_pe')}</span>
          <span style="color: var(--text-secondary);">52W Peak Loss:</span><span class="text-right font-bold" style="color: var(--loss-fg);">${formatMetric(h.drawdown_52w_pct, 'drawdown_52w_pct')}</span>
          <span style="color: var(--text-secondary);">YTD / 1Y:</span><span class="text-right font-bold">${formatMetric(h.return_ytd, 'return_ytd')} / ${formatMetric(h.return_1y, 'return_1y')}</span>
        </div>
      `;
      tip.classList.remove("hidden");
      const left = Math.min(wrap.width - 265, Math.max(8, evt.clientX - wrap.left + 14));
      const top = Math.max(8, evt.clientY - wrap.top - 24);
      tip.style.left = left + "px";
      tip.style.top = top + "px";
    }

    function hideScatterTooltip() {
      document.getElementById("scatter-tooltip").classList.add("hidden");
    }

    function renderTable(items) {
      const tbody = document.getElementById("heatmap-tbody");
      const metric = state.activeMetric;
      const sorted = [...items].sort((a, b) => compareHoldings(a, b, metric, state.sortDir));

      Object.keys(METRIC_META).forEach(k => {
        const el = document.getElementById("sort-ind-" + k);
        if (el) {
          el.textContent = (k === metric) ? (state.sortDir === "asc" ? "▲" : "▼") : "";
        }
      });

      tbody.innerHTML = sorted.map((h, idx) => {
        const ddWidth = h.drawdown_52w_pct !== null ? Math.min(100, Math.abs(h.drawdown_52w_pct)) : 0;
        const localPriceLine = h.currency !== "USD"
          ? `<div class="text-xs" style="color: var(--text-muted);">${formatCurrencyNative(h.price_native, h.currency)}</div>`
          : "";

        return `
          <tr onclick="openModal('${h.ticker}')" class="gf-row">
            <td class="font-bold" style="color: var(--text-muted);">${idx + 1}</td>
            <td>
              <div class="flex items-center gap-1.5">
                <span class="font-bold text-sm" style="color: var(--text-main);">${h.display_symbol}</span>
                ${starHtml(h.is_core)}
              </div>
              <div class="text-xs truncate max-w-[190px]" style="color: var(--text-secondary);">${h.name}</div>
            </td>
            <td>
              <span class="${SEGMENT_BADGE[h.segment] || ''}">${h.segment}</span>
              <div class="text-xs mt-0.5 truncate max-w-[175px]" style="color: var(--text-muted);">${h.sub_role}</div>
            </td>
            <td class="text-right font-bold">
              <div>${formatUsd(h.price_usd)}</div>
              ${localPriceLine}
            </td>
            <td class="text-right font-semibold" style="color: var(--text-secondary);">${formatMetric(h.market_cap_usd_bn, 'market_cap_usd_bn')}</td>
            <td class="text-right font-bold" title="${h.pe_note || ''}">${formatMetric(h.trailing_pe, 'trailing_pe')}</td>
            <td class="text-right font-bold" style="color: var(--accent-blue);">${formatMetric(h.forward_pe, 'forward_pe')}</td>
            <td class="text-right">
              <div class="flex items-center justify-end gap-2">
                <div class="w-16 h-2 rounded-full overflow-hidden hidden sm:block" style="background-color: var(--bg-subtle);">
                  <div class="h-full rounded-full" style="width: ${ddWidth.toFixed(0)}%; background-color: var(--loss-bar);"></div>
                </div>
                <span class="ret-pill-neg w-16 text-center">${formatMetric(h.drawdown_52w_pct, 'drawdown_52w_pct')}</span>
              </div>
              <div class="text-xs mt-0.5" style="color: var(--text-muted);">Peak ${h.peak_52w_date} (${formatUsd(h.peak_52w_usd)})</div>
            </td>
            <td class="text-right">${formatReturnPill(h.return_ytd)}</td>
            <td class="text-right">${formatReturnPill(h.return_1y)}</td>
            <td class="text-right">${formatReturnPill(h.return_2y)}</td>
            <td class="text-right">${formatReturnPill(h.return_3y)}</td>
            <td class="text-right">${formatReturnPill(h.return_5y)}</td>
          </tr>
        `;
      }).join("");
    }

    /* ==========================================================================
       HOLDING'S CARD MODAL:
       Interactive Graph + Earnings Bars + Dividends Bars + Google/Yahoo Links
       ========================================================================== */
    function openModal(ticker) {
      const h = PORTFOLIO_DATA.holdings.find(x => x.ticker === ticker);
      if (!h) return;

      state.modalPrimaryTicker = ticker;
      state.modalCompareTickers = [];
      state.modalMetric = "price_usd";
      state.modalRange = "1Y";

      document.getElementById("modal-title").textContent = `${h.display_symbol} · ${h.name}`;
      document.getElementById("modal-core-badge").innerHTML = h.is_core
        ? `<span class="px-2 py-0.5 rounded text-xs font-bold" style="background:rgba(245,159,0,0.16);color:var(--star-gold);">★ Screenshot Holding</span>`
        : "";
      const badge = document.getElementById("modal-seg-badge");
      badge.textContent = h.segment;
      badge.className = SEGMENT_BADGE[h.segment] || "";

      // Set Google Finance & Yahoo Finance links
      document.getElementById("modal-gf-link").href = h.google_finance_url || `https://www.google.com/finance/quote/${h.display_symbol}:NASDAQ`;
      document.getElementById("modal-yf-link").href = h.yahoo_finance_url || `https://finance.yahoo.com/quote/${h.ticker}`;

      const nativeExtra = h.currency !== "USD"
        ? ` · Local Close: ${formatCurrencyNative(h.price_native, h.currency)} (FX: ${h.fx_rate_to_usd} ${h.currency}/USD)`
        : "";
      document.getElementById("modal-subtitle").textContent =
        `${h.sub_role} · Market Cap: ${formatMetric(h.market_cap_usd_bn, 'market_cap_usd_bn')} · 52W Peak: ${formatUsd(h.peak_52w_usd)} (${h.peak_52w_date})${nativeExtra}`;

      const metrics = [
        { k: "Price (USD)", v: formatUsd(h.price_usd), color: "var(--text-main)" },
        { k: "Market Cap", v: formatMetric(h.market_cap_usd_bn, "market_cap_usd_bn"), color: "var(--text-main)" },
        { k: "P/E (TTM)", v: formatMetric(h.trailing_pe, "trailing_pe"), color: "var(--text-main)" },
        { k: "Forward P/E", v: formatMetric(h.forward_pe, "forward_pe"), color: "var(--accent-blue)" },
        { k: "52W Peak Loss", v: formatMetric(h.drawdown_52w_pct, "drawdown_52w_pct"), color: "var(--loss-fg)" },
        { k: "YTD Return", v: formatMetric(h.return_ytd, "return_ytd"), color: h.return_ytd >= 0 ? "var(--gain-fg)" : "var(--loss-fg)" },
        { k: "1Y Return", v: formatMetric(h.return_1y, "return_1y"), color: h.return_1y >= 0 ? "var(--gain-fg)" : "var(--loss-fg)" },
        { k: "5Y Return", v: formatMetric(h.return_5y, "return_5y"), color: h.return_5y >= 0 ? "var(--gain-fg)" : "var(--loss-fg)" }
      ];

      document.getElementById("modal-metrics-grid").innerHTML = metrics.map(m => `
        <div class="p-2.5 rounded-lg" style="background-color: var(--bg-subtle); border: 1px solid var(--border-color);">
          <div class="text-xs font-medium truncate" style="color: var(--text-muted);">${m.k}</div>
          <div class="text-sm font-bold tabular-nums mt-0.5" style="color: ${m.color};">${m.v}</div>
        </div>
      `).join("");

      syncModalButtons();
      renderModalChart();
      renderModalEarningsAndDividends();
      document.getElementById("detail-modal").classList.remove("hidden");
    }

    function syncModalButtons() {
      document.getElementById("modal-metric-select").value = state.modalMetric;
      ["1M", "3M", "6M", "YTD", "1Y", "2Y", "3Y", "5Y"].forEach(k => {
        const el = document.getElementById("mr-" + k);
        if (el) el.classList.toggle("active", k === state.modalRange);
      });
    }

    function setModalMetric(m) {
      state.modalMetric = m;
      const meta = METRIC_META[m];
      if (meta && meta.autoRange) {
        state.modalRange = meta.autoRange;
      }
      syncModalButtons();
      renderModalChart();
    }

    function setModalRange(r) {
      state.modalRange = r;
      syncModalButtons();
      renderModalChart();
    }

    function toggleModalCompareTicker(ticker) {
      const idx = state.modalCompareTickers.indexOf(ticker);
      if (idx !== -1) {
        state.modalCompareTickers.splice(idx, 1);
      } else {
        if (state.modalCompareTickers.length >= 5) state.modalCompareTickers.shift();
        state.modalCompareTickers.push(ticker);
        if (state.modalMetric === "price_usd") {
          state.modalMetric = "pct_window";
          syncModalButtons();
        }
      }
      renderModalChart();
    }

    function renderModalChart() {
      const svgEl = document.getElementById("modal-chart-svg");
      const allTickers = [state.modalPrimaryTicker, ...state.modalCompareTickers].filter(Boolean);
      state.modalPlotCache = buildInteractiveTimeSeriesPlot(
        svgEl,
        allTickers,
        state.modalMetric,
        state.modalRange,
        920,
        250
      );
      updateModalLegend(null);

      const chipsEl = document.getElementById("modal-compare-chips");
      const peers = PORTFOLIO_DATA.holdings.filter(x => x.ticker !== state.modalPrimaryTicker);
      chipsEl.innerHTML = peers.map(p => {
        const cIdx = state.modalCompareTickers.indexOf(p.ticker);
        const isAct = cIdx !== -1;
        const dotColor = isAct ? LINE_PALETTE[(cIdx + 1) % LINE_PALETTE.length] : "var(--border-strong)";
        return `
          <button onclick="toggleModalCompareTicker('${p.ticker}')" class="gf-pill ${isAct ? 'active' : ''}">
            <span style="width:8px;height:8px;border-radius:50%;background:${dotColor};display:inline-block;"></span>
            <span>${p.display_symbol}</span>
            ${starHtml(p.is_core)}
          </button>
        `;
      }).join("");
    }

    function updateModalLegend(dateStr) {
      const el = document.getElementById("modal-chart-legend");
      const cache = state.modalPlotCache;
      if (!cache || !cache.seriesList.length) {
        el.innerHTML = "";
        return;
      }
      const targetDate = dateStr || cache.sortedDates[cache.sortedDates.length - 1];
      const itemsHtml = cache.seriesList.map(s => {
        let pt = s.byDate[targetDate];
        if (!pt) {
          for (let i = s.pts.length - 1; i >= 0; i--) {
            if (s.pts[i].d <= targetDate) { pt = s.pts[i]; break; }
          }
        }
        return `
          <span class="inline-flex items-center gap-1.5 mr-3">
            <span style="width:9px;height:9px;border-radius:50%;background:${s.color};display:inline-block;"></span>
            <strong style="color:var(--text-main);">${s.holding.display_symbol}</strong>
            ${starHtml(s.holding.is_core)}:
            <strong style="color:${s.color};">${pt ? formatMetric(pt.v, state.modalMetric) : '—'}</strong>
          </span>
        `;
      }).join("");

      el.innerHTML = `
        <div>${itemsHtml}</div>
        <div class="font-bold" style="color:var(--text-secondary);">${dateStr ? 'Date: ' + targetDate : 'Latest: ' + targetDate + ' (hover graph to inspect)'}</div>
      `;
    }

    function onModalChartMouseMove(evt) {
      const cache = state.modalPlotCache;
      if (!cache || !cache.sortedDates.length) return;
      const svg = document.getElementById("modal-chart-svg");
      const rect = svg.getBoundingClientRect();
      const relX = ((evt.clientX - rect.left) / rect.width) * cache.W;
      const clampedX = Math.max(cache.pad.left, Math.min(cache.pad.left + cache.plotW, relX));
      const ratio = (clampedX - cache.pad.left) / (cache.plotW || 1);
      const dIdx = Math.round(ratio * (cache.sortedDates.length - 1));
      const dStr = cache.sortedDates[dIdx];
      const snapX = cache.dateToX(dStr);

      const layer = document.getElementById("modal-chart-svg-hover-layer");
      const line = document.getElementById("modal-chart-svg-crosshair");
      if (layer && line) {
        layer.classList.remove("hidden");
        line.setAttribute("x1", snapX.toFixed(1));
        line.setAttribute("x2", snapX.toFixed(1));
      }

      cache.seriesList.forEach((s, i) => {
        const dot = document.getElementById(`modal-chart-svg-dot-${i}`);
        let pt = s.byDate[dStr];
        if (!pt) {
          for (let j = s.pts.length - 1; j >= 0; j--) {
            if (s.pts[j].d <= dStr) { pt = s.pts[j]; break; }
          }
        }
        if (dot && pt) {
          dot.setAttribute("cx", snapX.toFixed(1));
          dot.setAttribute("cy", cache.yScale(pt.v).toFixed(1));
          dot.classList.remove("hidden");
        } else if (dot) {
          dot.classList.add("hidden");
        }
      });

      updateModalLegend(dStr);
    }

    function onModalChartMouseLeave() {
      const layer = document.getElementById("modal-chart-svg-hover-layer");
      if (layer) layer.classList.add("hidden");
      updateModalLegend(null);
    }

    /* ==========================================================================
       EARNINGS & DIVIDENDS BAR CHARTS ON HOLDING'S CARD
       ========================================================================== */
    function setEarningsMode(mode) {
      state.earningsMode = mode;
      document.getElementById("earn-btn-quarterly").classList.toggle("active", mode === "quarterly");
      document.getElementById("earn-btn-annual").classList.toggle("active", mode === "annual");
      renderModalEarningsAndDividends();
    }

    function setDividendMode(mode) {
      state.dividendMode = mode;
      ["buybacks", "dilution", "dividends"].forEach(m => {
        const el = document.getElementById("div-btn-" + m);
        if (el) el.classList.toggle("active", m === mode);
      });
      renderModalEarningsAndDividends();
    }

    function renderModalEarningsAndDividends() {
      const h = PORTFOLIO_DATA.holdings.find(x => x.ticker === state.modalPrimaryTicker);
      if (!h) return;

      // 1. Render Earnings Grouped Bar Chart (Revenue $B, Net Income $B, Free Cash Flow $B)
      const earnSvg = document.getElementById("modal-earnings-svg");
      const earnObj = h.earnings || { quarterly: [], annual: [] };
      const earnBars = state.earningsMode === "quarterly" ? (earnObj.quarterly || []) : (earnObj.annual || []);

      if (!earnBars.length) {
        earnSvg.innerHTML = `<text x="220" y="92" text-anchor="middle" fill="var(--text-muted)" font-size="12">No earnings history available</text>`;
      } else {
        const W = 440, H = 185;
        const padL = 42, padR = 10, padT = 24, padB = 28;
        const plotW = W - padL - padR;
        const plotH = H - padT - padB;

        const allVals = earnBars.flatMap(b => [b.revenue_bn || 0, b.net_income_bn || 0, b.fcf_bn || 0, 0]);
        const yMin = Math.min(0, ...allVals) * 1.15;
        const yMax = Math.max(1, ...allVals) * 1.15;
        const yScale = v => padT + plotH - ((v - yMin) / (yMax - yMin || 1)) * plotH;
        const yZero = yScale(0);
        const fmtBarVal = v => Math.abs(v) >= 100 ? v.toFixed(0) : v.toFixed(1);

        let html = "";
        for (let i = 0; i <= 3; i++) {
          const yv = yMin + (i / 3) * (yMax - yMin);
          const yp = yScale(yv);
          html += `<line x1="${padL}" y1="${yp.toFixed(1)}" x2="${padL + plotW}" y2="${yp.toFixed(1)}" stroke="var(--grid-line)" stroke-width="1" />`;
          html += `<text x="${padL - 6}" y="${(yp + 4).toFixed(1)}" text-anchor="end" fill="var(--text-muted)" font-size="11" class="tabular-nums">$${yv.toFixed(0)}B</text>`;
        }
        html += `<line x1="${padL}" y1="${yZero.toFixed(1)}" x2="${padL + plotW}" y2="${yZero.toFixed(1)}" stroke="var(--border-strong)" stroke-width="1.2" />`;

        const groupW = plotW / earnBars.length;
        const barW = Math.min(19, groupW * 0.25);
        const gap = 2;

        earnBars.forEach((b, idx) => {
          const cx = padL + (idx + 0.5) * groupW;
          const rev = b.revenue_bn || 0;
          const ni = b.net_income_bn || 0;
          const hasFcf = b.fcf_bn !== null && b.fcf_bn !== undefined;
          const fcf = hasFcf ? b.fcf_bn : 0;

          // 1. Revenue bar (left)
          const rX = cx - 1.5 * barW - gap;
          const rTop = Math.min(yZero, yScale(rev));
          const rH = Math.max(2, Math.abs(yZero - yScale(rev)));
          html += `<rect x="${rX.toFixed(1)}" y="${rTop.toFixed(1)}" width="${barW.toFixed(1)}" height="${rH.toFixed(1)}" rx="2.5" fill="#1a73e8"><title>${b.period} Revenue: $${rev.toFixed(2)}B</title></rect>`;
          html += `<text x="${(rX + barW / 2).toFixed(1)}" y="${(rTop - 4).toFixed(1)}" text-anchor="middle" fill="var(--text-secondary)" font-size="9.5" font-weight="600" class="tabular-nums">${fmtBarVal(rev)}</text>`;

          // 2. Net Income bar (center)
          const niX = cx - 0.5 * barW;
          const niTop = Math.min(yZero, yScale(ni));
          const niH = Math.max(2, Math.abs(yZero - yScale(ni)));
          const niColor = ni >= 0 ? "#00bfa5" : "#f03e3e";
          html += `<rect x="${niX.toFixed(1)}" y="${niTop.toFixed(1)}" width="${barW.toFixed(1)}" height="${niH.toFixed(1)}" rx="2.5" fill="${niColor}"><title>${b.period} Net Income: $${ni.toFixed(2)}B</title></rect>`;
          html += `<text x="${(niX + barW / 2).toFixed(1)}" y="${(ni >= 0 ? niTop - 4 : niTop + niH + 10).toFixed(1)}" text-anchor="middle" fill="${niColor}" font-size="9.5" font-weight="700" class="tabular-nums">${fmtBarVal(ni)}</text>`;

          // 3. Free Cash Flow bar (right)
          if (hasFcf) {
            const fcfX = cx + 0.5 * barW + gap;
            const fcfTop = Math.min(yZero, yScale(fcf));
            const fcfH = Math.max(2, Math.abs(yZero - yScale(fcf)));
            const fcfColor = fcf >= 0 ? "#f59f00" : "#f03e3e";
            html += `<rect x="${fcfX.toFixed(1)}" y="${fcfTop.toFixed(1)}" width="${barW.toFixed(1)}" height="${fcfH.toFixed(1)}" rx="2.5" fill="${fcfColor}"><title>${b.period} Free Cash Flow: $${fcf.toFixed(2)}B</title></rect>`;
            html += `<text x="${(fcfX + barW / 2).toFixed(1)}" y="${(fcf >= 0 ? fcfTop - 4 : fcfTop + fcfH + 10).toFixed(1)}" text-anchor="middle" fill="${fcfColor}" font-size="9.5" font-weight="700" class="tabular-nums">${fmtBarVal(fcf)}</text>`;
          }

          // Period label
          html += `<text x="${cx.toFixed(1)}" y="${H - 8}" text-anchor="middle" fill="var(--text-main)" font-size="11" font-weight="600">${b.period}</text>`;
        });

        earnSvg.innerHTML = html;
      }

      // 2. Render Dedicated Single-Metric Bar Views: Buybacks ($B), Dilution (YoY %), or Dividends ($B)
      const divSvg = document.getElementById("modal-dividends-svg");
      const divSummary = document.getElementById("modal-div-summary");
      const divObj = h.dividends || {
        yield_pct: 0, annual_rate_usd: 0, buyback_yield_pct: 0,
        total_shareholder_yield_pct: 0, cum_dilution_pct: null,
        annual_bars: [], cap_return_bars: [], dilution_bars: []
      };

      const W = 420, H = 175;
      const padL = 46, padR = 12, padT = 22, padB = 28;
      const plotW = W - padL - padR;
      const plotH = H - padT - padB;

      if (state.dividendMode === "buybacks") {
        const bbYield = (divObj.buyback_yield_pct || 0).toFixed(2);
        const dvYield = (divObj.yield_pct || 0).toFixed(2);
        const totYield = (divObj.total_shareholder_yield_pct || 0).toFixed(2);
        divSummary.innerHTML = `
          <span class="inline-flex items-center gap-1 mr-2"><span style="width:8px;height:8px;border-radius:2px;background:#7c3aed;display:inline-block;"></span>Buybacks (${bbYield}%)</span>
          <span class="inline-flex items-center gap-1 mr-2"><span style="width:8px;height:8px;border-radius:2px;background:var(--gain-bar);display:inline-block;"></span>Dividends (${dvYield}%)</span>
          · Total Yield: <strong style="color:var(--gain-fg);">${totYield}%</strong>
        `;

        const capBars = divObj.cap_return_bars || [];
        const hasAny = capBars.some(b => (b.buybacks_bn || 0) > 0 || (b.dividends_bn || 0) > 0);
        if (!capBars.length || !hasAny) {
          divSvg.innerHTML = `<text x="210" y="90" text-anchor="middle" fill="var(--text-muted)" font-size="12">No share buybacks or dividends reported in recent fiscal years</text>`;
        } else {
          const allVals = capBars.flatMap(b => [b.buybacks_bn || 0, b.dividends_bn || 0, 0.5]);
          const maxVal = Math.max(...allVals) * 1.18;
          const yScale = v => padT + plotH - (v / maxVal) * plotH;
          const yZero = padT + plotH;

          let html = "";
          for (let i = 0; i <= 3; i++) {
            const yv = (i / 3) * maxVal;
            const yp = yScale(yv);
            html += `<line x1="${padL}" y1="${yp.toFixed(1)}" x2="${padL + plotW}" y2="${yp.toFixed(1)}" stroke="var(--grid-line)" stroke-width="1" />`;
            html += `<text x="${padL - 6}" y="${(yp + 4).toFixed(1)}" text-anchor="end" fill="var(--text-muted)" font-size="11" class="tabular-nums">$${yv.toFixed(0)}B</text>`;
          }
          html += `<line x1="${padL}" y1="${yZero.toFixed(1)}" x2="${padL + plotW}" y2="${yZero.toFixed(1)}" stroke="var(--border-strong)" stroke-width="1.2" />`;

          const groupW = plotW / capBars.length;
          const barW = Math.min(24, groupW * 0.34);

          capBars.forEach((b, idx) => {
            const cx = padL + (idx + 0.5) * groupW;
            const bb = b.buybacks_bn || 0;
            const dv = b.dividends_bn || 0;

            // Buybacks bar (left, purple)
            const bbTop = yScale(bb);
            const bbH = Math.max(2, yZero - bbTop);
            html += `<rect x="${(cx - barW - 2).toFixed(1)}" y="${bbTop.toFixed(1)}" width="${barW.toFixed(1)}" height="${bbH.toFixed(1)}" rx="3" fill="#7c3aed"><title>${b.period} Buybacks: $${bb.toFixed(2)}B</title></rect>`;
            if (bb > 0.04) {
              html += `<text x="${(cx - barW / 2 - 2).toFixed(1)}" y="${(bbTop - 4).toFixed(1)}" text-anchor="middle" fill="#7c3aed" font-size="10" font-weight="700" class="tabular-nums">$${bb.toFixed(1)}B</text>`;
            }

            // Cash Dividends bar (right, green) — omit $0.0B label when dividends are 0 so it never looks like $0B buybacks!
            const dvTop = yScale(dv);
            const dvH = Math.max(2, yZero - dvTop);
            html += `<rect x="${(cx + 2).toFixed(1)}" y="${dvTop.toFixed(1)}" width="${barW.toFixed(1)}" height="${dvH.toFixed(1)}" rx="3" fill="var(--gain-bar)"><title>${b.period} Dividends: $${dv.toFixed(2)}B</title></rect>`;
            if (dv > 0.04) {
              html += `<text x="${(cx + barW / 2 + 2).toFixed(1)}" y="${(dvTop - 4).toFixed(1)}" text-anchor="middle" fill="var(--gain-fg)" font-size="10" font-weight="700" class="tabular-nums">$${dv.toFixed(1)}B</text>`;
            }

            html += `<text x="${cx.toFixed(1)}" y="${H - 8}" text-anchor="middle" fill="var(--text-main)" font-size="11" font-weight="600">${b.period}</text>`;
          });
          divSvg.innerHTML = html;
        }
      } else if (state.dividendMode === "dilution") {
        const dilBars = divObj.dilution_bars || [];
        const cumPct = divObj.cum_dilution_pct;
        const cumStr = cumPct !== null && cumPct !== undefined
          ? `<strong style="color:${cumPct <= 0 ? 'var(--gain-fg)' : 'var(--loss-fg)'};">${cumPct > 0 ? '+' : ''}${cumPct.toFixed(1)}%</strong> (${cumPct <= 0 ? 'Net Share Reduction' : 'Net Dilution'})`
          : "N/A";
        divSummary.innerHTML = `Multi-Year Share Count Change: ${cumStr} · Green (&lt;0%) = Anti-Dilutive`;

        if (!dilBars.length) {
          divSvg.innerHTML = `<text x="210" y="90" text-anchor="middle" fill="var(--text-muted)" font-size="12">Historical diluted share count series unavailable</text>`;
        } else {
          const vals = dilBars.map(b => b.yoy_pct || 0);
          const absMax = Math.max(1.5, ...vals.map(v => Math.abs(v))) * 1.25;
          const yMin = -absMax, yMax = absMax;
          const yScale = v => padT + plotH - ((v - yMin) / (yMax - yMin)) * plotH;
          const yZero = yScale(0);

          let html = "";
          [-absMax * 0.75, 0, absMax * 0.75].forEach(yv => {
            const yp = yScale(yv);
            html += `<line x1="${padL}" y1="${yp.toFixed(1)}" x2="${padL + plotW}" y2="${yp.toFixed(1)}" stroke="var(--grid-line)" stroke-width="1" />`;
            html += `<text x="${padL - 6}" y="${(yp + 4).toFixed(1)}" text-anchor="end" fill="var(--text-muted)" font-size="11" class="tabular-nums">${yv > 0 ? '+' : ''}${yv.toFixed(1)}%</text>`;
          });
          html += `<line x1="${padL}" y1="${yZero.toFixed(1)}" x2="${padL + plotW}" y2="${yZero.toFixed(1)}" stroke="var(--border-strong)" stroke-width="1.2" />`;

          const groupW = plotW / dilBars.length;
          const barW = Math.min(36, groupW * 0.48);

          dilBars.forEach((b, idx) => {
            const cx = padL + (idx + 0.5) * groupW;
            const pct = b.yoy_pct || 0;
            const bTop = Math.min(yZero, yScale(pct));
            const bH = Math.max(2, Math.abs(yZero - yScale(pct)));
            const barColor = pct <= 0 ? "var(--gain-bar)" : "var(--loss-bar)";
            const txtColor = pct <= 0 ? "var(--gain-fg)" : "var(--loss-fg)";
            const lblY = pct >= 0 ? bTop - 5 : bTop + bH + 11;

            html += `<rect x="${(cx - barW / 2).toFixed(1)}" y="${bTop.toFixed(1)}" width="${barW.toFixed(1)}" height="${bH.toFixed(1)}" rx="3" fill="${barColor}" />`;
            html += `<text x="${cx.toFixed(1)}" y="${lblY.toFixed(1)}" text-anchor="middle" fill="${txtColor}" font-size="11" font-weight="700" class="tabular-nums">${pct > 0 ? '+' : ''}${pct.toFixed(2)}%</text>`;
            html += `<text x="${cx.toFixed(1)}" y="${H - 8}" text-anchor="middle" fill="var(--text-main)" font-size="11" font-weight="600">${b.period}</text>`;
          });
          divSvg.innerHTML = html;
        }
      } else {
        // Annual Dividend Per Share ($/sh)
        const payoutExtra = divObj.payout_ratio_pct ? ` · Payout: ${divObj.payout_ratio_pct.toFixed(1)}%` : "";
        divSummary.innerHTML = `Yield: <strong style="color:var(--gain-fg);">${(divObj.yield_pct || 0).toFixed(2)}%</strong> · Rate: <strong>$${(divObj.annual_rate_usd || 0).toFixed(2)}/sh</strong>${payoutExtra}`;

        const divBars = divObj.annual_bars || [];
        if (!divBars.length) {
          divSvg.innerHTML = `<text x="210" y="90" text-anchor="middle" fill="var(--text-muted)" font-size="12">${h.display_symbol} does not currently pay a cash dividend (0.00% Yield)</text>`;
        } else {
          const maxVal = Math.max(0.1, ...divBars.map(b => b.amount_usd || 0)) * 1.18;
          const yScale = v => padT + plotH - (v / maxVal) * plotH;
          const yZero = padT + plotH;

          let html = "";
          for (let i = 0; i <= 3; i++) {
            const yv = (i / 3) * maxVal;
            const yp = yScale(yv);
            html += `<line x1="${padL}" y1="${yp.toFixed(1)}" x2="${padL + plotW}" y2="${yp.toFixed(1)}" stroke="var(--grid-line)" stroke-width="1" />`;
            html += `<text x="${padL - 6}" y="${(yp + 4).toFixed(1)}" text-anchor="end" fill="var(--text-muted)" font-size="11" class="tabular-nums">$${yv.toFixed(2)}</text>`;
          }
          html += `<line x1="${padL}" y1="${yZero.toFixed(1)}" x2="${padL + plotW}" y2="${yZero.toFixed(1)}" stroke="var(--border-strong)" stroke-width="1.2" />`;

          const groupW = plotW / divBars.length;
          const barW = Math.min(36, groupW * 0.48);

          divBars.forEach((b, idx) => {
            const cx = padL + (idx + 0.5) * groupW;
            const amt = b.amount_usd || 0;
            const bTop = yScale(amt);
            const bH = Math.max(2, yZero - bTop);

            html += `<rect x="${(cx - barW / 2).toFixed(1)}" y="${bTop.toFixed(1)}" width="${barW.toFixed(1)}" height="${bH.toFixed(1)}" rx="4" fill="var(--gain-bar)" />`;
            html += `<text x="${cx.toFixed(1)}" y="${(bTop - 5).toFixed(1)}" text-anchor="middle" fill="var(--gain-fg)" font-size="11" font-weight="700" class="tabular-nums">$${amt.toFixed(2)}</text>`;
            html += `<text x="${cx.toFixed(1)}" y="${H - 8}" text-anchor="middle" fill="var(--text-main)" font-size="11" font-weight="600">${b.period}</text>`;
          });
          divSvg.innerHTML = html;
        }
      }
    }

    function closeModal() {
      document.getElementById("detail-modal").classList.add("hidden");
    }

    function applyPreset(metric, dir) {
      state.activeMetric = metric;
      state.sortDir = dir;
      renderAll();
    }

    function setMetric(metric) {
      state.activeMetric = metric;
      const meta = METRIC_META[metric];
      if (meta && meta.defaultDir) {
        state.sortDir = meta.defaultDir;
      }
      renderAll();
    }

    function toggleSortDir() {
      state.sortDir = state.sortDir === "asc" ? "desc" : "asc";
      renderAll();
    }

    function sortTableBy(metric) {
      if (state.activeMetric === metric) {
        state.sortDir = state.sortDir === "asc" ? "desc" : "asc";
      } else {
        state.activeMetric = metric;
        const meta = METRIC_META[metric];
        state.sortDir = (meta && meta.defaultDir) ? meta.defaultDir : "desc";
      }
      renderAll();
    }

    function setScope(scope) {
      state.scope = scope;
      document.getElementById("scope-all").classList.toggle("active", scope === "all");
      document.getElementById("scope-core").classList.toggle("active", scope === "core");
      renderAll();
    }

    function setSegment(seg) {
      state.segment = seg;
      ["ALL", "HBM Memory", "Hyperscalers", "AI Semis & Infra"].forEach(s => {
        const el = document.getElementById("seg-" + s);
        if (el) el.classList.toggle("active", s === seg);
      });
      renderAll();
    }

    function setViewMode(mode) {
      state.viewMode = mode;
      ["all", "bars", "scatter", "table", "compare"].forEach(m => {
        const el = document.getElementById("view-" + m);
        if (el) el.classList.toggle("active", m === mode);
      });

      const comparePanel = document.getElementById("panel-compare");
      const grid = document.getElementById("charts-grid");
      const bars = document.getElementById("panel-bars");
      const scatter = document.getElementById("panel-scatter");
      const table = document.getElementById("panel-table");

      // Set base layout classes FIRST before toggling .hidden so .hidden is never overwritten!
      bars.className = mode === "bars"
        ? "xl:col-span-12 gf-card p-5 flex flex-col"
        : "xl:col-span-7 gf-card p-5 flex flex-col";

      scatter.className = mode === "scatter"
        ? "xl:col-span-12 gf-card p-5 flex flex-col justify-between"
        : "xl:col-span-5 gf-card p-5 flex flex-col justify-between";

      // Now toggle visibility cleanly:
      // Note: 'all' shows Overview (Ranked Bars + Scatter + Table) and hides Interactive Chart (#panel-compare)
      comparePanel.classList.toggle("hidden", mode !== "compare");
      grid.classList.toggle("hidden", mode === "table" || mode === "compare");
      bars.classList.toggle("hidden", mode !== "all" && mode !== "bars");
      scatter.classList.toggle("hidden", mode !== "all" && mode !== "scatter");
      table.classList.toggle("hidden", mode !== "all" && mode !== "table");

      renderAll();
    }

    function onSearchInput(val) {
      state.search = val.trim();
      renderAll();
    }

    function togglePositivePeOnly(checked) {
      state.positivePeOnly = checked;
      renderAll();
    }

    function renderAll() {
      const items = getFilteredHoldings();
      renderKpiStrip(items);
      if (state.viewMode === "compare") {
        renderMainComparisonChart();
      }
      if (state.viewMode === "all" || state.viewMode === "bars") {
        renderRankedBars(items);
      }
      if (state.viewMode === "all" || state.viewMode === "scatter") {
        renderScatter();
      }
      if (state.viewMode === "all" || state.viewMode === "table") {
        renderTable(items);
      }
    }

    (function init() {
      const allCount = PORTFOLIO_DATA.holdings.length;
      const coreCount = PORTFOLIO_DATA.holdings.filter(h => h.is_core).length;
      document.getElementById("count-all").textContent = allCount;
      document.getElementById("count-core").textContent = coreCount;
      const latestDate = PORTFOLIO_DATA.holdings.map(h => h.as_of_date).sort().pop() || PORTFOLIO_DATA.generated_at;
      document.getElementById("as-of-label").textContent = latestDate;
      setTheme("light");
    })();
  </script>
</body>
</html>
"""


def build_html() -> str:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    data["holdings"] = [
        h for h in data.get("holdings", [])
        if (h.get("market_cap_usd_bn") or 0) >= 150
    ]
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    for h in data.get("holdings", []):
        as_of = h.get("as_of_date", "9999-99-99")
        if "chart_history" in h:
            cleaned = [pt for pt in h["chart_history"] if pt["d"] <= as_of]
            h["chart_history"] = sorted(cleaned, key=lambda x: x["d"])
    json_str = json.dumps(data, separators=(",", ":"))
    html_content = HTML_TEMPLATE.replace("__PORTFOLIO_JSON_PLACEHOLDER__", json_str)
    with open(LOCAL_HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html_content)
    with open(INDEX_HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Generated interactive dashboard ({len(data['holdings'])} holdings >= $150B) at: {LOCAL_HTML_PATH} and {INDEX_HTML_PATH}")
    return html_content


if __name__ == "__main__":
    build_html()
