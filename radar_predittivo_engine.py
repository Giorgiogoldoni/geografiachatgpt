#!/usr/bin/env python3
"""Independent technical early-warning radar for geographic UCITS ETFs.

Reads the existing geographic universe, downloads adjusted OHLC prices, calculates
Alligator, KAMA, ROC38, Awesome Oscillator, Vortex, RSI and MA38/200, then writes
radar-predittivo.json. Does not modify the existing geographic engine or RAPTOR.
"""
from __future__ import annotations
import json, math, warnings
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "geografia-motore.json"
OUT = ROOT / "radar-predittivo.json"
MIN_HISTORY = 220
START_DATE = "2005-01-01"  # Storico originale del Radar geografico
FACTOR_START_DATE = "2015-01-01"  # Finestra dedicata agli ETF factor
CHUNK_SIZE = 10

def finite(value):
    try:
        x = float(value)
        return x if math.isfinite(x) else None
    except (TypeError, ValueError):
        return None

def collect_universe(data):
    """Use the current geographic rankings as the source of truth for membership."""
    found = {}
    for group, items in (data.get("rankings") or {}).items():
        if not isinstance(items, list):
            continue
        for row in items:
            symbol = str(row.get("symbol") or "").strip()
            if not symbol:
                continue
            bucket = str(row.get("bucket") or row.get("classification") or "geography")
            item = {
                "symbol": symbol,
                "ticker": row.get("ticker", symbol),
                "name": row.get("name", row.get("fund", symbol)),
                "geography": row.get("geography", row.get("country", "")),
                "module": row.get("module", row.get("module_id", group)),
                "group": group,
                "bucket": bucket,
                "isin": row.get("isin", ""),
            }
            # Prefer the row with an ISIN and a more specific geography label.
            old = found.get(symbol)
            if old is None or (not old.get("isin") and item.get("isin")):
                found[symbol] = item
    return list(found.values())

def collect_factor_universe():
    """Separate verified UCITS factor universe; never mixed with geographic rankings."""
    import re
    path = ROOT / "data" / "geografia_index_factor_14.csv"
    if not path.exists():
        return []
    catalog = pd.read_csv(path).fillna("")
    allowed = {"MOMENTUM", "QUALITY", "VALUE"}
    found = {}
    for _, row in catalog.iterrows():
        category = str(row.get("category", "")).upper()
        if category not in allowed:
            continue
        status = str(row.get("verification_status", ""))
        match = re.search(r"Yahoo Finance symbol ([A-Z0-9.^=_-]+)", status)
        if not match:
            continue
        symbol = match.group(1).strip()
        geography = str(row.get("geography", ""))
        if geography not in {"Globale", "Stati Uniti", "Europa"}:
            continue
        found[symbol] = {
            "symbol": symbol, "ticker": str(row.get("ticker", "")),
            "name": str(row.get("name", symbol)), "geography": geography,
            "module": f"{geography} · {category}", "group": category,
            "bucket": "factor", "isin": str(row.get("isin", "")),
            "factor": category, "universe": "factor"
        }
    return list(found.values())

def _clean_frame(raw, symbol):
    if raw is None or raw.empty:
        return None
    if isinstance(raw.columns, pd.MultiIndex):
        if symbol in raw.columns.get_level_values(0):
            part = raw[symbol]
        elif symbol in raw.columns.get_level_values(-1):
            part = raw.xs(symbol, axis=1, level=-1)
        elif "Close" in raw.columns.get_level_values(0):
            return None
        else:
            return None
    else:
        part = raw
    required = {"High", "Low", "Close"}
    if not required.issubset(set(part.columns)):
        return None
    part = part[["High", "Low", "Close"]].copy()
    part.index = pd.to_datetime(part.index)
    if getattr(part.index, "tz", None) is not None:
        part.index = part.index.tz_localize(None)
    part = part[~part.index.duplicated(keep="last")].sort_index()
    return part.apply(pd.to_numeric, errors="coerce").dropna()

def download_prices(symbols, start_date=START_DATE):
    frames, errors = {}, {}
    for start in range(0, len(symbols), CHUNK_SIZE):
        batch = symbols[start:start + CHUNK_SIZE]
        raw = None
        try:
            # Same Yahoo Finance request convention as the established UCITS engine.
            raw = yf.download(
                tickers=batch, start=start_date, auto_adjust=True,
                actions=False, progress=False, threads=True, group_by="column"
            )
        except Exception as exc:
            for symbol in batch:
                errors[symbol] = f"Batch download error: {type(exc).__name__}: {exc}"
        for symbol in batch:
            part = _clean_frame(raw, symbol) if raw is not None and not raw.empty else None
            if part is not None and not part.empty:
                frames[symbol] = part
                continue
            # Individual fallback is deliberately limited to symbols missed by the batch.
            try:
                one = yf.download(
                    tickers=symbol, start=start_date, auto_adjust=True,
                    actions=False, progress=False, threads=False
                )
                part = _clean_frame(one, symbol)
                if part is not None and not part.empty:
                    frames[symbol] = part
                    errors.pop(symbol, None)
                else:
                    errors[symbol] = "Yahoo Finance returned no usable OHLC rows (batch and individual retry)."
            except Exception as exc:
                errors[symbol] = f"Individual retry error: {type(exc).__name__}: {exc}"
    return frames, errors

def kama(series, er_period=10, fast=2, slow=30):
    values = series.to_numpy(dtype=float)
    out = np.full(len(values), np.nan)
    fast_sc = 2.0 / (fast + 1.0)
    slow_sc = 2.0 / (slow + 1.0)
    for i in range(er_period, len(values)):
        change = abs(values[i] - values[i-er_period])
        volatility = np.abs(np.diff(values[i-er_period:i+1])).sum()
        er = change / volatility if volatility else 0.0
        sc = (er * (fast_sc - slow_sc) + slow_sc) ** 2
        previous = out[i-1] if np.isfinite(out[i-1]) else values[i-1]
        out[i] = previous + sc * (values[i] - previous)
    return pd.Series(out, index=series.index)

def calculate(frame):
    high, low, close = frame["High"], frame["Low"], frame["Close"]
    median = (high + low) / 2.0
    # Bill Williams Alligator: smoothed median price, shifted into the future.
    jaw = median.ewm(alpha=1/13, adjust=False).mean().shift(8)
    teeth = median.ewm(alpha=1/8, adjust=False).mean().shift(5)
    lips = median.ewm(alpha=1/5, adjust=False).mean().shift(3)
    k = kama(close)
    roc = close.pct_change(38) * 100.0
    ao = median.rolling(5).mean() - median.rolling(34).mean()
    ao_signal = ao.rolling(5).mean()
    tr = pd.concat([
        high-low, (high-close.shift()).abs(), (low-close.shift()).abs()
    ], axis=1).max(axis=1)
    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0.0)
    minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0.0)
    atr14 = tr.ewm(alpha=1/14, adjust=False, min_periods=14).mean()
    plus_di = 100.0 * plus_dm.ewm(alpha=1/14, adjust=False, min_periods=14).mean() / atr14
    minus_di = 100.0 * minus_dm.ewm(alpha=1/14, adjust=False, min_periods=14).mean() / atr14
    dx = 100.0 * (plus_di-minus_di).abs() / (plus_di+minus_di).replace(0, np.nan)
    adx14 = dx.ewm(alpha=1/14, adjust=False, min_periods=14).mean()
    vm_plus = (high-low.shift()).abs()
    vm_minus = (low-high.shift()).abs()
    vi_plus = vm_plus.rolling(14).sum() / tr.rolling(14).sum()
    vi_minus = vm_minus.rolling(14).sum() / tr.rolling(14).sum()
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1/14, adjust=False, min_periods=14).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1/14, adjust=False, min_periods=14).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - 100/(1+rs)
    rsi = rsi.where(loss.ne(0), 100.0)
    ma38 = close.rolling(38).mean()
    ma50 = close.rolling(50).mean()
    ma200 = close.rolling(200).mean()

    out = pd.DataFrame({
        "close": close, "jaw": jaw, "teeth": teeth, "lips": lips,
        "kama": k, "roc38": roc, "ao": ao, "ao_signal": ao_signal,
        "vi_plus": vi_plus, "vi_minus": vi_minus, "adx14": adx14, "plus_di": plus_di, "minus_di": minus_di, "rsi14": rsi,
        "ma38": ma38, "ma50": ma50, "ma200": ma200,
    }).dropna(subset=["close"])
    # Block scores avoid counting several near-duplicate oscillators as independent votes.
    alligator_bull = (lips > teeth) & (teeth > jaw)
    alligator_open = (lips-jaw) > (lips-jaw).shift(5)
    kama_bull = (k > k.shift(5)) & (close > k)
    awakening = 12.5 * (alligator_bull & alligator_open).astype(float) + 12.5 * kama_bull.astype(float)
    acceleration = 12.5 * (roc > 0).astype(float) + 12.5 * ((roc > roc.shift(5)) & (ao > ao_signal)).astype(float)
    reversal = 10.0 * (vi_plus > vi_minus).astype(float) + 10.0 * ((rsi > 50) & (rsi < 70) & (rsi > rsi.shift(5))).astype(float)
    confirmation = 15.0 * (close > ma38).astype(float) + 15.0 * (ma38 > ma200).astype(float)
    out["score_awakening"] = awakening
    out["score_acceleration"] = acceleration
    out["score_reversal"] = reversal
    out["score_confirmation"] = confirmation
    out["score"] = awakening + acceleration + reversal + confirmation
    out["alligator_bull"] = alligator_bull
    out["alligator_open"] = alligator_open
    out["kama_rising"] = k > k.shift(5)
    out["vortex_bull"] = vi_plus > vi_minus    out["investable_filter"] = (close > ma200) & (ma38 > ma200) & (roc > 0)
    out["roc5"] = close.pct_change(5) * 100.0
    out["roc10"] = close.pct_change(10) * 100.0
    out["roc21"] = close.pct_change(21) * 100.0
    out["kama_slope5"] = k.pct_change(5) * 100.0
    # Early-warning score: deliberately avoids MA200/long-trend confirmation.
    # It rewards short-term positive momentum, acceleration and an improving structure.
    early = (
        15.0 * (out["roc5"] > 0).astype(float)
        + 10.0 * (out["roc10"] > 0).astype(float)
        + 10.0 * (out["roc21"] > 0).astype(float)
        + 15.0 * (out["roc5"] > out["roc10"]).astype(float)
        + 10.0 * (out["roc10"] > out["roc21"]).astype(float)
        + 10.0 * (close > k).astype(float)
        + 10.0 * (out["kama_slope5"] > 0).astype(float)
        + 10.0 * (lips > teeth).astype(float)
        + 5.0 * (vi_plus > vi_minus).astype(float)
        + 5.0 * ((rsi >= 45) & (rsi <= 68) & (rsi > rsi.shift(5))).astype(float)
    )
    out["score_early"] = early
    out["roc63"] = close.pct_change(63) * 100.0
    out["roc126"] = close.pct_change(126) * 100.0
    out["roc252"] = close.pct_change(252) * 100.0
    daily_returns = close.pct_change()
    out["return_68d"] = close.pct_change(68) * 100.0
    out["composite_momentum"] = (0.4*close.pct_change(63) + 0.3*close.pct_change(126) + 0.3*close.pct_change(252)) * 100.0
    rolling_vol = daily_returns.rolling(68).std(ddof=1)
    out["volatility_68"] = rolling_vol * np.sqrt(252) * 100.0
    out["trend_stability_21"] = (close > k).rolling(21).mean() * 100.0
    out["kama_slope21"] = k.pct_change(21) * 100.0
    out["modified_sharpe_68"] = daily_returns.rolling(68).mean() / rolling_vol.pow(2)
    return out

def latest_record(meta, ind):
    r = ind.iloc[-1]
    score = finite(r["score"]) or 0.0
    investable = bool(r["investable_filter"]) and score >= 65
    if score >= 75:
        label = "FORTE MIGLIORAMENTO"
    elif score >= 55:
        label = "IN MIGLIORAMENTO"
    else:
        label = "DEBOLE / NON CONFERMATO"
    if investable:
        invest_label = "FILTRO INVESTIBILE SUPERATO"
    else:
        invest_label = "FILTRO INVESTIBILE NON SUPERATO"
    return {
        **meta,
        "date": ind.index[-1].strftime("%Y-%m-%d"),
        "price": finite(r["close"]),
        "score": round(score, 1),
        "score_awakening": round(finite(r["score_awakening"]) or 0, 1),
        "score_acceleration": round(finite(r["score_acceleration"]) or 0, 1),
        "score_reversal": round(finite(r["score_reversal"]) or 0, 1),
        "score_confirmation": round(finite(r["score_confirmation"]) or 0, 1),
        "alligator_bull": bool(r["alligator_bull"]),
        "alligator_open": bool(r["alligator_open"]),
        "kama_rising": bool(r["kama_rising"]),
        "roc38": finite(r["roc38"]),
        "ao": finite(r["ao"]),
        "ao_signal": finite(r["ao_signal"]),
        "vortex_plus": finite(r["vi_plus"]),
        "vortex_minus": finite(r["vi_minus"]),
        "rsi14": finite(r["rsi14"]),
        "ma38": finite(r["ma38"]),
        "ma50": finite(r["ma50"]),
        "ma200": finite(r["ma200"]),
        "roc5": finite(r["roc5"]),
        "roc10": finite(r["roc10"]),
        "score_early": finite(r["score_early"]),
        "kama_slope5": finite(r["kama_slope5"]),
        "roc21": finite(r["roc21"]),
        "roc126": finite(r["roc126"]),
        "return_68d": finite(r["return_68d"]),
        "composite_momentum": finite(r["composite_momentum"]),
        "modified_sharpe_68": finite(r["modified_sharpe_68"]),
        "investable_filter": bool(r["investable_filter"]),
        "investable": investable,
        "radar_label": label,
        "investable_label": invest_label,
        "breadth": None,
        "macro": None,
    }

def build_monthly_panel(indicators, universe):
    """Create point-in-time month-end snapshots and forward outcomes."""
    meta = {x["symbol"]: x for x in universe}
    records = []
    for symbol, ind in indicators.items():
        grouped = ind.groupby(ind.index.to_period("M"), sort=True)
        positions = grouped.indices
        for period, idxs in positions.items():
            pos = int(idxs[-1])
            row = ind.iloc[pos]
            rec = {
                "symbol": symbol,
                "module": str(meta.get(symbol, {}).get("module") or "Non classificato"),
                "period": period,
                "date": ind.index[pos],
                "score": finite(row["score"]),
                "score_awakening": finite(row["score_awakening"]),
                "score_acceleration": finite(row["score_acceleration"]),
                "score_reversal": finite(row["score_reversal"]),
                "score_confirmation": finite(row["score_confirmation"]),
                "close": finite(row["close"]),
                "ma50": finite(row["ma50"]),
                "ma200": finite(row["ma200"]),
                "above_ma50": bool(row["close"] > row["ma50"]) if pd.notna(row["ma50"]) else None,
                "above_ma200": bool(row["close"] > row["ma200"]) if pd.notna(row["ma200"]) else None,
                "score_early": finite(row["score_early"]),
                "roc5": finite(row["roc5"]),
                "roc10": finite(row["roc10"]),
                "roc21": finite(row["roc21"]),
                "roc63": finite(row["roc63"]),
                "roc126": finite(row["roc126"]),
                "roc252": finite(row["roc252"]),
                "kama_slope5": finite(row["kama_slope5"]),
                "kama_slope21": finite(row["kama_slope21"]),
                "trend_stability_21": finite(row["trend_stability_21"]),
                "volatility_68": finite(row["volatility_68"]),
                "alligator_bull": bool(row["alligator_bull"]),
                "return_68d": finite(row["return_68d"]),
                "composite_momentum": finite(row["composite_momentum"]),
                "modified_sharpe_68": finite(row["modified_sharpe_68"]),
                "adx14": finite(row["adx14"]),
                "vortex_spread": finite(row["vi_plus"] - row["vi_minus"]) if pd.notna(row["vi_plus"]) and pd.notna(row["vi_minus"]) else None,
            }
            rec["future_date_1m"] = ind.index[pos+21] if pos+21 < len(ind) else pd.NaT
            for horizon, n in (("1m", 21), ("3m", 63), ("6m", 126)):
                rec[horizon] = (
                    finite(ind["close"].iloc[pos+n] / ind["close"].iloc[pos] - 1)
                    if pos+n < len(ind) and ind["close"].iloc[pos] else None
                )
            records.append(rec)
    if not records:
        return pd.DataFrame()
    panel = pd.DataFrame(records).sort_values(["period", "symbol"]).reset_index(drop=True)
    panel["monthly_return"] = panel.groupby("symbol")["close"].pct_change()
    panel["score_change_1m"] = panel.groupby("symbol")["score"].diff(1)
    panel["score_change_3m"] = panel.groupby("symbol")["score"].diff(3)
    return panel

def breadth_by_module(panel):
    """Cross-market ETF breadth, not constituent-level stock-market breadth."""
    if panel.empty:
        return {}
    latest_period = panel["period"].max()
    snap = panel[panel["period"] == latest_period]
    result = {}
    for module, group in snap.groupby("module"):
        valid50 = group["above_ma50"].dropna()
        valid200 = group["above_ma200"].dropna()
        valid_adv = group["monthly_return"].dropna()
        result[str(module)] = {
            "as_of": max(x.strftime("%Y-%m-%d") for x in group["date"]),
            "markets": int(len(group)),
            "above_ma50_pct": finite(valid50.mean()) if len(valid50) else None,
            "above_ma200_pct": finite(valid200.mean()) if len(valid200) else None,
            "advancers_1m_pct": finite((valid_adv > 0).mean()) if len(valid_adv) else None,
            "median_roc21": finite(group["roc21"].median()),
            "definition": "Percentuale degli ETF geografici del modulo sopra MA50/MA200 e in rialzo nell'ultimo mese; non è breadth dei singoli componenti azionari."
        }
    return result

def _portfolio_stats(monthly_returns, label):
    result = {"label": label, "months": int(len(monthly_returns))}
    for horizon in ("1m", "3m", "6m"):
        values = [x[horizon] for x in monthly_returns if x.get(horizon) is not None]
        result[horizon] = {
            "mean_return": finite(np.mean(values)) if values else None,
            "median_return": finite(np.median(values)) if values else None,
            "hit_rate": finite(np.mean(np.array(values) > 0)) if values else None,
            "observations": len(values),
        }
    return result

def monthly_validation(frames, indicators, universe, start_date=None, universe_label="ETF geografici"):
    """
    Historical monthly walk-forward replay.
    Each horizon is evaluated independently so the 6-month maturity lag
    does not truncate the 1- and 3-month results.
    """
    panel = build_monthly_panel(indicators, universe)
    if start_date and not panel.empty:
        panel = panel[panel["date"] >= pd.Timestamp(start_date)].copy()
    if panel.empty:
        return {"status": "DATI INSUFFICIENTI", "observations": 0,
                "note": "Nessuna serie mensile con prezzi e indicatori validi."}, {}
    periods = sorted(panel["period"].unique())
    benchmark_rows, fixed_rows, rolling_rows = [], [], []
    improving_1m_rows, improving_3m_rows = [], []
    top_quartile_rows = {m: [] for m in ("score", "score_awakening", "score_acceleration", "score_reversal", "score_confirmation", "return_68d", "modified_sharpe_68", "composite_momentum")}
    rolling_thresholds = []
    for period in periods:
        current = panel[panel["period"] == period].copy()
        prior_periods = [p for p in periods if p < period][-36:]
        prior = panel[panel["period"].isin(prior_periods)]
        threshold = None
        if len(prior_periods) >= 12 and len(prior):
            threshold = finite(prior["score"].dropna().quantile(0.75))
        if threshold is not None:
            rolling_thresholds.append({"date": current["date"].max().strftime("%Y-%m-%d"),
                                       "threshold": threshold})
        bench_rec = {"date": current["date"].max().strftime("%Y-%m-%d")}
        fixed_rec = {"date": bench_rec["date"]}
        rolling_rec = {"date": bench_rec["date"]}
        improving_1m_rec = {"date": bench_rec["date"]}
        improving_3m_rec = {"date": bench_rec["date"]}
        top_quartile_rec = {m: {"date": bench_rec["date"]} for m in top_quartile_rows}
        for horizon in ("1m", "3m", "6m"):
            valid = current.dropna(subset=[horizon])
            if valid.empty:
                bench_rec[horizon] = None
                fixed_rec[horizon] = None
                rolling_rec[horizon] = None
                improving_1m_rec[horizon] = None
                improving_3m_rec[horizon] = None
                for rec in top_quartile_rec.values(): rec[horizon] = None
                continue            bench_rec[horizon] = finite(valid[horizon].mean())
            fixed_group = valid[valid["score"] >= 65]
            fixed_rec[horizon] = finite(fixed_group[horizon].mean()) if len(fixed_group) else None
            if threshold is not None:
                rolling_group = valid[valid["score"] >= threshold]
                rolling_rec[horizon] = finite(rolling_group[horizon].mean()) if len(rolling_group) else None
            else:
                rolling_rec[horizon] = None
            improve1 = valid[valid["score_change_1m"] >= 12.5]
            improve3 = valid[valid["score_change_3m"] >= 25.0]
            improving_1m_rec[horizon] = finite(improve1[horizon].mean()) if len(improve1) else None
            improving_3m_rec[horizon] = finite(improve3[horizon].mean()) if len(improve3) else None
            for metric in top_quartile_rec:
                metric_group = valid.dropna(subset=[metric])
                if len(metric_group) >= 4:
                    cutoff_metric = metric_group[metric].quantile(0.75)
                    chosen = metric_group[metric_group[metric] >= cutoff_metric]
                    top_quartile_rec[metric][horizon] = finite(chosen[horizon].mean()) if len(chosen) else None
                else:
                    top_quartile_rec[metric][horizon] = None
        if any(bench_rec[h] is not None for h in ("1m", "3m", "6m")):
            benchmark_rows.append(bench_rec)
        if any(fixed_rec[h] is not None for h in ("1m", "3m", "6m")):
            fixed_rows.append(fixed_rec)
        if threshold is not None and any(rolling_rec[h] is not None for h in ("1m", "3m", "6m")):
            rolling_rows.append(rolling_rec)
        if any(improving_1m_rec[h] is not None for h in ("1m", "3m", "6m")):
            improving_1m_rows.append(improving_1m_rec)
        if any(improving_3m_rec[h] is not None for h in ("1m", "3m", "6m")):
            improving_3m_rows.append(improving_3m_rec)
        for metric, rec in top_quartile_rec.items():
            if any(rec[h] is not None for h in ("1m", "3m", "6m")):
                top_quartile_rows[metric].append(rec)
    breadth = breadth_by_module(panel)
    bucket_names = ["0-39", "40-54", "55-64", "65-74", "75-100"]
    bucket_months = {b: {h: [] for h in ("1m", "3m", "6m")} for b in bucket_names}
    bucket_counts = {b: [] for b in bucket_names}
    rank_ic = {h: [] for h in ("1m", "3m", "6m")}
    delta1_ic = {h: [] for h in ("1m", "3m", "6m")}
    delta3_ic = {h: [] for h in ("1m", "3m", "6m")}
    for period in periods:
        current = panel[panel["period"] == period].copy()
        conditions = [
            current["score"] < 40,
            (current["score"] >= 40) & (current["score"] < 55),
            (current["score"] >= 55) & (current["score"] < 65),
            (current["score"] >= 65) & (current["score"] < 75),
            current["score"] >= 75,
        ]
        current["score_bucket"] = np.select(conditions, bucket_names, default="0-39")
        for bucket in bucket_names:
            group = current[current["score_bucket"] == bucket]
            if len(group):
                bucket_counts[bucket].append(int(len(group)))
            for horizon in ("1m", "3m", "6m"):
                valid_group = group.dropna(subset=[horizon])
                if len(valid_group):
                    bucket_months[bucket][horizon].append(float(valid_group[horizon].mean()))
        for horizon in ("1m", "3m", "6m"):
            valid = current.dropna(subset=["score", horizon])
            if len(valid) >= 5 and valid["score"].nunique() > 1 and valid[horizon].nunique() > 1:
                ic = valid["score"].rank(method="average").corr(valid[horizon].rank(method="average"))
                if pd.notna(ic):
                    rank_ic[horizon].append(float(ic))
            for delta_col, target in (("score_change_1m", delta1_ic), ("score_change_3m", delta3_ic)):
                delta_valid = current.dropna(subset=[delta_col, horizon])
                if len(delta_valid) >= 5 and delta_valid[delta_col].nunique() > 1 and delta_valid[horizon].nunique() > 1:
                    delta_value = delta_valid[delta_col].rank(method="average").corr(delta_valid[horizon].rank(method="average"))
                    if pd.notna(delta_value):
                        target[horizon].append(float(delta_value))
    score_buckets = {}
    for bucket in bucket_names:
        score_buckets[bucket] = {
            "months_with_signals": max((len(bucket_months[bucket][h]) for h in ("1m", "3m", "6m")), default=0),
            "average_etfs_per_month": finite(np.mean(bucket_counts[bucket])) if bucket_counts[bucket] else None,
            **{
                h: {
                    "mean_forward_return": finite(np.mean(bucket_months[bucket][h])) if bucket_months[bucket][h] else None,
                    "positive_months_pct": finite(np.mean(np.array(bucket_months[bucket][h]) > 0)) if bucket_months[bucket][h] else None,
                    "months": len(bucket_months[bucket][h]),
                }
                for h in ("1m", "3m", "6m")
            }
        }
    rank_ic_summary = {
        h: {
            "mean_spearman_ic": finite(np.mean(rank_ic[h])) if rank_ic[h] else None,
            "median_spearman_ic": finite(np.median(rank_ic[h])) if rank_ic[h] else None,
            "positive_months_pct": finite(np.mean(np.array(rank_ic[h]) > 0)) if rank_ic[h] else None,
            "months": len(rank_ic[h]),
        }
        for h in ("1m", "3m", "6m")
    }
    delta_ic_summary = {
        "score_change_1m": {h: {"mean_spearman_ic": finite(np.mean(delta1_ic[h])) if delta1_ic[h] else None, "positive_months_pct": finite(np.mean(np.array(delta1_ic[h]) > 0)) if delta1_ic[h] else None, "months": len(delta1_ic[h])} for h in ("1m", "3m", "6m")},
        "score_change_3m": {h: {"mean_spearman_ic": finite(np.mean(delta3_ic[h])) if delta3_ic[h] else None, "positive_months_pct": finite(np.mean(np.array(delta3_ic[h]) > 0)) if delta3_ic[h] else None, "months": len(delta3_ic[h])} for h in ("1m", "3m", "6m")}
    }
    validation = {
        "status": "WALK-FORWARD STORICO ESPLORATIVO · NON VALIDATO",
        "observations": int(len(panel)),
        "months": int(len(periods)),
        "out_of_sample_from": periods[0].strftime("%Y-%m"),
        "out_of_sample_to": periods[-1].strftime("%Y-%m"),
        "benchmark_equal_weight": _portfolio_stats(benchmark_rows, f"Universo {universe_label} equiponderato"),
        "oos_score_ge_65": _portfolio_stats(fixed_rows, "Selezione mensile con score >= 65"),
        "walk_forward_rolling_percentile": _portfolio_stats(rolling_rows, "Selezione mensile sopra il 75° percentile dei 36 mesi precedenti"),
        "score_improving_1m": _portfolio_stats(improving_1m_rows, "Score in aumento di almeno 12,5 punti rispetto al mese precedente"),
        "score_improving_3m": _portfolio_stats(improving_3m_rows, "Score in aumento di almeno 25 punti rispetto a tre mesi prima"),
        "cross_sectional_top_quartile": {m: _portfolio_stats(rows, {"score":"Radar score top quartile","score_awakening":"Risveglio Alligator/KAMA top quartile","score_acceleration":"Accelerazione ROC/AO top quartile","score_reversal":"Inversione Vortex/RSI top quartile","score_confirmation":"Conferma MA38/MA200 top quartile","return_68d":"Rendimento 68 sedute top quartile","modified_sharpe_68":"Modified Sharpe 68 sedute top quartile","composite_momentum":"Momentum composito 3/6/12 mesi top quartile"}[m]) for m, rows in top_quartile_rows.items()},
        "score_buckets": score_buckets,
        "rank_information_coefficient": rank_ic_summary,
        "score_change_information_coefficient": delta_ic_summary,
        "rolling_threshold": {
            "observations": len(rolling_thresholds),
            "mean": finite(np.mean([x["threshold"] for x in rolling_thresholds])) if rolling_thresholds else None,
            "last": rolling_thresholds[-1] if rolling_thresholds else None,
            "rule": "Per ogni mese, soglia = 75° percentile degli score osservati nei 36 mesi precedenti; minimo 12 mesi di storia. Nessuna informazione del mese corrente entra nella soglia."
        },
        "breadth_note": "Breadth inter-mercato per modulo: quota degli ETF geografici sopra MA50/MA200 e quota in rialzo a un mese. Non sostituisce la breadth interna calcolata sui titoli componenti di ciascun indice.",
        "method": "Replay mensile point-in-time: snapshot all'ultima seduta disponibile del mese; rendimenti successivi a 21/63/126 sedute. Ogni orizzonte è valutato separatamente. Include benchmark equiponderato, selezione score >=65, soglia adattiva sui 36 mesi precedenti, test di miglioramento dello score a 1 e 3 mesi, confronto con i quattro blocchi tecnici separati e con top quartile di momentum 68 sedute, Modified Sharpe 68 sedute e momentum composito 3/6/12 mesi, rendimenti per fasce di score e Spearman rank-IC cross-sectional mensile. I rendimenti forward a 3 e 6 mesi si sovrappongono; gli ETF sono correlati e l'universo corrente introduce survivorship bias. Risultati lordi, senza costi, FX, spread o slippage."
    }
    return validation, breadth



def early_signal_validation(indicators, universe, start_date="2008-01-01"):
    """Monthly cross-sectional test of the early-warning score vs momentum baselines."""
    panel = build_monthly_panel(indicators, universe)
    if panel.empty:
        return {"status": "DATI INSUFFICIENTI", "months": 0, "note": "Nessun dato mensile."}
    panel = panel[panel["date"] >= pd.Timestamp(start_date)].copy()
    panel = panel.dropna(subset=["1m", "score_early", "roc21", "composite_momentum"])
    if panel.empty:
        return {"status": "DATI INSUFFICIENTI", "months": 0, "note": "Nessuna osservazione completa."}
    monthly = []
    ic_early, ic_roc21, ic_mom = [], [], []
    for period, group in panel.groupby("period", sort=True):
        g = group.copy()
        if len(g) < 5:
            continue
        q = max(1, int(math.ceil(len(g) * 0.25)))
        candidates = {
            "early_score": g.nlargest(q, "score_early"),
            "momentum_21d": g.nlargest(q, "roc21"),
            "momentum_3_6_12": g.nlargest(q, "composite_momentum"),
        }
        row = {"period": str(period), "date": g["date"].max().strftime("%Y-%m-%d"),
               "universe": finite(g["1m"].mean()), "universe_hit": finite((g["1m"] > 0).mean())}
        for key, selected in candidates.items():
            row[key] = finite(selected["1m"].mean())
            row[key + "_hit"] = finite((selected["1m"] > 0).mean())
            row[key + "_n"] = int(len(selected))
        for col, bucket in (("score_early", ic_early), ("roc21", ic_roc21), ("composite_momentum", ic_mom)):
            if g[col].nunique() > 1 and g["1m"].nunique() > 1:
                val = g[col].rank(method="average").corr(g["1m"].rank(method="average"))
                if pd.notna(val):
                    bucket.append(float(val))
        monthly.append(row)
    if not monthly:
        return {"status": "DATI INSUFFICIENTI", "months": 0, "note": "Meno di cinque ETF per mese."}
    def summary(key):
        vals = [x[key] for x in monthly if x.get(key) is not None]
        return {"mean_return": finite(np.mean(vals)) if vals else None,
                "median_return": finite(np.median(vals)) if vals else None,
                "hit_rate": finite(np.mean(np.array(vals) > 0)) if vals else None,
                "months": len(vals)}
    def ic_summary(vals):
        return {"mean_spearman_ic": finite(np.mean(vals)) if vals else None,
                "positive_months_pct": finite(np.mean(np.array(vals) > 0)) if vals else None,
                "months": len(vals)}
    return {
        "status": "TEST ESPLORATIVO · NESSUNA GARANZIA PREDITTIVA",
        "from": monthly[0]["period"], "to": monthly[-1]["period"],
        "months": len(monthly), "minimum_universe_per_month": 5,
        "benchmark_equal_weight": summary("universe"),
        "early_score_top_quartile": summary("early_score"),
        "momentum_21d_top_quartile": summary("momentum_21d"),
        "momentum_3_6_12_top_quartile": summary("momentum_3_6_12"),
        "rank_ic": {"early_score": ic_summary(ic_early),
                    "momentum_21d": ic_summary(ic_roc21),
                    "momentum_3_6_12": ic_summary(ic_mom)},
        "monthly_observations": monthly,
        "method": "Snapshot a fine mese; selezione del quartile superiore usando soltanto score/indicatori disponibili a quella data; rendimento nei successivi 21 giorni di borsa. Confronto equiponderato con ROC21 e momentum composito 3/6/12 mesi. Rendimenti lordi, orizzonte sovrapposto, ETF correlati e universo corrente con survivorship bias."
    }



def walk_forward_early_model(indicators, universe, start_date="2008-01-01", train_months=60):
    """Ridge model for next-month relative returns; only use matured historical labels."""
    panel = build_monthly_panel(indicators, universe)
    if panel.empty:
        return {"status": "DATI INSUFFICIENTI", "months": 0}
    panel = panel[panel["date"] >= pd.Timestamp(start_date)].copy()
    panel["future_date_1m"] = pd.to_datetime(panel["future_date_1m"])
    features = ["roc5", "roc10", "roc21", "kama_slope5", "score_early",
                "score_awakening", "score_acceleration", "score_reversal"]
    panel = panel.dropna(subset=features + ["1m", "future_date_1m"])
    if panel.empty:
        return {"status": "DATI INSUFFICIENTI", "months": 0}
    # Percentile ranks are calculated within each month, so different ETF scales are comparable.
    for col in features:
        panel["rank_" + col] = panel.groupby("period")[col].rank(pct=True)
    xcols = ["rank_" + x for x in features]
    predictions = []
    periods = sorted(panel["period"].unique())
    for period in periods:
        current = panel[panel["period"] == period].copy()
        if len(current) < 5:
            continue
        asof = current["date"].max()
        prior = panel[(panel["period"] < period) & (panel["future_date_1m"] <= asof)].copy()
        prior_periods = sorted(prior["period"].unique())[-train_months:]
        prior = prior[prior["period"].isin(prior_periods)].dropna(subset=xcols + ["1m"])
        if len(prior_periods) < 18 or len(prior) < 100:
            continue
        # Learn excess return over that month's universe average, not absolute market direction.
        prior["target"] = prior["1m"] - prior.groupby("period")["1m"].transform("mean")
        X = prior[xcols].to_numpy(dtype=float)
        y = prior["target"].to_numpy(dtype=float)
        x_mean = X.mean(axis=0)        y_mean = y.mean()
        Xc, yc = X - x_mean, y - y_mean
        alpha = 10.0
        try:
            coef = np.linalg.solve(Xc.T @ Xc + alpha * np.eye(Xc.shape[1]), Xc.T @ yc)
        except np.linalg.LinAlgError:
            continue
        Xnow = current[xcols].to_numpy(dtype=float)
        current["model_prediction"] = (Xnow - x_mean) @ coef + y_mean
        current["model_excess"] = current["1m"] - current["1m"].mean()
        predictions.append(current[["period", "date", "symbol", "model_prediction", "model_excess", "1m", "roc21"]])
    if not predictions:
        return {"status": "DATI INSUFFICIENTI · SERVONO PIÙ MESI DI TRAINING", "months": 0,
                "note": "Il modello richiede almeno 18 mesi di etichette 1m già maturate e 100 osservazioni ETF-mese."}
    pred = pd.concat(predictions, ignore_index=True)
    rows = []
    ic_values = []
    for period, g in pred.groupby("period", sort=True):
        q = max(1, int(math.ceil(len(g) * 0.25)))
        chosen = g.nlargest(q, "model_prediction")
        mom = g.nlargest(q, "roc21")
        rows.append({"period": str(period), "model": finite(chosen["1m"].mean()),
                     "model_hit": finite((chosen["1m"] > 0).mean()),
                     "momentum21": finite(mom["1m"].mean()),
                     "benchmark": finite(g["1m"].mean()), "n": int(len(chosen))})
        if g["model_prediction"].nunique() > 1 and g["model_excess"].nunique() > 1:
            ic = g["model_prediction"].rank().corr(g["model_excess"].rank())
            if pd.notna(ic):
                ic_values.append(float(ic))
    def stat(key, hit=False):
        vals = [x[key] for x in rows if x.get(key) is not None]
        return {"mean_return": finite(np.mean(vals)) if vals else None,
                "hit_rate": finite(np.mean([x["model_hit"] for x in rows])) if hit else None,
                "months": len(vals)}
    return {
        "status": "WALK-FORWARD RIDGE · ETICHETTE MATURATE",
        "from": rows[0]["period"], "to": rows[-1]["period"], "months": len(rows),
        "training_window_months": train_months, "minimum_training_months": 18,
        "ridge_alpha": 10.0, "features": features,
        "model_top_quartile": stat("model", True),
        "momentum21_top_quartile": stat("momentum21"),
        "benchmark_equal_weight": stat("benchmark"),
        "rank_ic_excess": {"mean": finite(np.mean(ic_values)) if ic_values else None,
                           "positive_months_pct": finite(np.mean(np.array(ic_values) > 0)) if ic_values else None,
                           "months": len(ic_values)},
        "monthly_observations": rows,
        "method": "Ogni mese il modello Ridge è stimato soltanto su rendimenti a 21 sedute già maturati alla data di previsione, finestra mobile massima 60 mesi, almeno 18 mesi di training e 100 osservazioni. Le feature sono ranghi cross-sectional del mese. Target: rendimento 1m relativo alla media del mese. Il test è walk-forward; costi e survivorship bias restano da considerare."
    }


def compare_predictive_candidates(indicators, universe, start_date="2015-01-01"):
    """Compare fixed cross-sectional candidates on identical month-end samples."""
    panel = build_monthly_panel(indicators, universe)
    if panel.empty:
        return {"status": "DATI INSUFFICIENTI", "models": {}}
    panel = panel[panel["date"] >= pd.Timestamp(start_date)].copy()
    required = ["roc5", "roc21", "roc63", "roc126", "kama_slope21",
                "trend_stability_21", "volatility_68", "alligator_bull", "above_ma200", "1m",
                "adx14", "vortex_spread", "modified_sharpe_68"]
    panel = panel.dropna(subset=required)
    if panel.empty:
        return {"status": "DATI INSUFFICIENTI", "models": {}}
    rank_cols = ["roc5", "roc21", "roc63", "roc126", "kama_slope21",
                 "trend_stability_21", "volatility_68", "adx14", "vortex_spread",
                 "modified_sharpe_68"]
    for col in rank_cols:
        panel["rank_" + col] = panel.groupby("period")[col].rank(pct=True)
    panel["rank_low_vol"] = 1.0 - panel["rank_volatility_68"]
    panel["rank_alligator"] = panel.groupby("period")["alligator_bull"].rank(pct=True)
    panel["rank_adx14"] = panel.groupby("period")["adx14"].rank(pct=True)
    panel["rank_vortex"] = panel.groupby("period")["vortex_spread"].rank(pct=True)
    panel["rank_risk_adjusted_momentum"] = panel.groupby("period")["modified_sharpe_68"].rank(pct=True)
    panel["candidate_momentum"] = (0.10*panel["rank_roc5"] + 0.20*panel["rank_roc21"] + 0.35*panel["rank_roc63"] + 0.35*panel["rank_roc126"])
    panel["candidate_trend_quality"] = (0.30*panel["rank_kama_slope21"] + 0.30*panel["rank_trend_stability_21"] + 0.20*panel["rank_alligator"] + 0.20*panel["rank_low_vol"])
    panel["candidate_relative_strength"] = 0.50*panel["rank_roc21"] + 0.50*panel["rank_roc63"]
    panel["candidate_roc21"] = panel["rank_roc21"]
    panel["candidate_alligator"] = panel["rank_alligator"]
    panel["candidate_kama"] = panel["rank_kama_slope21"]
    # ADX measures trend strength, not direction: only reward it when Vortex is bullish.
    panel["directional_adx"] = panel["adx14"] * np.sign(panel["vortex_spread"])
    panel["rank_directional_adx"] = panel.groupby("period")["directional_adx"].rank(pct=True)
    panel["candidate_adx"] = panel["rank_directional_adx"]
    panel["candidate_vortex"] = panel["rank_vortex"]
    panel["candidate_low_vol"] = panel["rank_low_vol"]
    panel["candidate_risk_adjusted"] = panel["rank_risk_adjusted_momentum"]
    panel["candidate_roc21_low_vol"] = 0.75*panel["rank_roc21"] + 0.25*panel["rank_low_vol"]
    panel["candidate_roc21_adx"] = 0.75*panel["rank_roc21"] + 0.25*panel["rank_adx14"]
    # Fixed blends: test whether trend quality adds value to the ROC21 baseline.
    panel["blend_70_30"] = 0.70*panel["rank_roc21"] + 0.30*panel["candidate_trend_quality"]
    panel["blend_50_50"] = 0.50*panel["rank_roc21"] + 0.50*panel["candidate_trend_quality"]
    panel["blend_30_70"] = 0.30*panel["rank_roc21"] + 0.70*panel["candidate_trend_quality"]
    names = ["candidate_momentum", "candidate_trend_quality", "candidate_relative_strength",
             "candidate_roc21", "candidate_alligator", "candidate_kama", "candidate_adx",
             "candidate_vortex", "candidate_low_vol", "candidate_risk_adjusted",
             "candidate_roc21_low_vol", "candidate_roc21_adx",
             "blend_70_30", "blend_50_50", "blend_30_70"]
    rows = {name: [] for name in names}
    regimes = {"risk_on": {name: [] for name in names}, "risk_off": {name: [] for name in names}}
    months = []
    for period, g in panel.groupby("period", sort=True):
        if len(g) < 5:
            continue
        regime = "risk_on" if float(g["above_ma200"].mean()) >= 0.50 and float(g["roc21"].median()) > 0 else "risk_off"
        q = max(1, int(math.ceil(len(g)*0.25)))
        months.append(str(period))
        benchmark = finite(g["1m"].mean())
        for name in names:
            chosen = g.nlargest(q, name)["1m"].dropna()
            if chosen.empty:
                continue
            item = {"return": finite(chosen.mean()), "excess": finite(chosen.mean()-benchmark) if benchmark is not None else None, "hit": finite((chosen>0).mean())}
            rows[name].append(item)
            regimes[regime][name].append(item)
    def stats(items):
        r=[x["return"] for x in items if x["return"] is not None]
        e=[x["excess"] for x in items if x["excess"] is not None]
        h=[x["hit"] for x in items if x["hit"] is not None]
        return {"months":len(r),"mean_forward_return":finite(np.mean(r)) if r else None,"median_forward_return":finite(np.median(r)) if r else None,"mean_excess_vs_equal_weight":finite(np.mean(e)) if e else None,"hit_rate":finite(np.mean(h)) if h else None}
    summary={name:stats(items) for name,items in rows.items()}
    ic={}
    for name in names:
        values=[]
        for _,g in panel.groupby("period",sort=True):
            if len(g)>=5 and g[name].nunique()>1 and g["1m"].nunique()>1:
                v=g[name].rank().corr(g["1m"].rank())
                if pd.notna(v): values.append(float(v))
        ic[name]={"mean_rank_ic":finite(np.mean(values)) if values else None,"positive_months_pct":finite(np.mean(np.array(values)>0)) if values else None,"months":len(values)}
    regime_summary={regime:{name:stats(items) for name,items in groups.items()} for regime,groups in regimes.items()}
    # Fixed chronological slices help expose regime/time concentration; labels still overlap by 21 sessions.
    time_slices = {"2015-2019": [], "2020-2022": [], "2023+": []}
    for period, g in panel.groupby("period", sort=True):
        if len(g) < 5:
            continue
        pstr = str(period)
        bucket = "2015-2019" if pstr < "2020-01" else ("2020-2022" if pstr < "2023-01" else "2023+")
        q = max(1, int(math.ceil(len(g)*0.25)))
        bench = finite(g["1m"].mean())
        item = {"period": pstr, "benchmark": bench, "models": {}}
        for name in names:
            chosen = g.nlargest(q, name)["1m"].dropna()
            item["models"][name] = finite(chosen.mean()) if not chosen.empty else None
        time_slices[bucket].append(item)
    slice_summary = {}
    for bucket, items in time_slices.items():
        slice_summary[bucket] = {"months":len(items),"models":{}}
        for name in names:
            vals=[x["models"][name] for x in items if x["models"].get(name) is not None]
            excess=[x["models"][name]-x["benchmark"] for x in items if x["models"].get(name) is not None and x["benchmark"] is not None]
            slice_summary[bucket]["models"][name]={"mean_forward_return":finite(np.mean(vals)) if vals else None,"mean_excess_vs_equal_weight":finite(np.mean(excess)) if excess else None}
    return {"status":"CONFRONTO SPERIMENTALE · NON È UN SEGNALE OPERATIVO","from":months[0] if months else None,"to":months[-1] if months else None,"common_months":len(months),"models":summary,"rank_ic":ic,"by_regime":regime_summary,"by_time_slice":slice_summary,"blend_definition":"Combinazioni fisse di ranking cross-sectional: 70/30, 50/50 e 30/70 tra ROC21 e qualità del trend. Non sono ottimizzate sui risultati.","benchmark_note":"Quartile superiore, stessi mesi e universo per tutti i modelli.","regime_definition":"Risk-on se almeno il 50% degli ETF del campione è sopra MA200 e ROC21 mediano positivo; altrimenti risk-off. Proxy ETF, non breadth dei titoli sottostanti.","method":"Pesi fissi e ranking cross-sectional. Oltre alle basi ROC21, momentum multi-orizzonte, trend quality e forza relativa, test separati Alligator, pendenza KAMA, ADX14, spread Vortex, bassa volatilità e Sharpe modificato 68 sedute; test combinati ROC21+low-vol e ROC21+ADX con peso 75/25. Rendimento forward 21 sedute, lordo e sovrapposto. Universo corrente: survivorship bias; costi, spread, tasse e cambio esclusi. Il miglior risultato non costituisce validazione indipendente."}



def walk_forward_predictive_v3(indicators, universe, start_date="2015-01-01", train_months=60):
    """
    Leakage-controlled monthly Ridge ranking.
    Train only on labels whose full 21-session outcome had matured by the
    forecast date. Compare top-3/5/10 selections with ROC21, 3/6/12 momentum
    and the equal-weight universe on identical months.
    """
    panel = build_monthly_panel(indicators, universe)
    if panel.empty:
        return {"status": "DATI INSUFFICIENTI", "months": 0}
    panel = panel[panel["date"] >= pd.Timestamp(start_date)].copy()
    panel["future_date_1m"] = pd.to_datetime(panel["future_date_1m"])
    required = ["roc21", "roc63", "roc126", "kama_slope21",
                "trend_stability_21", "alligator_bull", "adx14",
                "vortex_spread", "volatility_68", "1m", "future_date_1m"]
    panel = panel.dropna(subset=required).copy()
    if panel.empty:
        return {"status": "DATI INSUFFICIENTI", "months": 0}
    panel["directional_adx"] = panel["adx14"] * np.sign(panel["vortex_spread"])
    raw_features = ["roc21", "roc63", "roc126", "kama_slope21",
                    "trend_stability_21", "alligator_bull",
                    "directional_adx", "volatility_68"]
    for col in raw_features:
        panel["rank_" + col] = panel.groupby("period")[col].rank(pct=True)
    panel["rank_low_volatility"] = 1.0 - panel["rank_volatility_68"]
    features = ["rank_roc21", "rank_roc63", "rank_roc126",
                "rank_kama_slope21", "rank_trend_stability_21",
                "rank_alligator_bull", "rank_directional_adx",
                "rank_low_volatility"]
    panel = panel.dropna(subset=features).copy()
    periods = sorted(panel["period"].unique())
    predictions = []
    alpha = 12.0  # pre-registered; not selected on the test results
    for period in periods:
        current = panel[panel["period"] == period].copy()
        if len(current) < 5:
            continue
        asof = current["date"].max()
        # Purge every training label whose 21-session outcome is not yet known.
        prior = panel[(panel["period"] < period) &
                      (panel["future_date_1m"] <= asof)].copy()
        prior_periods = sorted(prior["period"].unique())[-train_months:]
        prior = prior[prior["period"].isin(prior_periods)].dropna(subset=features + ["1m"])
        if len(prior_periods) < 18 or len(prior) < 100:
            continue
        prior["target_excess"] = prior["1m"] - prior.groupby("period")["1m"].transform("mean")
        X = prior[features].to_numpy(dtype=float)
        y = prior["target_excess"].to_numpy(dtype=float)
        x_mean, y_mean = X.mean(axis=0), float(y.mean())
        Xc, yc = X - x_mean, y - y_mean
        try:
            coef = np.linalg.solve(Xc.T @ Xc + alpha * np.eye(Xc.shape[1]), Xc.T @ yc)
        except np.linalg.LinAlgError:
            continue
        current["predicted_excess"] = (current[features].to_numpy(dtype=float) - x_mean) @ coef + y_mean
        current["model"] = current["1m"]
        predictions.append(current[["period", "date", "symbol", "predicted_excess",
                                    "model", "roc21", "composite_momentum"]])
    if not predictions:
        return {"status": "DATI INSUFFICIENTI · TRAINING MATURATO NON SUFFICIENTE",
                "months": 0, "minimum_training_months": 18,
                "note": "Nessun risultato viene prodotto senza almeno 18 mesi e 100 osservazioni con etichette 21 sedute già maturate."}
    pred = pd.concat(predictions, ignore_index=True)
    meta = {x["symbol"]: x for x in universe}
    rows = []
    strategies = ("ridge", "roc21", "momentum_3_6_12", "benchmark")
    for period, group in pred.groupby("period", sort=True):
        benchmark = finite(group["model"].mean())
        item = {"period": str(period), "benchmark": benchmark, "portfolios": {}}
        for count in (3, 5, 10):
            n = min(count, len(group))
            selectors = {
                "ridge": group.nlargest(n, "predicted_excess"),
                "roc21": group.nlargest(n, "roc21"),
                "momentum_3_6_12": group.nlargest(n, "composite_momentum"),
            }
            selectors["benchmark"] = group
            for strategy, chosen in selectors.items():
                ret = finite(chosen["model"].mean())
                item["portfolios"].setdefault(strategy, {})[str(count)] = {
                    "return": ret,
                    "excess": finite(ret - benchmark) if ret is not None and benchmark is not None else None,
                    "hit_rate": finite((chosen["model"] > 0).mean()),
                    "selected": int(len(chosen))
                }
        rows.append(item)
    summary = {}
    for strategy in strategies:
        summary[strategy] = {}
        for count in (3, 5, 10):
            vals = [x["portfolios"][strategy][str(count)] for x in rows
                    if str(count) in x["portfolios"].get(strategy, {})]
            returns = [x["return"] for x in vals if x["return"] is not None]
            excess = [x["excess"] for x in vals if x["excess"] is not None]
            hits = [x["hit_rate"] for x in vals if x["hit_rate"] is not None]
            summary[strategy][str(count)] = {
                "months": len(returns),
                "mean_return": finite(np.mean(returns)) if returns else None,
                "median_return": finite(np.median(returns)) if returns else None,
                "mean_excess_vs_universe": finite(np.mean(excess)) if excess else None,
                "positive_months_pct": finite(np.mean(np.array(returns) > 0)) if returns else None,
                "average_portfolio_hit_rate": finite(np.mean(hits)) if hits else None
            }
    latest_period = pred["period"].max()
    latest = pred[pred["period"] == latest_period].sort_values("predicted_excess", ascending=False).head(15)
    latest_ranking = []
    for _, row in latest.iterrows():
        m = meta.get(row["symbol"], {})
        latest_ranking.append({
            "symbol": row["symbol"], "ticker": m.get("ticker", row["symbol"]),
            "name": m.get("name", row["symbol"]), "geography": m.get("geography", ""),
            "predicted_excess": finite(row["predicted_excess"]),
            "roc21": finite(row["roc21"]),
            "composite_momentum": finite(row["composite_momentum"])
        })
    return {
        "status": "WALK-FORWARD RIDGE 3.0 · ETICHETTE MATURATE · SPERIMENTALE",
        "from": rows[0]["period"], "to": rows[-1]["period"],
        "months": len(rows), "training_window_months": train_months,
        "minimum_training_months": 18, "minimum_training_observations": 100,
        "ridge_alpha": alpha, "features": features,
        "portfolio_sizes": [3, 5, 10], "results": summary,
        "latest_ranking_period": str(latest_period),
        "latest_ranking": latest_ranking,
        "monthly_observations": rows,
        "method": "Ogni mese Ridge stima l'extra-rendimento relativo a 21 sedute. Il training usa solo etichette con data di maturazione non successiva alla data di previsione; finestra massima 60 mesi, minimo 18 mesi e 100 righe. Feature cross-sectional rank: momentum 1/3/6 mesi, KAMA, stabilità del trend, Alligator, ADX con direzione Vortex e volatilità inversa. Confronto top 3/5/10 contro ROC21, momentum 3/6/12 e universo equiponderato sugli stessi mesi. Rendimento forward lordo e sovrapposto; costi e survivorship bias non inclusi."
    }


def factor_segment_validation(factor_universe, factor_frames, factor_indicators):
    """Separate walk-forward summaries by factor and geography, without mixing segments."""
    calculated_symbols = set(factor_indicators)
    segments = []
    for factor in ("MOMENTUM", "QUALITY", "VALUE"):
        for geography in ("Globale", "Stati Uniti", "Europa"):
            members = [x for x in factor_universe if x.get("factor") == factor and x.get("geography") == geography]
            usable = [x for x in members if x.get("symbol") in calculated_symbols]
            if not members:
                continue
            symbols = {x["symbol"] for x in usable}
            sub_frames = {k: v for k, v in factor_frames.items() if k in symbols}
            sub_indicators = {k: v for k, v in factor_indicators.items() if k in symbols}
            if usable:
                primary, _ = monthly_validation(sub_frames, sub_indicators, usable, start_date="2020-01-01", universe_label=f"{factor} · {geography}")
                extended, _ = monthly_validation(sub_frames, sub_indicators, usable, start_date="2015-01-01", universe_label=f"{factor} · {geography}")
            else:
                primary = {"status": "DATI INSUFFICIENTI", "observations": 0}
                extended = {"status": "DATI INSUFFICIENTI", "observations": 0}
            segments.append({
                "factor": factor, "geography": geography,
                "candidate_count": len(members), "calculated_count": len(usable),
                "tickers": [x.get("ticker") for x in usable],
                "symbols": [x.get("symbol") for x in usable],
                "first_price_date": min((factor_frames[x["symbol"]].index[0].strftime("%Y-%m-%d") for x in usable), default=None),
                "primary_2020": primary, "extended_2015": extended
            })
    return {
        "method": "Confronto separato per fattore e area. Rendimento medio forward del paniere equiponderato degli ETF disponibili in ciascuna combinazione; se c'è un solo ETF, il risultato descrive quell'ETF e non una replica diversificata del fattore. I gruppi non vengono mescolati.",
        "segments": segments
    }

def main():
    if not SOURCE.exists():
        raise SystemExit("geografia-motore.json non trovato: eseguire prima il motore geografico.")
    source_data = json.loads(SOURCE.read_text(encoding="utf-8"))
    universe = collect_universe(source_data)
    if not universe:
        raise SystemExit("Nessun ticker con simbolo trovato nel ranking geografico.")
    symbols = sorted({x["symbol"] for x in universe})
    frames, errors = download_prices(symbols)
    results, indicators = [], {}
    for meta in universe:
        symbol = meta["symbol"]
        frame = frames.get(symbol)
        if frame is None:
            results.append({**meta,"status":"DATI NON DISPONIBILI","error":errors.get(symbol,"Prezzi non restituiti")})
            continue
        if len(frame) < MIN_HISTORY:
            results.append({**meta,"status":"STORICO INSUFFICIENTE","observations":len(frame)})
            continue
        try:
            ind = calculate(frame)
            ind = ind.dropna(subset=["score","ma200","roc38","rsi14"])
            if ind.empty:
                results.append({**meta,"status":"STORICO INSUFFICIENTE","observations":len(frame)})
                continue
            indicators[symbol] = ind
            results.append({**latest_record(meta,ind),"status":"CALCOLATO","observations":len(frame)})
        except Exception as exc:
            results.append({**meta,"status":"ERRORE CALCOLO","error":f"{type(exc).__name__}: {exc}"})
    # Analyze factors separately; never contaminate country or region rankings.
    factor_universe = collect_factor_universe()
    factor_symbols = sorted({x["symbol"] for x in factor_universe})
    factor_frames, factor_errors = download_prices(factor_symbols, start_date=FACTOR_START_DATE) if factor_symbols else ({}, {})
    factor_results, factor_indicators = [], {}
    for meta in factor_universe:
        symbol = meta["symbol"]
        frame = factor_frames.get(symbol)
        if frame is None:
            factor_results.append({**meta, "status":"DATI NON DISPONIBILI", "error":factor_errors.get(symbol,"Prezzi non restituiti")})            continue
        if len(frame) < MIN_HISTORY:
            factor_results.append({**meta, "status":"STORICO INSUFFICIENTE", "observations":len(frame)})
            continue
        try:
            ind = calculate(frame).dropna(subset=["score","ma200","roc38","rsi14"])
            if ind.empty:
                factor_results.append({**meta, "status":"STORICO INSUFFICIENTE", "observations":len(frame)})
                continue
            factor_indicators[symbol] = ind
            factor_results.append({**latest_record(meta,ind), "status":"CALCOLATO", "observations":len(frame),
                                   "first_price_date":frame.index[0].strftime("%Y-%m-%d")})
        except Exception as exc:
            factor_results.append({**meta, "status":"ERRORE CALCOLO", "error":f"{type(exc).__name__}: {exc}"})
    factor_calculated = [x for x in factor_results if x["status"]=="CALCOLATO"]
    factor_calculated.sort(key=lambda x:(x["score"],x["factor"],x["geography"]),reverse=True)
    for rank, row in enumerate(factor_calculated,1):
        row["rank"] = rank
    insufficient = {"status":"DATI INSUFFICIENTI","observations":0,"note":"Nessun ETF factor con storico utilizzabile."}
    factor_validation_2020, factor_breadth = monthly_validation(
        factor_frames, factor_indicators, factor_universe, start_date="2020-01-01", universe_label="ETF factor"
    ) if factor_indicators else (dict(insufficient), {})
    factor_validation_2015, _ = monthly_validation(
        factor_frames, factor_indicators, factor_universe, start_date="2015-01-01", universe_label="ETF factor"
    ) if factor_indicators else (dict(insufficient), {})
    factor_comparison = factor_segment_validation(factor_universe, factor_frames, factor_indicators)
    factor_analysis = {
        "comparison_by_factor_geography": factor_comparison,
        "history_start": FACTOR_START_DATE,
        "primary_window": "2020-01-01",
        "extended_window": "2015-01-01",
        "universe_count": len(factor_universe),
        "calculated_count": len(factor_calculated),
        "unavailable_count": sum(x["status"]=="DATI NON DISPONIBILI" for x in factor_results),
        "short_history_count": sum(x["status"]=="STORICO INSUFFICIENTE" for x in factor_results),
        "error_count": sum(x["status"]=="ERRORE CALCOLO" for x in factor_results),
        "rankings": factor_calculated, "universe": factor_results,
        "validation": factor_validation_2020, "validation_primary_2020": factor_validation_2020,
        "validation_extended_2015": factor_validation_2015, "breadth": factor_breadth,
        "method": "ETF factor UCITS separati: Momentum, Quality e Value su Global, USA ed Europa. Confronto principale 2020-2026 e controllo esteso 2015-2026. Prezzi adjusted dal 2015 o dalla prima quotazione disponibile; nessun backfill artificiale.",
        "excluded": ["Minimum Volatility e Multifactor: esclusi finché ticker, listing e serie storiche non sono verificati."]
    }
    calculated = [x for x in results if x["status"]=="CALCOLATO"]
    calculated.sort(key=lambda x:(x["score"],x["geography"]),reverse=True)
    for rank, row in enumerate(calculated,1):
        row["rank"] = rank
    by_module = {}
    for row in calculated:
        by_module.setdefault(row.get("module") or "Non classificato",[]).append(row)
    validation, module_breadth = monthly_validation(frames,indicators,universe)
    early_v2 = early_signal_validation(indicators, universe)
    learned_v2 = walk_forward_early_model(indicators, universe)
    candidate_v3 = compare_predictive_candidates(indicators, universe, start_date="2015-01-01")
    momentum_baselines = {}
    for metric in ("modified_sharpe_68", "composite_momentum", "return_68d"):
        pool = [dict(x) for x in calculated if x.get(metric) is not None]
        pool.sort(key=lambda x: x.get(metric, -1e99), reverse=True)
        for rank, row in enumerate(pool, 1):
            row["baseline_rank"] = rank
        momentum_baselines[metric] = pool[:15]
    for row in calculated:
        row["breadth"] = module_breadth.get(str(row.get("module") or "Non classificato"))
    price_dates = [x["date"] for x in calculated if x.get("date")]
    output = {
        "generated_at":datetime.now(timezone.utc).isoformat(),
        "latest_price_date":max(price_dates) if price_dates else None,
        "status":("RADAR TECNICO ATTIVO · SCORE NON VALIDATO" if calculated else "NON OPERATIVO · DATI PREZZO ASSENTI"),
        "method":{
            "name":"Radar anticipatore tecnico — modello B preliminare",
            "score_max":100,
            "blocks":{
                "awakening":"25 punti: Alligator (allineamento + apertura) e KAMA (pendenza + prezzo sopra KAMA).",
                "acceleration":"25 punti: ROC 38 positivo; ROC 38 in aumento e AO sopra la propria media a 5 sedute.",
                "reversal":"20 punti: Vortex VI+ > VI-; RSI 14 tra 50 e 70 e in aumento.",
                "confirmation":"30 punti: prezzo sopra MA38; MA38 sopra MA200."
            },
            "investable_rule":"Filtro investibile preliminare soltanto se prezzo > MA200, MA38 > MA200, ROC38 > 0 e score >= 65. Non è un ordine.",
            "labels":{"75-100":"Forte miglioramento","55-74.9":"In miglioramento","0-54.9":"Debole / non confermato"},
            "limitations":[
                "Score tecnico provvisorio: non ancora validato come previsore di rendimenti.",
                "Breadth non calcolata: servono serie storiche di ampiezza di mercato/constituents per ciascun Paese.",
                "Macro (OECD CLI, PMI nuovi ordini, revisioni utili) non inclusi finché non sono disponibili dati storici coerenti e datati.",
                "Prezzi Yahoo Finance adjusted sono proxy e possono avere limiti, cambi valuta e differenze tra listing.",
                "L’universo usa gli ETF attualmente presenti nel ranking: il backtest storico può soffrire di survivorship bias e non ricostruisce le composizioni storiche degli indici.",
                "Le osservazioni sono coppie ETF-mese: non sono indipendenti e possono includere strumenti sovrapposti sulla stessa geografia.",
                "La verifica è un replay mensile point-in-time con soglia adattiva basata solo sui 36 mesi precedenti; i rendimenti forward si sovrappongono e il test resta esplorativo, non una validazione indipendente.",
                "Backtest esplorativo non incorpora costi, spread, slippage, tasse o rischio cambio."
            ],
            "no_lookahead":"Indicatori calcolati usando solo dati disponibili alla data dello snapshot. I rendimenti futuri sono usati esclusivamente nella sezione di valutazione.",
            "source":"Universo e gruppi letti da geografia-motore.json; prezzi OHLC adjusted da Yahoo Finance."
        },
        "coverage":{
            "universe_count":len(universe),
            "calculated_count":len(calculated),
            "unavailable_count":sum(x["status"]=="DATI NON DISPONIBILI" for x in results),
            "short_history_count":sum(x["status"]=="STORICO INSUFFICIENTE" for x in results),
            "error_count":sum(x["status"]=="ERRORE CALCOLO" for x in results)
        },
        "rankings":calculated,
        "by_module":by_module,
        "module_breadth":module_breadth,
        "momentum_baselines":momentum_baselines,
        "universe":results,
        "validation":validation,
        "predictive_v2": {"name": "Predittivo 2.0 · focus primo mese", "validation_1m": early_v2, "walk_forward_model_1m": learned_v2, "priority_horizon": "1m", "score_definition": "Score anticipatore 0-100: ROC5/10/21, accelerazione ROC, prezzo e pendenza KAMA, Lips/Teeth Alligator, Vortex e RSI in fascia costruttiva; nessun filtro MA200.", "status": "SPERIMENTALE FINO A SUPERAMENTO DEL TEST OUT-OF-SAMPLE"},
        "predictive_v3": candidate_v3,
        "predictive_v3_walk_forward": walk_forward_predictive_v3(indicators, universe),
        "factor_analysis":factor_analysis
    }
    OUT.write_text(json.dumps(output,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps(output["coverage"],ensure_ascii=False))
    print("Latest price date:",output["latest_price_date"])
    print("Validation:",validation.get("status"),validation.get("observations"))
    print("Output:",OUT)

if __name__=="__main__":
    main()