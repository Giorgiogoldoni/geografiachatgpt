#!/usr/bin/env python3
"""Six-area geographic ETF engine.

Uses the user's INDEX as the investable starting universe, classifies each
instrument by underlying exposure, and keeps country, regional, index, global
and factor instruments in separate ranking buckets. This is an independent
research model, not an exact Logical Invest replication.
"""
from __future__ import annotations
import json, math, warnings
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parent
INDEX = ROOT / "data" / "geografia_index_user_51.csv"
FACTORS = ROOT / "data" / "geografia_index_factor_14.csv"
OUT = ROOT / "geografia-motore.json"
LOOKBACK = 68
WINDOWS = {"1m": 21, "3m": 63, "6m": 126, "12m": 252}
COMPOSITE_WEIGHTS = {"3m": 0.40, "6m": 0.30, "12m": 0.30}
MIN_HISTORY = 253
BENCHMARK = "WRD.PA"

MODULES = {
    "north-america": "America del Nord",
    "latin-america": "Centro e Sud America",
    "asia": "Asia e Pacifico",
    "middle-east-africa": "Medio Oriente e Africa",
    "europe": "Europa",
    "global": "Global",
}
COUNTRY_MAP = {
    "stati uniti": "north-america", "usa": "north-america",
    "canada": "north-america",
    "messico": "latin-america", "brasile": "latin-america",
    "argentina": "latin-america", "cile": "latin-america",
    "colombia": "latin-america", "perù": "latin-america", "peru": "latin-america",
    "america latina": "latin-america", "latin america": "latin-america",
    "giappone": "asia", "cina": "asia", "india": "asia", "taiwan": "asia",
    "corea del sud": "asia", "hong kong": "asia", "singapore": "asia",
    "indonesia": "asia", "malesia": "asia", "thailandia": "asia",
    "filippine": "asia", "vietnam": "asia", "australia": "asia",
    "nuova zelanda": "asia", "pacifico ex giappone": "asia",
    "asia pacifico": "asia", "asia-pacifico": "asia", "hong kong / cina": "asia",
    "arabia saudita": "middle-east-africa", "sudafrica": "middle-east-africa",
    "sud africa": "middle-east-africa", "turchia": "middle-east-africa",
    "israele": "middle-east-africa", "emirati arabi uniti": "middle-east-africa",
    "qatar": "middle-east-africa", "kuwait": "middle-east-africa",
    "egitto": "middle-east-africa", "marocco": "middle-east-africa",
    "nigeria": "middle-east-africa", "kenya": "middle-east-africa",
    "regno unito": "europe", "svizzera": "europe", "germania": "europe",
    "francia": "europe", "italia": "europe", "spagna": "europe",
    "paesi bassi": "europe", "belgio": "europe", "austria": "europe",
    "irlanda": "europe", "portogallo": "europe", "svezia": "europe",
    "norvegia": "europe", "danimarca": "europe", "finlandia": "europe",
    "islanda": "europe", "polonia": "europe", "grecia": "europe",
    "repubblica ceca": "europe", "ungheria": "europe", "romania": "europe",
    "europa": "europe", "europa orientale": "europe", "paesi nordici": "europe",
    "globale": "global", "global": "global", "mondo": "global",
}
REGIONAL_LABELS = {"regione", "regional", "regione regionale"}
GLOBAL_LABELS = {"globale", "global"}
INDEX_LABELS = {"indice nazionale", "indice nazionale coperto",
                "indice settoriale/tematico", "indice"}
COUNTRY_LABELS = {"paese", "paese coperto"}
ETP_TICKERS = {"WNAS.MI"}

def clean(value):
    return str(value or "").strip()

def module_for(geography):
    g = clean(geography).lower()
    if g in COUNTRY_MAP:
        return COUNTRY_MAP[g]
    if "latin" in g or "america latina" in g:
        return "latin-america"
    if "global" in g or "globale" in g or "world" in g:
        return "global"
    if "pacific" in g or "pacifico" in g:
        return "asia"
    return None

def subgroup_for(geography):
    g = clean(geography).lower()
    if g in {"australia", "nuova zelanda", "pacifico ex giappone"}:
        return "Pacifico"
    if g in {"asia pacifico", "asia-pacifico"}:
        return "Asia-Pacifico regionale"
    if g in {"america latina", "latin america"}:
        return "America Latina regionale"
    if g in {"europa orientale", "paesi nordici"}:
        return "Europa regionale"
    if g in {"europa", "globale", "global"}:
        return "Ampio mercato"
    return "Paese / esposizione specifica"

def bucket_for(classification, geography, ticker):
    c = clean(classification).lower()
    g = clean(geography).lower()
    if ticker in ETP_TICKERS:
        return "etp"
    if c in GLOBAL_LABELS or g in GLOBAL_LABELS or g == "globale":
        return "global"
    if c in REGIONAL_LABELS:
        return "regional"
    if c in INDEX_LABELS:
        return "index"
    if c in COUNTRY_LABELS:
        return "country"
    # Conservative fallback: never silently mix a regional basket into a country ranking.
    if any(k in g for k in ("america latina", "pacifico", "europa orientale", "paesi nordici")):
        return "regional"
    return "unclassified"

def safe_float(value):
    try:
        x = float(value)
        return x if math.isfinite(x) else None
    except Exception:
        return None

def load_universe():
    df = pd.read_csv(INDEX, dtype=str).fillna("")
    rows = []
    for _, r in df.iterrows():
        ticker = clean(r.get("ticker"))
        geo = clean(r.get("geography"))
        bucket = bucket_for(r.get("classification"), geo, ticker)
        module = module_for(geo)
        rows.append({
            "ticker": ticker, "name": clean(r.get("name")),
            "geography": geo, "classification": clean(r.get("classification")),
            "module_id": module, "module": MODULES.get(module, "Da classificare"),
            "subgroup": subgroup_for(geo), "bucket": bucket,
            "portfolio": clean(r.get("portfolio")),
            "verification_status": clean(r.get("verification_status")),
            "symbol": ticker if "." in ticker else (ticker + ".MI" if ticker == "AUHEUA" else ticker),
            "instrument_status": "ETP separato" if bucket == "etp" else "Listing/forma giuridica da verificare",
        })
    return rows

def download_prices(symbols):
    symbols = sorted(set(x for x in symbols if x))
    if not symbols:
        return pd.DataFrame()
    raw = yf.download(symbols, start="2005-01-01", auto_adjust=True,
                      progress=False, threads=True, group_by="column")
    if raw is None or raw.empty:
        return pd.DataFrame()
    if isinstance(raw.columns, pd.MultiIndex):
        levels = list(raw.columns.get_level_values(0))
        key = "Close" if "Close" in levels else ("Adj Close" if "Adj Close" in levels else None)
        close = raw[key] if key else pd.DataFrame()
    else:
        key = "Close" if "Close" in raw.columns else ("Adj Close" if "Adj Close" in raw.columns else None)
        close = raw[[key]].rename(columns={key: symbols[0]}) if key else pd.DataFrame()
    if isinstance(close, pd.Series):
        close = close.to_frame(name=symbols[0])
    close.index = pd.to_datetime(close.index).tz_localize(None)
    return close.apply(pd.to_numeric, errors="coerce").sort_index()

def score_series(series):
    p = series.dropna()
    if len(p) < MIN_HISTORY:
        return None
    daily = p.pct_change().dropna()
    w = daily.tail(LOOKBACK)
    if len(w) < LOOKBACK:
        return None
    sd = float(w.std(ddof=1))
    if not math.isfinite(sd) or sd <= 0:
        return None
    last = float(p.iloc[-1])
    momentum = {}
    for label, n in WINDOWS.items():
        momentum[label] = safe_float(last / float(p.iloc[-n-1]) - 1) if len(p) > n else None
    sma200 = float(p.tail(200).mean()) if len(p) >= 200 else None
    composite = None
    if all(momentum.get(k) is not None for k in COMPOSITE_WEIGHTS):
        composite = sum(momentum[k] * weight for k, weight in COMPOSITE_WEIGHTS.items())
    return {
        "price": last,
        "return_68d": safe_float(last / float(p.iloc[-LOOKBACK-1]) - 1),
        "volatility_annual": safe_float(sd * math.sqrt(252)),
        "modified_sharpe_candidate": safe_float(float(w.mean()) / (sd ** 2)),
        "momentum_1m": momentum["1m"], "momentum_3m": momentum["3m"],
        "momentum_6m": momentum["6m"], "momentum_12m": momentum["12m"],
        "composite_momentum": safe_float(composite),
        "sma200": sma200, "above_sma200": bool(sma200 is not None and last > sma200),
        "absolute_momentum_positive": bool(momentum["12m"] is not None and momentum["12m"] > 0),
        "eligible_trend": bool(sma200 is not None and last > sma200 and momentum["12m"] is not None and momentum["12m"] > 0),
        "observations": int(len(p)), "price_date": p.index[-1].strftime("%Y-%m-%d"),
    }

def rank_key(row, key):
    return row.get(key) if row.get(key) is not None else -1e99

def monthly_winner_backtest(prices, rows):
    """One winner per module/bucket, monthly signal and next-month holding.
    It is a transparent research backtest, not the proprietary WTOP4 solver.
    """
    monthly = prices.resample("ME").last().dropna(how="all")
    if monthly.empty:
        return {}
    latest = prices.dropna(how="all").index.max()
    if latest is not None and latest.to_period("M") == pd.Timestamp.now(tz="UTC").to_period("M"):
        monthly = monthly.iloc[:-1]
    output = {}
    groups = {}
    for row in rows:
        if row["module_id"] and row["bucket"] in {"country", "regional", "index", "global"} and row["symbol"] in prices.columns:
            key = row["module_id"] + "|" + row["bucket"]
            groups.setdefault(key, []).append(row)
    dates = list(monthly.index)
    for key, candidates in groups.items():
        returns, picks, equity, curve = [], [], 1.0, []
        for i in range(1, len(dates)):
            signal_date, hold_end = dates[i-1], dates[i]
            ranked = []
            for candidate in candidates:
                s = prices.loc[:signal_date, candidate["symbol"]].dropna()
                m = score_series(s)
                if m and m["eligible_trend"]:
                    ranked.append((m["modified_sharpe_candidate"], candidate, m))
            if not ranked:
                ret, chosen = 0.0, None
            else:
                _, chosen, _ = max(ranked, key=lambda z: z[0] if z[0] is not None else -1e99)
                a = monthly.loc[signal_date, chosen["symbol"]] if chosen["symbol"] in monthly.columns else np.nan
                b = monthly.loc[hold_end, chosen["symbol"]] if chosen["symbol"] in monthly.columns else np.nan
                ret = float(b/a - 1) if pd.notna(a) and pd.notna(b) and a > 0 else 0.0
            equity *= (1.0 + ret)
            returns.append(ret)
            picks.append({"signal_date": signal_date.strftime("%Y-%m-%d"),
                          "holding_to": hold_end.strftime("%Y-%m-%d"),
                          "ticker": chosen["ticker"] if chosen else None,
                          "return": ret})
            curve.append({"date": hold_end.strftime("%Y-%m-%d"), "value": equity})
        if returns:
            arr = np.asarray(returns, dtype=float)
            years = len(arr) / 12.0
            cagr = equity ** (1/years) - 1 if years > 0 and equity > 0 else None
            vol = float(np.std(arr, ddof=1) * math.sqrt(12)) if len(arr) > 1 else None
            peak = np.maximum.accumulate(np.asarray(curve and [x["value"] for x in curve] or [1.0]))
            dd = np.asarray(curve and [x["value"] for x in curve] or [1.0]) / peak - 1
            output[key] = {
                "months": len(returns), "total_return": equity - 1,
                "cagr": safe_float(cagr), "volatility_annual": safe_float(vol),
                "max_drawdown": safe_float(float(dd.min())),
                "latest_signal": picks[-1], "history": picks[-36:], "equity_curve": curve[-120:],
                "note": "Backtest esplorativo: un ETF vincitore per modulo/categoria, filtro SMA200 + momentum 12m; costi, slippage e fiscalità esclusi."
            }
    return output

def main():
    rows = load_universe()
    factor_df = pd.read_csv(FACTORS, dtype=str).fillna("") if FACTORS.exists() else pd.DataFrame()
    factor_symbols = []
    if not factor_df.empty:
        factor_symbols = [clean(x) for x in factor_df["ticker"].tolist()
                          if clean(x).endswith((".MI", ".DE", ".PA", ".AS", ".L"))]
    symbols = [r["symbol"] for r in rows if r["module_id"] and r["bucket"] != "etp"]
    symbols += factor_symbols
    warnings_list = []
    try:
        prices = download_prices(symbols)
    except Exception as exc:
        prices = pd.DataFrame()
        warnings_list.append(f"Download prezzi non riuscito: {type(exc).__name__}: {exc}")
    for row in rows:
        symbol = row["symbol"]
        if row["bucket"] == "etp":
            row.update({"status": "ETP SEPARATO", "reason": "Non incluso nel ranking UCITS principale."})
        elif not row["module_id"]:
            row.update({"status": "DA CLASSIFICARE", "reason": "Esposizione geografica da normalizzare."})
        elif symbol not in prices.columns:
            row.update({"status": "PREZZI NON DISPONIBILI", "reason": "Ticker non restituito dal provider prezzi; listing da verificare."})
        else:
            metrics = score_series(prices[symbol])
            if metrics is None:
                row.update({"status": "STORICO INSUFFICIENTE", "reason": f"Servono almeno {MIN_HISTORY} osservazioni."})
            else:
                row.update(metrics)
                row["status"] = "CALCOLATO"
                row["reason"] = ""
    calculated = [r for r in rows if r["status"] == "CALCOLATO"]
    groups = {}
    for r in calculated:
        if r["bucket"] not in {"country", "regional", "index", "global"}:
            continue
        groups.setdefault(r["module_id"] + "|" + r["bucket"], []).append(r)
    rankings = {}
    selections = {}
    for key, pool in groups.items():
        rankings[key] = sorted(pool, key=lambda r: rank_key(r, "modified_sharpe_candidate"), reverse=True)
        eligible = [r for r in pool if r.get("eligible_trend")]
        selections[key] = eligible[0] if eligible else None
    # The factor register is deliberately separate from the geographic universe.
    factor_rows = []
    if not factor_df.empty:
        for _, f in factor_df.iterrows():
            ticker = clean(f.get("ticker"))
            factor_rows.append({
                "category": clean(f.get("category")), "ticker": ticker,
                "name": clean(f.get("name")), "isin": clean(f.get("isin")),
                "geography": clean(f.get("geography")),
                "benchmark_factor": clean(f.get("benchmark_factor")),
                "listing_venue": clean(f.get("listing_venue")),
                "status": "CALCOLATO" if ticker.endswith((".MI", ".DE", ".PA", ".AS", ".L")) and ticker in prices.columns else "LISTING DA MAPPARE",
                "note": "Ranking fattoriale separato; mai mescolato al ranking geografico."
            })
            if factor_rows[-1]["status"] == "CALCOLATO":
                metrics = score_series(prices[ticker])
                if metrics:
                    factor_rows[-1].update(metrics)
                else:
                    factor_rows[-1]["status"] = "STORICO INSUFFICIENTE"
    backtests = monthly_winner_backtest(prices, rows) if not prices.empty else {}
    all_dates = [r.get("price_date") for r in calculated if r.get("price_date")]
    coverage = {
        "index_count": len(rows),
        "calculated_count": sum(r["status"] == "CALCOLATO" for r in rows),
        "unmapped_geography_count": sum(r["status"] == "DA CLASSIFICARE" for r in rows),
        "price_unavailable_count": sum(r["status"] == "PREZZI NON DISPONIBILI" for r in rows),
        "insufficient_history_count": sum(r["status"] == "STORICO INSUFFICIENTE" for r in rows),
        "etp_separate_count": sum(r["status"] == "ETP SEPARATO" for r in rows),
        "factor_catalog_count": len(factor_rows),
        "factor_rankable_count": sum(r["status"] == "CALCOLATO" for r in factor_rows),
    }
    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "latest_price_date": max(all_dates) if all_dates else None,
        "method": {
            "lookback_sessions": LOOKBACK, "modified_sharpe_candidate": "mean(daily returns) / stdev(daily returns)^2",
            "momentum_windows_sessions": WINDOWS, "composite_weights": COMPOSITE_WEIGHTS,
            "trend_filter": "last adjusted price > SMA200 AND 12-month momentum > 0",
            "rebalance": "monthly signal; daily data refresh",
            "price_source": "Yahoo Finance auto_adjust=True; adjusted-price proxy, not an official total-return feed",
            "governance": [
                "Sei moduli geografici indipendenti; Global resta esclusivamente Global.",
                "Paesi, regionali, indici e Global sono classificati e classificati in ranking separati.",
                "ETF factor restano in un registro e ranking separato.",
                "ETP non UCITS espliciti non entrano nel ranking UCITS principale.",
                "Il Modified Sharpe con attenuatore 2 è un'approssimazione documentata storicamente, non la formula live proprietaria verificata.",
                "Il backtest mensile è esplorativo e non è la strategia ufficiale Logical Invest."
            ]
        },
        "modules": MODULES, "rankings": rankings, "selections": selections,
        "universe": rows, "factor_universe": factor_rows, "backtests": backtests,
        "coverage": coverage, "warnings": warnings_list
    }
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    print(json.dumps(coverage, ensure_ascii=False))
    print("Latest price date:", result["latest_price_date"])
    print("Output:", OUT)

if __name__ == "__main__":
    main()
