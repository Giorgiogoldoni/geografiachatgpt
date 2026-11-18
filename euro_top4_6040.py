"""European UCITS 60/40 portfolio, matched to the US research scenario.
Transparent approximation; only mapped UCITS listings and explicit EUR defensive proxies.
"""
import json, warnings
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import yfinance as yf
from world_top4 import stats, metrics

OUT=Path("euro_top4_6040.json")
START="2010-01-01"
# Explicitly mapped European listings from the UCITS seed.
REGIONS={
 "Developed": ["CSCA.MI","IAEX.AS","IBCJ.DE"],
 "Asia-Pacific": ["SJPA.MI","FLXK.MI","FLXI.MI"],
 "Latin America": ["D5BI.DE","FLXB.MI","LTAM.MI","ALAT.MI"],
 "Africa-Middle East": ["SRSA.MI","IQQ5.DE","QDVM.DE"],
}
# EUR defensive proxies: XEON is overnight-rate/cash-like; SGLD is a gold ETC,
# not a UCITS ETF. Their role is a research proxy, not a claim of equivalence
# to the US Treasury / GLD sleeve.
DEFENSIVE={"Cash-like EUR":("XEON.DE",0.24),"Gold ETC":("SGLD.MI",0.16)}
BENCH="VWCE.DE"

def download(symbols):
 raw=yf.download(sorted(set(symbols)),start=START,auto_adjust=True,progress=False,threads=True,group_by="column")
 if raw is None or raw.empty: raise RuntimeError("Nessun prezzo restituito")
 close=raw["Close"] if isinstance(raw.columns,pd.MultiIndex) else raw[["Close"]].rename(columns={"Close":symbols[0]})
 if isinstance(close,pd.Series): close=close.to_frame(name=symbols[0])
 close.index=pd.to_datetime(close.index).tz_localize(None)
 return close.apply(pd.to_numeric,errors="coerce").sort_index().dropna(how="all")

def main():
 symbols=sum(REGIONS.values(),[])+[x[0] for x in DEFENSIVE.values()]+[BENCH]
 p=download(symbols); latest=p.dropna(how="all").index[-1]
 monthly=p.resample("ME").last().dropna(how="all")
 if latest.to_period("M")==pd.Timestamp.now(tz="UTC").to_period("M"): monthly=monthly.iloc[:-1]
 dates=list(monthly.index); rows=[]
 for i in range(1,len(dates)):
  sig=dates[i-1]; end=dates[i]; picks=[]; weights={}
  for area,assets in REGIONS.items():
   ranked=[]
   for ticker in assets:
    if ticker not in p: continue
    z=stats(p[ticker],sig)
    if z and z["return_68d"]>0 and z.get("momentum_12m") is not None and z["momentum_12m"]>0:
     ranked.append({"ticker":ticker,**z,"score":z["return_68d"]/(z["vol_annual"]**2) if z["vol_annual"] else None})
   ranked=[x for x in ranked if x["score"] is not None]
   ranked.sort(key=lambda x:x["score"],reverse=True)
   if not ranked: break
   pick=ranked[0]; picks.append({"area":area,**pick}); weights[pick["ticker"]]=weights.get(pick["ticker"],0)+0.15
  if len(picks)!=4: continue
  for _,(ticker,w) in DEFENSIVE.items():
   if ticker not in p: break
   weights[ticker]=w
  if len(weights)<6: continue
  a=monthly.loc[sig]; b=monthly.loc[end]
  if any(t not in monthly.columns or pd.isna(a.get(t)) or pd.isna(b.get(t)) or a[t]<=0 for t in weights): continue
  ret=sum(w*(b[t]/a[t]-1) for t,w in weights.items())
  bench_ret=None
  if BENCH in monthly and pd.notna(a.get(BENCH)) and pd.notna(b.get(BENCH)) and a[BENCH]>0:
   bench_ret=float(b[BENCH]/a[BENCH]-1)
  rows.append({"signal_date":sig.strftime("%Y-%m-%d"),"holding_to":end.strftime("%Y-%m-%d"),
   "return":float(ret),"benchmark_return":bench_ret,"picks":picks,
   "defensive":[{"ticker":t,"weight":w} for t,w in weights.items() if t not in [x["ticker"] for x in picks]],
   "weights":weights})
 # Aligned benchmark and portfolio metrics on identical months.
 aligned=[x for x in rows if x["benchmark_return"] is not None]
 def series_metrics(key):
  sub=[{"holding_to":x["holding_to"],"return":x[key]} for x in aligned if x[key] is not None]
  return metrics(sub) if sub else {}
 counts={}
 for row in aligned:
  for pck in row["picks"]: counts[pck["ticker"]]=counts.get(pck["ticker"],0)+1
 result={"generated_at":datetime.now(timezone.utc).isoformat(),"latest_price_date":latest.strftime("%Y-%m-%d"),
  "data_source":"Yahoo Finance adjusted daily prices; European listing symbols",
  "methodology":{"equity_weight":0.60,"defensive_weight":0.40,"regional_equity_weights":"15% per each of four sleeves",
   "defensive_split":"24% XEON.DE EUR overnight-rate proxy + 16% SGLD.MI gold ETC",
   "ranking":"68-session return / annualized volatility squared; positive 68-session and 12-month momentum filter; monthly rebalance",
   "warning":"Independent European UCITS approximation, not official Logical Invest. The universe is limited to mapped seed candidates and has uneven country coverage. XEON is a cash-like proxy, SGLD is an ETC (not a UCITS ETF); neither is equivalent to US Treasury/GLD. No fees, taxes, slippage or currency-hedging adjustment. Benchmark VWCE.DE is a proxy."},
  "regions":REGIONS,"defensive":DEFENSIVE,"metrics":series_metrics("return"),
  "benchmark_metrics":series_metrics("benchmark_return"),"benchmark":BENCH,
  "selection_months":len(aligned),"history":aligned[-60:],"selection_frequency":dict(sorted(counts.items(),key=lambda x:(-x[1],x[0])))}
 OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False),encoding="utf-8")
 print("EURO 60/40",latest.date(),"months",len(aligned),"history",len(rows))
if __name__=="__main__":
 warnings.filterwarnings("ignore"); main()
