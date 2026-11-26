#!/usr/bin/env python3
"""Build weekly relative rotation trails using Yahoo Finance adjusted prices."""
from pathlib import Path
import json, warnings
import pandas as pd
import yfinance as yf
ROOT=Path(__file__).resolve().parent
GEO=ROOT/"data/geografia_index_user_53.csv"
FAC=ROOT/"data/geografia_index_factor_21.csv"
OUT=ROOT/"rrg-history.json"
BENCHMARKS={"WRD.PA":"MSCI World (WRD.PA)","SPY":"S&P 500 (SPY)","ACWI":"MSCI ACWI (ACWI)","EFA":"Developed ex-US (EFA)","FEZ":"Euro Stoxx 50 (FEZ)","IWM":"Russell 2000 (IWM)"}
OVERRIDES={"IWMO":"IWMO.MI","IEMO":"IEMO.MI","XDEM":"XDEM.MI","SPEQ":"SPEQ.MI","MWEQ":"MWEQ.MI","MEEQ":"MEEQ.MI","IEWQ":"IEWQ.MI","WELE":"WELE.MI","IWQU":"IWQU.MI","IEQU":"IEQU.MI","XDEQ":"XDEQ.MI","QDVB":"QDVB.DE","QCEU":"QCEU.MI","IWVL":"IWVL.MI","IEVL":"IEVL.MI","XDEV":"XDEV.MI","QDVI":"QDVI.DE","VCEU":"VCEU.MI","QDVA":"QDVA.DE","MCEU":"MCEU.PA"}
def symbol_for(t):
 t=str(t or "").strip()
 return OVERRIDES.get(t,t if "." in t else t+".MI")
def download_weekly(tickers):
 with warnings.catch_warnings():
  warnings.simplefilter("ignore")
  raw=yf.download(list(sorted(set(tickers))),period="2y",interval="1d",auto_adjust=True,group_by="ticker",threads=True,progress=False)
 if raw.empty:return pd.DataFrame()
 if isinstance(raw.columns,pd.MultiIndex):
  field_level=next((i for i in range(raw.columns.nlevels) if "Close" in raw.columns.get_level_values(i)),None)
  if field_level is None: raise RuntimeError("Yahoo multiindex missing Close: "+str(raw.columns.names))
  weekly=raw.xs("Close",axis=1,level=field_level)
 else:
  weekly=raw[["Close"]].rename(columns={"Close":tickers[0]})
 weekly.index=pd.to_datetime(weekly.index)
 return weekly.resample("W-FRI").last().dropna(how="all")
def main():
 geo=pd.read_csv(GEO,dtype=str).fillna(""); fac=pd.read_csv(FAC,dtype=str).fillna("")
 rows=[]
 for _,r in geo.iterrows():
  rows.append({"ticker":r.ticker,"name":r["name"],"group":"Geografici","geography":r.geography,"factor":"","symbol":symbol_for(r.ticker)})
 for _,r in fac.iterrows():
  rows.append({"ticker":r.ticker,"name":r["name"],"group":"Factor","geography":r.geography,"factor":r.category,"symbol":symbol_for(r.ticker)})
 tickers=[x["symbol"] for x in rows]+list(BENCHMARKS)
 prices=download_weekly(tickers)
 result={"generated_at":pd.Timestamp.utcnow().isoformat(),"source":"Yahoo Finance auto_adjust daily prices resampled weekly Friday; RRG-like formula (not proprietary SPDR)","weeks":[],"benchmarks":BENCHMARKS,"universe":[],"week_count":0}
 if prices.empty:
  OUT.write_text(json.dumps(result,indent=2));return
 dates=list(prices.index); result["weeks"]=[d.strftime("%Y-%m-%d") for d in dates];result["week_count"]=len(dates)
 for bench in BENCHMARKS:
  if bench not in prices.columns or prices[bench].dropna().size<30:continue
  bp=prices[bench]
  for item in rows:
   sym=item["symbol"]
   if sym not in prices.columns:continue
   pair=pd.concat([prices[sym],bp],axis=1).dropna()
   if len(pair)<30:continue
   relative=pair.iloc[:,0]/pair.iloc[:,1]
   ratio=relative/relative.shift(12)*100
   momentum=100+(ratio-ratio.shift(4))
   lookup={}
   for date,x,y in zip(pair.index,ratio,momentum):
    if pd.notna(x) and pd.notna(y):lookup[date.strftime("%Y-%m-%d")]={"date":date.strftime("%Y-%m-%d"),"x":round(float(x),4),"y":round(float(y),4)}
   series=[lookup.get(d.strftime("%Y-%m-%d")) for d in dates]
   if sum(v is not None for v in series)>=12:item.setdefault("series",{})[bench]=series
 result["universe"]=rows
 OUT.write_text(json.dumps(result,separators=(",",":")))
 count=sum(bool(x.get("series")) for x in rows)
 print(f"RRG history: {count}/{len(rows)} ETF; {len(dates)} weekly dates; {len(prices.columns)} symbols downloaded.")
if __name__=="__main__":main()
