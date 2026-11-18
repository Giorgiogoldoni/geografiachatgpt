# 🦅 GEOGRAFIA CHATGPT

Portfolio manager autonomo per ETF UCITS quotati in Europa.
Due portafogli separati: **PAESI** + **NEW AREA**.

## 📐 Regole operative

### ENTRATA (tutte e 7 soddisfatte)
| # | Condizione | Soglia |
|---|---|---|
| 1 | Segnale RAPTOR | LONG / EARLY / WATCH |
| 2 | Score | ≥ 40 |
| 3 | Trendycator | 🟢 VERDE |
| 4 | ER (Efficiency Ratio) | ≥ 0.50 |
| 5 | AO + Baffetti | ≥ 3 barre consecutive |
| 6 | Parabolic SAR | Bullish (prezzo > SAR) |
| 7 | Supertrend | Bullish |

- **Conferma**: a chiusura di sessione
- **Giorno preferito**: Mercoledì
- **Ranking**: per ER decrescente
- **Pesi**: proporzionali allo Score

### USCITA (basta 1)
| Condizione | Tipo |
|---|---|
| K% negativo (prezzo sotto KAMA) | Immediata |
| Trailing Stop colpito (Prezzo − 2×ATR) | Immediata |
| Score < 20 | Immediata |
| Supertrend gira rosso | Pre-allerta |
| Giorno 7 e gain < +5% | Pre-allerta |
| Giorno 10 | Time stop obbligatorio |

### Obiettivo per operazione
- **Target**: +5% dal prezzo di ingresso
- **Stop Loss**: MAX(Trailing Stop, Entry − 2×ATR)

### Cuscinetto
- **XEON** (Xtrackers EUR Overnight Rate) quando nessun ETF qualifica
- Allocazione XEON: 100% se 0 posizioni

## 🔄 Aggiornamento automatico

GitHub Actions esegue `raptor_geografia.py` ogni ora dalle 09:00 alle 19:00 CET (Lun–Ven).

## 🚀 Setup

```bash
git clone https://github.com/TUO_USERNAME/geografiachatgpt
cd geografiachatgpt
pip install -r requirements.txt
python raptor_geografia.py
python -m http.server 8080  # apri http://localhost:8080
```

## 📁 File

| File | Descrizione |
|---|---|
| `raptor_geografia.py` | Script principale — calcola indicatori, aggiorna portafogli, genera JSON |
| `index.html` | Dashboard visuale |
| `geografia.json` | Dati generati dallo script (auto-aggiornato) |
| `portfolio_state.json` | Stato portafogli persistente |
| `.github/workflows/update.yml` | GitHub Actions — aggiornamento orario |

## 📊 Indicatori calcolati

| Indicatore | Parametri |
|---|---|
| KAMA | n=10, fast=2, slow=30 |
| ER (Efficiency Ratio) | n=10 |
| AO (Awesome Oscillator) | SMA5 − SMA34 midpoint |
| Baffetti | barre AO consecutive crescenti |
| RSI | n=14 |
| Trendycator | EMA21 vs EMA55 |
| ATR | n=14 |
| Trailing Stop | Prezzo − 2×ATR |
| K% | (Prezzo/KAMA−1)×100 |
| MM Align | Prezzo > MM20 > MM50 > MM200 |
| Parabolic SAR | AF=0.02, max=0.20 |
| Supertrend | period=10, mult=3.0 |

---
🦅 GEOGRAFIA CHATGPT — *Fly High, Trade Smart*


## 🌍 World Top 4 — nuova area di ricerca

Il calcolo viene eseguito da GitHub Actions dopo gli aggiornamenti al branch main e ogni giorno feriale alle 22:30 UTC.

È stata aggiunta una dashboard autonoma ispirata alla strategia pubblica World Top 4 di Logical Invest:

- [Apri dashboard World Top 4](./world-top4.html)
- Motore: world_top4.py
- **Nuovo motore sperimentale solver Modified Sharpe**: `world_top4_solver_experimental.py` → `world_top4_solver_experimental.json` (confronto equal-weight, solver long-only e vincolo 10%-40%).
- Dati/backtest: world_top4.json (generato dal workflow giornaliero)
- Report audit USA preliminare: [WORLD_TOP4_AUDIT_REPORT.md](./WORLD_TOP4_AUDIT_REPORT.md)
- Ricerca sul motore storico Logical Invest: [LOGICAL_INVEST_ENGINE_RESEARCH.md](./LOGICAL_INVEST_ENGINE_RESEARCH.md)
- **Nuovo audit di fedeltà alla metodologia ufficiale**: [WORLD_TOP4_FIDELITY_AUDIT_2026-11-18.md](./WORLD_TOP4_FIDELITY_AUDIT_2026-11-18.md)
- Panieri ufficiali delle sottostrategie verificati: [logical_invest_substrategy_universe.csv](./logical_invest_substrategy_universe.csv)
- Metodo, limiti e ritardo holdings: WORLD_TOP4_METHOD.md
- Universo USA pubblico Logical Invest (49 ticker) e stato di classificazione: [logical_invest_universe.csv](./logical_invest_universe.csv)
- Registro per holdings Logical Invest pubblicati in ritardo: logical_invest_holdings.csv

Il modulo confronta tre varianti di momentum e ACWI. Un modulo sperimentale separato ricostruisce la formula storica documentata di Modified Sharpe (media dei rendimenti giornalieri / volatilità giornaliera²) e testa un solver trasparente a griglia 5%, senza modificare le baseline. L'audit ha registrato l'universo pubblico USA di Logical Invest e ha aggiunto metriche estese di rischio, drawdown, turnover e rendimenti annuali. La ricerca documentale ha identificato la metodologia storica: 68 sedute, ribilanciamento mensile, modified Sharpe con volatility attenuator 2 e ottimizzazione con solver. La formula corrente completa non è pubblica. Sono stati registrati i panieri Developed, Asia e South America; la quarta sleeve e i pesi correnti HEDGE restano da verificare. Il backtest corrente è ancora un modello indipendente preliminare, non una replica della formula proprietaria. Sharpe/Sortino interni sono calcolati con tasso risk-free/target zero e non sono direttamente confrontabili con i valori Logical Invest. Gli strumenti di ricerca sono ticker USA, non ancora la lista operativa UCITS.

- Snapshot ufficiale dei 49 ETF WTOP4 (16 ottobre 2026): [logical_invest_wtop4_universe_2026-10-16.csv](./logical_invest_wtop4_universe_2026-10-16.csv)
- Ricostruzione della quarta sleeve e discrepanze tra universo master e pagine regionali: [WORLD_TOP4_FOURTH_SLEEVE_RESEARCH_2026-11-18.md](./WORLD_TOP4_FOURTH_SLEEVE_RESEARCH_2026-11-18.md)
