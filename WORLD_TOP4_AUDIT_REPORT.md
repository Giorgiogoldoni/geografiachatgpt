# World Top 4 — audit USA preliminare
**Data analisi:** 18 novembre 2026  
**Prezzi del modello:** fino al 17 novembre 2026; backtest su mesi completi fino al 31 ottobre 2026  
**Stato:** preliminare, non replica ufficiale Logical Invest e non pronto per l'uso operativo

## 1. Correzioni tecniche completate
- Allineamento corretto: il segnale viene calcolato alla chiusura di fine mese e il rendimento viene attribuito al mese immediatamente successivo.
- Escluso il mese corrente incompleto dal backtest.
- Benchmark ACWI allineato agli stessi 223 rendimenti mensili.
- Aggiunte metriche: downside volatility, Sharpe/Sortino con target zero, Calmar, Ulcer Index, durata massima e media underwater, turnover medio, win rate, rendimenti annuali e CAGR mobili 1/3/5/10/15 anni.
- Il workflow GitHub Actions di calcolo è terminato con successo: https://github.com/Giorgiogoldoni/geografiachatgpt/actions/runs/44265655400

## 2. Risultati del modello esplorativo USA
**Periodo comune:** 30 aprile 2008 – 31 ottobre 2026 (223 rendimenti mensili).

| Modello | CAGR storico | Volatilità | Downside vol. | Max DD | Ulcer | Sharpe RF=0 | Sortino target=0 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Score rendimento/volatilità² | 7,07% | 11,97% | 7,36% | -20,35% | 7,27 | 0,63 | 1,03 |
| Momentum 68 sedute | 7,04% | 14,67% | 8,85% | -23,87% | 8,77 | 0,54 | 0,89 |
| Momentum 3/6/12 mesi | 7,36% | 13,27% | 7,85% | -20,35% | 7,71 | 0,60 | 1,02 |
| ACWI buy & hold | 8,39% | 16,53% | 11,16% | -51,70% | 12,58 | 0,57 | 0,85 |

**Lettura:** il modello esplorativo ha contenuto volatilità, Max Drawdown e Ulcer rispetto ad ACWI, ma ha prodotto un CAGR inferiore sul periodo massimo. Il momentum composito ha il miglior CAGR fra le tre varianti e il MaxDD più contenuto, ma resta sotto ACWI sul periodo completo.

Attenzione: Sharpe e Sortino qui usano tasso privo di rischio/target pari a zero. Logical Invest descrive lo Sharpe come rendimento in eccesso rispetto al tasso privo di rischio (normalmente Treasury Bill a 90 giorni), quindi i valori non sono direttamente confrontabili.

## 3. Finestre mobili
| Modello | 3 anni CAGR | 5 anni CAGR | 10 anni CAGR | 15 anni CAGR |
|---|---:|---:|---:|---:|
| Score rendimento/volatilità² | 19,59% | 11,87% | 7,74% | 6,20% |
| Momentum 68 sedute | 24,35% | 12,32% | 6,98% | 5,57% |
| Momentum 3/6/12 mesi | 25,17% | 13,22% | 7,47% | 6,76% |
| ACWI | 22,12% | 10,08% | 12,47% | 11,09% |

I periodi recenti di 3 e 5 anni sono più favorevoli al momentum; sui 10 e 15 anni ACWI è nettamente superiore. È un segnale di dipendenza dal regime di mercato e non basta osservare soltanto il quinquennio più recente.

### Metriche di rischio sulle finestre mobili
**Ultimi 5 anni completi (al 31 ottobre 2026):**

| Modello | CAGR | Vol. | DownVol | Sharpe RF=0 | Sortino target=0 | Max DD | Ulcer | Max underwater |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Score rendimento/volatilità² | 11,87% | 12,25% | 7,38% | 0,98 | 1,63 | -18,91% | 5,04 | 245 gg |
| Momentum 68 sedute | 12,32% | 15,89% | 9,65% | 0,81 | 1,34 | -23,87% | 7,61 | 426 gg |
| Momentum 3/6/12 mesi | 13,22% | 14,56% | 8,37% | 0,93 | 1,61 | -16,42% | 5,06 | 396 gg |
| ACWI | 10,08% | 14,80% | 9,16% | 0,72 | 1,17 | -25,74% | 8,47 | 699 gg |

**Ultimi 3 anni completi:**

| Modello | CAGR | Vol. | DownVol | Sharpe RF=0 | Sortino target=0 | Max DD | Ulcer | Max underwater |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Score rendimento/volatilità² | 19,59% | 10,55% | 5,80% | 1,76 | 3,20 | -8,66% | 1,93 | 153 gg |
| Momentum 68 sedute | 24,35% | 14,83% | 7,97% | 1,55 | 2,89 | -10,09% | 2,70 | 214 gg |
| Momentum 3/6/12 mesi | 25,17% | 14,16% | 7,27% | 1,67 | 3,25 | -9,90% | 2,39 | 122 gg |
| ACWI | 22,12% | 11,44% | 5,15% | 1,82 | 4,03 | -6,11% | 1,66 | 61 gg |

Le varianti di momentum superano ACWI per CAGR nelle finestre recenti, ma hanno volatilità, drawdown e/o durata underwater superiori. Il vantaggio recente non è quindi gratuito in termini di rischio.

## 4. Durata dei drawdown e turnover
| Modello | Max tempo underwater | Media underwater | Turnover medio mensile |
|---|---:|---:|---:|
| Score rendimento/volatilità² | 945 giorni | 141 giorni | 47,9% |
| Momentum 68 sedute | 1.461 giorni | 299 giorni | 50,4% |
| Momentum 3/6/12 mesi | 1.948 giorni | 258 giorni | 43,2% |
| ACWI | 1.645 giorni | 160 giorni | n.d. |

La variante modificata ha un MaxDD recuperato il 31 marzo 2022 dopo un minimo il 31 marzo 2020. Le altre due varianti hanno avuto periodi underwater massimi più lunghi dell'ACWI. Il turnover medio mensile è elevato: prima di qualunque uso pratico va stimato l'impatto di spread, commissioni e fiscalità.

## 5. Cosa sappiamo della strategia ufficiale
- Logical Invest descrive WTOP4 come quattro sottostrategie geografiche, ciascuna seleziona il miglior ETF del proprio segmento, combinate in quattro Paesi distinti.
- La pagina principale pubblica 49 ticker USA; le pagine secondarie consultabili aggiungono almeno ARGT e DBKO e presentano sovrapposizioni/anomalie fra le aree. Il dettaglio è in `logical_invest_universe.csv`.
- L'aggiornamento ufficiale del 27 dicembre 2019, operativo dal 1 gennaio 2020, documenta il passaggio da 70/30 a 60% equity / 40% HEDGE per WTOP4. Lo stesso aggiornamento descrive HEDGE internamente con 60% Treasury / 40% Gold; il solo GSY poteva raggiungere il 100% della sleeve.
- La pagina HEDGE aggiornata a ottobre 2026 descrive due blocchi: Treasury e GLD-USD. La pagina Gold-Currency Strategy II descrive la rotazione tra oro e dollaro. La documentazione LI del 2022 cita GSY come alternativa cash nella componente Treasury e GLD-USD; la newsletter di ottobre 2026 conferma l'uso di GSY come difensivo.
- Le holdings e allocazioni sul sito sono dichiarate in ritardo di un mese; i risultati possono includere storico sintetico e non considerano slippage, costi o imposte.

## 6. Perché il modello non è ancora una replica
1. L'universo e la classificazione delle quattro sleeve non sono ancora ricostruiti senza ambiguità.
2. La quarta sleeve e le sovrapposizioni fra gli elenchi pubblici richiedono conferma sulle holdings storiche.
3. Il peso 60/40 è documentato storicamente, ma il peso corrente va verificato.
4. La nostra HEDGE attuale è una semplificazione e non replica le due sottostrategie Treasury e GLD-USD.
5. Il ranking proprietario, i lookback e i parametri risk-adjusted non sono pubblicati integralmente.
6. Il nostro backtest usa proxy Yahoo Finance adjusted; non include costi, tasse, slippage o conversione FX.

## Confronto diagnostico con lo snapshot LI
Valori del nostro modello a confronto con la fotografia pubblica Logical Invest del 16 ottobre 2026. Le finestre non sono garantite identiche, quindi questa tabella serve a capire ordini di grandezza e differenze di rischio, non a certificare una replica.

**5 anni**

| Modello | CAGR | Vol. | DownVol | Ulcer | MaxDuration | AveDuration |
|---|---:|---:|---:|---:|---:|---:|
| Logical Invest (snapshot) | 12,2% | 8,6% | 5,9% | 2,89 | 247 gg | 51 gg |
| Nostro score rendimento/volatilità² | 11,87% | 12,25% | 7,38% | 5,04 | 245 gg | 58 gg |
| Nostro momentum 68 sedute | 12,32% | 15,89% | 9,65% | 7,61 | 426 gg | 207 gg |
| Nostro momentum 3/6/12 mesi | 13,22% | 14,56% | 8,37% | 5,06 | 396 gg | 88 gg |

**3 anni**

| Modello | CAGR | Vol. | DownVol | Ulcer | MaxDuration | AveDuration |
|---|---:|---:|---:|---:|---:|---:|
| Logical Invest (snapshot) | 18,4% | 9,7% | 6,7% | 2,47 | 131 gg | 26 gg |
| Nostro score rendimento/volatilità² | 19,59% | 10,55% | 5,80% | 1,93 | 153 gg | 31 gg |
| Nostro momentum 68 sedute | 24,35% | 14,83% | 7,97% | 2,70 | 214 gg | 55 gg |
| Nostro momentum 3/6/12 mesi | 25,17% | 14,16% | 7,27% | 2,39 | 122 gg | 26 gg |

Il composito 3/6/12 mesi è quello che si avvicina di più ad alcune metriche di rischio LI nella finestra triennale, ma la volatilità resta più alta e il rendimento è maggiore. Questo può indicare una diversa esposizione, non necessariamente una ricostruzione migliore. Sulla finestra quinquennale nessuna variante replica il profilo di bassa volatilità pubblicato da LI.

## 7. Prossime attività
1. Ricostruire le quattro sleeve usando catalogo ufficiale e holdings pubblicate con ritardo.
2. Separare Treasury Hedge e Gold-Currency II, poi ricostruire la combinazione HEDGE.
3. Testare la struttura storica 60/40 e confrontarla con i pesi osservati più recenti.
4. Confrontare metriche e rendimenti annuali con le finestre 1/3/5/10/15 anni di Logical Invest.
5. Solo dopo l'audit USA, costruire la mappatura degli ETF UCITS europei.

## Fonti Logical Invest
- World Top 4: https://logical-invest.com/app/strategy/WTOP4
- World Countries Developed: https://logical-invest.com/app/strategy/developed/world-countries-developed
- World Countries Asia: https://logical-invest.com/app/strategy/asia/world-countries-asia
- World Countries South America: https://logical-invest.com/app/strategy/soamerica/world-countries-south-america
- HEDGE: https://logical-invest.com/app/strategy/HEDGE
- Gold-Currency Strategy II: https://logical-invest.com/app/strategy/GLD-UUP
- Update 2020 (60/40): https://logical-invest.com/investment-strategy-update-2020/
- Newsletter October 2026: https://logical-invest.com/logical-invest-market-investment-outlook-for-october-2026/


## 8. Riferimento metriche Logical Invest (snapshot pubblico)
La pagina World Top 4 indicizzata con aggiornamento 16 ottobre 2026 riporta, come esempi di confronto:
- **5 anni:** total return 77,5%, CAGR 12,2%, volatilità 8,6%, downside volatility 5,9%, Sharpe 1,13, Sortino 1,66, Ulcer Index 2,89, MaxDuration 247 giorni, AveDuration 51 giorni.
- **3 anni:** total return 65,7%, CAGR 18,4%, volatilità 9,7%, downside volatility 6,7%, Sharpe 1,63, Sortino 2,39, Ulcer Index 2,47, MaxDuration 131 giorni, AveDuration 26 giorni.

Sono valori descrittivi pubblicati nella pagina e vanno trattati come snapshot indicativo, non come una serie dati esportata con date iniziali/finali precise. Le metriche vanno confrontate solo dopo aver allineato la finestra esatta, la frequenza dei rendimenti e la definizione di risk-free/downside deviation.

La tabella riepilogativa della homepage Logical Invest, indicizzata a metà novembre 2026, riporta inoltre circa **+7,4% YTD**, **+8,7% a 1 anno**, volatilità a 1 anno **11,6%**, Sharpe **0,5** e MaxDD a 1 anno **-9,6%**. È un dato di homepage soggetto a variazione giornaliera, non va confuso con lo snapshot pluriennale sopra.


## 9. Audit quantitativo del modello 60/40 — aggiornamento 18 novembre 2026

**Run completato:** https://github.com/Giorgiogoldoni/geografiachatgpt/actions/runs/44270881029  
**Prezzi fino al:** 17 novembre 2026; rendimenti mensili completi fino al 31 ottobre 2026.  
**Campione:** 223 rendimenti mensili, stesso periodo e stessi mesi per ACWI.

Il nuovo motore tiene separato il 60% equity dal 40% HEDGE: quattro sleeve azionarie provvisorie al 15% ciascuna; all'interno di HEDGE, 24% Treasury e 16% GLD-USD. La suddivisione interna 60/40 di HEDGE è una ricostruzione della configurazione storica descritta nel 2020, non una conferma del peso corrente. Le quattro aree e la formula di ranking restano ipotesi.

### Risultati sull'intero campione

| Variante 60/40 | CAGR | Vol. | DownVol | Sharpe con T-Bill | Sortino con T-Bill | Max DD | Ulcer |
|---|---:|---:|---:|---:|---:|---:|---:|
| Momentum 68 sedute | 4,98% | 13,12% | 8,70% | 0,33 | 0,49 | -34,05% | 11,35 |
| Rendimento/volatilità² | 4,97% | 12,25% | 8,34% | 0,34 | 0,50 | -38,93% | 9,95 |
| Composito 3/6/12 mesi | 5,64% | 13,24% | 8,64% | 0,38 | 0,56 | -35,52% | 12,59 |
| ACWI buy & hold | 8,39% | 16,53% | 11,16% | 0,49 | 0,71 | -51,70% | 12,58 |

Per Sharpe e Sortino è stato aggiunto il rendimento del Treasury Bill USA a 13 settimane (^IRX), usando il rendimento annualizzato mensile diviso per 12 come proxy del tasso privo di rischio. È una convenzione di ricerca ragionevole, ma non prova che la convenzione e la serie dati coincidano con quelle usate da LI.

### Finestre recenti: tre e cinque anni

| Variante | CAGR 3a | Vol. 3a | MaxDD 3a | CAGR 5a | Vol. 5a | MaxDD 5a |
|---|---:|---:|---:|---:|---:|---:|
| Momentum 68 sedute | 21,02% | 12,49% | -9,21% | 11,10% | 13,09% | -17,92% |
| Rendimento/volatilità² | 17,90% | 9,49% | -8,35% | 10,98% | 10,65% | -15,18% |
| Composito 3/6/12 mesi | 23,43% | 12,84% | -9,21% | 13,48% | 12,85% | -11,49% |
| ACWI | 22,12% | 11,44% | -6,11% | 10,08% | 14,80% | -25,74% |

### Confronto con lo snapshot pubblico LI

La fotografia LI pubblicata il 16 ottobre 2026 indicava CAGR 12,2%, volatilità 8,6%, DownVol 5,9%, Sharpe 1,13, Sortino 1,66 e Ulcer 2,89 sui cinque anni; sui tre anni CAGR 18,4%, volatilità 9,7%, DownVol 6,7%, Sharpe 1,63, Sortino 2,39 e Ulcer 2,47. Le finestre non hanno estremi ufficiali scaricabili e quindi il confronto è diagnostico, non perfettamente omogeneo.

- **5 anni:** il composito supera il CAGR LI (13,48% contro 12,2%) ma mostra più volatilità (12,85% contro 8,6%), più downside volatility (7,36% contro 5,9%), Sharpe inferiore (0,75 contro 1,13), Sortino inferiore (1,24 contro 1,66) e Ulcer più alto (3,84 contro 2,89). La durata massima underwater è simile: 245 contro 247 giorni.
- **3 anni:** il composito è più redditizio (23,43% contro 18,4%), ma più volatile (12,84% contro 9,7%), con Sharpe inferiore (1,38 contro 1,63), Ulcer leggermente più alto (2,65 contro 2,47) e drawdown più lunghi (214 contro 131 giorni). Il modello rendimento/volatilità² si avvicina maggiormente al profilo di rischio, ma rende meno (17,90% CAGR) e mantiene una durata massima underwater superiore.

### Diagnostica delle selezioni HEDGE

Nel periodo di 223 mesi, la frequenza delle selezioni varia sensibilmente con il ranking. Nel modello modificato GSY compare 179 mesi, UUP 114 e GLD 109; nel composito GLD 137, TLT 88, UUP 86 e GSY 74. Questo mostra che la scelta della formula cambia anche la composizione difensiva, non soltanto la selezione azionaria. La frequenza è conteggiata sulle sleeve e non rappresenta una quota percentuale del capitale.

### Conclusione provvisoria

Nessuna delle tre varianti è una replica soddisfacente di Logical Invest. Il composito è il migliore per CAGR sui tre e cinque anni, ma non riproduce la volatilità e i rapporti risk-adjusted di LI; sul periodo massimo tutte e tre le varianti sottoperformano ACWI in CAGR. Il vantaggio recente del composito non deve essere scambiato per una conferma dei parametri proprietari.

**Correzione importante:** la tabella sintetica comunicata nel precedente aggiornamento della chat riportava valori provvisori non corrispondenti all'output definitivo del motore 60/40. I numeri ufficiali di questo audit sono quelli delle tabelle qui sopra e del file `world_top4_6040.json`.

### Prossimo lavoro
1. Sostituire il bucket residuale con una quarta sleeve solo quando si trova una fonte primaria o una serie storica holdings che ne confermi composizione e perimetro.
2. Testare il Treasury hedge e il Gold-Currency II come sottostrategie distinte, senza assumere che GLD/UUP sia l'intero universo corrente.
3. Fare walk-forward/out-of-sample: parametri scelti sul training, congelati sul test, e sensibilità su lookback e date di ribilanciamento.
4. Aggiungere costi, spread e slippage realistici e controllare i ticker con storico incompleto/delisting.
5. Solo dopo queste verifiche passare alla mappatura UCITS europea.


## 10. Verifica della possibile quarta area: Medio Oriente / Africa
**Nuovo riscontro documentale — 18 novembre 2026**

La tua ipotesi sul Medio Oriente è fondata come pista di ricerca: nella lista ufficiale degli strumenti della pagina World Top 4 compaiono esplicitamente:
- **GULF** — WisdomTree Middle East Dividend;
- **MES** — VanEck Gulf States;
- **GAF** — SPDR Emerging Middle East & Africa;
- **EGPT** — Egitto;
- **AFK** — Africa;
- **EZA** — Sudafrica;
- **TUR** — Turchia.

Questa evidenza dimostra che l'universo WTOP4 contiene esposizioni Medio Oriente e Africa. **Non dimostra però che la quarta sottostrategia si chiami “Middle East”**: la pagina principale parla di quattro sottostrategie geografiche e cita Africa, Asia e America Latina come esempi, senza pubblicare il nome di tutte e quattro. La pagina Developed include inoltre Israele (EIS), mentre la pagina Asia pubblica presenta alcune classificazioni geograficamente anomale. Non è corretto quindi assegnare in modo definitivo EIS, TUR o gli ETF regionali a una sola sleeve senza la pagina ufficiale della quarta sottostrategia o le holdings storiche.

### Ipotesi di lavoro da testare, non da dare per acquisita
La pista più promettente è una quarta area **Africa / Middle East (o EMEA emergente)**, distinta da Developed, Asia e Latin America. Per testarla:
1. gruppo Africa: AFK, EGPT, EZA;
2. gruppo Medio Oriente/Golfo: GULF, MES;
3. strumento ponte: GAF, che combina Middle East e Africa;
4. TUR resta separato come caso EMEA/Turchia, finché non si trova conferma;
5. FM, FRN, RSX e altri strumenti non assegnati non vanno forzati nel gruppo solo per completare il paniere.

Il modello 60/40 attuale continua a usare il bucket residuale non verificato e **non incorpora ancora questa nuova ipotesi come se fosse la metodologia ufficiale**. Il prossimo test quantitativo dovrà confrontare almeno due alternative: (A) Africa + Middle East/Gulf; (B) Africa soltanto, lasciando GULF/MES/GAF fuori o in un paniere EMEA separato. Si confronteranno copertura storica, mesi senza prezzi, concentrazione, turnover e risultati fuori campione.

Fonte primaria: pagina World Top 4, sezione “Methodology & Assets”, che elenca GAF, GULF, MES, EGPT, AFK, EZA e TUR e descrive le quattro sottostrategie senza nominarle tutte: https://logical-invest.com/app/strategy/WTOP4


## 11. Approfondimento Medio Oriente: distinzione tra universo storico e strumenti attivi
**Aggiornamento ricerca — 18 novembre 2026**

La pagina principale WTOP4 elenca 49 strumenti e contiene effettivamente un blocco di esposizioni che rende plausibile la tua ipotesi:
- AFK, EGPT, EZA: Africa / paesi africani;
- GAF: Middle East & Africa;
- GULF: Middle East;
- MES: Gulf States / GCC;
- TUR: Turchia;
- EIS: Israele (ma è anche nella sottostrategia pubblica Developed).

Questa è una prova che il perimetro storico degli strumenti WTOP4 includeva Medio Oriente e Africa, ma non rivela da sola a quale sottostrategia appartenesse ogni ETF.

**Attenzione: GAF, MES e GULF sono strumenti storici non più negoziati.** Una fonte di settore che censisce gli ETF regionali riporta GAF liquidato nel luglio 2017, MES nell'ottobre 2016 e GULF nel maggio 2020. Non devono essere trattati come ETF utilizzabili oggi; possono servire solo per ricostruzioni storiche, se le serie prezzi sono complete e correttamente rettificate.

Esistono invece strumenti nazionali tuttora attivi:
- KSA — iShares MSCI Saudi Arabia ETF; factsheet BlackRock al 30 settembre 2026.
- UAE — iShares MSCI UAE ETF; incluso nei rendiconti semestrali iShares al 28 febbraio 2026.
- QAT — iShares MSCI Qatar ETF; incluso nei documenti regolamentari SEC.
Questi tre strumenti, insieme a TUR (Turchia), sono candidati più sensati per un test di una sleeve Medio Oriente / GCC attuale. Non sono però confermati come componenti della quarta sottostrategia LI.

### Conclusione aggiornata sull'ipotesi
La lettura più plausibile da testare non è “Medio Oriente puro” con GAF/GULF/MES, perché quei fondi sono chiusi. È **Africa + Medio Oriente / EMEA emergente**, con un universo storico e un universo investibile attuale distinti:
- storico: AFK, EGPT, EZA, GAF, GULF, MES, TUR;
- investibile attuale candidato: AFK, EGPT, EZA, KSA, UAE, QAT, TUR.
La classificazione definitiva della quarta sleeve resta non confermata: la pagina principale non nomina tutte e quattro le sottostrategie e non abbiamo trovato una pagina pubblica dedicata “World Countries Africa” o “World Countries Middle East”.

### Fonti consultate
- WTOP4, metodologia e lista strumenti: https://logical-invest.com/app/strategy/WTOP4
- Lista ETF Middle East e date di liquidazione GAF/MES/GULF: https://www.emergingmarketskeptic.com/emerging-market-etfs-list/asia-etfs-list/middle-east-etfs-list/middle-east-etfs-list-region-wide/
- Factsheet KSA BlackRock, 30 settembre 2026: https://www.blackrock.com/us/individual/literature/fact-sheet/ksa-ishares-msci-saudi-arabia-etf-fund-fact-sheet-en-us.pdf
- Rendiconti iShares 28 febbraio 2026 (KSA e UAE): https://www.ishares.com/us/library/stream-document?documentId=1164765~2318535~926204~2298022~2360029~2251464~2517642~2118037~2164935&iframeUrlOverride=%2Fus%2F%2Fliterature%2Fsemi-annual-financial-statements%2Fsafs-c-ishares-trust-msci-country-etfs-book1-02-28-en.pdf&product=IUS-KSA&shareClass=NA&stream=reg
- Documenti SEC 2026 con QAT e UAE: https://www.sec.gov/Archives/edgar/data/1100663/000143893426002282/0001438934-26-002282-index.htm

Il test di sensibilità va quindi aggiornato per confrontare il gruppo Africa + Middle East con i ticker attivi KSA/UAE/QAT/TUR, oltre alle ipotesi Africa-only e Middle East-only. I fondi liquidati GAF/GULF/MES resteranno solo nel test storico separato.


## 12. Ipotesi geografica ampliata: Mediterraneo orientale
**Aggiornamento — 18 novembre 2026, dopo confronto sui ticker**

La tua osservazione è importante: **GREK (Grecia) era già nell'universo ufficiale WTOP4** e va considerato insieme a **TUR (Turchia) ed EGPT (Egitto)** in una prova di “Mediterraneo orientale / Medio Oriente allargato”. La lista ufficiale WTOP4 contiene esplicitamente tutti e tre i ticker: GREK, TUR ed EGPT. Questo è un dato verificato; la loro assegnazione alla medesima sottostrategia resta invece un'ipotesi, perché LI non pubblica nel riepilogo principale la composizione completa delle quattro aree.

Nuova classificazione da testare:
- **Mediterraneo orientale / Medio Oriente allargato:** EGPT, GREK, TUR.
- **Golfo:** KSA, UAE, QAT (candidati investibili più recenti, non confermati nell'universo storico ufficiale WTOP4).
- **Africa:** AFK, EZA, con EGPT escluso dal gruppo Africa-only per evitare doppio conteggio negli scenari comparativi.
- **Storico regionale composito:** GAF, GULF, MES; strumenti legacy da trattare con cautela e non come universo investibile corrente.

Nel motore di sensibilità sono stati quindi aggiunti due scenari con GREK:
1. legacy Africa + Middle East, con GREK e TUR inclusi nel gruppo di confronto;
2. candidati attivi Eastern Mediterranean + Middle East: EGPT, GREK, TUR, KSA, UAE, QAT.

Nota geografica: Grecia non è Medio Oriente in senso stretto; viene inclusa soltanto nella variante “Mediterraneo orientale allargato”. Questa separazione permette di vedere se l'inclusione di GREK migliora o peggiora la stabilità e i risultati, senza spacciare la classificazione per ufficiale.

Fonte primaria per la presenza dei ticker nell'universo: https://logical-invest.com/app/strategy/WTOP4


## 13. Risultati aggiornati della sensibilità geografica — 18 novembre 2026

Run di riferimento: `44274863684` (successo), prezzi fino al 17 novembre 2026 e rendimenti completi fino al 31 ottobre 2026. Il motore ora richiede lookback completi per il ranking composito 3/6/12 mesi; i titoli con meno di 12 mesi di osservazioni non vengono valutati dal composito.

### Risultati composito 3/6/12 mesi

| Ipotesi quarta area | Mesi disponibili | CAGR 5 anni | Vol. 5 anni | Max DD 5 anni | Ulcer 5 anni |
|---|---:|---:|---:|---:|---:|
| Residual storico | 223 | 12,88% | 12,77% | -11,49% | 4,20 |
| Mediterraneo orientale (EGPT, GREK, TUR) | 211 | 13,27% | 12,53% | -12,02% | 3,98 |
| Golfo attivo (KSA, UAE, QAT) | 137 | 8,61% | 12,54% | -13,31% | 6,37 |
| Africa + Mediterraneo + Golfo | 223 | 11,95% | 12,64% | -11,78% | 4,32 |
| Africa + Turchia + Grecia + Golfo (paniere esplorativo) | 223 | 11,95% | 12,64% | -11,78% | 4,32 |
| Africa soltanto (AFK, EZA) | 223 | 10,31% | 13,94% | -14,26% | 6,33 |
| GAF, GULF, MES (legacy) | 0 | n.d. | n.d. | n.d. | n.d. |

Le finestre mobili a 3 e 5 anni sono calcolate sugli ultimi 36 e 60 rendimenti mensili disponibili, quindi hanno gli stessi estremi temporali per tutte le ipotesi attive. I CAGR dell'intero campione NON sono direttamente confrontabili perché l'inizio della storia varia (dal 2008 al 2015).

### Interpretazione

- Il paniere **EGPT + GREK + TUR** è il migliore tra le ipotesi testate sul quinquennio: CAGR 13,27%, rispetto al 12,88% del paniere residuale, con volatilità e Ulcer leggermente inferiori ma Max Drawdown leggermente peggiore.
- Il Golfo puro non emerge come soluzione convincente: la storia è corta (137 mesi per il composito) e il CAGR quinquennale è inferiore.
- Africa soltanto è più debole sul quinquennio, con maggiore volatilità, drawdown e Ulcer.
- Il paniere ampio Africa + Mediterraneo + Golfo non migliora il residuale. I suoi risultati sono identici al paniere esplorativo corrente: in questo backtest l'aggiunta di EGPT non cambia le selezioni/il rendimento finale.
- GAF, GULF e MES non hanno prodotto alcun mese investibile con la serie disponibile: il test legacy non può essere usato per giudicare la performance storica della regione.

### Limiti e controllo ancora necessario

Questa è una **sensibilità quantitativa**, non la prova della classificazione ufficiale Logical Invest. La migliore performance di EGPT/GREK/TUR non dimostra che LI abbia chiamato la sleeve “Middle East” o che abbia usato questi tre ETF. Inoltre il ranking e la copertura sono quelli del nostro modello indipendente, non i parametri proprietari LI.

È stato aggiunto al codice un ulteriore confronto con intersezione esatta delle date mensili tra tutte le ipotesi attive. Questo confronto matched-period deve ancora essere ricalcolato da GitHub Actions: il commit del codice è presente, ma il push effettuato dall'integrazione GitHub non ha avviato automaticamente un nuovo workflow. Non considerare quindi il campo `common_period` come già popolato nei dati pubblicati.

**Conclusione di ricerca:** fra le ipotesi disponibili, il Mediterraneo orientale (Egitto, Grecia, Turchia) è al momento il candidato quantitativo più interessante; il Golfo puro e Africa soltanto risultano meno convincenti. La denominazione ufficiale della quarta sleeve resta non verificata. Non si passa ancora alla mappatura UCITS né si dichiara replicata la strategia WTOP4.
