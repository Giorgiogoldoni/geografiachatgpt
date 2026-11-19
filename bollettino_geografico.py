#!/usr/bin/env python3
"""Create an append-only daily investment bulletin from geografia-motore.json."""
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "geografia-motore.json"
ARCHIVE = ROOT / "data" / "bollettino_geografico.json"
ARCHIVE.parent.mkdir(parents=True, exist_ok=True)

if not SOURCE.exists():
    raise SystemExit("geografia-motore.json non trovato")

data = json.loads(SOURCE.read_text(encoding="utf-8"))
now = datetime.now(timezone.utc)
edition_date = now.astimezone().date().isoformat()
price_date = data.get("latest_price_date", "non disponibile")
rankings = data.get("rankings", {})
selected = data.get("selected", data.get("selections", {}))

def pct(value):
    return None if value is None else round(float(value) * 100, 2)

def instrument(row):
    return {
        "ticker": row.get("ticker", ""),
        "name": row.get("name", row.get("fund", "")),
        "isin": row.get("isin", ""),
        "geography": row.get("geography", row.get("country", "")),
        "module": row.get("module", row.get("module_id", "")),
        "momentum_1m": pct(row.get("momentum_1m")),
        "momentum_3m": pct(row.get("momentum_3m")),
        "momentum_6m": pct(row.get("momentum_6m")),
        "momentum_12m": pct(row.get("momentum_12m")),
        "composite_momentum": pct(row.get("composite_momentum")),
        "return_68d": pct(row.get("return_68d")),
        "volatility_annual": pct(row.get("volatility_annual")),
        "modified_sharpe_candidate": row.get("modified_sharpe_candidate"),
        "sma200": row.get("sma200"),
        "price": row.get("price"),
        "distance_sma200": pct((row.get("price") / row.get("sma200") - 1) if row.get("price") and row.get("sma200") else None),
        "above_sma200": bool(row.get("above_sma200", False)),
        "absolute_momentum_positive": bool(row.get("absolute_momentum_positive", False)),
        "eligible_trend": bool(row.get("eligible_trend", False)),
        "observations": row.get("observations"),
        "price_date": row.get("price_date", price_date),
    }

rows = []
for group, items in rankings.items():
    if not isinstance(items, list):
        continue
    for row in items:
        if row.get("status") == "CALCOLATO":
            item = instrument(row)
            item["group"] = group
            item["rank_in_group"] = len(rows) + 1
            rows.append(item)

# The signal is a watchlist classification, not an order. Keep the bar high.
buy = [r for r in rows if r["eligible_trend"] and (r["momentum_3m"] or 0) > 0]
buy.sort(key=lambda r: (r["modified_sharpe_candidate"] if r["modified_sharpe_candidate"] is not None else -1e9), reverse=True)
avoid = [r for r in rows if not r["above_sma200"] and (r["momentum_12m"] or 0) < 0]
wait = [r for r in rows if r not in buy and r not in avoid and not r["eligible_trend"]]
hold = [r for r in rows if r["eligible_trend"] and (r["momentum_3m"] or 0) <= 0]
buy = [explain(r, "CANDIDATO ACQUISTO") for r in buy]
hold = [explain(r, "MANTENERE / NON INSEGUIRE") for r in hold]
wait = [explain(r, "ATTENDERE CONFERMA") for r in wait]
avoid = [explain(r, "EVITARE PER ORA") for r in avoid]

def explain(row, label):
    reasons = []
    if row["above_sma200"]:
        reasons.append("prezzo sopra SMA200")
    else:
        reasons.append("prezzo sotto SMA200")
    if row["absolute_momentum_positive"]:
        reasons.append("momentum 12 mesi positivo")
    else:
        reasons.append("momentum 12 mesi negativo")
    for period in ("1m", "3m", "6m", "12m"):
        value = row.get("momentum_" + period)
        if value is not None:
            reasons.append(f"{period}: {value:+.2f}%")
    if row.get("composite_momentum") is not None:
        reasons.append(f"momentum composito 40/30/30: {row['composite_momentum']:+.2f}%")
    if row.get("distance_sma200") is not None:
        reasons.append(f"distanza SMA200: {row['distance_sma200']:+.2f}%")
    if row.get("volatility_annual") is not None:
        reasons.append(f"volatilità annualizzata: {row['volatility_annual']:.2f}%")
    if row.get("modified_sharpe_candidate") is not None:
        reasons.append(f"indice rendimento/varianza 68 sedute: {row['modified_sharpe_candidate']:.4f}")
    row["decision"] = label
    row["reason"] = "; ".join(reasons)
    return row

def compact(items, limit=8):
    return items[:limit]

def factor_summary():
    result = []
    for group, items in data.get("factor_rankings", {}).items():
        if not isinstance(items, list):
            continue
        for row in items:
            if row.get("status") != "CALCOLATO":
                continue
            item = instrument(row)
            item["group"] = group
            item["category"] = row.get("category", group.split("|")[0])
            item["benchmark_factor"] = row.get("benchmark_factor", "")
            if item["eligible_trend"] and (item["momentum_3m"] or 0) > 0:
                label = "CANDIDATO FATTORE"
            elif not item["above_sma200"] and (item["momentum_12m"] or 0) < 0:
                label = "EVITARE PER ORA"
            elif item["eligible_trend"]:
                label = "MANTENERE / ATTENDERE"
            else:
                label = "ATTENDERE CONFERMA"
            result.append(explain(item, label))
    result.sort(key=lambda x: (x.get("category", ""), -(x.get("modified_sharpe_candidate") or -1e9)))
    return result

def area_summary():
    result = []
    for key, value in selected.items():
        if isinstance(value, dict) and value:
            result.append({
                "area": key,
                "ticker": value.get("ticker", ""),
                "name": value.get("name", value.get("fund", "")),
                "momentum_3m": pct(value.get("momentum_3m")),
                "momentum_6m": pct(value.get("momentum_6m")),
                "momentum_12m": pct(value.get("momentum_12m")),
                "composite_momentum": pct(value.get("composite_momentum")),
                "above_sma200": bool(value.get("above_sma200", False)),
                "absolute_momentum_positive": bool(value.get("absolute_momentum_positive", False)),
                "eligible_trend": bool(value.get("eligible_trend", False)),
                "distance_sma200": pct((value.get("price") / value.get("sma200") - 1) if value.get("price") and value.get("sma200") else None),
                "reason": ("Sopra SMA200 e momentum 12m positivo" if value.get("eligible_trend") else
                           "Filtro trend non superato: " + ("sotto SMA200; " if not value.get("above_sma200") else "") +
                           ("momentum 12m negativo" if not value.get("absolute_momentum_positive") else "momentum 12m positivo ma trend incompleto")),
            })
        elif isinstance(value, dict):
            result.append({"area": key, "ticker": "", "name": "Nessuna selezione"})
    return result

entry = {
    "date": edition_date,
    "generated_at": now.isoformat(),
    "price_date": price_date,
    "data_stale": price_date != edition_date,
    "headline": "Segnali quantitativi, non ordini automatici",
    "market_summary": (
        "Dati aggiornati al " + price_date + ". " +
        str(len(rows)) + " strumenti con serie calcolata. " +
        str(len(buy)) + " candidati con trend positivo e momentum a 3 mesi positivo; " +
        str(len(avoid)) + " strumenti con trend e momentum annuale negativi."
    ),
    "areas": area_summary(),
    "factors": factor_summary(),
    "buy": compact(buy, 5),
    "hold": compact(hold, 8),
    "wait": compact(wait, 8),
    "avoid": compact(avoid, 8),
    "indicator_legend": {
        "momentum": "Rendimento totale proxy su 21/63/126/252 sedute, calcolato su prezzi Yahoo auto-adjusted.",
        "composite_momentum": "40% momentum 3 mesi + 30% momentum 6 mesi + 30% momentum 12 mesi.",
        "trend_filter": "Filtro superato soltanto se prezzo > media mobile semplice 200 sedute e momentum 12 mesi > 0.",
        "distance_sma200": "Scostamento percentuale del prezzo dalla SMA200.",
        "volatility_annual": "Deviazione standard dei rendimenti giornalieri su 68 sedute, annualizzata per radice di 252.",
        "modified_sharpe_candidate": "Media rendimenti giornalieri / varianza giornaliera sulle ultime 68 sedute; indicatore sperimentale, NON Sharpe ratio standard e non va letto isolatamente."
    },
    "decision_rules": {
        "buy": "Candidato soltanto se prezzo sopra SMA200, momentum 12 mesi positivo e momentum 3 mesi positivo.",
        "factor_rule": "I fattori sono classificati separatamente dai Paesi e dalle aree; stessa lettura tecnica, nessuna fusione dei ranking geografici."
        "hold": "Filtro trend superato ma momentum 3 mesi nullo o negativo: non inseguire il prezzo.",
        "wait": "Filtro trend incompleto, ma non coesistono prezzo sotto SMA200 e momentum 12 mesi negativo.",
        "avoid": "Prezzo sotto SMA200 e momentum 12 mesi negativo."
    },
    "method_note": "Ogni etichetta è accompagnata dagli indicatori che l'hanno determinata. COMPRARE significa candidato quantitativo, non ordine né raccomandazione personalizzata. Prima di operare verificare ISIN, listing Fineco, spread, liquidità, sovrapposizioni e pesi. Modello indipendente, non replica la formula proprietaria Logical Invest."
}

archive = json.loads(ARCHIVE.read_text(encoding="utf-8")) if ARCHIVE.exists() else {"title": "Il Bollettino Geografico", "editions": []}
editions = archive.setdefault("editions", [])
# Idempotent: a rerun replaces today's edition rather than duplicating it.
editions = [e for e in editions if e.get("date") != edition_date]
editions.append(entry)
editions.sort(key=lambda e: e.get("date", ""))
archive["editions"] = editions
ARCHIVE.write_text(json.dumps(archive, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Edizione {edition_date} salvata. Prezzi al {price_date}; archivio: {len(editions)} pagine.")
