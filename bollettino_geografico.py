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
        "modified_sharpe": row.get("modified_sharpe_candidate", row.get("modified_sharpe")),
        "above_sma200": bool(row.get("above_sma200", row.get("above_SMA200", False))),
        "eligible_trend": bool(row.get("eligible_trend", False)),
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
            rows.append(item)

# The signal is a watchlist classification, not an order. Keep the bar high.
buy = [r for r in rows if r["eligible_trend"] and (r["momentum_3m"] or 0) > 0]
buy.sort(key=lambda r: (r["modified_sharpe"] if r["modified_sharpe"] is not None else -1e9), reverse=True)
avoid = [r for r in rows if not r["above_sma200"] and (r["momentum_12m"] or 0) < 0]
wait = [r for r in rows if r not in buy and r not in avoid and not r["eligible_trend"]]
hold = [r for r in rows if r["eligible_trend"] and (r["momentum_3m"] or 0) <= 0]

def compact(items, limit=8):
    return items[:limit]

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
                "eligible_trend": bool(value.get("eligible_trend", value.get("above_sma200", False))),
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
    "buy": compact(buy, 5),
    "hold": compact(hold, 8),
    "wait": compact(wait, 8),
    "avoid": compact(avoid, 8),
    "method_note": "COMPRARE indica una candidatura del modello, non un ordine né una raccomandazione personalizzata. Prima di operare verificare ISIN, listing Fineco, spread, liquidità, sovrapposizioni e pesi del portafoglio. Il modello è indipendente e non replica la formula proprietaria Logical Invest.",
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
