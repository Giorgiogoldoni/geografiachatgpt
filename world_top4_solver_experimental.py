"""Experimental reconstruction of the historical Logical Invest-style solver.

Research-only module. It deliberately keeps the existing models untouched.
Historical public QuantTrader documentation describes daily mean / daily
standard-deviation**f ranking, monthly rebalance and portfolio-level modified
Sharpe optimization. Exact live WTOP4 constraints and current fourth sleeve
are not publicly verified.

This test:
- ranks one equity ETF in each provisional sleeve using 68 daily observations
  and mean(daily return) / std(daily return)**2 (f=2);
- compares equal weights, unconstrained long-only 5%-grid optimization,
  and a diversified 10%-40% per-ETF constraint sensitivity;
- applies the documented historical 60/40 equity/HEDGE architecture only as
  a scenario: 24% Treasury + 16% GLD-USD, with provisional component universes;
- reports all assumptions and common-period comparisons.
"""
import itertools
import json
import math
import warnings
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

import world_top4_6040 as base

LB = 68
OUT = Path("world_top4_solver_experimental.json")
GRID = 0.05
TREASURY = ["TLT", "TIP", "GSY"]
GOLD_USD = ["GLD", "UUP"]
VARIANTS = ("equal_weight", "solver_unconstrained", "solver_10_40")


def daily_window(prices, ticker, signal_date):
    if ticker not in prices.columns:
        return None
    s = prices.loc[:signal_date, ticker].dropna()
    if len(s) < LB + 1:
        return None
    r = s.pct_change().dropna().tail(LB)
    if len(r) != LB or not np.isfinite(r.to_numpy()).all():
        return None
    return r


def modified_score(returns, factor=2.0):
    """QuantTrader documented form: mean daily return / daily std**factor."""
    if returns is None or len(returns) != LB:
        return None
    sd = float(returns.std(ddof=1))
    if not np.isfinite(sd) or sd <= 0:
        return None
    return float(returns.mean() / (sd ** factor))


def choose_one(prices, tickers, signal_date):
    ranked = []
    for ticker in tickers:
        r = daily_window(prices, ticker, signal_date)
        score = modified_score(r)
        if score is not None:
            ranked.append({"ticker": ticker, "score": score,
                           "return_68d": float((1 + r).prod() - 1),
                           "daily_volatility": float(r.std(ddof=1))})
    return sorted(ranked, key=lambda x: x["score"], reverse=True)


def weight_grids(n, min_units=0, max_units=20):
    for units in itertools.product(range(min_units, max_units + 1), repeat=n):
        if sum(units) == 20:
            yield np.asarray(units, dtype=float) * GRID


def solve_weights(prices, tickers, signal_date, min_units=0, max_units=20):
    series = [daily_window(prices, t, signal_date) for t in tickers]
    if any(x is None for x in series):
        return None
    frame = pd.concat(series, axis=1).dropna()
    frame.columns = tickers
    # Country ETFs trade on different calendars; optimize only on common sessions.
    if len(frame) < 50:
        return None
    best_score, best_weights = -np.inf, None
    for weights in weight_grids(len(tickers), min_units, max_units):
        port = frame.to_numpy() @ weights
        sd = float(np.std(port, ddof=1))
        if sd <= 0 or not np.isfinite(sd):
            continue
        score = float(np.mean(port) / (sd ** 2))
        if score > best_score:
            best_score, best_weights = score, weights
    if best_weights is None:
        return None
    return {t: float(w) for t, w in zip(tickers, best_weights)}


def make_weights(prices, signal_date, variant):
    picks = {}
    for region, universe in base.REGIONS.items():
        ranked = choose_one(prices, universe, signal_date)
        if not ranked:
            return None, None, None
        picks[region] = ranked[0]

    equity_tickers = [x["ticker"] for x in picks.values()]
    if len(set(equity_tickers)) != 4:
        # Do not double-count one ETF across regional sleeves.
        return None, None, None

    if variant == "equal_weight":
        equity_weights = {t: 0.25 for t in equity_tickers}
    elif variant == "solver_unconstrained":
        equity_weights = solve_weights(prices, equity_tickers, signal_date)
    else:
        # Sensitivity only: 10%-40% per regional winner, 5% grid.
        equity_weights = solve_weights(prices, equity_tickers, signal_date, 2, 8)
    if not equity_weights:
        return None, None, None

    treasury_rank = choose_one(prices, TREASURY, signal_date)
    gold_rank = choose_one(prices, GOLD_USD, signal_date)
    if not treasury_rank or not gold_rank:
        return None, None, None

    weights = {t: 0.60 * w for t, w in equity_weights.items()}
    for ticker, weight in ((treasury_rank[0]["ticker"], 0.24),
                           (gold_rank[0]["ticker"], 0.16)):
        weights[ticker] = weights.get(ticker, 0.0) + weight
    return weights, picks, {
        "equity_weights": equity_weights,
        "treasury": treasury_rank[0],
        "gold_usd": gold_rank[0],
        "equity_solver_score": (
            None if variant == "equal_weight" else float(
                solve_score(prices, equity_tickers, signal_date, equity_weights)
            )
        )
    }


def solve_score(prices, tickers, signal_date, weights):
    frame = pd.concat([daily_window(prices, t, signal_date) for t in tickers], axis=1).dropna()
    frame.columns = tickers
    if len(frame) < 50:
        return 0.0
    port = frame.to_numpy() @ np.asarray([weights[t] for t in tickers])
    sd = float(np.std(port, ddof=1))
    return float(np.mean(port) / (sd ** 2)) if sd > 0 else 0.0


def build_rows(prices, variant):
    monthly = prices.resample("ME").last().dropna(how="all")
    latest = prices.dropna(how="all").index[-1]
    if latest.to_period("M") == pd.Timestamp.now(tz="UTC").to_period("M"):
        monthly = monthly.iloc[:-1]
    rows = []
    dates = list(monthly.index)
    for i in range(1, len(dates)):
        signal, start, end = dates[i - 1], dates[i - 1], dates[i]
        weights, picks, detail = make_weights(prices, signal, variant)
        if not weights:
            continue
        a, b = monthly.loc[start], monthly.loc[end]
        if any(t not in monthly.columns or pd.isna(a.get(t)) or pd.isna(b.get(t))
               or a[t] <= 0 or b[t] <= 0 for t in weights):
            continue
        ret = sum(w * (float(b[t] / a[t]) - 1.0) for t, w in weights.items())
        rows.append({
            "signal_date": signal.strftime("%Y-%m-%d"),
            "holding_from": start.strftime("%Y-%m-%d"),
            "holding_to": end.strftime("%Y-%m-%d"),
            "return": float(ret), "weights": weights,
            "picks": {k: v["ticker"] for k, v in picks.items()},
            "solver": detail
        })
    return rows


def compact_metrics(rows):
    m = base.metrics(rows)
    if not m:
        return {"months": 0}
    keys = ("months", "total_return", "cagr", "volatility",
            "sharpe_zero_rf", "max_drawdown", "ulcer_index",
            "monthly_win_rate", "avg_monthly_turnover")
    return {k: m.get(k) for k in keys}


def main():
    tickers = sorted(set(
        sum(base.REGIONS.values(), []) + TREASURY + GOLD_USD + [base.BENCH]
    ))
    prices = base.download(tickers)
    latest = prices.dropna(how="all").index[-1]
    variants = {name: build_rows(prices, name) for name in VARIANTS}
    common = set.intersection(*[
        {r["holding_to"] for r in rows} for rows in variants.values()
    ]) if variants else set()
    common = sorted(common)

    # Align ACWI to the exact same holding_from / holding_to intervals.
    # Do not use the previous available ACWI month: that can create a
    # different holding period and an unfair benchmark comparison.
    benchmark = prices[base.BENCH].resample("ME").last().dropna()
    reference_rows = {
        r["holding_to"]: r
        for r in variants["solver_unconstrained"]
        if r["holding_to"] in common
    }
    common = [
        date for date in common
        if date in reference_rows
        and pd.Timestamp(reference_rows[date]["holding_from"]) in benchmark.index
        and pd.Timestamp(date) in benchmark.index
    ]
    benchmark_rows = []
    for date in common:
        start = pd.Timestamp(reference_rows[date]["holding_from"])
        end = pd.Timestamp(date)
        benchmark_rows.append({
            "holding_to": date,
            "return": float(benchmark.loc[end] / benchmark.loc[start] - 1)
        })

    results = {}
    for name, rows in variants.items():
        aligned = [r for r in rows if r["holding_to"] in common]
        results[name] = {
            "metrics_common_period": compact_metrics(aligned),
            "months_common_period": len(aligned),
            "history_last_36_months": aligned[-36:]
        }

    # Selection and concentration diagnostics on the optimized portfolio.
    solver_rows = [r for r in variants["solver_unconstrained"] if r["holding_to"] in common]
    selection_counts, weight_stats = {}, {}
    for row in solver_rows:
        for region, ticker in row["picks"].items():
            selection_counts.setdefault(region, {})
            selection_counts[region][ticker] = selection_counts[region].get(ticker, 0) + 1
        for ticker, weight in row["weights"].items():
            weight_stats.setdefault(ticker, []).append(float(weight))
    results["benchmark_acwi"] = {
        "metrics_common_period": compact_metrics(benchmark_rows),
        "months_common_period": len(benchmark_rows)
    }
    data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "latest_price_date": latest.strftime("%Y-%m-%d"),
        "data_source": "Yahoo Finance adjusted daily prices",
        "methodology": {
            "historical_reference": "QuantTrader public help: mean daily return / daily standard deviation^f; f=2; monthly rebalance; portfolio-level modified-Sharpe optimization",
            "lookback_trading_days": LB,
            "ranking_score": "mean(daily returns) / std(daily returns)^2",
            "equity_selection": "one highest-scoring ETF per provisional region; no absolute-momentum filter",
            "solver": "long-only 5%-step grid across the four selected regional ETFs",
            "weight_variants": {
                "equal_weight": "25% per equity sleeve",
                "solver_unconstrained": "0%-100% per ETF; fully invested",
                "solver_10_40": "10%-40% per ETF; sensitivity constraint, not an official LI rule"
            },
            "portfolio_architecture": "historical 2020 scenario: 60% equity / 40% HEDGE; HEDGE split 24% Treasury + 16% GLD-USD",
            "hedge_universes": {"treasury": TREASURY, "gold_usd": GOLD_USD},
            "fourth_region": "provisional residual bucket inherited from world_top4_6040.py; not verified as official LI fourth sleeve",
            "risk": "Research only. No current official constraints or 2026 live parameters confirmed. No fees, taxes, slippage or FX. The grid solver is a transparent approximation, not QuantTrader's proprietary solver."
        },
        "common_period": {"start": common[0] if common else None,
                          "end": common[-1] if common else None, "months": len(common)},
        "variants": results,
        "unconstrained_selection_frequency": selection_counts,
        "unconstrained_weight_distribution": {
            t: {"mean": float(np.mean(v)), "median": float(np.median(v)),
                "max": float(np.max(v)), "months": len(v)}
            for t, v in weight_stats.items()
        }
    }
    OUT.write_text(json.dumps(data, indent=2, allow_nan=False), encoding="utf-8")
    print("Experimental modified-Sharpe solver", latest.date(),
          "common months", len(common), "variants", len(VARIANTS))


if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    main()
