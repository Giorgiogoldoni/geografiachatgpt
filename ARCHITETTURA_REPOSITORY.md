# Mappa tecnica del repository

Ultimo controllo: 21 novembre 2026  
Branch esaminato: `main`  
Commit di riferimento: `4d4bca3d498607e4c1d3337ad0dd447927ea5977`

Questo documento descrive le dipendenze rilevate nel repository. È una mappa di orientamento, non una specifica matematica dei modelli. I file generati e gli archivi storici non vanno cancellati o rinominati senza prima aggiornare e testare tutti i riferimenti.

## 1. Dashboard pubblica e pagine

| Pagina | Ruolo / dati principali |
|---|---|
| `index.html` | Homepage UCITS; legge `ucits_geography.json` e `geografia-motore.json`; incorpora anche il Radar in iframe |
| `radar-predittivo.html` | Radar Momentum + Ridge; legge `radar-predittivo.json` |
| `geografia-motore.html` | Dashboard del motore geografico a sei aree; legge `geografia-motore.json` |
| `geografia-aree.html` | Tassonomia dei sei moduli; legge `geografia-moduli.json` |
| `bollettino.html` | Diario geografico; legge `data/bollettino_geografico.json` |
| `index-etf.html` | Catalogo INDEX geografico; legge `data/geografia_index_user_53.csv` |
| `factor-etf.html` | Catalogo ETF factor; legge `data/geografia_index_factor_21.csv` |
| `bollettino-factor.html` | Pagina bollettino factor |
| `portafogli-usa-euro.html` | Confronto portafogli; legge `world_top4_6040.json` e `euro_top4_6040.json` |
| `world-top4.html` | Dashboard ricerca World Top 4; legge `world_top4.json` |
| `etf-lifecycle.html` | Registro ciclo di vita ETF; usa `etf_lifecycle_registry.csv` e `geografia-motore.json` |
| `raptor-geografia-legacy.html` | Vecchia dashboard RAPTOR, ancora raggiungibile dalla homepage |
| `index-legacy.html` | Copia di sicurezza della homepage; conservarla finché non sia verificato che non serve più |

## 2. Motori e flussi dati

### A. UCITS Geography — homepage

- Motore: `ucits_geography.py`
- Universo iniziale: `ucits_country_universe_seed_2026-11-18.csv`
- Output: `ucits_geography.json`
- Workflow: `.github/workflows/ucits-geography.yml`
- Dashboard che consuma l'output: `index.html`

È la fonte dati principale della homepage. Non è un doppione eliminabile del motore geografico a sei aree: i due flussi hanno scopi e output distinti.

### B. Motore geografico a sei aree e Bollettino

- Motore: `geografia_engine.py`
- Input cataloghi: `data/geografia_index_user_51.csv`, `data/geografia_index_factor_14.csv` e `ucits_country_universe_seed_2026-11-18.csv`
- Output: `geografia-motore.json`
- Dashboard: `geografia-motore.html`
- Bollettino: `bollettino_geografico.py` legge l'output del motore e genera `data/bollettino_geografico.json`
- Workflow: `.github/workflows/geografia-engine.yml`

I due CSV con suffisso 51 e 14 sono gli input esplicitamente usati dal motore secondo il controllo del codice e del workflow. Non sostituirli automaticamente con i file dal suffisso 53 e 21: questi ultimi alimentano le pagine catalogo.

### C. Radar predittivo

- Motore: `radar_predittivo_engine.py`
- Input: `geografia-motore.json`, `data/geografia_index_factor_14.csv`, `data/historical_country_etfs_2007.csv`
- Output: `radar-predittivo.json`
- Dashboard: `radar-predittivo.html`
- Workflow: `.github/workflows/radar-predittivo.yml`

Il JSON del Radar è voluminoso (circa 8,3 MB al controllo). Un workflow verde conferma l'esecuzione, ma non garantisce da solo che ogni browser mobile riesca a scaricare e interpretare il file: in caso di problemi va testato anche il caricamento della pagina pubblica.

### D. Pipeline RAPTOR precedente

- Motore: `raptor_geografia.py`
- Output: `geografia.json`, `data/charts/*.json`, `data/signals/*.json`
- Workflow: `.github/workflows/update.yml`
- Dashboard: `raptor-geografia-legacy.html`

È ancora presente una pipeline automatizzata e la pagina legacy è collegata dalla homepage. Non trattarla come archivio morto senza una decisione esplicita e una verifica dei consumatori.

### E. World Top 4 e portafogli

- Baseline: `world_top4.py` → `world_top4.json`
- Variante 60/40: `world_top4_6040.py` → `world_top4_6040.json`
- Sensibilità regionale: `world_top4_region_sensitivity.py` → `world_top4_region_sensitivity.json`
- Robustezza: `world_top4_robustness.py` → `world_top4_robustness.json`
- Solver sperimentale: `world_top4_solver_experimental.py` → `world_top4_solver_experimental.json`
- Portafoglio EURO: `euro_top4_6040.py` → `euro_top4_6040.json`
- Workflow: `.github/workflows/world-top4.yml` e `.github/workflows/euro-top4-6040.yml`
- Dashboard: `world-top4.html` e `portafogli-usa-euro.html`

I moduli di sensibilità, robustezza e solver sono esperimenti distinti: mantenere separati i loro output dalle baseline.

## 3. CSV simili o duplicati

Al controllo risultano due gruppi di file con contenuto identico (stesso blob Git):

| File | Stato | Nota |
|---|---|---|
| `data/geografia_index_user_51.csv` e `data/geografia_index_user_53.csv` | Duplicati byte-per-byte al controllo | Nomi diversi, usi diversi nei motori/pagine |
| `data/geografia_index_factor_14.csv`, `_20.csv` e `_21.csv` | Duplicati byte-per-byte al controllo | Nomi diversi, riferimenti diversi |

La duplicazione del contenuto non rende intercambiabili i percorsi: workflow, script e dashboard possono riferirsi a nomi precisi. Prima di consolidare questi file occorre aggiornare tutti i riferimenti, verificare i trigger dei workflow e provare le pagine.

## 4. Classificazione pratica

- **Operativi**: `index.html`, `ucits_geography.py`, `ucits_geography.json`, `geografia_engine.py`, `geografia-motore.json`, `radar_predittivo_engine.py`, `radar-predittivo.json`, `bollettino_geografico.py` e i rispettivi workflow/output.
- **Ricerca e validazione**: famiglia `world_top4*`, report di audit e ricerca, cataloghi factor, analisi ETF lifecycle e file storici di test.
- **Legacy / storico ancora accessibile**: `raptor_geografia.py`, `raptor-geografia-legacy.html`, `geografia.json`, `data/charts/`, `data/signals/`, `index-legacy.html`.

Questa classificazione è funzionale, non una proposta di spostamento in cartelle: spostare file può rompere GitHub Pages, workflow, link e percorsi relativi.

## 5. Regole per le prossime manutenzioni

1. Non cancellare né rinominare output JSON, CSV o pagine senza una ricerca completa dei riferimenti.
2. Non unificare i CSV con suffissi diversi solo perché oggi hanno lo stesso hash.
3. Modificare un solo flusso per volta e controllare i workflow che lo producono.
4. Dopo ogni modifica verificare: run GitHub Actions, file JSON pubblicato, pagina HTML live e visualizzazione da mobile.
5. Conservare separati risultati operativi, esperimenti e storico legacy finché non esiste una migrazione verificata.

## 6. Workflow presenti

- `.github/workflows/update.yml`
- `.github/workflows/ucits-geography.yml`
- `.github/workflows/geografia-engine.yml`
- `.github/workflows/radar-predittivo.yml`
- `.github/workflows/world-top4.yml`
- `.github/workflows/euro-top4-6040.yml`

---
Mappa ricavata dall'albero Git e dai riferimenti presenti negli script, nelle dashboard e nei workflow al commit indicato in apertura. Ricontrollare la mappa dopo modifiche strutturali.
