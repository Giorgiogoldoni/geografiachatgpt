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
START_DATE = "2005-01-01"
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

def download_prices(symbols):
    frames, errors = {}, {}
    for start in range(0, len(symbols), CHUNK_SIZE):
        batch = symbols[start:start + CHUNK_SIZE]
        raw = None
        try:
            # Same Yahoo Finance request convention as the established UCITS engine.
            raw = yf.download(
                tickers=batch, start=START_DATE, auto_adjust=True,
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
                    tickers=symbol, start=START_DATE, auto_adjust=True,
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
    ma200 = close.rolling(200).mean()

    out = pd.DataFrame({
        "close": close, "jaw": jaw, "teeth": teeth, "lips": lips,
        "kama": k, "roc38": roc, "ao": ao, "ao_signal": ao_signal,
        "vi_plus": vi_plus, "vi_minus": vi_minus, "rsi14": rsi,
        "ma38": ma38, "ma200": ma200,
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
    out["vortex_bull"] = vi_plus > vi_minus
    out["investable_filter"] = (close > ma200) & (ma38 > ma200) & (roc > 0)
    out["roc126"] = close.pct_change(126) * 100.0
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
        "ma200": finite(r["ma200"]),
        "roc126": finite(r["roc126"]),
        "investable_filter": bool(r["investable_filter"]),
        "investable": investable,
        "radar_label": label,
        "investable_label": invest_label,
        "breadth": None,
        "macro": None,
    }

def monthly_validation(frames, indicators):
    observations = []
    for symbol, ind in indicators.items():
        # One observation per month; future returns are outcomes, never inputs to score.
        monthly = ind[["score"]].resample("ME").last().dropna()
        close = frames[symbol]["Close"].reindex(ind.index)
        for date, row in monthly.iterrows():
            pos = ind.index.searchsorted(date)
            if pos >= len(ind.index):
                continue
            rec = {"symbol": symbol, "date": date, "score": float(row["score"])}
            for horizon, n in (("1m",21),("3m",63),("6m",126)):
                if pos+n < len(ind.index):
                    rec[horizon] = float(ind["close"].iloc[pos+n] / ind["close"].iloc[pos] - 1)
            observations.append(rec)
    if not observations:
        return {"status":"DATI INSUFFICIENTI","observations":0,"note":"Nessuna serie mensile con rendimenti futuri completi."}
    panel = pd.DataFrame(observations).sort_values("date")
    panel = panel.dropna(subset=["1m","3m","6m"])
    if panel.empty:
        return {"status":"DATI INSUFFICIENTI","observations":0}
    split_date = panel["date"].quantile(0.70)
    test = panel[panel["date"] > split_date].copy()
    if test.empty:
        test = panel.copy()
        split_date = panel["date"].min()
    high = test[test["score"] >= 65]
    def stats(frame, label):
        result = {"label":label,"n":int(len(frame))}
        for h in ("1m","3m","6m"):
            values = frame[h] if len(frame) else pd.Series(dtype=float)
            result[h] = {
                "mean_return": finite(values.mean()) if len(values) else None,
                "hit_rate": finite((values > 0).mean()) if len(values) else None,
            }
        return result
    return {
        "status":"ESPLORATIVO NON VALIDATO",
        "observations":int(len(panel)),
        "out_of_sample_from":split_date.strftime("%Y-%m-%d"),
        "out_of_sample":stats(test,"Tutte le osservazioni OOS"),
        "oos_score_ge_65":stats(high,"Score >= 65 OOS"),
        "method":"Snapshot mensili; split temporale unico 70/30 (non ancora walk-forward rolling); rendimenti futuri a 21/63/126 sedute. Nessun parametro ottimizzato. Rendimenti lordi, senza costi, FX e slippage.",
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
    calculated = [x for x in results if x["status"]=="CALCOLATO"]
    calculated.sort(key=lambda x:(x["score"],x["geography"]),reverse=True)
    for rank, row in enumerate(calculated,1):
        row["rank"] = rank
    by_module = {}
    for row in calculated:
        by_module.setdefault(row.get("module") or "Non classificato",[]).append(row)
    validation = monthly_validation(frames,indicators)
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
                "Le osservazioni sono coppie ETF-mese: non sono indipendenti e possono includere strumenti sovrapposti sulla stessa geografia.",
                "Il test attuale è un singolo holdout cronologico 70/30, non un walk-forward rolling; serve una validazione rolling e confronto con benchmark prima dell’uso operativo.",
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
        "universe":results,
        "validation":validation
    }
    OUT.write_text(json.dumps(output,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps(output["coverage"],ensure_ascii=False))
    print("Latest price date:",output["latest_price_date"])
    print("Validation:",validation.get("status"),validation.get("observations"))
    print("Output:",OUT)

if __name__=="__main__":
    main()
