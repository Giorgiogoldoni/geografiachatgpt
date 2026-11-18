"""Robustness and attribution audit for the exploratory 60/40 World Top 4 model.
Adds fixed sub-periods, rolling windows, market-regime splits and EWY/GREK
selection attribution. Not an official Logical Invest replication.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd
import world_top4_6040 as engine

OUT = Path("world_top4_robustness.json")
VARIANTS = ("momentum", "modified", "composite")
SUBPERIODS = {
    "2006_2011": ("2006-01-01", "2011-12-31"),
    "2012_2016": ("2012-01-01", "2016-12-31"),
    "2017_2021": ("2017-01-01", "2021-12-31"),
    "2022_2026": ("2022-01-01", "2026-12-31"),
}


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


def align_rows(rows_a, rows_b):
    common = {r["holding_to"] for r in rows_a} & {r["holding_to"] for r in rows_b}
    return ([r for r in rows_a if r["holding_to"] in common],
            [r for r in rows_b if r["holding_to"] in common])


def compact_metrics(rows):
    m = engine.metrics(rows)
    if not m:
        return {"months": 0}
    keys = ("months", "total_return", "cagr", "volatility", "sharpe_zero_rf",
            "max_drawdown", "ulcer_index", "monthly_win_rate")
    return {k: m.get(k) for k in keys}


def comparison(rows_a, rows_b):
    a, b = align_rows(rows_a, rows_b)
    dates = [r["holding_to"] for r in a]
    return {
        "common_months": len(dates), "start": min(dates) if dates else None,
        "end": max(dates) if dates else None,
        "baseline": compact_metrics(a), "test": compact_metrics(b),
        "delta_test_minus_baseline": {
            k: (compact_metrics(b).get(k, 0) - compact_metrics(a).get(k, 0))
            for k in ("cagr", "volatility", "max_drawdown", "ulcer_index", "sharpe_zero_rf")
            if compact_metrics(a).get(k) is not None and compact_metrics(b).get(k) is not None
        }
    }


def subperiod_comparisons(rows_a, rows_b):
    a, b = align_rows(rows_a, rows_b)
    out = {}
    for name, (lo, hi) in SUBPERIODS.items():
        aa = [r for r in a if lo <= r["holding_to"] <= hi]
        bb = [r for r in b if lo <= r["holding_to"] <= hi]
        out[name] = comparison(aa, bb)
    return out


def rolling_comparison(rows_a, rows_b, window):
    a, b = align_rows(rows_a, rows_b)
    a = sorted(a, key=lambda x: x["holding_to"])
    b = sorted(b, key=lambda x: x["holding_to"])
    by_b = {r["holding_to"]: r for r in b}
    pairs = [(r, by_b[r["holding_to"]]) for r in a if r["holding_to"] in by_b]
    diffs = []
    for i in range(window, len(pairs) + 1):
        aa = [x[0] for x in pairs[i-window:i]]
        bb = [x[1] for x in pairs[i-window:i]]
        ma, mb = compact_metrics(aa), compact_metrics(bb)
        diffs.append({k: mb[k] - ma[k] for k in ("cagr", "max_drawdown", "ulcer_index", "sharpe_zero_rf")})
    if not diffs:
        return {"window_months": window, "windows": 0}
    result = {"window_months": window, "windows": len(diffs)}
    for key in diffs[0]:
        vals = [x[key] for x in diffs]
        result[key + "_delta_percentiles"] = {
            "p10": float(np.percentile(vals, 10)), "median": float(np.percentile(vals, 50)),
            "p90": float(np.percentile(vals, 90)), "test_better_pct": float(100 * np.mean(np.array(vals) > 0))
        }
    return result


def regime_comparison(rows_a, rows_b, prices):
    monthly = prices.resample("ME").last()
    bench = monthly[engine.BENCH].dropna()
    regimes = {}
    for row in rows_a:
        signal = pd.Timestamp(row["signal_date"])
        hist = bench.loc[bench.index <= signal]
        if len(hist) < 13:
            continue
        trailing = float(hist.iloc[-1] / hist.iloc[-13] - 1)
        regime = "risk_on" if trailing > 0.05 else ("risk_off" if trailing < -0.05 else "sideways")
        regimes[row["holding_to"]] = regime
    a, b = align_rows(rows_a, rows_b)
    out = {}
    for regime in ("risk_on", "sideways", "risk_off"):
        aa = [r for r in a if regimes.get(r["holding_to"]) == regime]
        bb = [r for r in b if regimes.get(r["holding_to"]) == regime]
        out[regime] = comparison(aa, bb)
    out["definition"] = "ACWI trailing 12-month return measured at the prior month-end signal: >+5% risk_on, <-5% risk_off, otherwise sideways. Descriptive classification, not causal."
    return out


def candidate_attribution(rows, prices, candidate, region_name):
    monthly = prices.resample("ME").last()
    selected = []
    for row in rows:
        pick = next((p for p in row.get("picks", []) if p.get("region") == region_name and p.get("ticker") == candidate), None)
        if not pick:
            continue
        start, end = pd.Timestamp(row["holding_from"]), pd.Timestamp(row["holding_to"])
        if candidate not in monthly or pd.isna(monthly.loc[start].get(candidate)) or pd.isna(monthly.loc[end].get(candidate)):
            continue
        asset_return = float(monthly.loc[end, candidate] / monthly.loc[start, candidate] - 1)
        weight = float(pick.get("weight", 0.15))
        selected.append({"date": row["holding_to"], "asset_return": asset_return,
                         "weight": weight, "portfolio_return": float(row["return"]),
                         "weighted_contribution": weight * asset_return})
    if not selected:
        return {"candidate": candidate, "selection_months": 0}
    contributions = [x["weighted_contribution"] for x in selected]
    asset_returns = [x["asset_return"] for x in selected]
    return {
        "candidate": candidate, "selection_months": len(selected),
        "selection_frequency_pct": 100 * len(selected) / len(rows) if rows else None,
        "average_asset_return_when_selected": float(np.mean(asset_returns)),
        "average_weighted_monthly_contribution_pct_points": float(100 * np.mean(contributions)),
        "cumulative_sum_of_weighted_monthly_contributions_pct_points": float(100 * np.sum(contributions)),
        "compounded_contribution_only": float(np.prod([1+x for x in contributions]) - 1),
        "average_full_portfolio_return_in_selected_months": float(np.mean([x["portfolio_return"] for x in selected])),
        "note": "Weighted contribution is sleeve weight multiplied by the ETF's monthly return; cumulative sum is attribution arithmetic, not a standalone tradable portfolio return."
    }


def full_audit(rows_a, rows_b, prices, candidate, region):
    a, b = align_rows(rows_a, rows_b)
    return {
        "full_sample": comparison(a, b),
        "fixed_subperiods": subperiod_comparisons(a, b),
        "rolling_36m": rolling_comparison(a, b, 36),
        "rolling_60m": rolling_comparison(a, b, 60),
        "market_regimes": regime_comparison(a, b, prices),
        "candidate_attribution": candidate_attribution(a, prices, candidate, region)
    }


def main():
    base = engine.REGIONS
    east_med = {"Developed": base["Developed"], "Asia": base["Asia"],
                "Latin America": base["Latin America"],
                "Eastern Mediterranean": ["EGPT", "GREK", "TUR"]}
    east_med_no_grek = {**east_med, "Eastern Mediterranean": ["EGPT", "TUR"]}
    tickers = sorted(
        {t for members in base.values() for t in members}
        | {t for members in east_med.values() for t in members}
        | set(engine.TREASURY + engine.GOLD_USD + [engine.BENCH, "^IRX"])
    )
    prices = engine.download(tickers)
    latest = prices.dropna(how="all").index[-1]
    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "latest_price_date": latest.strftime("%Y-%m-%d"),
        "data_source": "Yahoo Finance adjusted daily prices; monthly close-to-close holding returns",
        "methodology": {
            "asia_two_slots": "Asia 15% sleeve split equally between rank 1 and rank 2 (7.5% each); other equity sleeves 15%; hedge 40%.",
            "greece_exclusion": "EGPT/GREK/TUR versus EGPT/TUR, same 15% fourth sleeve.",
            "coverage": "Strict complete coverage; every comparison uses exact common holding months.",
            "subperiods": SUBPERIODS,
            "rolling_windows": "36 and 60 common monthly observations; report distribution of test-minus-baseline metric differences.",
            "regimes": "ACWI trailing 12-month return at signal date: above +5% risk-on, below -5% risk-off, otherwise sideways.",
            "limitations": "Exploratory model, not official Logical Invest replication. No fees, taxes, FX or slippage. Attribution arithmetic is descriptive, not causal or a tradable counterfactual."
        },
        "variants": {}
    }
    for variant in VARIANTS:
        baseline = engine.run_backtest(prices, variant, base)
        asia2 = run_two_asia(prices, variant, base)
        grek_in = engine.run_backtest(prices, variant, east_med)
        grek_out = engine.run_backtest(prices, variant, east_med_no_grek)
        output["variants"][variant] = {
            "asia_two_slots": full_audit(baseline, asia2, prices, "EWY", "Asia"),
            "grek_inclusion": full_audit(grek_in, grek_out, prices, "GREK", "Eastern Mediterranean")
        }
    OUT.write_text(json.dumps(output, indent=2, allow_nan=False), encoding="utf-8")
    print("Robustness and attribution audit", latest.date(), "variants", len(output["variants"]))


if __name__ == "__main__":
    main()
