"""European UCITS 60/40 monthly research backtest.

Builds a continuous monthly series from the first date at which every sleeve has
at least one ETF with a full 12-month signal history. If no ETF in a sleeve has
positive momentum, it holds the highest risk-adjusted candidate in that sleeve
(rather than dropping the month). No prices or returns are fabricated.
"""
import json, warnings
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import yfinance as yf
from world_top4 import stats, metrics

OUT=Path("euro_top4_6040.json")
START="2010-01-01"
REGIONS={
 "Developed": ["CSCA.MI","IAEX.AS","IBCJ.DE"],
 "Asia-Pacific": ["SJPA.MI","FLXK.MI","FLXI.MI"],
 "Latin America": ["D5BI.DE","FLXB.MI","LTAM.MI","ALAT.MI"],
 "Africa-Middle East": ["SRSA.MI","IQQ5.DE","QDVM.DE"],
}
DEFENSIVE={"Cash-like EUR":("XEON.DE",0.24),"Gold ETC":("SGLD.MI",0.16)}
BENCH="VWCE.DE"

def download(symbols):
 raw=yf.download(sorted(set(symbols)),start=START,auto_adjust=True,progress=False,threads=True,group_by="column")
 if raw is None or raw.empty: raise RuntimeError("Nessun prezzo restituito da Yahoo Finance")
 close=raw["Close"] if isinstance(raw.columns,pd.MultiIndex) else raw[["Close"]].rename(columns={"Close":symbols[0]})
 if isinstance(close,pd.Series): close=close.to_frame(name=symbols[0])
 close.index=pd.to_datetime(close.index).tz_localize(None)
 return close.apply(pd.to_numeric,errors="coerce").sort_index().dropna(how="all")

def candidate_list(prices, assets, signal_date, start_month, end_month):
 ranked=[]
 for ticker in assets:
  if ticker not in prices: continue
  z=stats(prices[ticker],signal_date)
  if not z or z.get("momentum_12m") is None: continue
  a=start_month.get(ticker); b=end_month.get(ticker)
  if pd.isna(a) or pd.isna(b) or a<=0: continue
  vol=z.get("vol_annual")
  if not vol or vol<=0: continue
  ranked.append({"ticker":ticker,**z,"score":z["return_68d"]/(vol**2)})
 positive=[x for x in ranked if x["return_68d"]>0 and x["momentum_12m"]>0]
 pool=positive if positive else ranked
 return sorted(pool,key=lambda x:x["score"],reverse=True), bool(positive)

def contiguous(rows):
 dates=[pd.Period(x["holding_to"],freq="M") for x in rows]
 return all((dates[i]-dates[i-1]).n==1 for i in range(1,len(dates)))

def main():
 symbols=sum(REGIONS.values(),[])+[x[0] for x in DEFENSIVE.values()]+[BENCH]
 prices=download(symbols); latest=prices.dropna(how="all").index[-1]
 monthly=prices.resample("ME").last().dropna(how="all")
 # Never treat the current, unfinished month as a completed holding period.
 if latest.to_period("M")==pd.Timestamp.now(tz="UTC").to_period("M"): monthly=monthly.iloc[:-1]
 dates=list(monthly.index); rows=[]; skipped=[]
 for i in range(1,len(dates)):
  signal_date=dates[i-1]; end_date=dates[i]
  start_prices=monthly.loc[signal_date]; end_prices=monthly.loc[end_date]
  picks=[]; weights={}; fallback_areas=[]
  for area,assets in REGIONS.items():
   ranked,has_positive=candidate_list(prices,assets,signal_date,start_prices,end_prices)
   if not ranked:
    picks=[]; break
   chosen=ranked[0]
   if not has_positive: fallback_areas.append(area)
   picks.append({"area":area,**chosen,"positive_momentum_pool":has_positive})
   weights[chosen["ticker"]]=weights.get(chosen["ticker"],0)+0.15
  if len(picks)!=len(REGIONS):
   skipped.append({"signal_date":signal_date.strftime("%Y-%m-%d"),"reason":"At least one regional sleeve has no ETF with complete 12-month history and valid month prices"})
   continue
  defensive_ok=True
  for _,(ticker,w) in DEFENSIVE.items():
   a=start_prices.get(ticker); b=end_prices.get(ticker)
   if pd.isna(a) or pd.isna(b) or a<=0:
    defensive_ok=False; break
   weights[ticker]=w
  if not defensive_ok:
   skipped.append({"signal_date":signal_date.strftime("%Y-%m-%d"),"reason":"Missing defensive sleeve price"})
   continue
  ret=sum(w*(float(end_prices[t]/start_prices[t])-1) for t,w in weights.items())
  ba=start_prices.get(BENCH); bb=end_prices.get(BENCH)
  bench_ret=float(bb/ba-1) if pd.notna(ba) and pd.notna(bb) and ba>0 else None
  rows.append({"signal_date":signal_date.strftime("%Y-%m-%d"),"holding_to":end_date.strftime("%Y-%m-%d"),
   "return":float(ret),"benchmark_return":bench_ret,"picks":picks,
   "defensive":[{"ticker":t,"weight":w} for t,w in weights.items() if t not in [x["ticker"] for x in picks]],
   "weights":weights,"fallback_areas":fallback_areas})
 # Metrics are meaningful only on a contiguous monthly return stream.
 is_contiguous=contiguous(rows)
 if rows and not is_contiguous:
  raise RuntimeError("Il controllo qualità ha rilevato mesi mancanti nella serie EURO; metriche non pubblicate")
 benchmark_rows=[{"holding_to":x["holding_to"],"return":x["benchmark_return"]} for x in rows if x["benchmark_return"] is not None]
 benchmark_contiguous=contiguous(benchmark_rows)
 result={"generated_at":datetime.now(timezone.utc).isoformat(),"latest_price_date":latest.strftime("%Y-%m-%d"),
  "data_source":"Yahoo Finance adjusted daily prices; European listing symbols; not official issuer NAV data",
  "methodology":{"equity_weight":0.60,"defensive_weight":0.40,"regional_equity_weights":"15% per each of four sleeves",
   "defensive_split":"24% XEON.DE EUR overnight-rate proxy + 16% SGLD.MI gold ETC",
   "ranking":"68-session return / annualized volatility squared; prefer positive 68-session and 12-month momentum; if a sleeve has no positive candidate, use its highest-scoring candidate with full 12-month history; monthly rebalance",
   "signal_rule":"Signal at prior month-end close; hold selected assets over the following calendar month",
   "warning":"Independent European UCITS approximation, not official Logical Invest. Universe limited to mapped candidates with uneven coverage. XEON is cash-like; SGLD is an ETC, not a UCITS ETF. No fees, taxes, slippage, FX hedging or currency conversion. Benchmark VWCE.DE is a proxy."},
  "regions":REGIONS,"defensive":DEFENSIVE,"metrics":metrics(rows),
  "benchmark_metrics":metrics(benchmark_rows),"benchmark":BENCH,
  "selection_months":len(rows),"history":rows[-120:],
  "selection_frequency":{},"quality":{"continuous_months":is_contiguous,"benchmark_continuous_months":benchmark_contiguous,
   "first_month":rows[0]["holding_to"] if rows else None,"last_month":rows[-1]["holding_to"] if rows else None,
   "skipped_months":skipped,"fallback_months":sum(bool(x["fallback_areas"]) for x in rows),
   "fallback_area_frequency":{area:sum(area in x["fallback_areas"] for x in rows) for area in REGIONS}},
  "selection_frequency":{}}
 counts={}
 for row in rows:
  for pick in row["picks"]: counts[pick["ticker"]]=counts.get(pick["ticker"],0)+1
 result["selection_frequency"]=dict(sorted(counts.items(),key=lambda x:(-x[1],x[0])))
 OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False),encoding="utf-8")
 print("EURO 60/40",latest.date(),"months",len(rows),"continuous",is_contiguous,
       "first",result["quality"]["first_month"],"last",result["quality"]["last_month"],
       "skipped",len(skipped),"fallback",result["quality"]["fallback_months"])
if __name__=="__main__":
 warnings.filterwarnings("ignore"); main()
