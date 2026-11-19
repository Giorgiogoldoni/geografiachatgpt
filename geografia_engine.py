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
SEED = ROOT / "ucits_country_universe_seed_2026-11-18.csv"
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
# Yahoo Finance symbols for listings explicitly identified on Borsa Italiana.
# Bare product tickers are never guessed into price symbols.
FACTOR_SYMBOL_MAP = {
    # Momentum: listing Borsa Italiana verificato
    "IWMO": "IWMO.MI", "IEMO": "IEMO.MI", "XDEM": "XDEM.MI",
    # Equal weight: listing Borsa Italiana verificato
    "SPEQ": "SPEQ.MI", "MWEQ": "MWEQ.MI", "MEEQ": "MEEQ.MI",
    "IEWQ": "IEWQ.MI", "WELE": "WELE.MI",
    # Quality
    "IWQU": "IWQU.MI", "IEQU": "IEQU.MI",
    "IAPD.MI": "IAPD.MI",
}

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
            "isin": "",
            "seed_eligibility": "",
            "verification_status": clean(r.get("verification_status")),
            "symbol": ticker if "." in ticker else (ticker + ".MI" if ticker == "AUHEUA" else ticker),
            "instrument_status": "ETP separato" if bucket == "etp" else "Listing/forma giuridica da verificare",
        })
    # Add researched UCITS seed candidates missing from the user INDEX.
    # Duplicate price listings are skipped; regional funds remain regional.
    seed_symbols = {
        "FLXK": ("FLXK.MI", "Corea del Sud"),
        "SJPA": ("SJPA.MI", "Giappone"),
        "FLXI": ("FLXI.MI", "India"),
        "CSCA": ("CSCA.MI", "Canada"),
        "IAEX": ("IAEX.AS", "Paesi Bassi"),
        "IBCJ": ("IBCJ.DE", "Polonia"),
        "D5BI": ("D5BI.DE", "Messico"),
        "SRSA": ("SRSA.MI", "Sudafrica"),
        "FLXB": ("FLXB.MI", "Brasile"),
        "IQQ5": ("IQQ5.DE", "Turchia"),
        "LTAM": ("LTAM.MI", "America Latina"),
        "ALAT": ("ALAT.MI", "America Latina"),
        "QDVM": ("QDVM.DE", "Israele"),
    }
    known = {r["symbol"]: r for r in rows}
    if SEED.exists():
        seed = pd.read_csv(SEED, dtype=str).fillna("")
        for _, s in seed.iterrows():
            base_ticker = clean(s.get("justetf_primary_ticker")).split()[0]
            if base_ticker not in seed_symbols:
                continue
            symbol, geography = seed_symbols[base_ticker]
            isin = clean(s.get("isin"))
            eligibility = clean(s.get("eligibility"))
            if symbol in known:
                known[symbol]["isin"] = isin
                known[symbol]["seed_eligibility"] = eligibility
                continue
            is_regional = base_ticker in {"LTAM", "ALAT"}
            module_id = module_for(geography)
            new_row = {
                "ticker": base_ticker, "name": clean(s.get("ucits_fund")),
                "geography": geography, "classification": "Regione" if is_regional else "Paese",
                "module_id": module_id, "module": MODULES.get(module_id, "Da classificare"),
                "subgroup": subgroup_for(geography), "bucket": "regional" if is_regional else "country",
                "portfolio": "REGIONALI" if is_regional else "PAESI",
                "isin": isin, "seed_eligibility": eligibility, "verification_status": eligibility,
                "symbol": symbol, "instrument_status": "UCITS seed; listing/data checks still required",
            }
            rows.append(new_row)
            known[symbol] = new_row
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


MOMENTUM_WEIGHT_SCENARIOS = {
    "prudente_40_30_20_10": {"label": "Prudente 40/30/20/10", "weights": {"12m": 0.40, "6m": 0.30, "3m": 0.20, "1m": 0.10}},
    "intermedia_35_30_20_15": {"label": "Intermedia 35/30/20/15", "weights": {"12m": 0.35, "6m": 0.30, "3m": 0.20, "1m": 0.15}},
    "reattiva_30_30_20_20": {"label": "Reattiva 30/30/20/20", "weights": {"12m": 0.30, "6m": 0.30, "3m": 0.20, "1m": 0.20}},
}

def momentum_weight_backtest(prices, rows):
    """Walk-forward monthly test of 1/3/6/12m momentum weight alternatives."""
    monthly = prices.resample("ME").last().dropna(how="all")
    if monthly.empty:
        return {"scenarios": {}, "note": "Prezzi mensili non disponibili."}
    latest = prices.dropna(how="all").index.max()
    if latest is not None and latest.to_period("M") == pd.Timestamp.now(tz="UTC").to_period("M"):
        monthly = monthly.iloc[:-1]
    groups = {}
    for row in rows:
        if row["module_id"] and row["bucket"] in {"country", "regional", "index", "global"} and row["symbol"] in prices.columns:
            groups.setdefault(row["module_id"] + "|" + row["bucket"], []).append(row)
    dates = list(monthly.index)
    if len(dates) < 2:
        return {"scenarios": {}, "note": "Storico mensile insufficiente."}

    sleeve_results = {}
    for group_key, candidates in groups.items():
        series_by_symbol = {c["symbol"]: prices[c["symbol"]].dropna() for c in candidates}
        scenario_data = {sid: {"returns": [], "picks": []} for sid in MOMENTUM_WEIGHT_SCENARIOS}
        for i in range(1, len(dates)):
            signal_date, hold_end = dates[i-1], dates[i]
            eligible = []
            for candidate in candidates:
                p = series_by_symbol[candidate["symbol"]].loc[:signal_date]
                if len(p) < MIN_HISTORY or len(p) < 253:
                    continue
                last = float(p.iloc[-1])
                if last <= 0:
                    continue
                mom = {
                    "1m": last / float(p.iloc[-22]) - 1,
                    "3m": last / float(p.iloc[-64]) - 1,
                    "6m": last / float(p.iloc[-127]) - 1,
                    "12m": last / float(p.iloc[-253]) - 1,
                }
                sma200 = float(p.tail(200).mean())
                if last > sma200 and mom["12m"] > 0:
                    eligible.append((candidate, mom))
            for sid, config in MOMENTUM_WEIGHT_SCENARIOS.items():
                ranked = [(sum(mom[k] * config["weights"][k] for k in config["weights"]), candidate)
                          for candidate, mom in eligible]
                chosen = max(ranked, key=lambda x: x[0])[1] if ranked else None
                ret = 0.0
                if chosen is not None:
                    a = monthly.loc[signal_date, chosen["symbol"]] if chosen["symbol"] in monthly.columns else np.nan
                    b = monthly.loc[hold_end, chosen["symbol"]] if chosen["symbol"] in monthly.columns else np.nan
                    if pd.notna(a) and pd.notna(b) and a > 0:
                        ret = float(b / a - 1)
                scenario_data[sid]["returns"].append(ret)
                scenario_data[sid]["picks"].append(chosen["ticker"] if chosen else None)
        sleeve_results[group_key] = scenario_data

    output = {"scenarios": {}, "method": {
        "signal": "Momentum composito 1/3/6/12 mesi a fine mese precedente",
        "filter": "Prezzo > SMA200 e momentum 12 mesi > 0",
        "holding": "Vincitore detenuto nel mese successivo; nessun vincitore = rendimento 0 (proxy liquidità)",
        "portfolio": "Media equiponderata delle sleeve area/categoria",
        "turnover": "Percentuale media mensile di sleeve con cambio ETF rispetto al mese precedente",
        "warmup_sessions": MIN_HISTORY, "sleeves": sorted(sleeve_results.keys())
    }}
    for sid, config in MOMENTUM_WEIGHT_SCENARIOS.items():
        returns, turnover = [], []
        for month_i in range(len(dates) - 1):
            sleeve_month_returns, switches, comparable = [], 0, 0
            for data in sleeve_results.values():
                sleeve_month_returns.append(data[sid]["returns"][month_i])
                picks = data[sid]["picks"]
                if month_i > 0:
                    comparable += 1
                    switches += int(picks[month_i] != picks[month_i-1])
            returns.append(float(np.mean(sleeve_month_returns)) if sleeve_month_returns else 0.0)
            turnover.append(switches / comparable if comparable else 0.0)
        periods = {}
        for period_key, requested_months in (("5y", 60), ("10y", 120)):
            n_months = min(requested_months, len(returns))
            arr = np.asarray(returns[-n_months:], dtype=float) if n_months else np.asarray([])
            turn = np.asarray(turnover[-n_months:], dtype=float) if n_months else np.asarray([])
            if len(arr):
                equity = np.cumprod(1.0 + arr)
                years = len(arr) / 12.0
                cagr = float(equity[-1] ** (1 / years) - 1) if equity[-1] > 0 and years > 0 else None
                vol = float(np.std(arr, ddof=1) * math.sqrt(12)) if len(arr) > 1 else None
                peaks = np.maximum.accumulate(np.concatenate(([1.0], equity)))
                drawdowns = np.concatenate(([1.0], equity)) / peaks - 1
                periods[period_key] = {
                    "months": int(len(arr)), "cagr": safe_float(cagr),
                    "volatility_annual": safe_float(vol),
                    "max_drawdown": safe_float(float(drawdowns.min())),
                    "total_return": safe_float(float(equity[-1] - 1)),
                    "avg_monthly_turnover": safe_float(float(np.mean(turn)) if len(turn) else 0.0),
                    "switches": int(round(float(np.sum(turn)) * max(1, len(sleeve_results))))
                }
            else:
                periods[period_key] = {"months": 0, "cagr": None, "volatility_annual": None,
                                       "max_drawdown": None, "total_return": None,
                                       "avg_monthly_turnover": None, "switches": 0}
        output["scenarios"][sid] = {"label": config["label"], "weights": config["weights"], "periods": periods}
    output["note"] = "Confronto sperimentale walk-forward. Non modifica il ranking operativo corrente, basato sul Modified Sharpe candidato."
    return output


def momentum_research_backtest(prices, rows):
    """Point-in-time monthly research: three trend filters, four momentum mixes,
    1/3/5/10y windows, explicit turnover costs and a global benchmark.
    Current-universe survivorship and listing-currency limitations are disclosed.
    """
    monthly = prices.resample("ME").last()
    if monthly.empty:
        return {"strategies": {}, "benchmark": {}, "note": "Prezzi mensili non disponibili."}
    latest = prices.dropna(how="all").index.max()
    if latest is not None and latest.to_period("M") == pd.Timestamp.now(tz="UTC").to_period("M"):
        monthly = monthly.iloc[:-1]
    groups = {}
    for row in rows:
        if row["module_id"] and row["bucket"] in {"country", "regional", "index", "global"} and row["symbol"] in prices.columns:
            groups.setdefault(row["module_id"] + "|" + row["bucket"], []).append(row)
    dates = list(monthly.index)
    if len(dates) < 2:
        return {"strategies": {}, "benchmark": {}, "note": "Storico mensile insufficiente."}

    mixes = {
        "12m": {"12m": 1.0},
        "prudente_40_30_20_10": {"12m": .40, "6m": .30, "3m": .20, "1m": .10},
        "intermedia_35_30_20_15": {"12m": .35, "6m": .30, "3m": .20, "1m": .15},
        "reattiva_30_30_20_20": {"12m": .30, "6m": .30, "3m": .20, "1m": .20},
    }
    filters = {
        "momentum_puro": "Solo ranking momentum; nessun filtro trend",
        "momentum_sma200": "Prezzo > SMA200",
        "momentum_sma200_assoluto": "Prezzo > SMA200 e momentum 12m > 0",
    }
    # Each sleeve is kept independent; a missing signal is a cash sleeve (0 return).
    results = {}
    for mix_id, weights in mixes.items():
        for filter_id, filter_label in filters.items():
            sleeve_months = {g: {"returns": [], "picks": [], "missing": 0} for g in groups}
            for i in range(1, len(dates)):
                signal_date, hold_end = dates[i-1], dates[i]
                for group_key, candidates in groups.items():
                    ranked = []
                    for c in candidates:
                        hist = prices[c["symbol"]].loc[:signal_date].dropna()
                        if len(hist) < 253:
                            continue
                        last = float(hist.iloc[-1])
                        if last <= 0:
                            continue
                        mom = {
                            "1m": last / float(hist.iloc[-22]) - 1,
                            "3m": last / float(hist.iloc[-64]) - 1,
                            "6m": last / float(hist.iloc[-127]) - 1,
                            "12m": last / float(hist.iloc[-253]) - 1,
                        }
                        sma = float(hist.tail(200).mean())
                        if filter_id in ("momentum_sma200", "momentum_sma200_assoluto") and not last > sma:
                            continue
                        if filter_id == "momentum_sma200_assoluto" and not mom["12m"] > 0:
                            continue
                        score = sum(mom[k] * w for k, w in weights.items())
                        ranked.append((score, c))
                    chosen = max(ranked, key=lambda z: z[0])[1] if ranked else None
                    ret = 0.0
                    if chosen is not None:
                        a = monthly.at[signal_date, chosen["symbol"]] if chosen["symbol"] in monthly.columns else np.nan
                        b = monthly.at[hold_end, chosen["symbol"]] if chosen["symbol"] in monthly.columns else np.nan
                        if pd.notna(a) and pd.notna(b) and a > 0:
                            ret = float(b / a - 1)
                        else:
                            sleeve_months[group_key]["missing"] += 1
                    sleeve_months[group_key]["returns"].append(ret)
                    sleeve_months[group_key]["picks"].append(chosen["ticker"] if chosen else None)

            n_sleeves = max(1, len(sleeve_months))
            gross = []
            turnover = []
            for mi in range(len(dates)-1):
                vals, switches = [], 0
                for data in sleeve_months.values():
                    vals.append(data["returns"][mi])
                    picks = data["picks"]
                    if mi > 0 and picks[mi] != picks[mi-1]:
                        switches += 1
                gross.append(float(np.mean(vals)) if vals else 0.0)
                turnover.append(switches / n_sleeves)
            results[mix_id + "|" + filter_id] = {
                "label": mix_id + " · " + filter_id,
                "weights": weights, "filter": filter_label,
                "gross_returns": gross, "turnover": turnover,
                "missing_holding_prices": int(sum(x["missing"] for x in sleeve_months.values())),
                "periods": {}
            }

    def metrics_for(arr):
        if len(arr) == 0:
            return {"months": 0, "cagr": None, "volatility_annual": None, "max_drawdown": None, "total_return": None}
        equity = np.cumprod(1.0 + arr)
        peak = np.maximum.accumulate(np.concatenate(([1.0], equity)))
        curve = np.concatenate(([1.0], equity))
        years = len(arr) / 12.0
        return {
            "months": int(len(arr)),
            "cagr": safe_float(float(equity[-1] ** (1/years) - 1) if equity[-1] > 0 and years else None),
            "volatility_annual": safe_float(float(np.std(arr, ddof=1) * math.sqrt(12)) if len(arr) > 1 else 0.0),
            "max_drawdown": safe_float(float((curve / peak - 1).min())),
            "total_return": safe_float(float(equity[-1] - 1)),
        }

    cost_sides_bps = [0, 5, 10, 15]  # per side; a full ETF switch incurs sell + buy
    for item in results.values():
        for period, months in (("1y",12),("3y",36),("5y",60),("10y",120)):
            n = min(months, len(item["gross_returns"]))
            start = len(item["gross_returns"]) - n
            gross = np.asarray(item["gross_returns"][start:], dtype=float)
            turns = np.asarray(item["turnover"][start:], dtype=float)
            period_result = {"gross": metrics_for(gross), "cost_sensitivity": {}}
            for bps in cost_sides_bps:
                net = gross - (turns * (2.0 * bps / 10000.0))
                period_result["cost_sensitivity"][str(bps) + "_bps_per_side"] = metrics_for(net)
            period_result["avg_monthly_turnover"] = safe_float(float(np.mean(turns)) if len(turns) else 0.0)
            period_result["switch_months"] = int(np.sum(turns > 0))
            item["periods"][period] = period_result

    # Global benchmark is shown independently, not blended into geographic sleeves.
    benchmark = {}
    if BENCHMARK in monthly.columns:
        b = monthly[BENCHMARK].dropna().pct_change().dropna()
        for period, months in (("1y",12),("3y",36),("5y",60),("10y",120)):
            benchmark[period] = metrics_for(np.asarray(b.iloc[-months:], dtype=float))
    return {
        "strategies": results,
        "benchmark": {"ticker": BENCHMARK, "periods": benchmark,
                      "note": "Benchmark globale buy-and-hold; rendimento nella valuta di quotazione del simbolo."},
        "method": {
            "signal": "Prezzi disponibili fino alla chiusura del mese precedente; detenzione nel mese successivo.",
            "universe": "ETF correnti dell'indice; storico minimo 253 sedute alla data del segnale.",
            "costs": "Sensibilità 0/5/10/15 punti base per lato; cambio ETF addebita vendita + acquisto.",
            "portfolio": "Sleeve area/categoria equiponderate; nessun segnale = liquidità a rendimento zero.",
            "currency": "Rendimenti nella valuta della quotazione Yahoo; non convertiti in EUR in questo test.",
            "survivorship": "Il filtro di anzianità rispetta la data di prima osservazione, ma l'indice corrente non contiene ETF delistati: survivorship bias residuo.",
            "dividends": "Yahoo auto_adjust=True; proxy adjusted-price, non NAV ufficiale né feed total-return dell'emittente.",
            "missing_prices": "Mese senza prezzo di uscita per l'ETF selezionato conteggiato a rendimento zero e segnalato; da verificare prima dell'uso operativo."
        },
        "note": "Ricerca comparativa; non modifica selezioni o ranking operativo."
    }


# Curated inception dates: only dates supported by issuer or exchange documents.
TICKER_ISIN_OVERRIDES = {
    "ALAT": "LU1681045024", "VUSA": "IE00B3XXRP09",
    "CSMIB": "IE00B53L4X51", "IMIB": "IE00B1XNH568",
    "WMIB": "XS2427354985", "XCHA": "LU0779800910",
    "DJE": "FR0007056841",
    "LCCN": "LU1841731745", "XDEB": "IE00BL25JN58",
    "MCHN": "IE00BK80XL30", "FLXT": "IE000CM02H85",
    "FLXU": "IE00BF2B0P08", "SAUDI": "IE000C7DDDX4",
    "SAUS": "IE00B5377D42", "IS3U": "IE00BP3QZJ36",
    "HSTE": "IE00BMWXKN31", "LGUS": "IE00BFXR5Q31",
    "AUHEUA": "IE00BWT3KS11", "SPXE": "IE00BYYW2V44",
    "CSNDX": "IE00B53SZB19", "INDO": "LU1900065811",
    "TUR": "LU1900067601", "WRTY": "XS3003324129",
    "WS5X": "XS2427362145", "WSPX": "XS2427355958",
    "C40": "LU1681046931", "FMI": "LU1681037518",
    "VJPE": "IE00BFMXYY33", "SPY5": "IE00B6YX5C33",
    "SVE": "LU1169830103", "SP1E": "IE000YELA4E3",
    "WNAS": "XS3003325795", "WSPE": "XS3151431957",
    "XBAS": "LU0659578842", "XPQP": "LU0592215403",
    "EXS1": "DE0005933931", "CN1": "LU1681044647", "EST": "LU1900066462",
    "QTOP": "IE000Z7P04F4",
    "IBZL": "IE00B0M63516", "SPXJ": "IE00B4WXJD03",
    "XCS3": "LU0514694370", "XCS4": "LU0514694966",
    "XESD": "LU0994505336", "XSMI": "LU0274221281",
    "D5BI": "LU0476289466", "IAEX": "IE00B0M62Y33",
    "WRD": "IE00B4X9L533",
}
ETF_LAUNCH_OVERRIDES = {
    "IE00BHZRQZ17": ("2019-06-25", "Franklin Templeton", "ALTA"),
    "IE00BHZRR030": ("2019-06-04", "Franklin Templeton", "ALTA"),
    "IE00BHZRQY00": ("2019-06-04", "justETF", "MEDIA"),
    "IE00B14X4T88": ("2006-06-02", "justETF", "MEDIA"),
    "IE00B52SF786": ("2010-01-12", "justETF", "MEDIA"),
    "IE00B4M7GH52": ("2011-01-21", "justETF", "MEDIA"),
    "IE00B52XQP83": ("2010-01-22", "justETF", "MEDIA"),
    "IE00B4L5YX21": ("2009-09-25", "justETF", "MEDIA"),
    "IE00B1FZS574": ("2006-11-03", "justETF", "MEDIA"),
    "IE00BD1F4N50": ("2016-10-13", "justETF", "MEDIA"),
    "IE00BP3QZG05": ("2016-01-18", "justETF", "MEDIA"),
    "LU1841731745": ("2018-07-05", "justETF", "MEDIA"),
    "IE00BL25JN58": ("2014-09-05", "DWS / justETF", "ALTA"),
    "IE00BK80XL30": ("2021-03-01", "Invesco", "ALTA"),
    "IE000CM02H85": ("2022-03-21", "justETF", "MEDIA"),
    "IE00BF2B0P08": ("2017-09-06", "justETF", "MEDIA"),
    "IE000C7DDDX4": ("2024-10-28", "justETF", "MEDIA"),
    "IE00B5377D42": ("2010-01-22", "justETF", "MEDIA"),
    "IE00BP3QZJ36": ("2014-09-05", "justETF", "MEDIA"),
    "IE00BMWXKN31": ("2020-12-09", "justETF", "MEDIA"),
    "IE00BFXR5Q31": ("2018-10-08", "justETF", "MEDIA"),
    "IE00BWT3KS11": ("2015-11-27", "justETF", "MEDIA"),
    "IE00BYYW2V44": ("2018-10-31", "justETF / State Street", "ALTA"),
    "IE00B53SZB19": ("2010-01-26", "justETF", "MEDIA"),
    "LU1900065811": ("2011-07-04", "justETF", "MEDIA"),
    "LU1900067601": ("2006-08-11", "justETF / Amundi first NAV", "MEDIA"),
    "XS3003324129": ("2025-04-08", "WisdomTree", "ALTA"),
    "XS2427362145": ("2022-03-02", "WisdomTree", "ALTA"),
    "XS2427355958": ("2022-03-02", "WisdomTree", "ALTA"),
    "LU1681046931": ("2003-02-28", "Amundi first NAV / justETF", "MEDIA"),
    "LU1681037518": ("2010-06-08", "Amundi", "ALTA"),
    "IE00BFMXYY33": ("2020-01-31", "Vanguard", "ALTA"),
    "IE00B6YX5C33": ("2012-03-19", "State Street", "ALTA"),
    "LU1169830103": ("2020-06-18", "justETF", "MEDIA"),
    "IE000YELA4E3": ("2025-07-17", "justETF", "MEDIA"),
    "XS3003325795": ("2025-04-08", "WisdomTree", "ALTA"),
    "XS3151431957": ("2025-09-25", "WisdomTree", "ALTA"),
    "LU0659578842": ("2011-09-19", "justETF", "MEDIA"),
    "LU0592215403": ("2011-04-12", "justETF", "MEDIA"),
    "DE0005933931": ("2000-12-27", "BlackRock", "ALTA"),
    "LU1681044647": ("2008-09-16", "Amundi first NAV", "ALTA"),
    "LU1900066462": ("2005-07-21", "Amundi / justETF", "MEDIA"),
    "IE00B0M63516": ("2005-11-18", "justETF", "MEDIA"),
    "IE00B4WXJD03": ("2009-04-17", "BlackRock / justETF", "ALTA"),
    "LU0514694370": ("2010-06-24", "justETF", "MEDIA"),
    "LU0514694966": ("2011-12-20", "justETF", "MEDIA"),
    "LU0994505336": ("2013-12-19", "justETF", "MEDIA"),
    "LU0274221281": ("2007-01-22", "DWS / justETF", "ALTA"),
    "LU0476289466": ("2010-03-26", "justETF", "MEDIA"),
    "IE00B0M62Y33": ("2005-11-18", "justETF", "MEDIA"),
    "IE00B4X9L533": ("2010-12-08", "HSBC / justETF", "ALTA"),
    "IE000Z7P04F4": ("2025-01-28", "justETF", "MEDIA"),
    "IE00BQN1K786": ("2015-01-16", "justETF", "MEDIA"),
    "IE00BQN1K901": ("2015-01-16", "justETF", "MEDIA"),
    "IE00BQN1KC32": ("2015-01-16", "justETF", "MEDIA"),
    "IE00BP3QZ825": ("2014-10-03", "justETF", "MEDIA"),
    "IE00BP3QZB59": ("2014-10-03", "justETF", "MEDIA"),
    "IE00BL25JP72": ("2014-09-05", "justETF", "MEDIA"),
    "IE00BL25JM42": ("2014-09-11", "justETF", "MEDIA"),
    "IE000OEF25S1": ("2024-09-04", "justETF", "MEDIA"),
    "IE000LUZJNI7": ("2025-03-04", "justETF", "MEDIA"),
    "IE000LAP5Z18": ("2022-05-24", "justETF", "MEDIA"),
    "IE00BNGJJT35": ("2021-04-06", "justETF", "MEDIA"),
    "IE00B27YCK28": ("2007-10-15", "justETF", "MEDIA"),
    "IE00BP3QZ601": ("2014-10-03", "justETF", "MEDIA"),
    "IE00BQN1K562": ("2015-01-16", "justETF", "MEDIA"),
    "LU1681045024": ("2011-04-28", "justETF", "MEDIA"),
    "IE00B3XXRP09": ("2012-05-22", "justETF", "MEDIA"),
    "IE00B53L4X51": ("2010-01-26", "justETF", "MEDIA"),
    "IE00B1XNH568": ("2007-07-06", "justETF", "MEDIA"),
    "XS2427354985": ("2022-03-02", "WisdomTree / justETF", "ALTA"),
    "LU0779800910": ("2012-06-27", "justETF", "MEDIA"),
    "FR0007056841": ("2001-04-04", "justETF", "MEDIA"),
}
SHARE_CLASS_LAUNCH_OVERRIDES = {
    "LU1681046931": ("2018-02-14", "Amundi factsheet"),
    "LU1681037518": ("2018-01-31", "Amundi factsheet / listing"),
    "LU1681044647": ("2018-03-22", "Amundi factsheet"),
    "LU1900067601": ("2019-03-14", "Amundi factsheet"),
    "LU1900066462": ("2019-03-14", "Amundi factsheet"),
}
BORSA_LISTING_OVERRIDES = {
    "IE00BP3QZ601": ("2015-02-16", "Borsa Italiana"),
    "IE00BP3QZ825": ("2015-02-16", "Borsa Italiana"),
    "IE00BP3QZB59": ("2015-02-16", "Borsa Italiana"),
    "IE00BP3QZD73": ("2015-02-16", "Borsa Italiana"),
    "IE00BQN1K562": ("2015-02-16", "Borsa Italiana"),
    "IE00BQN1K786": ("2015-02-16", "Borsa Italiana"),
    "IE00BQN1K901": ("2015-02-16", "Borsa Italiana"),
    "IE00BQN1KC32": ("2015-02-16", "Borsa Italiana"),
}

def build_lifecycle_registry(rows, factor_rows, prices):
    """Build auditable ETF lifecycle register; never infer inception from price history."""
    combined = [(r, "GEOGRAFICO") for r in rows] + [(r, "FACTOR") for r in factor_rows]
    registry, seen = [], set()
    for row, source_type in combined:
        isin = row.get("isin", "") or TICKER_ISIN_OVERRIDES.get((row.get("ticker", "").split(".")[0]), "")
        symbol = row.get("symbol") or ""
        identity = isin or symbol or row.get("ticker", "")
        if not identity or identity in seen:
            continue
        seen.add(identity)
        launch = ETF_LAUNCH_OVERRIDES.get(isin, ("", "", "DA VERIFICARE"))
        listing = BORSA_LISTING_OVERRIDES.get(isin, ("", ""))
        series = prices[symbol].dropna() if symbol and symbol in prices.columns else pd.Series(dtype=float)
        registry.append({
            "universe": source_type, "ticker": row.get("ticker", ""),
            "symbol": symbol, "isin": isin, "name": row.get("name", ""),
            "geography": row.get("geography", ""),
            "category": row.get("bucket", row.get("category", "")),
            "fund_launch_date": launch[0], "fund_launch_source": launch[1],
            "fund_launch_confidence": launch[2],
            "share_class_launch_date": SHARE_CLASS_LAUNCH_OVERRIDES.get(isin, ("", ""))[0], "listing_date": listing[0],
            "listing_date_source": listing[1],
            "first_price_date": series.index[0].strftime("%Y-%m-%d") if not series.empty else "",
            "last_price_date": series.index[-1].strftime("%Y-%m-%d") if not series.empty else "",
            "status": ("ETP/ETN - forma distinta da ETF" if row.get("ticker", "").split(".")[0] in {"WMIB", "WRTY", "WS5X", "WSPX", "WNAS", "WSPE"} else ("DATA LANCIO VERIFICATA" if launch[0] else "DA VERIFICARE")),
        })
    return sorted(registry, key=lambda x: (x["ticker"], x["isin"]))


def main():
    rows = load_universe()
    factor_df = pd.read_csv(FACTORS, dtype=str).fillna("") if FACTORS.exists() else pd.DataFrame()
    factor_symbols = []
    if not factor_df.empty:
        factor_symbols = [FACTOR_SYMBOL_MAP.get(clean(x), clean(x))
                          for x in factor_df["ticker"].tolist()
                          if clean(x).endswith((".MI", ".DE", ".PA", ".AS", ".L"))
                          or clean(x) in FACTOR_SYMBOL_MAP]
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
            symbol = FACTOR_SYMBOL_MAP.get(ticker, ticker if ticker.endswith((".MI", ".DE", ".PA", ".AS", ".L")) else "")
            geo = clean(f.get("geography"))
            factor_row = {
                "category": clean(f.get("category")), "ticker": ticker, "symbol": symbol or None,
                "name": clean(f.get("name")), "isin": clean(f.get("isin")),
                "geography": geo, "module_id": module_for(geo),
                "benchmark_factor": clean(f.get("benchmark_factor")),
                "listing_venue": clean(f.get("listing_venue")),
                "status": "IN ATTESA MAPPATURA" if not symbol else ("CALCOLATO" if symbol in prices.columns else "PREZZI NON DISPONIBILI"),
                "note": "Ranking fattoriale separato; mai mescolato al ranking geografico."
            }
            if factor_row["status"] == "CALCOLATO":
                metrics = score_series(prices[symbol])
                if metrics:
                    factor_row.update(metrics)
                else:
                    factor_row["status"] = "STORICO INSUFFICIENTE"
            factor_rows.append(factor_row)
    lifecycle_registry = build_lifecycle_registry(rows, factor_rows, prices)
    pd.DataFrame(lifecycle_registry).to_csv(ROOT / "etf_lifecycle_registry.csv", index=False)
    factor_rankings = {}
    for factor in sorted({x["category"] for x in factor_rows}):
        for geography in sorted({x["geography"] for x in factor_rows if x["category"] == factor}):
            pool = [x for x in factor_rows if x["category"] == factor and x["geography"] == geography and x["status"] == "CALCOLATO"]
            if pool:
                factor_rankings[factor + "|" + geography] = sorted(
                    pool, key=lambda x: rank_key(x, "modified_sharpe_candidate"), reverse=True)
    backtests = monthly_winner_backtest(prices, rows) if not prices.empty else {}
    momentum_weight_comparison = momentum_weight_backtest(prices, rows) if not prices.empty else {"scenarios": {}, "note": "Prezzi non disponibili."}
    momentum_research = momentum_research_backtest(prices, rows) if not prices.empty else {"strategies": {}, "benchmark": {}, "note": "Prezzi non disponibili."}
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
        "factor_pending_mapping_count": sum(r["status"] == "IN ATTESA MAPPATURA" for r in factor_rows),
    }
    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "latest_price_date": max(all_dates) if all_dates else None,
        "method": {
            "lookback_sessions": LOOKBACK, "modified_sharpe_candidate": "mean(daily returns) / stdev(daily returns)^2",
            "momentum_windows_sessions": WINDOWS, "composite_weights": COMPOSITE_WEIGHTS,
            "momentum_weight_scenarios": MOMENTUM_WEIGHT_SCENARIOS,
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
        "universe": rows, "factor_universe": factor_rows, "factor_rankings": factor_rankings,
        "etf_lifecycle_registry": lifecycle_registry, "backtests": backtests,
        "coverage": coverage, "momentum_weight_comparison": momentum_weight_comparison,
        "momentum_research": momentum_research, "warnings": warnings_list
    }
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    print(json.dumps(coverage, ensure_ascii=False))
    print("Latest price date:", result["latest_price_date"])
    print("Output:", OUT)

if __name__ == "__main__":
    main()
