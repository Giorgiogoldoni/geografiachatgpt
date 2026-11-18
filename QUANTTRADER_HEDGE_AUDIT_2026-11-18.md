# Audit approfondito QuantTrader e HEDGE — 18 novembre 2026

## Scopo e conclusione

Questa nota integra la ricostruzione di World Top 4 con il manuale ufficiale QuantTrader e la documentazione Logical Invest sulle sottostrategie HEDGE.

**Risultato:** abbiamo ora una descrizione tecnica pubblica del motore storico molto più precisa. Non abbiamo però le impostazioni effettivamente associate alla strategia WTOP4 nel 2026, né i pesi mensili completi dei moduli HEDGE. Non modificare ancora i motori operativi o le baseline.

## 1. Manuale QuantTrader: formula e ottimizzazione

Il manuale ufficiale QuantTrader (PDF, edizione 2016) documenta:

- Modified Sharpe: media dei rendimenti giornalieri divisa per la deviazione standard giornaliera elevata al fattore di volatilità f;
- nessun risk-free rate nella formula di ranking;
- f=1 equivale allo Sharpe ordinario; valori superiori a 1 attribuiscono più importanza alla volatilità; f=2 è quindi coerente con la formula storica riferita nell'articolo World Country ETF Rotation;
- il numero di sedute di lookback e il periodo di ribilanciamento sono parametri configurabili;
- ribilanciamento mensile a fine mese indicato come sufficiente per strategie standard.

Il manuale descrive diverse logiche di ranking/allocazione, che non sono intercambiabili:

1. **NO (No Ranking):** assegna inizialmente pesi uguali agli strumenti equity; successivamente aggiunge il Treasury e ne ottimizza il peso per massimizzare il Modified Sharpe del portafoglio.
2. **SR (Static Ranking):** ottimizza in un unico passaggio le allocazioni di tutti i componenti per massimizzare il Modified Sharpe del portafoglio.
3. **DR (Dynamic Ranking):** confronta ciascun ETF equity con lo strumento hedge finale (normalmente un Treasury), valuta le combinazioni e tiene conto della correlazione incrociata; poi ottimizza il peso del Treasury sul portafoglio complessivo.
4. **SRE:** come SR, ma con pesi uguali fra gli ETF.
5. **DRE:** come DR, ma gli ETF equity hanno pesi uguali e varia il peso dell'hedge.

Sono inoltre documentati:
- Top-N: numero di componenti ammessi dopo il ranking;
- pesi minimi e massimi per componente;
- limite di volatilità, che può lasciare una quota in cash;
- Mean Reversion Weight/Period, che modifica il ranking aggiungendo il rendimento di breve periodo;
- Smoothing Weight e Rebalance Strength, che riducono l'ampiezza dei cambi di peso;
- Volatility Multiplier per modificare la volatilità percepita di un singolo strumento;
- Trading Delay e Trading Costs.

**Impatto sulla nostra implementazione:** il solver a griglia 5% è una buona prova trasparente, ma non è ancora una ricostruzione del set-up WTOP4. Per avvicinarci al motore storico dobbiamo conoscere almeno Ranking Logic (NO/SR/DR/SRE/DRE), Top-N, limiti min/max, eventuali volatility limit, smoothing e rebalance strength. Non è corretto scegliere questi parametri in base al risultato migliore del backtest.

Fonte primaria: https://logical-invest.com/wp-content/uploads/2016/10/QuantTraderHelp.pdf

## 2. HEDGE: architettura confermata

La newsletter Logical Invest di aprile 2022 descrive esplicitamente la costruzione:

- **Gold-Currency Strategy II (GLD-UUP):** gestisce l'allocazione fra oro e un fondo monetario/short-term market fund GSY; può arrivare al 100% in oro, al 100% in GSY o a pesi intermedi.
- **Treasury Hedge (TRESHEDGE):** seleziona/combina Treasury a lunga durata TLT, Treasury inflation-protected TIP e fondo monetario GSY.
- **HEDGE:** alloca fra le due sottostrategie in funzione delle condizioni di mercato.

La pagina HEDGE corrente (7 ottobre 2026) conferma i due blocchi Treasury e GLD-USD. La pagina Gold-Currency Strategy II corrente (12 ottobre 2026) descrive la selezione fra oro e dollaro sulla base della performance recente corretta per il rischio. La pagina Treasury Hedge (24 giugno 2026) è accessibile, ma i dettagli delle allocazioni sono premium e ritardati di un mese.

**Precisazione importante:** il nome GLD-UUP non autorizza a codificare una semplice alternanza GLD contro UUP. La documentazione del 2022 descrive GLD/GSY per la versione Gold-Currency Strategy II disponibile allora; la pagina attuale parla di oro e dollaro USA. La newsletter del 2022 documenta anche che i pesi possono essere intermedi. Occorre quindi verificare holdings effettive per data, non dedurre il paniere dal nome.

Fonti:
- HEDGE: https://logical-invest.com/app/strategy/HEDGE
- Gold-Currency Strategy II: https://logical-invest.com/app/strategy/GLD-UUP
- Treasury Hedge: https://logical-invest.com/app/strategy.php?symbol=TRESHEDGE
- Newsletter aprile 2022: https://logical-invest.com/the-logical-invest-newsletter-for-april-2022/

## 3. Cosa non è ancora noto

Non abbiamo prove pubbliche sufficienti per fissare:
- i pesi correnti di HEDGE fra Treasury Hedge e Gold-Currency Strategy II;
- i pesi mensili interni di TRESHEDGE e GLD-UUP;
- la formula/parametri correnti di ranking delle due sottostrategie;
- se i parametri QuantTrader 2016 e quelli dell'articolo WTOP4 2019 siano rimasti invariati nel 2026;
- la quarta sleeve geografica WTOP4 e la sua lista ufficiale di ticker.

Il 60% equity / 40% HEDGE e il rapporto interno 60% Treasury / 40% Gold sono riferimenti storici documentati in aggiornamenti precedenti, non pesi live confermati per novembre 2026.

## 4. Implicazioni per il codice

Non sostituire il modello pubblicato. Preparare in seguito un modulo sperimentale separato con:
- score Modified Sharpe parametrico e annualizzazione dichiarata;
- ranking logic selezionabile (NO, SR, DR, SRE, DRE);
- vincoli Top-N, min/max, volatility limit e smoothing configurabili;
- modulo Treasury Hedge separato;
- modulo Gold-Currency separato;
- livello HEDGE che combina le due sottostrategie;
- log mensile di score, correlazioni, pesi e strumenti selezionati.

Tutti i parametri non ricavati da fonti o holdings ufficiali devono essere etichettati come ipotesi. Evitare ottimizzazione retrospettiva sull'intero campione: usare training, validazione e out-of-sample walk-forward.

## 5. Evidenza necessaria per chiudere la ricostruzione

La priorità è ottenere gli export QuantTrader o gli snapshot premium Logical Invest. Per ogni data servono:
- data di pubblicazione e mese effettivo;
- nome della strategia/sottostrategia;
- ticker e peso;
- eventuali dati sintetici o estensioni storiche;
- fonte e schermata/export originale.

Un export QuantTrader con parametri WTOP4 sarebbe particolarmente utile: consentirebbe di verificare Ranking Logic, lookback, volatility attenuator, Top-N, limiti e pesi. In assenza di questi dati possiamo sviluppare test di sensibilità, ma non chiamarli replica ufficiale.

## Stato finale

- **Verificato da documentazione ufficiale:** formula Modified Sharpe parametrica; logiche NO/SR/DR/SRE/DRE; ruolo di Treasury e Gold-Currency nella struttura HEDGE.
- **Confermato ma incompleto:** architettura a due moduli di HEDGE; universo principale WTOP4; tre pagine regionali pubbliche.
- **Non verificato:** settaggi QuantTrader effettivi WTOP4 2026, pesi HEDGE correnti, quarta sleeve e holdings storiche mensili.
- **Decisione:** nessuna modifica al motore operativo o alla dashboard finché non arrivano dati di configurazione/holdings che permettano una validazione senza look-ahead.
