# Logical Invest World Top 4 — ricostruzione dell'universo ufficiale e della quarta sleeve

**Data verifica:** 18 novembre 2026  
**Fonte primaria WTOP4:** https://logical-invest.com/app/strategy/WTOP4 (pagina indicata come aggiornata al 16 ottobre 2026)  
**Fonti delle sottostrategie:** Developed (30 settembre 2026), Asia (28 settembre 2026), South America (7 ottobre 2026).

## 1. Nuova evidenza ufficiale

La pagina ufficiale World Top 4 afferma che:
- la strategia contiene quattro sottostrategie;
- ogni sottostrategia seleziona il miglior ETF paese di una specifica area geografica;
- gli esempi geografici forniti sono Africa, Asia e Latin America;
- i quattro risultati vengono combinati per mantenere diversificazione geografica;
- la strategia è coperta da HEDGE.

La stessa pagina pubblica l'universo WTOP4 di 49 ticker. Lo snapshot è stato archiviato in `logical_invest_wtop4_universe_2026-10-16.csv`.

**Limite decisivo:** la pagina elenca i 49 ETF, ma non associa ogni ETF a una delle quattro sottostrategie. La parola "Africa" compare come esempio di area, non come prova che esista una sleeve Africa autonoma con una precisa lista pubblica. Non si deve assegnare automaticamente AFK, EGPT, GAF, GULF, MES, TUR, GREK, FRN, FM o RSX a una quarta sleeve.

## 2. Cosa sappiamo delle aree

| Area | Evidenza disponibile | Stato |
|---|---|---|
| Developed | Pagina regionale dedicata, universo pubblicato | Confermata |
| Asia | Pagina regionale dedicata, universo pubblicato | Confermata, ma contiene classificazioni anomale |
| South America | Pagina regionale dedicata, universo pubblicato | Confermata, ma include EWW/Messico |
| Quarta area | La pagina WTOP4 cita Africa tra gli esempi; il resto dell'universo include ETF Africa, Middle East, Frontier, EMEA e altri | Non ricostruita in modo verificabile |

## 3. Discrepanze tra master list e pagine regionali

Le pagine regionali non coincidono perfettamente con l'universo master WTOP4:
- Developed include SPY e DIA, che non compaiono nell'elenco master WTOP4.
- Asia include DBKO, assente dall'elenco master.
- South America include ARGT, assente dall'elenco master.
- South America pubblica EPU e GXG come componenti, mentre le liste e gli snapshot vanno mantenuti separati per data e fonte.
- EWJ ed EWM compaiono sia in Developed sia in Asia.
- EWZ compare in Asia e South America.
- EZA (Sudafrica) compare nella pagina Asia.
- EWW (Messico) compare nella pagina South America.
- QQQ è incluso in Developed/WTOP4 pur non essendo un ETF di un singolo Paese.

Queste incongruenze non vanno "corrette" a intuito: potrebbero dipendere da aggiornamenti asincroni, universi diversi fra strategia madre e sottostrategie, o classificazioni proprie del provider. Per una replica serve capire quale lista alimenta davvero ogni sleeve nel periodo storico.

## 4. HEDGE: evidenza corrente

La pagina HEDGE, aggiornata il 7 ottobre 2026, descrive due componenti:
1. una sottostrategia Treasury;
2. una sottostrategia GLD-USD.

La motivazione dichiarata è aggiungere l'oro per gestire periodi d'inflazione prolungata in cui le obbligazioni possono attraversare un mercato ribassista pluriennale.

La pagina non espone pubblicamente, nel contenuto accessibile a questo audit, i segnali completi, i pesi correnti e le regole di selezione dei due moduli. Quindi il nostro attuale schema 24% Treasury + 16% GLD/USD non è verificato come allocazione live: resta esclusivamente una sensibilità basata sull'architettura storica 60/40.

Fonte: https://logical-invest.com/app/strategy/HEDGE

## 5. Implicazioni per il motore

Non modificare ancora `base.REGIONS` né `world_top4_solver_experimental.py`.

Il prossimo motore non deve trattare l'insieme dei candidati Africa/Frontier/Middle East come una quarta sleeve ufficiale. Fino a quando non recuperiamo una mappa ufficiale:
- mantenere Developed, Asia e South America come universi documentati;
- conservare separatamente l'elenco master WTOP4;
- marcare come "sleeve non assegnata" ogni componente senza pagina regionale verificata;
- evitare doppie assegnazioni degli ETF nelle prove principali;
- eseguire solo analisi di sensibilità esplicitamente etichettate per le ipotesi sulla quarta area.

## 6. Passo successivo di ricerca

Per chiudere la quarta sleeve serve almeno una delle seguenti evidenze:
- una pagina Logical Invest dedicata alla quarta sottostrategia;
- uno snapshot storico ufficiale delle holdings/allocazioni con identificativo della sottostrategia;
- un documento del provider che associ i ticker alle quattro aree;
- una serie mensile delle quattro sottostrategie che permetta di riconciliare i ticker selezionati.

Le allocazioni WTOP4 pubbliche sono dichiarate ritardate di un mese e le serie storiche possono includere dati sintetici. In ogni confronto bisogna quindi conservare data di pubblicazione, data effettiva e flag sintetico/effettivo.

## Conclusione

Abbiamo ora l'universo master WTOP4 aggiornato e la conferma ufficiale dell'architettura a quattro aree. **Non abbiamo ancora la classificazione ufficiale dei 49 ETF nelle quattro aree.** La quarta sleeve resta non identificata in modo sufficiente per un backtest fedele. La ricerca è avanzata, ma il motore non va ancora modificato.


## 7. Approfondimento HEDGE: identificati i due moduli pubblici

La ricerca aggiuntiva ha individuato anche le pagine dei moduli sottostanti:

- **Gold-Currency Strategy II (GLD-UUP)**, aggiornata al 12 ottobre 2026 nella pagina corrente. La descrizione ufficiale dice che alterna oro e dollaro USA in base alla loro recente performance corretta per il rischio. La pagina pubblica indica che è un aggiornamento della strategia originaria GLD-USD, che utilizzava ETF inversi a leva. Fonte: https://logical-invest.com/app/strategy/GLD-UUP
- **Treasury Hedge (TRESHEDGE)**, pagina ufficiale aggiornata al 24 giugno 2026. Fonte: https://logical-invest.com/app/strategy.php?symbol=TRESHEDGE
- **HEDGE**, aggiornato al 7 ottobre 2026, dichiara di combinare proprio una componente Treasury e una componente GLD-USD. Fonte: https://logical-invest.com/app/strategy/HEDGE

Questa evidenza chiarisce il ruolo di GLD/UUP: non è sufficiente scegliere semplicemente il migliore dei due ETF applicando il nostro score Modified Sharpe. La strategia Gold-Currency II usa una misura di performance risk-adjusted recente, ma la pagina pubblica consultata non rende disponibili tutti i parametri numerici necessari per riprodurla esattamente.

Analogamente, la presenza della pagina Treasury Hedge conferma che il modulo Treasury è una strategia autonoma: la nostra selezione diretta fra TLT, TIP e GSY non è dimostrata equivalente al suo algoritmo. I pesi correnti dei due moduli all'interno di HEDGE e i segnali effettivi non sono pubblicamente leggibili nelle pagine consultate.

**Conseguenza sul codice:** la parte HEDGE del motore sperimentale resta un'approssimazione più forte di quanto vorremmo. Non va promossa a replica ufficiale. Prima di modificare il codice bisogna ottenere gli snapshot storici o i segnali dei moduli Treasury Hedge e Gold-Currency II, e verificare come HEDGE li combina.
