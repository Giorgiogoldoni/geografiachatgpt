# World Top 4 — metodo e registro holdings

## Obiettivo
Ricostruire una strategia momentum geografica ispirata alle informazioni pubbliche di Logical Invest, senza affermare di replicarne il codice proprietario.

## Struttura
- Quattro gruppi regionali: Developed, Asia, South America e Africa & Middle East. Il quarto gruppo è un'aggregazione di ricerca: le fonti pubbliche reperite confermano almeno Developed, Asia e South America, ma non consentono di attribuire con certezza tutti i ticker alle quattro sleeve correnti.
- Lookback primario: 68 sedute di borsa.
- Tre varianti confrontate: rendimento 68 sedute, rendimento/volatilità annualizzata al quadrato (proxy Sharpe modificato), composito momentum 3/6/12 mesi.
- Ribilanciamento mensile: il segnale usa la chiusura del mese precedente; il rendimento viene misurato nel mese successivo.
- Sleeve hedge di test: 20% ripartito tra i due migliori tra GLD, TLT, IEF, SHY. È una convenzione di test, non un peso attribuito a Logical Invest.
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
