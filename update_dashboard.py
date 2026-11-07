"""
One-step script to manage the persisted company list in portfolio_config.json,
refresh market data via yfinance, and rebuild dashboard.html.

Usage:
  python update_dashboard.py
  python update_dashboard.py --add KLAC --name "KLA Corp" --segment "HBM Memory" --role "Process Control & Wafer Inspection"
"""

import argparse
import json
from pathlib import Path
from fetch_portfolio_data import CONFIG_PATH, fetch_all_portfolio_data
from build_dashboard import build_html

ARTIFACT_HTML_PATH = Path(r"C:\Users\Denis\.gemini\antigravity\brain\30114e2a-1a15-474e-a21c-4e325c7351ea\hbm_hyperscalers_dashboard.html")


def add_holding_to_config(ticker: str, name: str, segment: str, sub_role: str, is_core: bool = False):
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    existing = [h for h in cfg["holdings"] if h["ticker"].upper() == ticker.upper()]
    if existing:
        existing[0]["name"] = name or existing[0]["name"]
        existing[0]["segment"] = segment or existing[0]["segment"]
        existing[0]["sub_role"] = sub_role or existing[0]["sub_role"]
        print(f"Updated existing ticker {ticker} in {CONFIG_PATH}")
    else:
        cfg["holdings"].append({
            "ticker": ticker,
            "display_symbol": ticker.split(".")[0],
            "name": name or ticker,
            "segment": segment,
            "sub_role": sub_role,
            "is_core": is_core,
        })
        print(f"Added {ticker} ({name}) to {CONFIG_PATH}")

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Refresh HBM & Hyperscalers portfolio data and HTML dashboard.")
    parser.add_argument("--add", help="Ticker symbol to add/update in portfolio_config.json (e.g. KLAC, 6857.T)")
    parser.add_argument("--name", default="", help="Company display name")
    parser.add_argument("--segment", default="AI Semis & Infra", choices=["HBM Memory", "Hyperscalers", "AI Semis & Infra"])
    parser.add_argument("--role", default="", help="Short description of HBM/AI role")
    parser.add_argument("--skip-fetch", action="store_true", help="Rebuild HTML from existing portfolio_data.json without re-fetching")
    args = parser.parse_args()

    if args.add:
        add_holding_to_config(args.add, args.name, args.segment, args.role)

    if not args.skip_fetch:
        fetch_all_portfolio_data()

    html_content = build_html()

    if ARTIFACT_HTML_PATH.parent.exists():
        ARTIFACT_HTML_PATH.write_text(html_content, encoding="utf-8")
        print(f"Synced Antigravity side-pane artifact: {ARTIFACT_HTML_PATH}")


if __name__ == "__main__":
    main()
