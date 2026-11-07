"""
Fetches market valuation metrics and 5-year closing price history
for all companies in portfolio_config.json (Market Cap >= $150B):
  - Daily (1D) granularity for the last 1 year, Weekly (1W-FRI) for years 2-5
  - USD-adjusted prices, 52W & 5Y drawdowns, historical Market Cap & Trailing P/E
  - Quarterly & Annual Earnings bars (Revenue & Net Income in USD $B, plus EPS)
  - Historical Dividend bars (Annual & Quarterly dividends in USD + Yield %)
  - Direct links to Google Finance and Yahoo Finance
"""

import datetime
import json
import math
from pathlib import Path
import pandas as pd
import yfinance as yf

PROJECT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = PROJECT_DIR / "portfolio_config.json"
DATA_OUTPUT_PATH = PROJECT_DIR / "portfolio_data.json"


def safe_float(val, decimals=2):
    if val is None:
        return None
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return None
        return round(f, decimals)
    except (ValueError, TypeError):
        return None


def fetch_fx_series(currency: str, fx_cache: dict) -> pd.Series | None:
    """Fetches daily USD -> Foreign Currency exchange rate (e.g. KRW=X)."""
    if currency == "USD":
        return None
    if currency not in fx_cache:
        fx_ticker = f"{currency}=X"
        print(f"Fetching FX history for {fx_ticker}...")
        hist = yf.Ticker(fx_ticker).history(period="5y", interval="1d")
        if hist.empty:
            raise RuntimeError(f"Could not fetch FX series for {fx_ticker}")
        s = hist["Close"].dropna().copy()
        s.index = pd.to_datetime(s.index).tz_localize(None).normalize()
        s = s[~s.index.duplicated(keep="last")].sort_index()
        fx_cache[currency] = s
    return fx_cache[currency]


def compute_horizon_return(s_usd: pd.Series, latest_date: pd.Timestamp, years: int) -> float | None:
    """Computes percentage return over N years using daily closing USD prices."""
    target_date = latest_date - pd.DateOffset(years=years)
    if s_usd.index[0] > target_date + pd.Timedelta(days=20):
        return None
    sub = s_usd[s_usd.index <= target_date]
    base_val = float(sub.iloc[-1]) if len(sub) > 0 else float(s_usd.iloc[0])
    if base_val <= 0:
        return None
    latest_val = float(s_usd.iloc[-1])
    return safe_float(((latest_val - base_val) / base_val) * 100.0, 2)


def get_google_finance_url(ticker: str, exchange: str) -> str:
    if ticker.endswith(".KS"):
        code = ticker.split(".")[0]
        return f"https://www.google.com/finance/quote/{code}:KRX"
    ex_map = {
        "NMS": "NASDAQ",
        "NGM": "NASDAQ",
        "NCM": "NASDAQ",
        "NAS": "NASDAQ",
        "NYQ": "NYSE",
        "NYS": "NYSE",
    }
    gf_ex = ex_map.get(exchange, "NASDAQ")
    return f"https://www.google.com/finance/quote/{ticker}:{gf_ex}"


def extract_earnings_bars(t: yf.Ticker, fin_fx: float) -> dict:
    """Extracts Quarterly and Annual Revenue, Net Income & Free Cash Flow (in USD $B) for bar charts."""
    quarterly = []
    annual = []

    def extract_fcf_map(cf_df) -> dict:
        """Maps (year, month) -> Free Cash Flow in USD $B from a cashflow DataFrame."""
        fcf_map = {}
        if cf_df is None or cf_df.empty:
            return fcf_map
        fcf_key = next((k for k in ["Free Cash Flow"] if k in cf_df.index), None)
        ocf_key = next((k for k in ["Operating Cash Flow", "Cash Flow From Continuing Operating Activities"] if k in cf_df.index), None)
        capex_key = next((k for k in ["Capital Expenditure", "Purchase Of PPE", "Net PPE Purchase And Sale"] if k in cf_df.index), None)

        for col in cf_df.columns:
            ts = pd.to_datetime(col)
            val = None
            if fcf_key is not None and pd.notna(cf_df.loc[fcf_key, col]):
                val = float(cf_df.loc[fcf_key, col])
            elif ocf_key is not None and pd.notna(cf_df.loc[ocf_key, col]):
                ocf = float(cf_df.loc[ocf_key, col])
                capex = float(cf_df.loc[capex_key, col]) if (capex_key is not None and pd.notna(cf_df.loc[capex_key, col])) else 0.0
                val = ocf + capex if capex <= 0 else ocf - capex
            if val is not None:
                fcf_map[(ts.year, ts.month)] = safe_float((val / fin_fx) / 1e9, 2)
        return fcf_map

    def parse_stmt(df, cf_df, is_quarterly=False):
        out = []
        if df is None or df.empty:
            return out
        fcf_map = extract_fcf_map(cf_df)
        rev_key = next((k for k in ["Total Revenue", "Operating Revenue"] if k in df.index), None)
        ni_key = next((k for k in ["Net Income Common Stockholders", "Net Income", "Normalized Income"] if k in df.index), None)
        eps_key = next((k for k in ["Diluted EPS", "Basic EPS"] if k in df.index), None)

        cols = sorted(list(df.columns))
        if is_quarterly:
            cols = cols[-5:]  # last 5 quarters
        else:
            cols = cols[-4:]  # last 4 fiscal years

        for col in cols:
            ts = pd.to_datetime(col)
            rev = df.loc[rev_key, col] if rev_key is not None else None
            ni = df.loc[ni_key, col] if ni_key is not None else None
            eps = df.loc[eps_key, col] if eps_key is not None else None

            rev_usd_bn = safe_float((float(rev) / fin_fx) / 1e9, 2) if pd.notna(rev) else None
            ni_usd_bn = safe_float((float(ni) / fin_fx) / 1e9, 2) if pd.notna(ni) else None
            eps_usd = safe_float(float(eps) / fin_fx, 2) if pd.notna(eps) else None
            fcf_usd_bn = fcf_map.get((ts.year, ts.month))

            if rev_usd_bn is None and ni_usd_bn is None:
                continue

            if is_quarterly:
                q_num = (ts.month - 1) // 3 + 1
                label = f"Q{q_num} '{str(ts.year)[-2:]}"
            else:
                label = f"FY{ts.year}"

            out.append({
                "period": label,
                "date": ts.strftime("%Y-%m-%d"),
                "revenue_bn": rev_usd_bn,
                "net_income_bn": ni_usd_bn,
                "fcf_bn": fcf_usd_bn,
                "eps_usd": eps_usd,
            })
        return out

    try:
        quarterly = parse_stmt(t.quarterly_income_stmt, t.quarterly_cashflow, is_quarterly=True)
    except Exception:
        pass

    try:
        annual = parse_stmt(t.income_stmt, t.cashflow, is_quarterly=False)
        # If the latest completed fiscal year is < 2026 (e.g. FY2025 for Dec year-end companies),
        # append a '2026 TTM' bar from the last 4 reported quarters so 2026 is always included!
        if annual and not any("2026" in b["period"] for b in annual) and len(quarterly) >= 4:
            last4 = quarterly[-4:]
            if "26" in last4[-1]["period"]:
                ttm_rev = sum(q["revenue_bn"] or 0.0 for q in last4)
                ttm_ni = sum(q["net_income_bn"] or 0.0 for q in last4)
                has_fcf = any(q.get("fcf_bn") is not None for q in last4)
                ttm_fcf = sum(q.get("fcf_bn") or 0.0 for q in last4) if has_fcf else None
                ttm_eps = sum(q["eps_usd"] or 0.0 for q in last4) if all(q["eps_usd"] is not None for q in last4) else None
                annual.append({
                    "period": "2026 TTM",
                    "date": last4[-1]["date"],
                    "revenue_bn": safe_float(ttm_rev, 2),
                    "net_income_bn": safe_float(ttm_ni, 2),
                    "fcf_bn": safe_float(ttm_fcf, 2) if ttm_fcf is not None else None,
                    "eps_usd": safe_float(ttm_eps, 2),
                })
                annual = annual[-5:]
    except Exception:
        pass

    return {"quarterly": quarterly, "annual": annual}


def extract_dividend_bars(t: yf.Ticker, info: dict, latest_fx: float, fin_fx: float, price_usd: float, mcap_usd_bn: float | None) -> dict:
    """
    Extracts:
      1. Annual Dividends per share (in USD)
      2. Annual Capital Return ($B USD): Share Buybacks ($B) & Cash Dividends Paid ($B)
      3. Annual Share Count & YoY Dilution / Reduction (%)
    """
    annual_bars = []
    try:
        divs = t.dividends
        if divs is not None and not divs.empty:
            s_div = divs.dropna().copy()
            s_div.index = pd.to_datetime(s_div.index).tz_localize(None).normalize()
            s_div_usd = s_div / latest_fx

            current_yr = datetime.date.today().year
            by_yr = s_div_usd.groupby(s_div_usd.index.year).sum()
            for yr in range(current_yr - 4, current_yr + 1):
                val = float(by_yr.get(yr, 0.0))
                if val > 0 or len(annual_bars) > 0:
                    annual_bars.append({
                        "period": str(yr),
                        "amount_usd": safe_float(val, 2),
                    })
    except Exception:
        pass

    # Extract Annual Buybacks ($B) and Cash Dividends Paid ($B) from Cashflow Statement
    cap_return_bars = []
    latest_buyback_bn = 0.0
    try:
        cf = t.cashflow
        if cf is not None and not cf.empty:
            bb_key = next((k for k in ["Repurchase Of Capital Stock", "Common Stock Payments"] if k in cf.index), None)
            dv_key = next((k for k in ["Cash Dividends Paid", "Common Stock Dividend Paid"] if k in cf.index), None)
            sbc_key = next((k for k in ["Stock Based Compensation"] if k in cf.index), None)

            cols = sorted(list(cf.columns))[-4:]
            for col in cols:
                ts = pd.to_datetime(col)
                raw_bb = cf.loc[bb_key, col] if bb_key is not None else 0.0
                raw_dv = cf.loc[dv_key, col] if dv_key is not None else 0.0
                raw_sbc = cf.loc[sbc_key, col] if sbc_key is not None else 0.0

                # Repurchases and dividends paid are negative cash outflows in cashflow statement
                bb_bn = max(0.0, -(float(raw_bb) / fin_fx) / 1e9) if pd.notna(raw_bb) else 0.0
                dv_bn = max(0.0, -(float(raw_dv) / fin_fx) / 1e9) if pd.notna(raw_dv) else 0.0
                sbc_bn = max(0.0, (float(raw_sbc) / fin_fx) / 1e9) if pd.notna(raw_sbc) else 0.0

                cap_return_bars.append({
                    "period": f"FY{ts.year}",
                    "buybacks_bn": safe_float(bb_bn, 2) or 0.0,
                    "dividends_bn": safe_float(dv_bn, 2) or 0.0,
                    "sbc_bn": safe_float(sbc_bn, 2) or 0.0,
                })
            if cap_return_bars:
                latest_buyback_bn = cap_return_bars[-1]["buybacks_bn"] or 0.0

        # If latest annual cashflow column is < 2026 (e.g. FY2025), append '2026 TTM' from quarterly_cashflow
        if cap_return_bars and not any("2026" in b["period"] for b in cap_return_bars):
            qcf = t.quarterly_cashflow
            if qcf is not None and not qcf.empty:
                qcols = sorted(list(qcf.columns))[-4:]
                if qcols and pd.to_datetime(qcols[-1]).year >= 2026:
                    bb_key = next((k for k in ["Repurchase Of Capital Stock", "Common Stock Payments"] if k in qcf.index), None)
                    dv_key = next((k for k in ["Cash Dividends Paid", "Common Stock Dividend Paid"] if k in qcf.index), None)
                    sbc_key = next((k for k in ["Stock Based Compensation"] if k in qcf.index), None)

                    ttm_bb = 0.0
                    ttm_dv = 0.0
                    ttm_sbc = 0.0
                    for qc in qcols:
                        r_bb = qcf.loc[bb_key, qc] if bb_key is not None else 0.0
                        r_dv = qcf.loc[dv_key, qc] if dv_key is not None else 0.0
                        r_sbc = qcf.loc[sbc_key, qc] if sbc_key is not None else 0.0
                        if pd.notna(r_bb):
                            ttm_bb += max(0.0, -(float(r_bb) / fin_fx) / 1e9)
                        if pd.notna(r_dv):
                            ttm_dv += max(0.0, -(float(r_dv) / fin_fx) / 1e9)
                        if pd.notna(r_sbc):
                            ttm_sbc += max(0.0, (float(r_sbc) / fin_fx) / 1e9)

                    # Fallback for dividends if quarterly cashflow omits Cash Dividends Paid (e.g. 000660.KS)
                    if ttm_dv == 0.0 and cap_return_bars[-1]["dividends_bn"] > 0:
                        ttm_dv = cap_return_bars[-1]["dividends_bn"]

                    cap_return_bars.append({
                        "period": "2026 TTM",
                        "buybacks_bn": safe_float(ttm_bb, 2) or 0.0,
                        "dividends_bn": safe_float(ttm_dv, 2) or 0.0,
                        "sbc_bn": safe_float(ttm_sbc, 2) or 0.0,
                    })
                    cap_return_bars = cap_return_bars[-5:]
                    if ttm_bb > 0:
                        latest_buyback_bn = safe_float(ttm_bb, 2) or latest_buyback_bn
    except Exception:
        pass

    # Extract Diluted Share Count & YoY Dilution / Reduction (%)
    dilution_bars = []
    cum_dilution_pct = None
    try:
        inc = t.income_stmt
        bs = t.balance_sheet
        s_shares = None
        if inc is not None and not inc.empty:
            sh_key = next((k for k in ["Diluted Average Shares", "Basic Average Shares"] if k in inc.index), None)
            if sh_key:
                s_shares = inc.loc[sh_key].dropna().sort_index()
        if (s_shares is None or len(s_shares) < 2) and bs is not None and not bs.empty:
            sh_key = next((k for k in ["Ordinary Shares Number", "Share Issued"] if k in bs.index), None)
            if sh_key:
                s_shares = bs.loc[sh_key].dropna().sort_index()

        if s_shares is not None and len(s_shares) >= 2:
            s_shares.index = pd.to_datetime(s_shares.index).tz_localize(None)
            s_shares = s_shares.sort_index()

            # Prepend prior fiscal year's baseline share count so the first fiscal year in income_stmt (e.g. FY2022)
            # also has a YoY dilution bar matching cap_return_bars!
            first_dt = pd.to_datetime(s_shares.index[0])
            prev_dt = first_dt - pd.DateOffset(years=1)
            est_prev_sh = None
            try:
                sf = t.get_shares_full(start=f"{prev_dt.year - 1}-01-01")
                if sf is not None and not sf.empty:
                    sf = sf.dropna().astype(float).copy()
                    sf.index = pd.to_datetime(sf.index).tz_localize(None)
                    sf = sf[~sf.index.duplicated(keep="last")].sort_index()
                    sp = t.splits
                    if sp is not None and not sp.empty:
                        sp.index = pd.to_datetime(sp.index).tz_localize(None)
                        for sdt, ratio in sp.items():
                            if ratio and float(ratio) > 0:
                                sf.loc[sf.index < sdt] = sf.loc[sf.index < sdt] * float(ratio)
                    sub_prev = sf[(sf.index > prev_dt - pd.DateOffset(months=12)) & (sf.index <= prev_dt + pd.DateOffset(months=2))]
                    sub_curr = sf[(sf.index > first_dt - pd.DateOffset(months=12)) & (sf.index <= first_dt + pd.DateOffset(months=2))]
                    if not sub_prev.empty and not sub_curr.empty and float(sub_curr.median()) > 0:
                        rel_ratio = float(sub_prev.median()) / float(sub_curr.median())
                        if 0.75 <= rel_ratio <= 1.35:
                            est_prev_sh = float(s_shares.iloc[0]) * rel_ratio
            except Exception:
                pass

            if est_prev_sh is None and cap_return_bars and mcap_usd_bn and mcap_usd_bn > 0:
                first_cap = next((b for b in cap_return_bars if b["period"] == f"FY{first_dt.year}"), None)
                if first_cap is not None:
                    net_issuance_bn = (first_cap.get("sbc_bn") or 0.0) - (first_cap.get("buybacks_bn") or 0.0)
                    est_yoy_frac = max(-0.08, min(0.08, net_issuance_bn / (mcap_usd_bn * 0.45)))
                    est_prev_sh = float(s_shares.iloc[0]) / (1.0 + est_yoy_frac)

            if est_prev_sh is not None and est_prev_sh > 0:
                s_shares.loc[prev_dt] = est_prev_sh
                s_shares = s_shares.sort_index()

            # Also check if latest annual share count is < 2026; if so, append latest 2026 quarterly diluted shares
            qinc = t.quarterly_income_stmt
            if pd.to_datetime(s_shares.index[-1]).year < 2026 and qinc is not None and not qinc.empty:
                qsh_key = next((k for k in ["Diluted Average Shares", "Basic Average Shares"] if k in qinc.index), None)
                if qsh_key:
                    qs = qinc.loc[qsh_key].dropna().sort_index()
                    if len(qs) > 0 and pd.to_datetime(qs.index[-1]).year >= 2026:
                        s_shares.loc[pd.to_datetime(qs.index[-1]).tz_localize(None)] = qs.iloc[-1]
                        s_shares = s_shares.sort_index()

            items = list(s_shares.items())[-6:]
            first_sh = float(items[0][1])
            last_sh = float(items[-1][1])
            if first_sh > 0:
                cum_dilution_pct = safe_float(((last_sh - first_sh) / first_sh) * 100.0, 2)

            for i in range(1, len(items)):
                prev_sh = float(items[i - 1][1])
                curr_dt, curr_sh = items[i][0], float(items[i][1])
                ts = pd.to_datetime(curr_dt)
                yoy_pct = ((curr_sh - prev_sh) / prev_sh) * 100.0 if prev_sh > 0 else 0.0
                lbl = "2026 YTD" if (ts.year == 2026 and ts.month != 12 and i == len(items) - 1 and pd.to_datetime(items[i-1][0]).month == 12) else f"FY{ts.year}"
                dilution_bars.append({
                    "period": lbl,
                    "shares_bn": safe_float(curr_sh / 1e9, 3),
                    "yoy_pct": safe_float(yoy_pct, 2) or 0.0,
                })
            dilution_bars = dilution_bars[-5:]
    except Exception:
        pass

    raw_rate = info.get("dividendRate") or info.get("trailingAnnualDividendRate")
    rate_usd = safe_float(float(raw_rate) / latest_fx, 2) if raw_rate else None
    yield_pct = 0.0
    if rate_usd and price_usd > 0:
        yield_pct = safe_float((rate_usd / price_usd) * 100.0, 2) or 0.0
    elif info.get("trailingAnnualDividendYield"):
        yield_pct = safe_float(float(info.get("trailingAnnualDividendYield")) * 100.0, 2) or 0.0

    buyback_yield_pct = 0.0
    if mcap_usd_bn and mcap_usd_bn > 0 and latest_buyback_bn > 0:
        buyback_yield_pct = safe_float((latest_buyback_bn / mcap_usd_bn) * 100.0, 2) or 0.0

    payout = info.get("payoutRatio")
    payout_pct = safe_float(float(payout) * 100.0, 1) if payout else None

    return {
        "yield_pct": yield_pct,
        "annual_rate_usd": rate_usd or 0.0,
        "payout_ratio_pct": payout_pct,
        "buyback_yield_pct": buyback_yield_pct,
        "latest_buyback_bn": safe_float(latest_buyback_bn, 2) or 0.0,
        "total_shareholder_yield_pct": safe_float(yield_pct + buyback_yield_pct, 2) or 0.0,
        "cum_dilution_pct": cum_dilution_pct,
        "annual_bars": annual_bars,
        "cap_return_bars": cap_return_bars,
        "dilution_bars": dilution_bars,
    }


def build_historical_ttm_earnings_bn(
    t: yf.Ticker,
    target_index: pd.DatetimeIndex,
    mcap_usd_bn: float | None,
    trailing_pe: float | None,
    fin_fx_to_usd: float,
) -> pd.Series | None:
    pts = {}
    try:
        inc = t.income_stmt
        if inc is not None and not inc.empty:
            row_key = next((k for k in ["Net Income Common Stockholders", "Net Income", "Normalized Income"] if k in inc.index), None)
            if row_key:
                for dt, val in inc.loc[row_key].dropna().items():
                    ts = pd.to_datetime(dt).tz_localize(None).normalize()
                    pts[ts] = (float(val) / fin_fx_to_usd) / 1e9
    except Exception:
        pass

    try:
        qinc = t.quarterly_income_stmt
        if qinc is not None and not qinc.empty:
            row_key = next((k for k in ["Net Income Common Stockholders", "Net Income", "Normalized Income"] if k in qinc.index), None)
            if row_key:
                s_q = qinc.loc[row_key].dropna().sort_index()
                if len(s_q) >= 4:
                    for dt, val in s_q.rolling(4).sum().dropna().items():
                        ts = pd.to_datetime(dt).tz_localize(None).normalize()
                        pts[ts] = (float(val) / fin_fx_to_usd) / 1e9
    except Exception:
        pass

    if mcap_usd_bn and trailing_pe and trailing_pe != 0:
        pts[target_index[-1]] = mcap_usd_bn / trailing_pe

    if not pts:
        return None

    s_earn = pd.Series(pts).sort_index()
    s_earn = s_earn[~s_earn.index.duplicated(keep="last")]
    combined = s_earn.reindex(s_earn.index.union(target_index)).sort_index()
    combined = combined.interpolate(method="time").bfill().ffill()
    return combined.reindex(target_index)


def fetch_all_portfolio_data() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)

    fx_cache = {}
    records = []

    for item in config["holdings"]:
        ticker_sym = item["ticker"]
        print(f"Processing {ticker_sym} ({item['name']})...")
        t = yf.Ticker(ticker_sym)
        info = t.info or {}

        currency = info.get("currency", "USD")
        fin_currency = info.get("financialCurrency", currency)
        exchange = info.get("exchange", "NMS")

        hist = t.history(period="5y", interval="1d", auto_adjust=False)
        if hist.empty or "Close" not in hist:
            print(f"  WARNING: No price history found for {ticker_sym}, skipping.")
            continue

        s_native = hist["Close"].dropna().copy()
        s_native.index = pd.to_datetime(s_native.index).tz_localize(None).normalize()
        s_native = s_native[~s_native.index.duplicated(keep="last")].sort_index()

        if currency != "USD":
            fx_series = fetch_fx_series(currency, fx_cache)
            aligned_fx = fx_series.reindex(s_native.index).ffill().bfill()
            s_usd = s_native / aligned_fx
            latest_fx = float(aligned_fx.iloc[-1])
        else:
            s_usd = s_native.copy()
            latest_fx = 1.0

        fin_fx = latest_fx
        if fin_currency != "USD" and fin_currency != currency:
            try:
                fin_fx_series = fetch_fx_series(fin_currency, fx_cache)
                fin_fx = float(fin_fx_series.iloc[-1])
            except Exception:
                fin_fx = 1.0

        latest_date = s_usd.index[-1]
        price_native = float(s_native.iloc[-1])
        price_usd = float(s_usd.iloc[-1])

        raw_mcap = info.get("marketCap")
        mcap_usd_bn = None
        if raw_mcap:
            mcap_usd_bn = safe_float((float(raw_mcap) / latest_fx) / 1e9, 2)

        min_mcap = config.get("min_market_cap_usd_bn", 150)
        if mcap_usd_bn is not None and mcap_usd_bn < min_mcap:
            print(f"  Skipping {ticker_sym}: Market Cap ${mcap_usd_bn}B is below ${min_mcap}B threshold.")
            continue

        # Valuation: Trailing P/E & Forward P/E
        trailing_pe = safe_float(info.get("trailingPE"), 2)
        pe_note = "Reported TTM P/E"
        if trailing_pe is None:
            net_inc = info.get("netIncomeToCommon")
            if raw_mcap and net_inc and currency == fin_currency and float(net_inc) > 0:
                trailing_pe = safe_float(float(raw_mcap) / float(net_inc), 2)
                pe_note = "Computed (Market Cap / TTM Net Income)"
            else:
                t_eps = info.get("trailingEps") or info.get("epsTrailingTwelveMonths")
                if t_eps and float(t_eps) < 0:
                    trailing_pe = safe_float(price_native / float(t_eps), 2)
                    pe_note = "Negative TTM EPS (Unprofitable TTM)"
                else:
                    pe_note = "N/A"

        forward_pe = safe_float(info.get("forwardPE"), 2)
        current_yr_pe = safe_float(info.get("priceEpsCurrentYear"), 2)
        peg_ratio = safe_float(info.get("pegRatio") or info.get("trailingPegRatio"), 2)

        # 52-Week High & Drawdown (Daily Close in USD)
        cutoff_52w = latest_date - pd.DateOffset(days=365)
        s_52w_usd = s_usd[s_usd.index >= cutoff_52w]
        s_52w_native = s_native[s_native.index >= cutoff_52w]

        peak_52w_usd = float(s_52w_usd.max())
        peak_52w_idx = s_52w_usd.idxmax()
        peak_52w_date = peak_52w_idx.strftime("%Y-%m-%d")
        peak_52w_native = float(s_52w_native.loc[peak_52w_idx])
        drawdown_52w_pct = safe_float(((price_usd - peak_52w_usd) / peak_52w_usd) * 100.0, 2)

        # 5-Year High & Drawdown (Daily Close in USD)
        peak_5y_usd = float(s_usd.max())
        peak_5y_idx = s_usd.idxmax()
        peak_5y_date = peak_5y_idx.strftime("%Y-%m-%d")
        drawdown_5y_pct = safe_float(((price_usd - peak_5y_usd) / peak_5y_usd) * 100.0, 2)

        # YTD Return (USD)
        ytd_base_slice = s_usd[s_usd.index < pd.Timestamp(f"{latest_date.year}-01-01")]
        ytd_base = float(ytd_base_slice.iloc[-1]) if len(ytd_base_slice) > 0 else float(s_usd.iloc[0])
        return_ytd = safe_float(((price_usd - ytd_base) / ytd_base) * 100.0, 2)

        # 1Y, 2Y, 3Y, 5Y Returns (USD)
        return_1y = compute_horizon_return(s_usd, latest_date, 1)
        return_2y = compute_horizon_return(s_usd, latest_date, 2)
        return_3y = compute_horizon_return(s_usd, latest_date, 3)
        return_5y = compute_horizon_return(s_usd, latest_date, 5)

        # Compute full daily 52W rolling drawdown and 5Y running drawdown on s_usd BEFORE sampling
        rolling_52w_max = s_usd.rolling("365D", min_periods=1).max()
        dd_52w_daily = ((s_usd - rolling_52w_max) / rolling_52w_max) * 100.0

        running_5y_max = s_usd.cummax()
        dd_5y_daily = ((s_usd - running_5y_max) / running_5y_max) * 100.0

        # Hybrid Granularity:
        #   - Older than 1 year: Weekly Friday closes (1W-FRI)
        #   - Last 1 year (>= cutoff_52w): Daily trading closes (1D)
        s_older = s_usd[s_usd.index < cutoff_52w].resample("1W-FRI").last().dropna()
        s_recent = s_usd[s_usd.index >= cutoff_52w]
        combined_idx = s_older.index.union(s_recent.index).sort_values()
        sampled_usd = s_usd.reindex(combined_idx).dropna()

        mcap_series = None
        if mcap_usd_bn and price_usd > 0:
            mcap_series = mcap_usd_bn * (sampled_usd / price_usd)

        earn_series = build_historical_ttm_earnings_bn(
            t, sampled_usd.index, mcap_usd_bn, trailing_pe, fin_fx
        )

        chart_history = []
        for idx, val in sampled_usd.items():
            mc_val = safe_float(mcap_series.loc[idx], 1) if mcap_series is not None else None
            pe_val = None
            if mc_val is not None and earn_series is not None:
                e_val = earn_series.loc[idx]
                if e_val and e_val > 0.05:
                    raw_pe = mc_val / e_val
                    if 0 < raw_pe <= 260:
                        pe_val = safe_float(raw_pe, 1)
            chart_history.append({
                "d": idx.strftime("%Y-%m-%d"),
                "p": safe_float(val, 2),
                "dd52": safe_float(dd_52w_daily.loc[idx], 1),
                "dd": safe_float(dd_5y_daily.loc[idx], 1),
                "mc": mc_val,
                "pe": pe_val,
            })

        earnings_data = extract_earnings_bars(t, fin_fx)
        dividend_data = extract_dividend_bars(t, info, latest_fx, fin_fx, price_usd, mcap_usd_bn)

        records.append({
            "ticker": ticker_sym,
            "display_symbol": item.get("display_symbol", ticker_sym),
            "name": item["name"],
            "segment": item["segment"],
            "sub_role": item.get("sub_role", ""),
            "is_core": bool(item.get("is_core", False)),
            "currency": currency,
            "fx_rate_to_usd": safe_float(latest_fx, 4),
            "price_native": safe_float(price_native, 2),
            "price_usd": safe_float(price_usd, 2),
            "market_cap_usd_bn": mcap_usd_bn,
            "trailing_pe": trailing_pe,
            "pe_note": pe_note,
            "forward_pe": forward_pe,
            "current_yr_pe": current_yr_pe,
            "peg_ratio": peg_ratio,
            "peak_52w_usd": safe_float(peak_52w_usd, 2),
            "peak_52w_native": safe_float(peak_52w_native, 2),
            "peak_52w_date": peak_52w_date,
            "drawdown_52w_pct": drawdown_52w_pct,
            "peak_5y_usd": safe_float(peak_5y_usd, 2),
            "peak_5y_date": peak_5y_date,
            "drawdown_5y_pct": drawdown_5y_pct,
            "return_ytd": return_ytd,
            "return_1y": return_1y,
            "return_2y": return_2y,
            "return_3y": return_3y,
            "return_5y": return_5y,
            "as_of_date": latest_date.strftime("%Y-%m-%d"),
            "yahoo_finance_url": f"https://finance.yahoo.com/quote/{ticker_sym}",
            "google_finance_url": get_google_finance_url(ticker_sym, exchange),
            "earnings": earnings_data,
            "dividends": dividend_data,
            "chart_history": chart_history,
        })

    payload = {
        "portfolio_name": config.get("portfolio_name", "HBM & Hyperscalers Portfolio"),
        "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "base_currency": "USD",
        "segments": config.get("segments", []),
        "holdings": records,
    }

    with open(DATA_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(f"\nSaved {len(records)} holdings to {DATA_OUTPUT_PATH}")
    return payload


if __name__ == "__main__":
    fetch_all_portfolio_data()
