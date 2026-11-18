"""Robustness tests for the 60/40 exploratory World Top 4 model.
Tests: split the 15% Asia sleeve across its top two ranked ETFs (7.5% each);
and compare the Eastern Mediterranean sleeve with/without GREK.
No official Logical Invest rules are implied.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import world_top4_6040 as engine

OUT = Path("world_top4_robustness.json")


def run_two_asia(prices, variant, regions):
    monthly = prices.resample("ME").last().dropna(how="all")
    latest = prices.dropna(how="all").index[-1]
    if latest.to_period("M") == pd.Timestamp.now(tz="UTC").to_period("M"):
        monthly = monthly.iloc[:-1]
    dates = list(monthly.index)
    rows = []
    for i in range(1, len(dates)):
        signal, start, end = dates[i-1], dates[i-1], dates[i]
        picks, hedge, weights = [], [], {}
        for region, assets in regions.items():
            ranked = engine.rank(prices, assets, signal, variant)
            if region == "Asia":
                chosen = ranked[:2]
                if len(chosen) < 2:
                    picks = []
                    break
                for item in chosen:
                    picks.append({"region": region, **item, "weight": 0.075})
                    weights[item["ticker"]] = weights.get(item["ticker"], 0) + 0.075
            elif ranked:
                item = ranked[0]
                picks.append({"region": region, **item, "weight": 0.15})
                weights[item["ticker"]] = weights.get(item["ticker"], 0) + 0.15
            else:
                picks = []
                break
        treasury = engine.rank(prices, engine.TREASURY, signal, variant)
        gold = engine.rank(prices, engine.GOLD_USD, signal, variant)
        if not treasury or not gold or len(picks) != 5:
            continue
        for sleeve, item, weight in (("Treasury", treasury[0], 0.24), ("GLD-USD", gold[0], 0.16)):
            hedge.append({"sleeve": sleeve, "ticker": item["ticker"], "score": item["score"], "weight": weight})
            weights[item["ticker"]] = weights.get(item["ticker"], 0) + weight
        a, b = monthly.loc[start], monthly.loc[end]
        if abs(sum(weights.values()) - 1.0) > 1e-8:
            continue
        if any(t not in monthly.columns or pd.isna(a.get(t)) or pd.isna(b.get(t)) or a[t] <= 0 or b[t] <= 0 for t in weights):
            continue
        ret = sum(w * (b[t] / a[t] - 1) for t, w in weights.items())
        rows.append({"signal_date": signal.strftime("%Y-%m-%d"), "holding_from": start.strftime("%Y-%m-%d"),
                     "holding_to": end.strftime("%Y-%m-%d"), "return": float(ret),
                     "picks": picks, "hedge": hedge, "weights": weights})
    return rows


def common_metrics(rows_a, rows_b):
    dates_a = {r["holding_to"] for r in rows_a}
    dates_b = {r["holding_to"] for r in rows_b}
    common = dates_a & dates_b
    a = [r for r in rows_a if r["holding_to"] in common]
    b = [r for r in rows_b if r["holding_to"] in common]
    return {"common_months": len(common),
            "start": min(common) if common else None, "end": max(common) if common else None,
            "baseline": engine.metrics(a), "test": engine.metrics(b)}


def main():
    base = engine.REGIONS
    east_med = {"Developed": base["Developed"], "Asia": base["Asia"],
                "Latin America": base["Latin America"],
                "Eastern Mediterranean": ["EGPT", "GREK", "TUR"]}
    east_med_no_grek = {**east_med, "Eastern Mediterranean": ["EGPT", "TUR"]}
    tickers = sorted(set(sum([list(x) for x in []], []) |
                         {t for members in base.values() for t in members} |
                         {t for members in east_med.values() for t in members} |
                         set(engine.TREASURY + engine.GOLD_USD + [engine.BENCH, "^IRX"])))
    prices = engine.download(tickers)
    latest = prices.dropna(how="all").index[-1]
    output = {"generated_at": datetime.now(timezone.utc).isoformat(),
              "latest_price_date": latest.strftime("%Y-%m-%d"),
              "data_source": "Yahoo Finance adjusted daily prices; identical 60/40 engine, hedge and ranking settings",
              "methodology": {
                  "asia_two_slots": "Asia 15% sleeve split equally between rank 1 and rank 2 (7.5% each); other three equity sleeves remain 15%; hedge remains 40%.",
                  "greece_exclusion": "Compare EGPT/GREK/TUR against EGPT/TUR; the fourth sleeve remains 15%, with no forced replacement weight or change to other sleeves.",
                  "coverage": "Strict complete coverage for every selected equity and both hedge assets; compare each pair on exact common holding months.",
                  "limitations": "Exploratory model, not an official Logical Invest replication. No fees, taxes, FX or slippage. Excluding GREK tests its contribution to selection, not a synthetic cap on its underlying constituents."},
              "variants": {}}
    for variant in ("momentum", "modified", "composite"):
        baseline = engine.run_backtest(prices, variant, base)
        asia2 = run_two_asia(prices, variant, base)
        output["variants"].setdefault(variant, {})["asia_two_slots"] = common_metrics(baseline, asia2)
        grek_in = engine.run_backtest(prices, variant, east_med)
        grek_out = engine.run_backtest(prices, variant, east_med_no_grek)
        output["variants"][variant]["grek_inclusion"] = common_metrics(grek_in, grek_out)
    OUT.write_text(json.dumps(output, indent=2, allow_nan=False), encoding="utf-8")
    print("Robustness tests", latest.date(), "variants", len(output["variants"]))


if __name__ == "__main__":
    main()
