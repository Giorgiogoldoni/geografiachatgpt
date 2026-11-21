# 🌍 GEOGRAFIA CHATGPT

Dashboard e motori quantitativi indipendenti per ETF UCITS quotati in Europa.

> **Mappa tecnica del repository:** [ARCHITETTURA_REPOSITORY.md](./ARCHITETTURA_REPOSITORY.md) — flussi dati, motori, dashboard, workflow e archivi.

## Stato operativo

- **Homepage:** [Geografia ChatGPT](https://giorgiogoldoni.github.io/geografiachatgpt/).
- **Motore UCITS principale:** `ucits_geography.py` → `ucits_geography.json`, eseguito da GitHub Actions.
- **Motore geografico a sei aree:** `geografia_engine.py` → `geografia-motore.json`.
- **Radar predittivo Momentum/Ridge:** [pagina dedicata](./radar-predittivo.html), alimentata da `radar_predittivo_engine.py` e `radar-predittivo.json`.
- **Bollettino:** [pagina dedicata](./bollettino.html), con archivio storico append-only.
- **RAPTOR precedente:** dashboard e aggiornamento automatico ritirati. I file storici e il vecchio sorgente sono conservati come archivio e non fanno parte del flusso operativo.

I file Python sono motori server-side: GitHub Actions li esegue e pubblica i JSON consumati dalle pagine HTML. Non vanno aperti come pagine web.

---

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
- **Nuovo audit tecnico QuantTrader e HEDGE**: [QUANTTRADER_HEDGE_AUDIT_2026-11-18.md](./QUANTTRADER_HEDGE_AUDIT_2026-11-18.md) — logiche NO/SR/DR/SRE/DRE, vincoli e architettura dei due moduli hedge.
- **Adattamento operativo agli ETF europei UCITS**: [WORLD_TOP4_UCITS_ADAPTATION.md](./WORLD_TOP4_UCITS_ADAPTATION.md) e [registro iniziale ETF per Paese](./ucits_country_universe_seed_2026-11-18.csv). Obiettivo: avvicinarsi alle scelte geografiche Logical Invest usando strumenti europei verificati.


## 🌍 Strategia geografica UCITS — dashboard e motore

La pagina principale del repository è ora la dashboard della strategia geografica europea:
- **Dashboard:** [Apri Geografia ChatGPT](https://giorgiogoldoni.github.io/geografiachatgpt/)
- **Motore:** \`ucits_geography.py\`
- **Dati giornalieri:** \`ucits_geography.json\`
- **Workflow:** \`.github/workflows/ucits-geography.yml\`
- **Universo di partenza:** \`ucits_country_universe_seed_2026-11-18.csv\`
- **Archivio RAPTOR precedente:** sorgente e dati storici sono conservati nel repository, ma la vecchia dashboard non è più pubblicata.

Il motore scarica prezzi rettificati delle quotazioni europee mappate, calcola Modified Sharpe su 68 sedute, momentum a 3/6/12 mesi e filtro prezzo sopra SMA200 + momentum 12 mesi positivo. Le quattro aree sono classificate separatamente. LTAM e ALAT sono alternative regionali e non vengono confuse con Brasile e Messico.

**Limiti della prima release:** il motore mostra lo snapshot corrente e non ancora un backtest walk-forward; i ticker non mappati, le quotazioni senza dati e gli storici insufficienti sono segnalati ed esclusi. Non è una replica del motore proprietario Logical Invest né un sistema di ordini automatici.


## Portafogli USA ed EURO — 60/40

- **Dashboard composizioni e confronto:** [Portafogli USA/EURO](./portafogli-usa-euro.html).
- **USA:** quattro sleeve azionarie geografiche al 15% ciascuna; 24% Treasury e 16% oro/strumento USD difensivo. I rendimenti sono convertiti in EUR.
- **EURO:** quattro sleeve azionarie UCITS al 15% ciascuna; 24% XEON e 16% SGLD. Se una regione non presenta momentum positivo, la relativa quota del 15% passa a XEON.
- I segnali si formano alla chiusura del mese precedente; la composizione è mantenuta per il mese successivo. Il motore aggiorna quotidianamente i dati e pubblica la composizione corrente con ticker e pesi.
- La dashboard mostra le composizioni mensili, i pesi, il confronto su mesi comuni e gli orizzonti 12/36/60/120 mesi.
- Sono adattamenti indipendenti per universi USA ed europei, non una replica certificata della metodologia proprietaria Logical Invest. SGLD è un ETC, non un ETF UCITS; costi, slippage e fiscalità non sono inclusi.

## INDEX ETF geografici

- Dashboard ricercabile: [INDEX ETF — 53 strumenti](./index-etf.html)
- Archivio CSV dell'elenco PAESI originale fornito il 18 novembre 2026: [data/geografia_index_user_53.csv](./data/geografia_index_user_53.csv)
- L'INDEX contiene 53 strumenti: i 51 ticker dell'elenco originario più Canada (CSCA.MI) e Polonia (IBCJ.DE). I Paesi Bassi erano già presenti. La verifica di ISIN, borsa, valuta, struttura ETF/ETP, liquidità e disponibilità dei prezzi è un passaggio distinto prima dell'inclusione nel motore quantitativo.


## 🧭 INDEX ETF factor

È stato aggiunto un archivio separato di ETF UCITS factor, distinto dall'universo geografico:
- [Dashboard ETF Factor](./factor-etf.html)
- [CSV Factor (21 strumenti)](./data/geografia_index_factor_21.csv)
- Categorie: Equal Weight, Momentum, Value e Quality.
- Il catalogo non alimenta automaticamente il ranking Paesi. Prima dell'uso quantitativo occorre completare la verifica dei ticker per listing, valuta negoziata, liquidità e disponibilità dello storico prezzi.


## Aggiornamento classificazione geografica — 19/11/2026

- **Grecia → Europa**: aggiunto GRC, Amundi MSCI Greece UCITS ETF Dist, ISIN FR0010405431, quotazione Euronext Milan in EUR. Il listing UCITS è verificato; il simbolo del provider prezzi `GRC.MI` resta da validare al primo aggiornamento del motore.
- **Turchia → Medio Oriente**: TUR / IQQ5 è classificato nel modulo Medio Oriente e Africa, mai in Europa.
- **ETF Expat esclusi** dall'universo operativo perché non acquistabili dall'utente.
- I fondi globali restano nel modulo GLOBAL e non vengono duplicati nelle aree regionali.

## 🗺️ Architettura geografica a sei moduli

- [Moduli geografici](./geografia-aree.html) e tassonomia strutturata in `geografia-moduli.json`.
- **America del Nord**: Stati Uniti e Canada; indici USA/Canada e fattori.
- **Centro e Sud America**: singoli Paesi e panieri regionali LTAM/ALAT, separati.
- **Asia**: Paesi asiatici e panieri regionali.
- **Medio Oriente e Africa**: Paesi del Golfo, Medio Oriente e Africa.
- **Europa**: Paesi, indici europei e fattori.
- **Global**: World, ACWI, All-World, Emerging Markets e fattori globali, sempre separati dai moduli regionali.

La tassonomia è la prima fase strutturale: elenchi e ticker di esempio non equivalgono a copertura quantitativa già attiva. Ogni strumento dovrà essere verificato per ISIN, listing UCITS, ticker di borsa, liquidità e serie storica prima di entrare nei ranking. Il catalogo factor resta distinto dall'universo Paesi.


## Motore geografico a sei aree

La nuova dashboard `geografia-motore.html` usa il catalogo INDEX dell'utente come universo iniziale e aggiorna i ranking tramite `geografia_engine.py`.

- Aree: America del Nord, Centro/Sud America, Asia e Pacifico, Medio Oriente/Africa, Europa e Global.
- Sotto-ranking separati: Paesi, ETF regionali, indici/strategie nazionali e Global.
- Momentum: 1, 3, 6 e 12 mesi; score principale candidato Modified Sharpe su 68 sedute.
- Filtro trend: prezzo rettificato sopra SMA200 e momentum a 12 mesi positivo.
- Backtest esplorativo: segnale mensile e detenzione nel mese successivo, un vincitore per area/categoria.
- ETF factor: archivio separato; non entrano nelle classifiche geografiche.
- ETP espliciti: separati dal ranking UCITS principale.
- Workflow automatico nei giorni di mercato, con avvio manuale disponibile da GitHub Actions.

Il motore è una ricerca quantitativa indipendente. La formula Modified Sharpe con attenuatore 2 è una ricostruzione storica plausibile, non una formula live proprietaria verificata di Logical Invest. I prezzi Yahoo rettificati sono una proxy e richiedono controlli su listing, ISIN, valuta, liquidità e corporate actions. Il backtest non include costi, slippage o fiscalità e non genera ordini.


## 📘 Il Bollettino Geografico — diario quotidiano

- **Pagina web:** [Apri il Bollettino](./bollettino.html)
- **Generatore:** `bollettino_geografico.py`
- **Archivio append-only:** `data/bollettino_geografico.json`
- Il workflow del motore crea una nuova edizione ogni giorno, anche nei giorni senza nuove quotazioni; in quel caso la pagina dichiara chiaramente la data dell'ultimo prezzo disponibile.
- Ogni edizione separa **COMPRARE** (candidati quantitativi), **MANTENERE**, **ATTENDERE** ed **EVITARE**. Le pagine precedenti restano consultabili.
- Le etichette sono segnali del modello e non ordini automatici. Prima di ogni acquisto vanno verificati ISIN, disponibilità Fineco, spread, liquidità, sovrapposizioni e pesi.
