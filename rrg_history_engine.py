#!/usr/bin/env python3
"""Weekly RRG history for GeografiaChatGPT ETF universe (Yahoo adjusted-price proxy)."""
from pathlib import Path
import json, time, warnings
import pandas as pd
import yfinance as yf

ROOT=Path(__file__).resolve().parent
GEO=ROOT/"data/geografia_index_user_53.csv"
FAC=ROOT/"data/geografia_index_factor_21.csv"
OUT=ROOT/"rrg-history.json"
PERIOD="2y"
BENCHMARKS={
 "WRD.PA":"MSCI World (WRD.PA)",
 "SPY":"S&P 500 (SPY)",
 "ACWI":"MSCI ACWI (ACWI)",
 "EFA":"Developed ex-US (EFA)",
 "FEZ":"Euro Stoxx 50 (FEZ)",
 "IWM":"Russell 2000 (IWM)",
}
def norm_symbol(s):
 s=str(s or "").strip()
 return s if "." in s else s+".MI"
def weekly_close(tickers):
 with warnings.catch_warnings():
  warnings.simplefilter("ignore")
  raw=yf.download(sorted(set(tickers)),period=PERIOD,interval="1d",auto_adjust=True,group_by="ticker",threads=True,progress=False)
 if raw.empty: return pd.DataFrame()
 if isinstance(raw.columns,pd.MultiIndex):
  field="Close"
  if field not in raw.columns.get_level_values(0): field="Adj Close"
  df=raw[field]
 else:
  df=raw[["Close"]].rename(columns={"Close":tickers[0]})
 df.index=pd.to_datetime(df.index)
 return df.resample("W-FRI").last().dropna(how="all")
def main():
 geo=pd.read_csv(GEO,dtype=str).fillna("")
 fac=pd.read_csv(FAC,dtype=str).fillna("")
 rows=[]
 for _,r in geo.iterrows():
  rows.append({"ticker":r.ticker,"name":r["name"],"group":"Geografici","geography":r.geography,"factor":"","symbol":norm_symbol(r.ticker)})
 for _,r in fac.iterrows():
  sym=str(r.ticker).strip()
  # explicit verified mappings; avoid silently assigning uncertain listings
  overrides={"IWMO":"IWMO.MI","IEMO":"IEMO.MI","XDEM":"XDEM.MI","SPEQ":"SPEQ.MI","MWEQ":"MWEQ.MI","MEEQ":"MEEQ.MI","IEWQ":"IEWQ.MI","WELE":"WELE.MI","IWQU":"IWQU.MI","IEQU":"IEQU.MI","XDEQ":"XDEQ.MI","QDVB":"QDVB.DE","QCEU":"QCEU.MI","IWVL":"IWVL.MI","IEVL":"IEVL.MI","XDEV":"XDEV.MI","QDVI":"QDVI.DE","VCEU":"VCEU.MI","QDVA":"QDVA.DE","MCEU":"MCEU.PA"}
  rows.append({"ticker":sym,"name":r["name"],"group":"Factor","geography":r.geography,"factor":r.category,"symbol":overrides.get(sym,sym if "." in sym else sym+".MI")})
 benchmarks={k:v for k,v in BENCHMARKS.items()}
 tickers=[x["symbol"] for x in rows]+list(benchmarks)
 prices=weekly_close(tickers)
 data={"generated_at":pd.Timestamp.utcnow().isoformat(),"source":"Yahoo Finance auto_adjust weekly Friday close (proxy; FX/listing differences possible)","weeks":[], "benchmarks":benchmarks,"universe":[],"status":{}}
 if prices.empty:
  OUT.write_text(json.dumps(data,indent=2));return
 # Retain common week dates and require minimum history.
 weeks=prices.index.strftime("%Y-%m-%d").tolist()
 data["weeks"]=weeks
 for b in benchmarks:
  if b not in prices.columns or prices[b].dropna().size<30: continue
  bprice=prices[b].dropna()
  for item in rows:
   s=item["symbol"]
   if s not in prices.columns: continue
   p=prices[s].dropna()
   # relative-strength series aligned on common weekly closes
   pair=pd.concat([p,bprice],axis=1,join="inner").dropna()
   if len(pair)<30: continue
   rel=pair.iloc[:,0]/pair.iloc[:,1]
   # RS-Ratio: normalized relative strength vs 12-week ago, baseline 100
   rsratio=(rel/rel.shift(12))*100
   # RS-Momentum: RS-Ratio change over 4 weeks, normalized baseline 100
   rsmom=100+(rsratio-rsratio.shift(4))
   values=[]
   for date,rr,rm in zip(pair.index,rsratio,rsmom):
    if pd.notna(rr) and pd.notna(rm):
     values.append({"date":date.strftime("%Y-%m-%d"),"x":round(float(rr),4),"y":round(float(rm),4)})
   if len(values)>=12:
    item.setdefault("series",{})[b]=values
 # Ensure one object per instrument, compact series for each benchmark
 data["universe"]=rows
 data["week_count"]=len(weeks)
 OUT.write_text(json.dumps(data,separators=(",",":")))
 print(f"Saved {OUT.name}; weeks={len(weeks)}, universe={len(rows)}, tickers={len(prices.columns)}")
if __name__=="__main__": main()
