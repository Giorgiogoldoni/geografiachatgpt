# World Top 4 — audit di fedeltà alla metodologia Logical Invest

**Data:** 18 novembre 2026  
**Ambito:** confronto documentale e revisione statica del modulo `world_top4_solver_experimental.py`  
**Esito:** il backtest sperimentale attuale NON è una replica della strategia Logical Invest.

## 1. Evidenze ufficiali utilizzabili

### Strategia storica 2019
L'articolo Logical Invest del 20 gennaio 2019 descrive:
- lookback di 68 sedute;
- ribilanciamento mensile;
- ranking Modified Sharpe con volatility attenuator pari a 2;
- combinazione dei country ETF e del Treasury TMF per massimizzare il Modified Sharpe;
- allocazione azionaria normalmente almeno 70%, con TMF variabile fra 0% e 30%;
- un universo di circa 49 ETF paese/regione.

Fonte: https://logical-invest.com/world-country-etf-rotation-strategy/

Questa è evidenza storica, non prova che tutti i parametri siano ancora identici nel 2026.

### Modifica annunciata per il 2020
L'aggiornamento del 27 dicembre 2019, operativo dal 1 gennaio 2020, afferma che:
- le quattro sottostrategie azionarie World Country Top 4 vengono riunite in una strategia equity separata;
- questa strategia equity viene bilanciata contro la strategia HEDGE;
- per World Country Top 4 il rapporto equity/HEDGE passa da 70/30 a 60/40;
- HEDGE ruota fra GLD, TLT, TIP e GSY; la componente Treasury/Gold è descritta con rapporto 60/40, con GSY che può arrivare al 100% della componente hedge.

Fonte: https://logical-invest.com/investment-strategy-update-2020/

È un'architettura storicamente documentata. Non abbiamo una prova pubblica sufficiente che il peso 60/40 sia rimasto invariato nella versione live 2026.

### Descrizione pubblica attuale
La pagina WTOP4 descrive quattro sottostrategie geografiche, ognuna orientata a selezionare il miglior ETF del proprio segmento. Dichiara inoltre che holdings e allocazioni sono ritardati di un mese e che le serie storiche possono includere dati sintetici; i risultati sono ipotetici e non includono slippage, commissioni e imposte.

Fonte: https://logical-invest.com/app/strategy/WTOP4

Le pagine regionali verificabili nel repository documentano Developed, Asia e South America. Non è stata ancora verificata una pagina corrente con i componenti della quarta sottostrategia.

## 2. Revisione del codice sperimentale attuale

File esaminato: `world_top4_solver_experimental.py`.

| Area | Codice attuale | Valutazione |
|---|---|---|
| Lookback | 68 rendimenti giornalieri | Coerente con la fonte storica |
| Frequenza | Mensile | Coerente con la fonte storica |
| Score | media giornaliera / deviazione standard giornaliera² | Interpretazione plausibile del fattore 2; formula live completa non verificata |
| Universo equity | Quattro panieri regionali provvisori ereditati da `world_top4_6040.py` | Non verificato |
| Selezione equity | Prima sceglie un vincitore indipendente per ciascuna regione | Coerente con la descrizione delle sottostrategie, ma non dimostra la logica di combinazione ufficiale |
| Solver | Ottimizza solo i quattro vincitori già scelti, long-only, griglia 5% | Non equivale al solver proprietario QuantTrader |
| HEDGE | Seleziona separatamente un ETF Treasury e uno GLD/USD con score individuale | Approssimazione; non replica la strategia HEDGE ufficiale |
| Pesi | 60% equity + 24% Treasury + 16% GLD/USD | Scenario storico 2020, non peso live 2026 verificato |
| Vincolo 10%-40% | Variante di sensibilità | Non è una regola Logical Invest documentata |
| Prezzi | Yahoo Finance adjusted, ticker USA | Da validare per storia, dividendi, valuta e strumenti |
| Costi/FX | Non inclusi | Limite sostanziale per un confronto operativo |

### Disallineamento più importante
Il codice non esegue un'ottimizzazione congiunta equity + hedge:
1. sceglie prima quattro ETF azionari, uno per ciascun paniere provvisorio;
2. ottimizza i pesi soltanto fra quei quattro ETF;
3. sceglie separatamente il Treasury e il GLD/USD migliori;
4. assegna a questi ultimi pesi fissi del 24% e 16%.

Questa procedura non replica né il modello descritto nel 2019 (country ETF e Treasury combinati per massimizzare il Modified Sharpe) né dimostra la replica dell'architettura a due livelli introdotta nel 2020 (quattro sottostrategie equity poi bilanciate contro HEDGE).

## 3. Problemi aperti che impediscono una replica fedele

1. **Quarta sottostrategia:** composizione corrente non verificata.
2. **Universo non coerente:** le liste regionali pubblicate contengono sovrapposizioni e anomalie; alcuni ticker delle pagine regionali non compaiono nell'elenco principale e viceversa.
3. **Solver proprietario:** non sono pubblici tutti i vincoli, il trattamento dei pesi, le soglie e le convenzioni numeriche.
4. **HEDGE:** non sono stati ricostruiti i segnali mensili e le regole complete delle componenti Treasury e GLD-USD.
5. **Pesi live:** il 60/40 equity/HEDGE è documentato per il 2020, ma non verificato come peso corrente 2026.
6. **Timing:** il segnale calcolato alla chiusura di fine mese e l'investimento valorizzato dalla stessa chiusura presuppongono la possibilità di eseguire a quel prezzo. Va testata anche un'esecuzione dal primo prezzo negoziabile successivo.
7. **Confronto benchmark:** il confronto ACWI è stato allineato agli stessi intervalli mensili, ma resta da rendere omogeneo anche in valuta e trattamento dei dividendi.
8. **Dati storici:** occorre controllare survivorship bias, date di lancio, ticker cessati e serie sintetiche. La pagina ufficiale dichiara l'uso di estensioni sintetiche nella storia pubblicata.

## 4. Conclusione sull'esito del backtest

Il risultato precedente (CAGR sperimentale inferiore ad ACWI) non dimostra che Logical Invest non sia valida. Dimostra soltanto che questa particolare implementazione incompleta ha avuto risultati inferiori nel campione testato.

Non usare il backtest attuale per giudicare la strategia ufficiale, né per produrre segnali operativi.

## 5. Piano di lavoro ordinato

### Fase A — ricostruzione delle regole
- recuperare e archiviare le pagine correnti delle quattro sottostrategie;
- identificare la quarta sleeve senza classificazioni arbitrarie;
- ottenere snapshots delle holdings ufficiali con data di pubblicazione e mese effettivo separati;
- ricostruire le due componenti HEDGE e le loro regole;
- distinguere esplicitamente motore 2019, aggiornamento 2020 e versione live 2026.

### Fase B — motore sperimentale separato
Implementare almeno due ipotesi, senza sovrascrivere le baseline:
- **Modello storico 2019:** universo e selezione country/Treasury con ottimizzazione congiunta, usando solo vincoli documentabili e marcando ogni assunzione;
- **Modello architettura 2020:** quattro sottostrategie equity distinte, HEDGE ricostruito separatamente, poi combinazione equity/HEDGE con il 60/40 come scenario storico.

### Fase C — validazione
- confrontare ticker e pesi mensili contro holdings ufficiali, tenendo conto del ritardo di pubblicazione;
- misurare la concordanza delle selezioni, non solo il rendimento;
- confrontare ACWI nello stesso periodo, valuta e convenzione total-return;
- eseguire test out-of-sample e sensibilità dei parametri;
- introdurre costi, turnover, FX e imposte solo dopo aver validato la meccanica.

## Decisione

**Nessuna modifica al motore operativo e nessuna sostituzione delle baseline.** Il modulo solver corrente resta un test esplorativo. Il prossimo sviluppo corretto è ricostruire le quattro sottostrategie e HEDGE prima di ricalcolare le performance.
