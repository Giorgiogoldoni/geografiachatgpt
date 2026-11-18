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


### HEDGE — ulteriore riscontro pubblico
La pagina ufficiale della sub-strategia HEDGE aggiornata a ottobre 2026 descrive due componenti: una strategia Treasury e una strategia GLD-USD. Una newsletter Logical Invest di ottobre 2026 riferisce inoltre che la sleeve ha selezionato GSY (ultra-short paper) in settembre, quando oro e Treasury erano entrambi in calo. Un thread storico del forum Logical Invest descrive, come universo di allora, GLD/GSY/MINT/TIP/UUP per GLD-USD e GSY/TIP/TLT per Treasury; MINT e TIP erano marcati non attivi in quel post. Questi dettagli storici non vanno assunti come lista corrente senza conferma.

Di conseguenza, la nostra attuale selezione piatta fra GLD/TLT/IEF/SHY e il peso HEDGE minimo del 20% sono ipotesi semplificative, non una replica del motore HEDGE. Il passo successivo è ricostruire separatamente le due sottostrategie e verificare come WTOP4 ne determina il peso complessivo.


### Architettura equity/HEDGE: peso storico documentato
L'aggiornamento ufficiale Logical Invest del 27 dicembre 2019, operativo dal 1 gennaio 2020, descrive per World Country Top 4 il passaggio da 70/30 a **60% equity / 40% HEDGE**. La pagina principale attuale continua a descrivere WTOP4 come strategia azionaria coperta da HEDGE, ma non espone pubblicamente un peso corrente numerico. Perciò 60/40 è un riferimento storico ufficiale importante, da verificare contro le holdings/allocazioni correnti prima di chiamarlo peso attuale.

La pagina HEDGE aggiornata a ottobre 2026 descrive due blocchi: Treasury e GLD-USD. La pagina Gold-Currency Strategy II aggiornata a ottobre 2026 descrive la rotazione tra oro e dollaro in base alla performance risk-adjusted. La documentazione Logical Invest del 2022 descrive Treasury Hedge come rotazione fra TLT, TIP e GSY e GLD-USD come rotazione tra GLD e GSY; la newsletter di ottobre 2026 conferma che GSY è stato usato come difensivo in settembre. Questo permette di ricostruire l'architettura, ma non i pesi mensili o tutti i parametri proprietari.

### Disallineamenti del catalogo pubblico
La pagina principale pubblica 49 ticker. Le pagine delle sottostrategie consultabili aggiungono almeno ARGT e DBKO, assenti dall'elenco principale, e riportano sovrapposizioni/anomalie (EWJ/EWM tra Developed e Asia; EWZ/EZA nella pagina Asia; EWZ anche in South America). Il CSV conserva sia i 49 ticker principali sia i ticker aggiuntivi e le classificazioni pubblicate. Non normalizzare queste discrepanze senza verificare la composizione mensile effettiva.

### Implicazione per il nostro backtest
Il modello attualmente pubblicato resta un test esplorativo con HEDGE semplificato e pesi provvisori. Non va interpretato come il backtest della configurazione ufficiale 60/40. La prossima revisione del motore deve:
1. usare il catalogo USA completo (main page + sottopagine);
2. risolvere le quattro sleeve effettive senza duplicare arbitrariamente gli ETF;
3. costruire HEDGE come combinazione delle sottostrategie Treasury e GLD-USD;
4. testare il 60/40 storico e confrontarlo con eventuali pesi più recenti osservati;
5. calibrare i ranking/parametri solo su periodi di training, verificando out-of-sample e senza look-ahead.


**Dettaglio pesi HEDGE documentato nel 2020:** oltre al 60% equity / 40% HEDGE di WTOP4, l'aggiornamento del 2020 descriveva la componente HEDGE con **60% Treasury / 40% Gold**; il solo GSY poteva raggiungere il 100% della sleeve. Il paniere Treasury pubblicato era GLD, TLT, TIP e GSY, con rotazione fra i componenti. È un'architettura storicamente documentata, ma il peso effettivo corrente va ancora controllato sulle allocazioni mensili.


## Ricostruzione documentale del motore Logical Invest — 18 novembre 2026

La ricerca successiva ha individuato una descrizione storica più precisa del motore, pubblicata da Logical Invest il 20 gennaio 2019:
- lookback di 68 sedute;
- ribilanciamento mensile;
- ranking basato su modified Sharpe;
- volatility attenuator pari a 2;
- combinazione/ottimizzazione con un solver per massimizzare il modified Sharpe del portafoglio, non soltanto ordinamento indipendente dei singoli ETF.

In un commento del 2015 l'autore conferma che il calcolo veniva eseguito in QuantTrader, software proprietario C# con un solver simile a Excel Solver. Questo descrive il motore storico; non certifica che tutti i parametri siano rimasti identici nella versione 2026.

Il nostro score return / volatility² è quindi una possibile interpretazione del modified Sharpe con attenuatore 2, ma non è una formula ufficiale verificata. Il codice attuale seleziona i primi classificati per regione e non replica l'ottimizzazione congiunta storica.

Le pagine pubbliche correnti confermano i panieri regionali Developed (23 ticker), Asia (16) e South America (6). Le appartenenze ufficiali, comprese le sovrapposizioni e anomalie geografiche, sono state registrate in logical_invest_substrategy_universe.csv. Non è stata individuata una pagina corrente con la composizione della quarta sottostrategia: i candidati Africa/EMEA/frontier restano tali e non vanno promossi a universo ufficiale senza ulteriore prova.

Il rapporto completo delle evidenze, delle discrepanze e dei prossimi test è in LOGICAL_INVEST_ENGINE_RESEARCH.md.

**Regola di progetto:** mantenere intatti i backtest correnti come baseline; sviluppare il motore solver in un modulo sperimentale separato; non cambiare dashboard, pesi o strategia operativa prima della validazione.
