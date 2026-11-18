"""Sensitivity test for the uncertain fourth World Top 4 geographic sleeve.
All Africa/Middle East classifications below are research hypotheses, not official LI confirmation.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd\nimport world_top4_6040 as engine

OUT = Path("world_top4_region_sensitivity.json")


def candidate_selection_audit(prices, rows, variant, region_name, candidate):
    """Measure candidate rank, selection frequency and next-month opportunity cost."""
    monthly = prices.resample("ME").last().dropna(how="all")
    rank_counts = {}
    selected_count = 0
    candidate_forward = []
    chosen_forward = []
    missed_excess = []
    observations = 0
    rank_sum = 0.0
    rank_observations = 0
    for row in rows:
        signal = __import__("pandas").Timestamp(row["signal_date"])
        start = __import__("pandas").Timestamp(row["holding_from"])
        end = __import__("pandas").Timestamp(row["holding_to"])
        ranked = engine.rank(prices, region_assets, signal, variant) if False else None
        # region_assets is supplied by the caller through the audit closure below.
        ranked = engine.rank(prices, candidate_universe, signal, variant)
        positions = {item["ticker"]: i + 1 for i, item in enumerate(ranked)}
        rank = positions.get(candidate)
        if rank is not None:
            rank_counts[str(rank)] = rank_counts.get(str(rank), 0) + 1
            rank_sum += rank
            rank_observations += 1
        chosen = next((p["ticker"] for p in row.get("picks", []) if p.get("region") == region_name), None)
        if chosen is None:
            continue
        if candidate not in monthly.columns or chosen not in monthly.columns:
            continue
        a, b = monthly.loc[start], monthly.loc[end]
        if pd.isna(a.get(candidate)) or pd.isna(b.get(candidate)) or pd.isna(a.get(chosen)) or pd.isna(b.get(chosen)):
            continue
        if a[candidate] <= 0 or a[chosen] <= 0:
            continue
        cand_ret = float(b[candidate] / a[candidate] - 1)
        chosen_ret = float(b[chosen] / a[chosen] - 1)
        candidate_forward.append(cand_ret)
        chosen_forward.append(chosen_ret)
        observations += 1
        if chosen == candidate:
            selected_count += 1
        else:
            missed_excess.append(cand_ret - chosen_ret)
    return {
        "candidate": candidate,
        "region": region_name,
        "eligible_observations": observations,
        "rank_observations": rank_observations,
        "selection_months": selected_count,
        "selection_frequency_pct": 100.0 * selected_count / observations if observations else None,
        "rank_counts": rank_counts,
        "average_rank_when_ranked": rank_sum / rank_observations if rank_observations else None,
        "candidate_average_next_month_return": sum(candidate_forward) / len(candidate_forward) if candidate_forward else None,
        "selected_asset_average_next_month_return": sum(chosen_forward) / len(chosen_forward) if chosen_forward else None,
        "average_missed_excess_return": sum(missed_excess) / len(missed_excess) if missed_excess else None,
        "missed_months": len(missed_excess),
        "interpretation": "Average missed excess is candidate ETF next-month return minus the ETF actually selected in the same sleeve, only in months when the candidate was not selected. It is descriptive, not a tradable counterfactual."
    }


def build_candidate_audits(prices, rows, variant, regions):
    audits = {}
    # Korea is tested inside the Asia sleeve, against the full eligible Asia universe.
    global candidate_universe
    candidate_universe = regions.get("Asia", [])
    if "EWY" in candidate_universe:
        audits["EWY"] = candidate_selection_audit(prices, rows, variant, "Asia", "EWY")
    # Greece is tested wherever it is eligible in the fourth sleeve.
    fourth_name, fourth_assets = list(regions.items())[-1]
    if "GREK" in fourth_assets:
        candidate_universe = fourth_assets
        audits["GREK"] = candidate_selection_audit(prices, rows, variant, fourth_name, "GREK")
    return audits


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
    rows_by_scenario = {}
    active_scenarios = [n for n in scenarios if n != "legacy_middle_east_instruments"]
    for name, regions in scenarios.items():
        results[name] = {"regions": regions, "fourth_sleeve_size": len(list(regions.values())[-1]), "variants": {}}
        rows_by_scenario[name] = {}
        for variant in ("momentum", "modified", "composite"):
            rows = engine.run_backtest(prices, variant, regions)
            rows = [r for r in rows if r["holding_to"] in bench_dates]
            rows_by_scenario[name][variant] = rows
            results[name]["variants"][variant]["candidate_audit"] = build_candidate_audits(prices, rows, variant, regions)
            m = engine.metrics(rows)
            engine.add_risk_free_metrics(m, rows, rf_by_date)
            results[name]["variants"][variant] = {
                "metrics": m, "months": len(rows),
                "start": rows[0]["holding_to"] if rows else None,
                "end": rows[-1]["holding_to"] if rows else None
            }

    # Fair comparison: recalculate each active hypothesis on the exact same
    # holding months. The legacy closed-fund group has no usable history and
    # is intentionally excluded from the common-date intersection.
    common_periods = {}
    for variant in ("momentum", "modified", "composite"):
        date_sets = [
            {r["holding_to"] for r in rows_by_scenario[name][variant]}
            for name in active_scenarios
        ]
        common_dates = set.intersection(*date_sets) if date_sets else set()
        common_dates = sorted(common_dates)
        common_periods[variant] = {
            "start": common_dates[0] if common_dates else None,
            "end": common_dates[-1] if common_dates else None,
            "months": len(common_dates)
        }
        for name in active_scenarios:
            common_rows = [
                r for r in rows_by_scenario[name][variant]
                if r["holding_to"] in common_dates
            ]
            m = engine.metrics(common_rows)
            engine.add_risk_free_metrics(m, common_rows, rf_by_date)
            results[name]["variants"][variant]["common_period"] = {
                "metrics": m,
                "months": len(common_rows),
                "start": common_rows[0]["holding_to"] if common_rows else None,
                "end": common_rows[-1]["holding_to"] if common_rows else None
            }
    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "latest_price_date": latest.strftime("%Y-%m-%d"),
        "data_source": "Yahoo Finance adjusted daily prices; same engine, hedge and ranking settings across scenarios",
        "candidate_audit_method": "EWY (Korea) is ranked against the Asia ETF universe; GREK (Greece) against each scenario’s fourth-sleeve universe. Reports selection frequency, rank distribution and next-month return difference versus the actually selected ETF. No forced inclusion or portfolio weight change.",
        "warning": "Exploratory sensitivity only. Africa/Middle East sleeve assignments are not confirmed by Logical Invest. Strict price coverage: all four equity picks and both hedge picks must have valid start/end prices; months with missing selected prices are excluded. Legacy closed funds may yield no usable history. Results exclude fees, taxes, slippage and FX.",
        "scenarios": results
    }
    OUT.write_text(json.dumps(output, indent=2, allow_nan=False), encoding="utf-8")
    print("Fourth-region sensitivity", latest.date(), "scenarios", len(results))

if __name__ == "__main__":
    main()
