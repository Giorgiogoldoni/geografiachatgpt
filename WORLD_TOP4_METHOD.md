# World Top 4 — metodo e registro holdings

## Obiettivo
Ricostruire una strategia momentum geografica ispirata alle informazioni pubbliche di Logical Invest, senza affermare di replicarne il codice proprietario.

## Struttura
- Quattro gruppi regionali: Developed, Asia, South America e Africa & Middle East. Il quarto gruppo è un'aggregazione di ricerca: le fonti pubbliche reperite confermano almeno Developed, Asia e South America, ma non consentono di attribuire con certezza tutti i ticker alle quattro sleeve correnti.
- Lookback primario: 68 sedute di borsa.
- Tre varianti confrontate: rendimento 68 sedute, rendimento/volatilità annualizzata al quadrato (proxy Sharpe modificato), composito momentum 3/6/12 mesi.
- Ribilanciamento mensile: il segnale usa la chiusura del mese precedente; il rendimento viene misurato nel mese successivo.
- Filtro absolute momentum: un Paese entra nella sleeve soltanto se il rendimento degli ultimi 68 giorni è positivo. Ogni regione selezionata pesa il 20%; la quota delle regioni senza momentum positivo viene trasferita alla sleeve HEDGE. La sleeve hedge sceglie fino a due strumenti positivi tra GLD, TLT, IEF e SHY; se nessuno supera il filtro, la quota resta su SHY. È una regola prudenziale sperimentale, non un peso attribuito a Logical Invest.
- Benchmark: ACWI buy & hold.

## Holdings pubblicati con un mese di ritardo
Il sito Logical Invest segnala che holdings e allocazioni sono ritardati di un mese. Per il confronto manuale compilare logical_invest_holdings.csv indicando:
- publication_date: giorno in cui la composizione è stata vista;
- effective_month: mese di riferimento dichiarato o inferito;
- strategy/sleeve: World Top 4 o sottostrategia;
- ticker e weight: ogni holding e il relativo peso;
- source_url e notes: pagina e note di verifica.

Non retrodatare mai un holding come informazione disponibile alla data del segnale. Se il mese effettivo non è esplicito, marcarlo come inferito e non usarlo per una replica "senza look-ahead".

## Limiti
Dati Yahoo Finance adjusted, ticker USA, nessuna commissione, slippage, imposta o FX. I ticker possono avere storia incompleta o non corrispondere alle share class UCITS. La quarta regione e il peso hedge sono ipotesi esplicite. La formula proprietaria attuale non è pubblica. Prima dell'uso operativo occorre validare i dati e mappare strumenti UCITS.


## Audit tecnico — aggiornamento 18 novembre 2026

### Universo USA Logical Invest: riscontro sulle pagine pubbliche
La pagina World Top 4 elenca 49 ticker USA nel proprio universo pubblico. Le pagine pubbliche delle sottostrategie consultabili espongono gli elenchi Developed, Asia e South America. Gli elenchi non sono perfettamente disgiunti: ad esempio EWJ ed EWM compaiono sia in Developed sia in Asia; EWZ compare in Asia e South America; EZA compare nell'elenco Asia nonostante sia un ETF Sud Africa. Queste sovrapposizioni vanno conservate nel registro di fonte e verificate, non corrette arbitrariamente.

Il file `logical_invest_universe.csv` registra tutti i 49 ticker elencati dalla pagina principale, la classificazione esplicitamente visibile nelle pagine secondarie e i casi non ancora attribuibili con sufficiente certezza. La quarta sleeve e la sua composizione non sono ancora ricostruite: non si deve considerare il raggruppamento Africa & Middle East attuale una replica verificata.

### Metriche aggiunte al motore
Il calcolo ora espone: rendimento totale, CAGR, volatilità, downside volatility, Sharpe con tasso privo di rischio pari a zero, Sortino con target pari a zero, Max Drawdown, Calmar, Ulcer Index, durata massima/media dei periodi underwater, date di picco/minimo/recupero del MaxDD, percentuale di mesi positivi, turnover medio stimato, rendimenti annuali e periodi mobili 1/3/5/10/15 anni.

**Avvertenza di confrontabilità:** Logical Invest descrive lo Sharpe come rendimento in eccesso rispetto a un tasso privo di rischio (normalmente Treasury Bill a 90 giorni). Il nostro Sharpe a tasso zero e Sortino a target zero sono diagnostici interni e non sono direttamente confrontabili con i valori pubblicati da Logical Invest. Per un confronto numerico corretto occorre integrare una serie storica coerente del tasso risk-free e replicare la convenzione di frequenza/annualizzazione del fornitore.

### Stato e prossime verifiche
- Universo complessivo: trascritto dalla pagina ufficiale principale (49 ticker).
- Sottostrategie: elenchi pubblici Developed, Asia e South America registrati.
- Quarta sleeve: non verificata; serve recuperare la pagina/composizione ufficiale.
- HEDGE: la pagina principale descrive Treasury e oro, ma il paniere e le regole di allocazione non sono ancora ricostruiti.
- Performance: il backtest esistente resta un modello indipendente preliminare; non va presentato come replica né confrontato come se usasse le stesse regole.
- La pagina Logical Invest dichiara che i dati storici possono includere estensioni sintetiche e che i risultati sono ipotetici, senza slippage, commissioni e imposte.
