"""Sensitivity test for the uncertain fourth World Top 4 geographic sleeve.
All Africa/Middle East classifications below are research hypotheses, not official LI confirmation.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
import world_top4_6040 as engine

OUT = Path("world_top4_region_sensitivity.json")

def main():
    base = engine.REGIONS
    scenarios = {
        "baseline_residual": base,
        "mena_eastern_mediterranean": {
            "Developed": base["Developed"], "Asia": base["Asia"],
            "Latin America": base["Latin America"],
            "Eastern Mediterranean": ["EGPT", "GREK", "TUR"]
        },
        "gulf_only_active": {
            "Developed": base["Developed"], "Asia": base["Asia"],
            "Latin America": base["Latin America"],
            "Gulf only": ["KSA", "UAE", "QAT"]
        },
        "mena_broad_active": {
            "Developed": base["Developed"], "Asia": base["Asia"],
            "Latin America": base["Latin America"],
            "Africa + Eastern Mediterranean + Gulf": ["AFK", "EZA", "EGPT", "GREK", "TUR", "KSA", "UAE", "QAT"]
        },
        "current_exploratory_bucket": {
            "Developed": base["Developed"], "Asia": base["Asia"],
            "Latin America": base["Latin America"],
            "Africa & Middle East (exploratory model)": ["AFK", "EZA", "TUR", "GREK", "KSA", "UAE", "QAT"]
        },
        "africa_only": {
            "Developed": base["Developed"], "Asia": base["Asia"],
            "Latin America": base["Latin America"],
            "Africa only": ["AFK", "EZA"]
        },
        "legacy_middle_east_instruments": {
            "Developed": base["Developed"], "Asia": base["Asia"],
            "Latin America": base["Latin America"],
            "Legacy ME instruments (closed / unverified history)": ["GAF", "GULF", "MES"]
        }
    }
    tickers = sorted(set(
        [t for regions in scenarios.values() for members in regions.values() for t in members]
        + engine.TREASURY + engine.GOLD_USD + [engine.BENCH, "^IRX"]
    ))
    prices = engine.download(tickers)
    latest = prices.dropna(how="all").index[-1]
    monthly = prices.resample("ME").last()
    if latest.to_period("M") == __import__("pandas").Timestamp.now(tz="UTC").to_period("M"):
        monthly = monthly.iloc[:-1]
    bench = monthly[engine.BENCH].dropna()
    rf = monthly["^IRX"].dropna() / 100.0 / 12.0
    rf_by_date = {d.strftime("%Y-%m-%d"): float(rf.loc[d]) for d in rf.index}
    bench_dates = set(d.strftime("%Y-%m-%d") for d in bench.index[1:])
    results = {}
    for name, regions in scenarios.items():
        results[name] = {"regions": regions, "fourth_sleeve_size": len(list(regions.values())[-1]), "variants": {}}
        for variant in ("momentum", "modified", "composite"):
            rows = engine.run_backtest(prices, variant, regions)
            rows = [r for r in rows if r["holding_to"] in bench_dates]
            m = engine.metrics(rows)
            engine.add_risk_free_metrics(m, rows, rf_by_date)
            results[name]["variants"][variant] = {
                "metrics": m, "months": len(rows),
                "start": rows[0]["holding_to"] if rows else None,
                "end": rows[-1]["holding_to"] if rows else None
            }
    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "latest_price_date": latest.strftime("%Y-%m-%d"),
        "data_source": "Yahoo Finance adjusted daily prices; same engine, hedge and ranking settings across scenarios",
        "warning": "Exploratory sensitivity only. Africa/Middle East sleeve assignments are not confirmed by Logical Invest. Strict price coverage: all four equity picks and both hedge picks must have valid start/end prices; months with missing selected prices are excluded. Legacy closed funds may yield no usable history. Results exclude fees, taxes, slippage and FX.",
        "scenarios": results
    }
    OUT.write_text(json.dumps(output, indent=2, allow_nan=False), encoding="utf-8")
    print("Fourth-region sensitivity", latest.date(), "scenarios", len(results))

if __name__ == "__main__":
    main()
