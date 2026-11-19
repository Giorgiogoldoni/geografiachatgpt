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
HEDGE=["GLD","TLT","IEF","SHY"]\nFX="EURUSD=X"  # USD per EUR; converts USD portfolio returns into EUR
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
 def mom(n):
  # Require n+1 observations for a genuine n-session return; never shorten
  # the lookback for recently listed ETFs.
  if len(p)<n+1:return None
  return float(p.iloc[-1]/p.iloc[-n-1]-1)
 return {"return_68d":ret,"vol_annual":vol,"sharpe_68d":float(r.mean()/r.std()*math.sqrt(252)),
 "modified_score":ret/vol**2,"momentum_1m":mom(22),"momentum_3m":mom(63),"momentum_6m":mom(126),"momentum_12m":mom(252)}
def rank(prices,tickers,date,variant):
 out=[]
 for t in tickers:
  if t not in prices:continue
  z=stats(prices[t],date)
  if z:
   if variant=="composite":
    # Composite needs complete 3/6/12-month history.
    if any(z[k] is None for k in ("momentum_3m","momentum_6m","momentum_12m")):continue
    score=.4*z["momentum_3m"]+.3*z["momentum_6m"]+.3*z["momentum_12m"]
   else:
    score=z["return_68d"] if variant=="momentum" else z["modified_score"]
   out.append({"ticker":t,**z,"score":float(score)})
 return sorted(out,key=lambda x:x["score"],reverse=True)
def metrics(rows):
 if not rows:return {}
 r=pd.Series([float(x["return"]) for x in rows],dtype=float)
 dates=pd.Series(pd.to_datetime([x.get("holding_to") for x in rows]))
 eq=(1+r).cumprod(); peak=eq.cummax(); dd=eq/peak-1
 vol=float(r.std(ddof=1)*math.sqrt(12)) if len(r)>1 else 0.0
 downside=float(np.sqrt(np.mean(np.minimum(r,0.0)**2))*math.sqrt(12)) if len(r) else 0.0
 years=len(r)/12
 cagr=float(eq.iloc[-1]**(1/years)-1) if years else 0.0
 sharpe=float(r.mean()*12/vol) if vol>0 else 0.0
 sortino=float(r.mean()*12/downside) if downside>0 else 0.0
 max_dd=float(dd.min())
 calmar=float(cagr/abs(max_dd)) if max_dd<0 else None
 underwater=(dd < -1e-10).tolist()
 episodes=[]; start=None
 for i,flag in enumerate(underwater):
  if flag and start is None:start=i
  if start is not None and (not flag or i==len(underwater)-1):
   end=i-1 if not flag else i
   episodes.append({"start":dates.iloc[start].strftime("%Y-%m-%d"),"end":dates.iloc[end].strftime("%Y-%m-%d"),"days":int((dates.iloc[end]-dates.iloc[start]).days)})
   start=None
 max_under=max([x["days"] for x in episodes],default=0)
 avg_under=float(np.mean([x["days"] for x in episodes])) if episodes else 0.0
 trough=int(dd.idxmin()); peak_idx=int(eq.iloc[:trough+1].idxmax()); peak_value=float(eq.iloc[peak_idx])
 recovery=next((i for i in range(trough+1,len(eq)) if float(eq.iloc[i])>=peak_value),None)
 maxdd_recovery=dates.iloc[recovery].strftime("%Y-%m-%d") if recovery is not None else None
 maxdd_duration=int((dates.iloc[recovery if recovery is not None else len(dates)-1]-dates.iloc[peak_idx]).days)
 yearly={}
 frame=pd.DataFrame({"return":r.values,"date":dates})
 for year,g in frame.groupby(frame["date"].dt.year):
  yearly[str(int(year))]=float((1+g["return"]).prod()-1)
 periods={}
 for n in (1,3,5,10,15):
  k=12*n
  if len(r)>=k:
   sub=r.tail(k).reset_index(drop=True); sub_dates=dates.tail(k).reset_index(drop=True)
   sub_eq=(1+sub).cumprod(); sub_dd=sub_eq/sub_eq.cummax()-1
   sub_vol=float(sub.std(ddof=1)*math.sqrt(12)) if len(sub)>1 else 0.0
   sub_down=float(np.sqrt(np.mean(np.minimum(sub,0.0)**2))*math.sqrt(12))
   sub_total=float(sub_eq.iloc[-1]-1); sub_cagr=float((1+sub_total)**(1/n)-1)
   sub_under=(sub_dd < -1e-10).tolist(); sub_runs=[]; sub_start=None
   for j,flag in enumerate(sub_under):
    if flag and sub_start is None:sub_start=j
    if sub_start is not None and (not flag or j==len(sub_under)-1):
     sub_end=j-1 if not flag else j
     sub_runs.append(int((sub_dates.iloc[sub_end]-sub_dates.iloc[sub_start]).days));sub_start=None
   sub_downside=float(np.sqrt(np.mean(np.minimum(sub,0.0)**2))*math.sqrt(12))
   periods[f"{n}y"]={"total_return":sub_total,"cagr":sub_cagr,
    "volatility":sub_vol,"downside_volatility":sub_downside,
    "sharpe_zero_rf":float(sub.mean()*12/sub_vol) if sub_vol>0 else 0.0,
    "sortino_zero_target":float(sub.mean()*12/sub_downside) if sub_downside>0 else 0.0,
    "max_drawdown":float(sub_dd.min()),"ulcer_index":float(np.sqrt(np.mean((sub_dd*100)**2))),
    "max_underwater_days":max(sub_runs,default=0),
    "avg_underwater_days":float(np.mean(sub_runs)) if sub_runs else 0.0}
 weights_prev={}; turnovers=[]
 for row in rows:
  current={k:float(v) for k,v in row.get("weights",{}).items()}
  if weights_prev:
   keys=set(weights_prev)|set(current)
   turnovers.append(0.5*sum(abs(current.get(k,0)-weights_prev.get(k,0)) for k in keys))
  weights_prev=current
 return {"months":len(r),"total_return":float(eq.iloc[-1]-1),"cagr":cagr,
 "volatility":vol,"downside_volatility":downside,"sharpe_zero_rf":sharpe,"sortino_zero_target":sortino,
 "max_drawdown":max_dd,"calmar":calmar,"ulcer_index":float(np.sqrt(np.mean((dd*100)**2))),
 "max_underwater_days":max_under,"avg_underwater_days":avg_under,"drawdown_episodes":len(episodes),
 "maxdd_peak_date":dates.iloc[peak_idx].strftime("%Y-%m-%d"),"maxdd_trough_date":dates.iloc[trough].strftime("%Y-%m-%d"),
 "maxdd_recovery_date":maxdd_recovery,"maxdd_recovery_days":maxdd_duration,
 "monthly_win_rate":float((r>0).mean()),"avg_monthly_turnover":float(np.mean(turnovers)) if turnovers else 0.0,
 "periods":periods,"yearly_returns":yearly,
 "equity_curve":[{"date":dates.iloc[i].strftime("%Y-%m-%d"),"value":float(v)} for i,v in enumerate(eq)]}
def backtest(p,variant,common_start=None):
 m=p.resample("ME").last().dropna(how="all")
 latest=p.dropna(how="all").index[-1]
 # Exclude the still-open calendar month; never treat a partial month as a full holding period.
 if latest.to_period("M")==pd.Timestamp.now(tz="UTC").to_period("M") and len(m):m=m.iloc[:-1]
 dates=list(m.index); out=[]
 for i in range(1,len(dates)):
  sig=start=dates[i-1]; end=dates[i]; picks=[]
  if common_start is not None and sig<common_start:continue
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
 tickers=sum(REGIONS.values(),[])+HEDGE+[BENCH,FX]; p=download(tickers); latest=p.dropna(how="all").index[-1]
 monthly=p.resample("ME").last()
 if latest.to_period("M")==pd.Timestamp.now(tz="UTC").to_period("M"):monthly=monthly.iloc[:-1]
 bm=monthly[BENCH].dropna()
 variants={}
 for v in ["modified","momentum","composite"]:
  h=backtest(p,v,bm.index[0]);variants[v]={"metrics":metrics(h),"history":h[-120:]}
 fxm=monthly[FX].dropna()\n bh=[]\n for i in range(1,len(bm)):\n  d0,d1=bm.index[i-1],bm.index[i]\n  if d0 not in fxm.index or d1 not in fxm.index or bm.iloc[i-1]<=0 or fxm.loc[d1]<=0: continue\n  eur_ret=(bm.iloc[i]/bm.iloc[i-1])*(fxm.loc[d0]/fxm.loc[d1])-1\n  bh.append({"holding_to":d1.strftime("%Y-%m-%d"),"return":float(eur_ret)})
 d={"generated_at":datetime.now(timezone.utc).isoformat(),"latest_price_date":latest.strftime("%Y-%m-%d"),"data_source":"Yahoo Finance adjusted daily prices; USD portfolio and ACWI benchmark converted to EUR using EURUSD=X",
 "methodology":{"lookback_trading_days":LB,"rebalance":"monthly","decision_timing":"previous month-end close; execute from next month","hedge_weight_assumption":.20,"reporting_currency":"EUR; USD asset returns converted monthly using EURUSD=X (USD per EUR)",
 "regions":"Developed, Asia, South America, Africa & Middle East (fourth sleeve approximate)","warning":"Independent approximation, not Logical Invest formula. US-listed research tickers; excludes fees, taxes, slippage and FX. Sharpe/Sortino here use zero risk-free/target assumptions and are not directly comparable with Logical Invest."},
 "regions":{k:rank(p,v,latest,"modified")[:10] for k,v in REGIONS.items()},
 "selected":{k:(rank(p,v,latest,"modified")[0] if rank(p,v,latest,"modified") and rank(p,v,latest,"modified")[0]["return_68d"]>0 else None) for k,v in REGIONS.items()},
 "hedge":rank(p,HEDGE,latest,"modified")[:10],"variants":variants,"benchmark":{"ticker":BENCH,"metrics":metrics(bh)}}
 OUT.write_text(json.dumps(d,indent=2,allow_nan=False),encoding="utf-8");print("World Top 4",latest.date(),len(p.columns),"tickers")
if __name__=="__main__":
 warnings.filterwarnings("ignore");main()
