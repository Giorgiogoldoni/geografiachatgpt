#!/usr/bin/env python3
"""UCITS Geographic Rotation Engine — independent, transparent research model.

Downloads adjusted daily prices for explicitly mapped European listings, ranks
country ETFs by 68-session Modified Sharpe and 3/6/12-month momentum, and applies
an absolute trend filter. Regional Latin America ETFs are ranked separately
from country ETFs to avoid treating a region as a country.
"""
from __future__ import annotations
import json, math, os, warnings
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parent
UNIVERSE = ROOT / "ucits_country_universe_seed_2026-11-18.csv"
OUT = ROOT / "ucits_geography.json"
LOOKBACK = 68
START = "2005-01-01"
# Yahoo Finance symbols refer to a specific European listing where possible.
# A blank symbol means that the listing/price series still needs verification.
MAP = {
    "IE00BHZRR030": ("FLXK.MI", "Borsa Italiana", "EUR", "country"),
    "IE00B52SF786": ("CSCA.MI", "Borsa Italiana", "EUR", "country"),
    "IE00B0M62Y33": ("IAEX.AS", "Euronext Amsterdam", "EUR", "country"),
    "IE00BHZRQZ17": ("FLXI.MI", "Borsa Italiana", "EUR", "country"),
    "IE00B4L5YX21": ("SJPA.MI", "Borsa Italiana", "EUR", "country"),
    "IE00B4M7GH52": ("IBCJ.DE", "Xetra", "EUR", "country"),
    "IE00BHZRQY00": ("FLXB.MI", "Borsa Italiana", "EUR", "country"),
    "LU0476289466": ("D5BI.DE", "Xetra", "EUR", "country"),
    "IE00B52XQP83": ("SRSA.MI", "Borsa Italiana", "EUR", "country"),
    "IE00B1FZS574": ("IQQ5.DE", "Xetra", "EUR", "country"),
    "IE00B27YCK28": ("LTAM.MI", "Borsa Italiana", "EUR", "regional"),
    "LU1681045024": ("ALAT.MI", "Borsa Italiana", "EUR", "regional"),
    "IE00BP3QZG05": ("QDVM.DE", "Xetra", "EUR", "country"),
}
AREAS = {
    "Developed": ["Poland", "Japan", "Canada", "Netherlands"],
    "Asia-Pacific emergente": ["South Korea", "Taiwan", "India", "China"],
    "America Latina": ["Brazil", "Mexico"],
    "Africa e Medio Oriente": ["South Africa", "Turkey", "Israel"],
}
REGIONAL_FUNDS = {"America Latina": ["LTAM", "ALAT"]}

def safe_float(x):
    try:
        v=float(x)
        return v if math.isfinite(v) else None
    except Exception:
        return None

def download_prices(symbols):
    if not symbols:
        return pd.DataFrame()
    raw=yf.download(sorted(set(symbols)), start=START, auto_adjust=True,
                    progress=False, threads=True, group_by="column")
    if raw is None or raw.empty:
        return pd.DataFrame()
    if isinstance(raw.columns, pd.MultiIndex):
        level0=list(raw.columns.get_level_values(0))
        key="Close" if "Close" in level0 else "Adj Close"
        close=raw[key] if key in level0 else pd.DataFrame()
    else:
        key="Close" if "Close" in raw.columns else "Adj Close"
        close=raw[[key]].rename(columns={key:symbols[0]}) if key in raw.columns else pd.DataFrame()
    if isinstance(close,pd.Series):
        close=close.to_frame(name=symbols[0])
    close.index=pd.to_datetime(close.index).tz_localize(None)
    return close.apply(pd.to_numeric,errors="coerce").sort_index()

def score_series(series):
    p=series.dropna()
    if len(p)<max(LOOKBACK+1,253):
        return None
    daily=p.pct_change().dropna()
    r=daily.tail(LOOKBACK)
    if len(r)<LOOKBACK:
        return None
    mu=float(r.mean()); sd=float(r.std(ddof=1))
    if not math.isfinite(sd) or sd<=0:
        return None
    last=float(p.iloc[-1])
    def momentum(n):
        return safe_float(last/float(p.iloc[-n-1])-1) if len(p)>=n+1 else None
    m3,m6,m12=momentum(63),momentum(126),momentum(252)
    sma200=float(p.tail(200).mean()) if len(p)>=200 else None
    trend=bool(sma200 is not None and last>sma200)
    absolute=bool(m12 is not None and m12>0)
    return {
        "price":last,"return_68d":safe_float(last/float(p.iloc[-LOOKBACK-1])-1),
        "volatility_annual":safe_float(sd*math.sqrt(252)),
        "modified_sharpe":safe_float(mu/(sd**2)),
        "momentum_3m":m3,"momentum_6m":m6,"momentum_12m":m12,
        "composite_momentum":safe_float(.4*m3+.3*m6+.3*m12) if None not in (m3,m6,m12) else None,
        "sma200":sma200,"above_sma200":trend,"absolute_momentum_positive":absolute,
        "eligible_trend":bool(trend and absolute),
        "observations":int(len(p)),"price_date":p.index[-1].strftime("%Y-%m-%d")
    }

def main():
    uni=pd.read_csv(UNIVERSE).fillna("")
    records=[]
    for _,r in uni.iterrows():
        isin=str(r.get("isin","")).strip()
        meta=MAP.get(isin)
        if not meta:
            records.append({"region":r.get("region",""),"country":r.get("country",""),
                "fund":r.get("ucits_fund",""),"isin":isin,"ticker":r.get("justetf_primary_ticker",""),
                "status":"NON MAPPATO","reason":"Quotazione e serie prezzi non ancora mappate"})
            continue
        symbol,exchange,currency,kind=meta
        records.append({"region":r.get("region",""),"country":r.get("country",""),
            "fund":r.get("ucits_fund",""),"isin":isin,"ticker":r.get("justetf_primary_ticker",""),
            "symbol":symbol,"exchange":exchange,"currency":currency,"kind":kind,
            "status":"IN ATTESA DATI"})
    symbols=[x["symbol"] for x in records if x.get("symbol")]
    warnings_list=[]
    try:
        prices=download_prices(symbols)
    except Exception as e:
        prices=pd.DataFrame()
        warnings_list.append(f"Errore download prezzi: {type(e).__name__}: {e}")
    for x in records:
        sym=x.get("symbol")
        if not sym: continue
        if sym not in prices.columns:
            x.update({"status":"DATI NON DISPONIBILI","reason":"Yahoo Finance non ha restituito la quotazione"})
            continue
        s=score_series(prices[sym])
        if s is None:
            x.update({"status":"STORICO INSUFFICIENTE","reason":f"Servono almeno {max(LOOKBACK+1,253)} osservazioni"})
            continue
        x.update(s)
        x["status"]="CALCOLATO"
        x["score_rank_modified"]=s["modified_sharpe"]
        x["score_rank_momentum"]=s["return_68d"]
        x["score_rank_composite"]=s["composite_momentum"]
    countries=[x for x in records if x.get("kind")=="country" and x["status"]=="CALCOLATO"]
    regional=[x for x in records if x.get("kind")=="regional" and x["status"]=="CALCOLATO"]
    rankings={}
    selected={}
    for area,names in AREAS.items():
        pool=[x for x in countries if x["country"] in names]
        pool.sort(key=lambda x:(x.get("modified_sharpe") is not None,x.get("modified_sharpe") or -1e99),reverse=True)
        rankings[area]=pool
        eligible=[x for x in pool if x["eligible_trend"]]
        selected[area]=eligible[0] if eligible else None
    regional_rank={}
    for area,names in REGIONAL_FUNDS.items():
        pool=[x for x in regional if x["ticker"] in names]
        pool.sort(key=lambda x:x.get("modified_sharpe") or -1e99,reverse=True)
        regional_rank[area]=pool
    all_dates=[x.get("price_date") for x in records if x.get("price_date")]
    result={
        "generated_at":datetime.now(timezone.utc).isoformat(),
        "latest_price_date":max(all_dates) if all_dates else None,
        "method":{"lookback_sessions":LOOKBACK,"primary_score":"mean(daily returns) / stdev(daily returns)^2",
          "momentum_windows_sessions":{"3m":63,"6m":126,"12m":252},
          "composite_weights":{"3m":.4,"6m":.3,"12m":.3},
          "trend_filter":"last price > SMA200 AND 12-month momentum > 0",
          "rebalance":"monthly; current snapshot only in this first engine release",
          "notes":["Modified Sharpe is a documented historical reference, not a verified current Logical Invest formula.",
            "Country ETFs and regional Latin America ETFs are ranked separately.",
            "Unmapped or insufficient-history instruments are not silently substituted."]},
        "areas":AREAS,"rankings":rankings,"selected":selected,
        "regional_alternatives":regional_rank,"universe":records,
        "coverage":{"universe_count":len(records),"calculated_count":sum(x["status"]=="CALCOLATO" for x in records),
          "unmapped_count":sum(x["status"]=="NON MAPPATO" for x in records),
          "price_unavailable_count":sum(x["status"]=="DATI NON DISPONIBILI" for x in records),
          "insufficient_history_count":sum(x["status"]=="STORICO INSUFFICIENTE" for x in records)},
        "warnings":warnings_list
    }
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False),encoding="utf-8")
    print(json.dumps(result["coverage"],ensure_ascii=False))
    print("Latest price date:",result["latest_price_date"])
    print("Output:",OUT)

if __name__=="__main__":
    main()
