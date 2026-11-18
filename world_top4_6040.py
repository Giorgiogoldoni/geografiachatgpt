"""Independent 60/40 research scenario for World Top 4.
Not an official Logical Invest replication: ranking, exact regional taxonomy and
HEDGE sub-strategy rules remain partly undisclosed.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
import warnings
import pandas as pd
import yfinance as yf
from world_top4 import BENCH, START, download, rank, metrics

# Public LI pages show four geographic sub-strategies but only three public
# region pages were identified. The fourth bucket below is an explicit residual
# approximation, not a verified LI sleeve. Overlapping/unresolved tickers are
# assigned once here solely to avoid double counting.
REGIONS = {
    "Developed": ["EIRL","EIS","ENZL","EPOL","EWA","EWC","EWD","EWG","EWH","EWI","EWK","EWL","EWN","EWO","EWP","EWQ","EWU","NORW"],
    "Asia": ["ASHR","DBKO","EIDO","EPHE","EPI","EWS","EWT","EWY","FXI","IDX","THD","VNM"],
    "Latin America": ["ARGT","ECH","EPU","EWW","EWZ","GXG"],
    "Other / residual (unverified)": ["AFK","EGPT","EZA","FM","FRN","GAF","GULF","GREK","MCHI","MES","RSX","TUR"],
}
TREASURY = ["TLT", "TIP", "GSY"]
GOLD_USD = ["GLD", "UUP"]
OUT = Path("world_top4_6040.json")

def run_backtest(prices, variant="modified"):
    monthly = prices.resample("ME").last().dropna(how="all")
    latest = prices.dropna(how="all").index[-1]
    if latest.to_period("M") == pd.Timestamp.now(tz="UTC").to_period("M"):
        monthly = monthly.iloc[:-1]
    dates = list(monthly.index)
    rows = []
    for i in range(1, len(dates)):
        signal_date, hold_from, hold_to = dates[i-1], dates[i-1], dates[i]
        picks = []
        weights = {}
        for region, assets in REGIONS.items():
            ranked = rank(prices, assets, signal_date, variant)
            if ranked:
                item = ranked[0]
                picks.append({"region": region, **item, "weight": 0.15})
                weights[item["ticker"]] = weights.get(item["ticker"], 0.0) + 0.15
        treasury = rank(prices, TREASURY, signal_date, variant)
        gold_usd = rank(prices, GOLD_USD, signal_date, variant)
        hedge = []
        if treasury:
            item = treasury[0]
            hedge.append({"sleeve":"Treasury","ticker":item["ticker"],"score":item["score"],"weight":0.24})
            weights[item["ticker"]] = weights.get(item["ticker"],0.0) + 0.24
        if gold_usd:
            item = gold_usd[0]
            hedge.append({"sleeve":"GLD-USD","ticker":item["ticker"],"score":item["score"],"weight":0.16})
            weights[item["ticker"]] = weights.get(item["ticker"],0.0) + 0.16
        start_px, end_px = monthly.loc[hold_from], monthly.loc[hold_to]
        valid = {t:w for t,w in weights.items()
                 if t in monthly.columns and pd.notna(start_px.get(t)) and pd.notna(end_px.get(t))
                 and start_px[t] > 0 and end_px[t] > 0}
        if len(valid) < 6:
            continue
        # Require the four equity sleeves plus both HEDGE components to be present.
        if len(picks) != 4 or len(hedge) != 2:
            continue
        total = sum(valid.values())
        ret = sum(w * (end_px[t]/start_px[t]-1) for t,w in valid.items()) / total
        rows.append({
            "signal_date":signal_date.strftime("%Y-%m-%d"),
            "holding_from":hold_from.strftime("%Y-%m-%d"),
            "holding_to":hold_to.strftime("%Y-%m-%d"),
            "return":float(ret), "picks":picks, "hedge":hedge,
            "weights":{t:float(w/total) for t,w in valid.items()}
        })
    return rows

def main():
    tickers = sorted(set(sum(REGIONS.values(),[]) + TREASURY + GOLD_USD + [BENCH]))
    prices = download(tickers)
    latest = prices.dropna(how="all").index[-1]
    monthly = prices.resample("ME").last()
    if latest.to_period("M") == pd.Timestamp.now(tz="UTC").to_period("M"):
        monthly = monthly.iloc[:-1]
    bench = monthly[BENCH].dropna()
    by_date = {d.strftime("%Y-%m-%d"): float(bench.loc[d]/bench.shift(1).loc[d]-1)
               for d in bench.index[1:]}
    variants = {}
    for variant in ("momentum", "modified", "composite"):
        full_history = run_backtest(prices, variant)
        aligned = [x for x in full_history if x["holding_to"] in by_date]
        benchmark_rows = [{"holding_to":x["holding_to"],"return":by_date[x["holding_to"]]}
                          for x in aligned]
        counts = {}
        for row in aligned:
            for item in row["picks"]:
                counts[item["ticker"]] = counts.get(item["ticker"],0) + 1
            for item in row["hedge"]:
                counts[item["ticker"]] = counts.get(item["ticker"],0) + 1
        variants[variant] = {
            "metrics":metrics(aligned),
            "benchmark":metrics(benchmark_rows),
            "selection_months":len(aligned),
            "selection_frequency":dict(sorted(counts.items(), key=lambda kv:(-kv[1],kv[0]))),
            "history":aligned[-36:]
        }
    data = {
        "generated_at":datetime.now(timezone.utc).isoformat(),
        "latest_price_date":latest.strftime("%Y-%m-%d"),
        "data_source":"Yahoo Finance adjusted daily prices",
        "methodology":{
            "equity_weight":0.60, "hedge_weight":0.40,
            "equity_region_weights":"15% each across four provisional regional sleeves",
            "hedge_split":"24% Treasury (60% of HEDGE) + 16% GLD-USD (40% of HEDGE)",
            "treasury_candidates":TREASURY, "gold_usd_candidates":GOLD_USD,
            "ranking_variants":["68-day return","68-day return / annualized volatility squared","3/6/12-month composite"],
            "absolute_momentum_filter":False,
            "fourth_region":"Other / residual universe, not verified as the official fourth LI sub-strategy",
            "warning":"Scenario test only. Historical 60/40 and internal 60/40 hedge split are documented for 2020, not verified as current. Exact regional buckets, HEDGE selection algorithms, execution timing and ranking formula remain unconfirmed. The residual bucket is not a verified region. No fees, taxes, slippage or FX."
        },
        "regions":REGIONS,
        "variants":variants
    }
    OUT.write_text(json.dumps(data,indent=2,allow_nan=False),encoding="utf-8")
    print("World Top 4 60/40 scenario",latest.date(),"variants",len(variants),"tickers",len(tickers))

if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    main()
