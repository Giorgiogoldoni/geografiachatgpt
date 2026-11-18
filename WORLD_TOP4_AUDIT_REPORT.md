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
| Score rendimento/volatilità² | 6,53% | 11,98% | 7,44% | -22,78% | 7,60 | 0,59 | 0,95 |
| Momentum 68 sedute | 6,57% | 14,63% | 8,88% | -24,63% | 9,06 | 0,51 | 0,84 |
| Momentum 3/6/12 mesi | 7,57% | 13,21% | 7,80% | -20,06% | 7,46 | 0,62 | 1,05 |
| ACWI buy & hold | 8,39% | 16,53% | 11,16% | -51,70% | 12,58 | 0,57 | 0,85 |

**Lettura:** il modello esplorativo ha contenuto volatilità, Max Drawdown e Ulcer rispetto ad ACWI, ma ha prodotto un CAGR inferiore sul periodo massimo. Il momentum composito ha il miglior CAGR fra le tre varianti e il MaxDD più contenuto, ma resta sotto ACWI sul periodo completo.

Attenzione: Sharpe e Sortino qui usano tasso privo di rischio/target pari a zero. Logical Invest descrive lo Sharpe come rendimento in eccesso rispetto al tasso privo di rischio (normalmente Treasury Bill a 90 giorni), quindi i valori non sono direttamente confrontabili.

## 3. Finestre mobili
| Modello | 3 anni CAGR | 5 anni CAGR | 10 anni CAGR | 15 anni CAGR |
|---|---:|---:|---:|---:|
| Score rendimento/volatilità² | 19,88% | 12,03% | 7,55% | 5,91% |
| Momentum 68 sedute | 24,96% | 12,56% | 6,85% | 5,28% |
| Momentum 3/6/12 mesi | 25,17% | 13,53% | 7,66% | 7,02% |
| ACWI | 22,12% | 10,08% | 12,47% | 11,09% |

I periodi recenti di 3 e 5 anni sono più favorevoli al momentum; sui 10 e 15 anni ACWI è nettamente superiore. È un segnale di dipendenza dal regime di mercato e non basta osservare soltanto il quinquennio più recente.

## 4. Durata dei drawdown e turnover
| Modello | Max tempo underwater | Media underwater | Turnover medio mensile |
|---|---:|---:|---:|
| Score rendimento/volatilità² | 945 giorni | 145 giorni | 48,0% |
| Momentum 68 sedute | 1.948 giorni | 321 giorni | 50,7% |
| Momentum 3/6/12 mesi | 1.918 giorni | 225 giorni | 43,1% |
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
