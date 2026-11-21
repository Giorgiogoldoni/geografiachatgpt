# Universo ETF storico per test crisi 2007-2009

Aggiornamento: 21 novembre 2026.

## Obiettivo e separazione dei campioni

Il test storico della crisi 2007-2009 usa un campione dedicato di ETF azionari geografici quotati negli Stati Uniti, con data di lancio anteriore al 2007 e prezzi adjusted giornalieri reali. Sono ETF effettivamente negoziati, non indici ricostruiti; tuttavia **non sono le classi UCITS europee** del radar operativo. Sono proxy geografici storici, scelti perché le serie UCITS attualmente scaricate dal registro non arrivano al 2005-2006.

Il campione operativo UCITS resta separato e non viene modificato da questo test. I risultati storici non vanno trasferiti automaticamente ai ticker UCITS o a un portafoglio in EUR.

## Universo storico selezionato

File sorgente: `data/historical_country_etfs_2007.csv`.

Sono stati selezionati ETF iShares country-specific con lunga storia, più SPY come mercato USA:

| Ticker | Area | ETF | Lancio |
|---|---|---|---:|
| SPY | Stati Uniti | SPDR S&P 500 ETF Trust | 1993 |
| EWA | Australia | iShares MSCI Australia | 1996 |
| EWC | Canada | iShares MSCI Canada | 1996 |
| EWD | Svezia | iShares MSCI Sweden | 1996 |
| EWG | Germania | iShares MSCI Germany | 1996 |
| EWH | Hong Kong | iShares MSCI Hong Kong | 1996 |
| EWI | Italia | iShares MSCI Italy | 1996 |
| EWJ | Giappone | iShares MSCI Japan | 1996 |
| EWL | Svizzera | iShares MSCI Switzerland | 1996 |
| EWM | Malaysia | iShares MSCI Malaysia | 1996 |
| EWN | Paesi Bassi | iShares MSCI Netherlands | 1996 |
| EWO | Austria | iShares MSCI Austria | 1996 |
| EWP | Spagna | iShares MSCI Spain | 1996 |
| EWQ | Francia | iShares MSCI France | 1996 |
| EWS | Singapore | iShares MSCI Singapore | 1996 |
| EWU | Regno Unito | iShares MSCI United Kingdom | 1996 |
| EWW | Messico | iShares MSCI Mexico | 1996 |
| EWK | Belgio | iShares MSCI Belgium | 1996 |
| EWT | Taiwan | iShares MSCI Taiwan | 2000 |
| EWY | Corea del Sud | iShares MSCI South Korea | 2000 |
| EWZ | Brasile | iShares MSCI Brazil | 2000 |
| FXI | Cina | iShares China Large-Cap | 2004 |

Le date di lancio sono documentate nel catalogo ufficiale iShares/BlackRock (product list, sezione international ETFs): https://www.blackrock.com/it/consulenti/literature/brochure/ishares-product-list-en-us.pdf. Il file CSV conserva simbolo, area, nome, data di lancio e mercato di quotazione.

## Regole di ammissione e controlli

1. Download giornaliero adjusted da Yahoo Finance a partire dal 2005-01-01.
2. Nessun prezzo viene inventato prima della data di effettiva disponibilità del fondo.
3. Ogni ticker viene riportato con prima/ultima data osservata, numero di sedute e stato del download nel JSON.
4. Il fondo entra nel ranking soltanto dopo che gli indicatori richiesti sono calcolabili; le geografie non ancora quotate non vengono retrodatate.
5. Il modello può usare come training le osservazioni pre-2007, ma genera risultati OOS soltanto dal 2007-01 in avanti.
6. Il modello Ridge usa solo etichette a 21 sedute già maturate alla data della previsione.
7. La selezione nested Top 3 usa soltanto i rendimenti dei mesi precedenti il cui orizzonte a 21 sedute è già maturato; i rendimenti sovrapposti non vengono anticipati nella selezione.

## Interpretazione e limiti

- Le quote sono ETF reali, ma il campione è US-listed e i prezzi sono in USD. Il test misura quindi rendimenti total-return in USD (secondo l'aggiustamento del provider), non la performance di un investitore EUR al netto del cambio.
- Il campione è composto da ETF sopravvissuti e presenta survivorship bias; non include tutti i fondi chiusi o liquidati prima del 2026.
- La selezione dei fondi usa la storia di lancio e non prova che ogni fondo fosse già accessibile a ogni investitore europeo.
- Il campione non è un universo investibile UCITS del 2007 e non deve essere mescolato con il radar corrente.
- I risultati sono lordi: costi, spread, imposte, commissioni, slippage e fiscalità non sono inclusi.
- Le performance mensili forward a 21 sedute si sovrappongono; le statistiche HAC e il confronto con ROC21/equal-weight sono necessari per evitare conclusioni basate soltanto sul CAGR.

## Precedente limite del campione UCITS

Il test del run 44871424936 aveva richiesto il 2007 ma il primo mese out-of-sample era 2010-05: la serie prezzi del registro UCITS corrente cominciava troppo tardi per addestrare il modello nel 2005-2006. Quel run non costituisce un test della crisi 2007-2009.

## Esito del nuovo test

Il nuovo workflow aggiunge un campo separato `historical_etf_crisis_test` in `radar-predittivo.json`. Il risultato sarà considerato valido solo se:
- la copertura mostra un numero sufficiente di ETF con prezzi effettivi prima del 2007;
- il primo mese OOS è 2007 (o il primo mese successivo in cui sono soddisfatti i minimi predefiniti, dichiarato esplicitamente);
- i mesi 2007-2009 sono effettivamente presenti;
- il confronto Top 3 vs ROC21 ed equal-weight è riportato separatamente dal test UCITS operativo.

