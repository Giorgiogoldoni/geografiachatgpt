# World Top 4 — adattamento operativo agli ETF UCITS europei

**Versione:** 18 novembre 2026  
**Obiettivo:** avvicinare le scelte geografiche di Logical Invest World Top 4 usando strumenti UCITS negoziabili in Europa. Non è obiettivo replicare i ticker USA, il codice QuantTrader o i pesi proprietari.

## 1. Principio guida

La strategia va valutata sulla qualità delle scelte geografiche e sulla disciplina di rotazione, non sulla corrispondenza letterale dei ticker.

Un ETF USA come EWY può essere sostituito da un UCITS che replica lo stesso Paese o un indice molto vicino. La sostituzione va registrata per:
- Paese/mercato e indice sottostante;
- ISIN del fondo UCITS;
- ticker della specifica quotazione usata;
- valuta di negoziazione e valuta base;
- politica di distribuzione;
- TER, dimensione del fondo e liquidità;
- data di lancio e disponibilità della serie storica;
- eventuale differenza fra benchmark originale e benchmark sostitutivo.

Non usare il ticker primario del fondo come se fosse universale: lo stesso ISIN può avere ticker differenti su Borsa Italiana, Xetra, Euronext e LSE. Il motore deve identificare il fondo tramite ISIN e la serie prezzi tramite una quotazione precisa.

## 2. Architettura geografica di lavoro

Le quattro aree saranno una nostra classificazione operativa, non una dichiarazione sulle quattro sleeve proprietarie di Logical Invest:

1. **Developed Markets:** Europa sviluppata, Nord America, Giappone e Australia.
2. **Asia-Pacifico emergente:** Cina, India, Corea del Sud, Taiwan, Indonesia, Thailandia, Malesia, Filippine e Vietnam, dove esistono strumenti UCITS idonei.
3. **America Latina:** Brasile, Messico, Cile, Perù e Colombia, secondo disponibilità e liquidità degli ETF UCITS.
4. **Africa / Medio Oriente / Frontier:** Sudafrica, Turchia, Israele, paesi del Golfo e mercati frontier, solo quando esistono strumenti sufficientemente liquidi e dati storici affidabili.

Questa suddivisione è deliberatamente trasparente e modificabile. Evitare di forzare un ETF in un'area solo per far quadrare quattro gruppi: in mancanza di strumenti adeguati, la sleeve può restare in liquidità o essere esclusa dal test.

## 3. Registro iniziale degli ETF

Il file `ucits_country_universe_seed_2026-11-18.csv` contiene i primi candidati identificati con ISIN e fonti. È uno **starter universe**, non una lista completa né una raccomandazione d'acquisto.

Prima dell'inclusione definitiva ogni fondo deve superare:
- verifica UCITS e disponibilità per investitori retail UE;
- verifica della quotazione effettivamente utilizzabile, preferibilmente Borsa Italiana o Xetra;
- controllo della storia prezzi, dividendi e corporate actions;
- controllo di AUM, spread e volumi;
- controllo del benchmark e della sovrapposizione con gli altri ETF;
- controllo che la serie sia in EUR o che il trattamento valutario sia coerente.

Preferire un solo ETF rappresentativo per Paese. Se esistono più fondi sullo stesso indice, selezionare il più adatto sulla base di liquidità, dimensione, costi, storia e qualità dei dati, non in base al rendimento futuro.

## 4. Motore di selezione: vicinanza metodologica, non clonazione

Configurazione iniziale da testare:
- ribilanciamento mensile;
- finestra principale di 68 sedute;
- Modified Sharpe candidato: media rendimenti giornalieri / deviazione standard giornaliera elevata al quadrato;
- confronto con momentum 3, 6 e 12 mesi e con rendimento corretto per volatilità;
- selezione del migliore Paese in ogni sleeve, solo se il punteggio supera un filtro di trend/absolute momentum;
- pesi iniziali semplici e robusti, poi confronto con ottimizzazione a livello di portafoglio che considera correlazioni e limiti di concentrazione.

La formula Modified Sharpe con attenuatore 2 è un riferimento storico documentato, ma non dimostra che la versione corrente WTOP4 utilizzi ancora esattamente gli stessi parametri. Le varianti vanno confrontate out-of-sample, senza scegliere a posteriori quella che ha il CAGR migliore sull'intero storico.

## 5. Componente difensiva europea

Costruire una sleeve difensiva distinta, con strumenti UCITS europei e serie total-return coerenti:
- governativi Euro a breve durata / overnight per liquidità;
- governativi Euro o globali coperti EUR per duration;
- inflation-linked se disponibili e coerenti;
- oro fisico UCITS/ETC ammesso dal mandato e dalla struttura fiscale del conto.

Non presumere che un ETF obbligazionario europeo sia equivalente a TLT, TIP o GSY. Durata, rischio tasso, valuta, copertura e struttura legale possono essere molto diversi. Non presumere nemmeno che l'oro ETC sia un UCITS ETF: classificazione e trattamento vanno registrati separatamente.

Il 60% equity / 40% hedge e il rapporto 60/40 Treasury/Oro sono riferimenti storici Logical Invest, non pesi correnti dimostrati. Nel modello europeo saranno scenari da testare, insieme a varianti meno difensive, senza fissare il peso prima dei risultati.

## 6. Valutazione corretta

Il confronto con World Top 4 dovrà concentrarsi su:
- Paese/area selezionata e stabilità della leadership;
- frequenza di rotazione e turnover;
- rendimento relativo e drawdown;
- esposizione valutaria e costi;
- comportamento nelle fasi risk-on e risk-off;
- differenza fra scelta geografica e scelta del singolo ETF.

Quando disponibili, holdings pubblicati da Logical Invest saranno un benchmark qualitativo con un mese di ritardo, non un target da copiare retroattivamente. Ogni confronto deve rispettare publication date ed effective month.

## 7. Roadmap

1. Completare il catalogo UCITS per i Paesi del master universe WTOP4.
2. Verificare quotazioni, ISIN, valuta e qualità delle serie prezzi.
3. Creare un mapping trasparente fra ETF USA Logical Invest e sostituto UCITS.
4. Testare la selezione geografica su dati total-return e valute coerenti.
5. Costruire la componente difensiva con strumenti europei.
6. Eseguire confronti walk-forward e analisi di sensibilità.
7. Solo dopo validazione, collegare il modello alla dashboard operativa.

## Decisione di progetto

Da questa versione in avanti il risultato principale sarà una **strategia geografica UCITS ispirata a Logical Invest**, non una replica USA della strategia proprietaria. I ticker USA restano un riferimento per confrontare la scelta del mercato; i segnali e i portafogli operativi saranno generati esclusivamente dall'universo europeo verificato.
