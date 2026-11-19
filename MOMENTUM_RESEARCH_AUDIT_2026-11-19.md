# Audit e ricerca Momentum — 19 novembre 2026

## Stato
- Motore quantitativo eseguito con successo in GitHub Actions: run 44531084098.
- Output aggiornato in `geografia-motore.json`.
- Pagina motore aggiornata per mostrare la nuova ricerca comparativa.
- Il ranking geografico operativo non viene modificato.

## Correzioni metodologiche implementate
1. Segnale calcolato usando solo prezzi disponibili fino alla chiusura del mese precedente; rendimento detenuto nel mese successivo.
2. Universo candidato filtrato con almeno 253 osservazioni storiche alla data del segnale.
3. Prezzi mensili calcolati per singolo ETF, evitando di richiedere una quotazione nello stesso identico giorno di calendario a tutti gli strumenti.
4. Tre filtri separati: momentum puro; momentum + SMA200; momentum + SMA200 + momentum assoluto 12 mesi positivo.
5. Quattro schemi di punteggio: solo 12 mesi, 40/30/20/10, 35/30/20/15, 30/30/20/20.
6. Finestre 1, 3, 5 e 10 anni; CAGR, volatilità, massimo drawdown, turnover e sensibilità ai costi (0/5/10/15 bps per lato).
7. Benchmark globale WRD.PA riportato separatamente.

## Lettura dei risultati correnti
Con pesi 40/30/20/10:
- Momentum puro, 5 anni: CAGR lordo 11,99%; CAGR con 10 bps per lato 11,30%; volatilità 11,83%; max drawdown -10,05%; turnover mensile medio 25,69%.
- Momentum puro, 10 anni: CAGR lordo 9,83%; CAGR con 10 bps per lato 9,27%; volatilità 12,29%; max drawdown -22,08%; turnover 21,32%.
- Momentum + SMA200 + momentum assoluto, 5 anni: CAGR lordo 8,39%; netto costi ipotetici 7,65%; volatilità 9,72%; max drawdown -12,37%; turnover 28,33%.
- Momentum + SMA200 + momentum assoluto, 10 anni: CAGR lordo 5,85%; netto costi ipotetici 5,12%; volatilità 8,46%; max drawdown -15,90%; turnover 28,82%.

Benchmark WRD.PA:
- 5 anni: CAGR 11,40%; volatilità 13,08%; max drawdown -14,19%.
- 10 anni: CAGR 12,95%; volatilità 13,16%; max drawdown -18,69%.

Aumentare il peso a 1 mese non migliora il risultato in questa simulazione: con momentum puro e 40/30/20/10 il CAGR netto è 11,30% a 5 anni e 9,27% a 10 anni; con 35/30/20/15 scende a 11,04% e 8,93%; con 30/30/20/20 scende a 10,43% e 8,60%. Il turnover cresce.

## Conclusione provvisoria
- Non aumentare il peso a 1 mese: mantenere 40/30/20/10 come configurazione di riferimento per la ricerca.
- Il filtro SMA200 riduce volatilità e drawdown in alcuni periodi, ma in questo test penalizza sensibilmente il CAGR. Va valutato come controllo del rischio, non come miglioratore automatico del rendimento.
- Non promuovere ancora nessuna configurazione a strategia operativa definitiva.

## Limiti residui da risolvere prima di una validazione robusta
- Survivorship bias: l'universo di partenza è quello degli ETF attualmente presenti nell'indice; gli ETF delistati o liquidati non sono ricostruiti.
- Valuta: i rendimenti sono nella valuta della quotazione Yahoo e non sono tutti convertiti in EUR; il confronto con WRD.PA non è quindi perfettamente omogeneo.
- Costi: la sensibilità applica una stima fissa per lato, non spread storici effettivi, commissioni reali, imposte o slippage variabile.
- Prezzi mancanti all'uscita: l'episodio è contato a rendimento zero e segnalato; non equivale a ricostruire un evento di delisting.
- Yahoo auto_adjust è una proxy e non sostituisce NAV ufficiali o total-return certificati dagli emittenti.
- Il numero di mesi disponibile è riportato per ogni finestra: una finestra più corta dello storico richiesto non va letta come un periodo completo.

## Decisione
Ricerca aggiornata e visibile nel motore. Mantenere i pesi operativi e completare in una fase successiva la normalizzazione EUR e la ricostruzione dell'universo storico, inclusi fondi cessati.
