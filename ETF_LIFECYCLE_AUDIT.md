# ETF Lifecycle Registry — audit iniziale (19 novembre 2026)

## Scopo
Separare quattro concetti che non vanno confusi:
- **Data di lancio del fondo**: inizio vita del fondo.
- **Data di lancio della classe**: nascita della specifica share class; da completare quando distinta.
- **Data di quotazione**: avvio delle negoziazioni su una determinata Borsa.
- **Prima osservazione prezzi**: primo dato storico restituito dal provider per il simbolo Yahoo Finance utilizzato.

Il campo prima osservazione prezzi è calcolato dal motore. Non viene mai usato come sostituto della data di lancio.

## Date verificate in questa prima passata

| ISIN | Fondo | Data lancio fondo | Fonte |
|---|---|---:|---|
| IE00BHZRQZ17 | Franklin FTSE India UCITS ETF | 25/06/2019 | Franklin Templeton |
| IE00BHZRR030 | Franklin FTSE Korea UCITS ETF | 04/06/2019 | Franklin Templeton |
| IE00B27YCK28 | iShares MSCI EM Latin America UCITS ETF | 15/10/2007 | justETF |
| IE00BP3QZ601 | iShares Edge MSCI World Quality Factor UCITS ETF | 03/10/2014 | justETF |
| IE00BQN1K562 | iShares Edge MSCI Europe Quality Factor UCITS ETF | 16/01/2015 | justETF |

## Date di quotazione verificate

Borsa Italiana ha pubblicato l'avvio delle negoziazioni, dal **16/02/2015**, per gli otto ETF factor iShares con ISIN:
IE00BP3QZ601, IE00BP3QZ825, IE00BP3QZB59, IE00BP3QZD73, IE00BQN1K562, IE00BQN1K786, IE00BQN1K901 e IE00BQN1KC32.

Questa è una data di quotazione su Borsa Italiana, non la data di nascita del fondo. Per i primi due ETF con data di lancio verificata sopra, la distinzione è esplicita.

## Fonti
- Franklin Templeton, schede ETF e date di lancio: https://www.franklintempleton.it/prodotti/i-nostri-etf
- justETF, ISIN IE00B27YCK28: https://www.justetf.com/it/etf-profile.html?isin=IE00B27YCK28
- justETF, ISIN IE00BP3QZ601: https://www.justetf.com/it/etf-profile.html?isin=IE00BP3QZ601
- justETF, ISIN IE00BQN1K562: https://www.justetf.com/en-it/etf-profile.html?isin=IE00BQN1K562
- Borsa Italiana, avvio negoziazioni 16/02/2015: https://www.borsaitaliana.it/etf/notiziedettaglio/12etfstyleishares.htm

## Regole per il backtest
1. Mai generare prezzi prima della prima osservazione effettiva.
2. Mai retrodatare la storia al lancio del fondo se la serie prezzi utilizzata inizia più tardi.
3. Per ogni data di segnale, ammettere lo strumento solo se esiste storia sufficiente fino a quel giorno.
4. Se la data di lancio è sconosciuta, usare la prima osservazione prezzi come limite prudenziale per la disponibilità storica, ma etichettarla come proxy, non come data di lancio.
5. Gli ETF delistati/chiusi devono essere ricostruiti separatamente per ridurre il survivorship bias.

## Stato e limiti
Questa è una prima tranche verificata, non il censimento completo. I campi non documentati restano vuoti. Il CSV viene aggiornato dal motore e include anche strumenti privi di ISIN verificato, per consentire il lavoro di riconciliazione. La data Yahoo può dipendere dalla quotazione scelta, dal cambio ticker e dalla disponibilità del provider.
