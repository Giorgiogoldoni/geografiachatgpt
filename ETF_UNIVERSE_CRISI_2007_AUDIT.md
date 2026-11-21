# Universo ETF storico per test crisi 2007-2009

Aggiornamento: 21 novembre 2026.

## Criterio

Per il backtest si distingue fra:
- data di lancio del fondo/classe;
- prima osservazione effettiva della serie prezzi usata dal motore;
- data da cui lo strumento può entrare nel ranking point-in-time.

La data di lancio da sola non autorizza a ricostruire prezzi precedenti alla prima osservazione disponibile. Le serie devono essere scaricate e verificate prima del calcolo. Nessun ETF viene retrodatato.

## Shortlist storica verificata nel registro corrente

| Simbolo dati | ISIN | ETF / esposizione | Lancio fondo | Prima osservazione prezzi registrata | Esito |
|---|---|---|---:|---:|---|
| EXS1.DE | DE0005933931 | iShares Core DAX / Germania | 27/12/2000 | 02/01/2008 | Selezionato dal primo prezzo effettivo |
| DJE.PA | FR0007056841 | Amundi Dow Jones Industrial Average / USA | 04/04/2001 | 02/01/2008 | Selezionato dal primo prezzo effettivo |
| IAEX.AS | IE00B0M62Y33 | iShares AEX / Paesi Bassi | 18/11/2005 | 02/01/2008 | Selezionato dal primo prezzo effettivo |
| IBZL.MI | IE00B0M63516 | iShares MSCI Brazil / Brasile | 18/11/2005 | 02/01/2008 | Selezionato dal primo prezzo effettivo |
| IAPD.MI | IE00B14X4T88 | iShares Asia Pacific Dividend / Asia-Pacifico | 02/06/2006 | 02/01/2008 | Selezionato dal primo prezzo effettivo |
| IQQ5.DE | IE00B1FZS574 | iShares MSCI Turkey / Turchia | 03/11/2006 | 22/12/2008 | Selezionato dal primo prezzo effettivo; entra più tardi |
| XSMI.MI | LU0274221281 | Xtrackers Switzerland / Svizzera | 22/01/2007 | 02/01/2008 | Selezionato dal primo prezzo effettivo |
| IMIB.MI | IE00B1XNH568 | iShares FTSE MIB / Italia | 06/07/2007 | 02/01/2008 | Selezionato dal primo prezzo effettivo |
| LTAM.MI | IE00B27YCK28 | iShares MSCI EM Latin America / America Latina | 15/10/2007 | 18/03/2008 | Selezionato dal primo prezzo effettivo; entra più tardi |

Le date di lancio sono quelle del registro ETF_LIFECYCLE_AUDIT.md; le prime osservazioni sono quelle restituite dal download prezzi del motore e conservate in etf_lifecycle_registry.csv.

## Esclusioni e cautele

- C40.PA non viene incluso nella shortlist principale: la prima NAV del fondo è del 2003, ma la classe oggi identificata è stata creata nel 2018. Non si deve confondere la storia del fondo con quella della classe.
- I fondi factor momentum, quality e value disponibili nell'universo attuale sono nati dal 2014 in avanti. Entrano soltanto nel test dal momento in cui esistono; non sono utilizzabili per una selezione nel 2007.
- Gli ETF lanciati dopo il 2007 possono entrare nel ranking solo dalla loro prima osservazione effettiva.
- Questa shortlist è una base storica più pulita, ma non elimina il survivorship bias: include fondi sopravvissuti e presenti nel registro corrente.

## Limite decisivo per il test 2007

Nel registro attuale, la prima osservazione prezzi dei candidati più vecchi è il 2 gennaio 2008, non il 2005-2006. Di conseguenza non esistono, in questa fonte prezzi, osservazioni ETF effettive sufficienti per addestrare il modello nel 2005-2006 e iniziare un walk-forward nel 2007.

Il run 44871424936 ha infatti richiesto il 2007 ma ha prodotto il primo mese out-of-sample in 2010-05 (197 mesi fino a 2026-09). Non va descritto come test della crisi 2007-2009.

## Prossimo passaggio tecnico

1. Mantenere questi ETF come shortlist UCITS/ETF storici.
2. Cercare una fonte storica alternativa per le quotazioni effettive 2005-2007 (preferibilmente NAV/total-return ufficiali o dati di borsa).
3. Verificare per ogni ISIN la data iniziale e la continuità, prima di usare la serie.
4. Se i dati 2005-2007 non sono recuperabili, eseguire un test distinto su indici/proxy e mantenerlo chiaramente separato dal test ETF.
