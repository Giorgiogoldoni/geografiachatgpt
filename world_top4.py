import json, math, warnings
from datetime import datetime, timezone
from pathlib import Path
import numpy as np, pandas as pd, yfinance as yf
LB=68; START="2006-01-01"; BENCH="ACWI"; OUT=Path("world_top4.json")
REGIONS={
"Developed":["SPY","DIA","EIRL","EIS","ENZL","EPOL","EWA","EWC","EWD","EWG","EWH","EWI","EWJ","EWK","EWL","EWM","EWN","EWO","EWP","EWQ","EWU","NORW","QQQ"],
"Asia":["ASHR","EIDO","EPHE","EPI","EWJ","EWM","EWS","EWT","EWY","FXI","THD","VNM"],
"South America":["ARGT","ECH","EPU","EWW","EWZ"],
"Africa & Middle East":["AFK","EZA","TUR","GREK","KSA","UAE","QAT"]}
HEDGE=["GLD","TLT","IEF","SHY"]
def download(ts):
 d=yf.download(sorted(set(ts)),start=START,auto_adjust=True,progress=False,threads=True,group_by="column")
 if d is None or d.empty: raise RuntimeError("Nessun prezzo Yahoo Finance")
 c=d["Close"] if isinstance(d.columns,pd.MultiIndex) else d[["Close"]].rename(columns={"Close":ts[0]})
 if isinstance(c,pd.Series): c=c.to_frame(name=ts[0])
 return c.sort_index().apply(pd.to_numeric,errors="coerce").dropna(how="all")
def stats(s,date):
 p=s.loc[:date].dropna()
 if len(p)<LB+1:return None
 r=p.pct_change().dropna().tail(LB); vol=float(r.std()*math.sqrt(252)); ret=float(p.iloc[-1]/p.iloc[-LB-1]-1)
 if not np.isfinite(vol) or vol<=0:return None
 mom=lambda n:float(p.iloc[-1]/p.iloc[-min(n,len(p))]-1)
 return {"return_68d":ret,"vol_annual":vol,"sharpe_68d":float(r.mean()/r.std()*math.sqrt(252)),
 "modified_score":ret/vol**2,"momentum_1m":mom(22),"momentum_3m":mom(63),"momentum_6m":mom(126),"momentum_12m":mom(252)}
def rank(prices,tickers,date,variant):
 out=[]
 for t in tickers:
  if t not in prices:continue
  z=stats(prices[t],date)
  if z:
   score=z["return_68d"] if variant=="momentum" else (.4*z["momentum_3m"]+.3*z["momentum_6m"]+.3*z["momentum_12m"] if variant=="composite" else z["modified_score"])
   out.append({"ticker":t,**z,"score":float(score)})
 return sorted(out,key=lambda x:x["score"],reverse=True)
def metrics(rows):
 if not rows:return {}
 r=pd.Series([x["return"] for x in rows]); eq=(1+r).cumprod(); dd=eq/eq.cummax()-1; vol=float(r.std()*math.sqrt(12)) if len(r)>1 else 0
 neg=r[r<0]; down=float(neg.std()*math.sqrt(12)) if len(neg)>1 else 0; years=len(r)/12
 return {"months":len(r),"total_return":float(eq.iloc[-1]-1),"cagr":float(eq.iloc[-1]**(1/years)-1) if years else 0,
 "volatility":vol,"sharpe":float(r.mean()*12/(vol+1e-12)),"sortino":float(r.mean()*12/(down+1e-12)),
 "max_drawdown":float(dd.min()),"ulcer_index":float(np.sqrt(np.mean((dd*100)**2))),
 "equity_curve":[{"date":x.get("holding_to"),"value":float(v)} for x,v in zip(rows,eq)]}
def backtest(p,variant,common_start=None):
 m=p.resample("ME").last().dropna(how="all"); dates=list(m.index); out=[]
 for i in range(1,len(dates)-1):
  sig,start,end=dates[i-1],dates[i],dates[i+1]; picks=[]
  if common_start is not None and start<common_start:continue
  for region,assets in REGIONS.items():
   rr=rank(p,assets,sig,variant)
   if rr:picks.append({"region":region,**rr[0]})
  picks=[x for x in picks if x["return_68d"]>0]
  hedge_weight=.2+.2*(4-len(picks))
  w={x["ticker"]:.2 for x in picks}
  hr=[h for h in rank(p,HEDGE,sig,variant) if h["return_68d"]>0][:2]
  if hr:
   for h in hr:w[h["ticker"]]=hedge_weight/len(hr)
  else:w["SHY"]=hedge_weight
  a=m.loc[start];b=m.loc[end]; valid={t:(wt,float(b[t]/a[t]-1)) for t,wt in w.items() if t in m and pd.notna(a.get(t)) and pd.notna(b.get(t)) and a[t]>0}
  if valid:
   den=sum(v[0] for v in valid.values()); ret=sum(x*y for x,y in valid.values())/den
   out.append({"signal_date":sig.strftime("%Y-%m-%d"),"holding_from":start.strftime("%Y-%m-%d"),"holding_to":end.strftime("%Y-%m-%d"),"return":ret,"picks":picks,"hedge":[{"ticker":h["ticker"],"score":h["score"]} for h in hr],"weights":w})
 return out
def main():
 tickers=sum(REGIONS.values(),[])+HEDGE+[BENCH]; p=download(tickers); latest=p.dropna(how="all").index[-1]
 bm=p.resample("ME").last()[BENCH].dropna()
 variants={}
 for v in ["modified","momentum","composite"]:
  h=backtest(p,v,bm.index[0]);variants[v]={"metrics":metrics(h),"history":h[-36:]}
 bh=[{"holding_to":bm.index[i].strftime("%Y-%m-%d"),"return":float(bm.iloc[i]/bm.iloc[i-1]-1)} for i in range(1,len(bm))]
 d={"generated_at":datetime.now(timezone.utc).isoformat(),"latest_price_date":latest.strftime("%Y-%m-%d"),"data_source":"Yahoo Finance adjusted daily prices",
 "methodology":{"lookback_trading_days":LB,"rebalance":"monthly","decision_timing":"previous month-end close; execute from next month","hedge_weight_assumption":.20,
 "regions":"Developed, Asia, South America, Africa & Middle East (fourth sleeve approximate)","warning":"Independent approximation, not Logical Invest formula. US-listed research tickers; excludes fees, taxes, slippage and FX."},
 "regions":{k:rank(p,v,latest,"modified")[:10] for k,v in REGIONS.items()},
 "selected":{k:(rank(p,v,latest,"modified")[0] if rank(p,v,latest,"modified") and rank(p,v,latest,"modified")[0]["return_68d"]>0 else None) for k,v in REGIONS.items()},
 "hedge":rank(p,HEDGE,latest,"modified")[:10],"variants":variants,"benchmark":{"ticker":BENCH,"metrics":metrics(bh)}}
 OUT.write_text(json.dumps(d,indent=2,allow_nan=False),encoding="utf-8");print("World Top 4",latest.date(),len(p.columns),"tickers")
if __name__=="__main__":
 warnings.filterwarnings("ignore");main()
