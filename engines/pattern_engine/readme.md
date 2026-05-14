# PATTERN ENGINE

## Historical Pattern Retrieval & Probabilistic Context Engine


# Overview

`pattern\_engine` è il modulo del progetto dedicato alla:

```
`ricerca, comparazione e contestualizzazione statistica di pattern OHLCV`
```

Il sistema nasce con un obiettivo molto preciso:

```
`trasformare il comportamento storico del mercato`

`in una struttura ricercabile, confrontabile e statisticamente analizzabile`
```

A differenza dei classici sistemi di pattern recognition “visivi” o discrezionali:

```
`Pattern Engine lavora tramite feature extraction, similarity retrieval e outcome statistics`
```

L’idea centrale del modulo è estremamente semplice:

```
`se una situazione simile è già accaduta nel passato,`

`allora possiamo studiare statisticamente cosa succedeva dopo.`
```

Il motore NON prende decisioni operative.

NON genera segnali automatici.

NON è una black-box AI.

È invece:

- deterministicamente auditabile;

- completamente interpretabile;

- statisticamente orientato;

- runtime-safe;

- costruito per essere estendibile.


# Filosofia del modulo

Il Pattern Engine è stato progettato attorno a una filosofia molto precisa:

```
`il mercato può essere trattato come una collezione di strutture ricorrenti`
```

Queste strutture vengono:

- trasformate in feature numeriche;

- normalizzate;

- confrontate;

- ricercate nello storico;

- statisticamente misurate.

Il motore quindi NON lavora su:

```
`opinioni`
```

ma su:

```
`similarità strutturale misurabile`
```


# Cosa fa realmente il Pattern Engine

Il modulo permette di:

- definire pattern OHLCV;

- confrontare finestre storiche;

- estrarre feature runtime-safe;

- calcolare similarità tra pattern;

- trovare analoghi storici;

- misurare outcome successivi;

- esportare dataset riproducibili;

- costruire retrieval probabilistici.

In pratica:

```
`il sistema prende una struttura di mercato`

`ed effettua una ricerca storica di contesti simili`
```


# Architettura generale

Il Pattern Engine è costruito come pipeline modulare.

Workflow semplificato:

```
`OHLCV bars`

`    ↓`

`Feature Extraction`

`    ↓`

`Similarity Engine`

`    ↓`

`Sliding Historical Matching`

`    ↓`

`Outcome Statistics`

`    ↓`

`Structured Export`
```

Ogni modulo è separato.

Ogni passaggio è deterministicamente verificabile.

Ogni output può essere auditato.


# Core Concepts

## 1. Feature Extraction

Il cuore reale del sistema è:

```
`la trasformazione del mercato in feature numeriche comparabili`
```

Il modulo:

```
`features/feature\_extractor.py`
```

trasforma finestre OHLCV in:

```
`feature vectors normalizzati`
```

Le feature principali includono:

- candle range;

- body size;

- upper wick;

- lower wick;

- volume behavior;

- delta behavior.


# Perché la feature extraction è così importante

Il mercato NON può essere confrontato direttamente tramite:

```
`prezzi assoluti`
```

Perché:

```
`100 ticks oggi non equivalgono a 100 ticks in un altro regime di volatilità`
```

Il motore quindi utilizza:

```
`normalizzazione relativa`
```

Questo permette di riconoscere:

```
`forme simili`
```

anche in contesti di prezzo completamente differenti.


# Price Normalization

Il sistema utilizza:

```
`PriceNormalizer`
```

per evitare che il matching dipenda:

- dal prezzo assoluto;

- dal livello del mercato;

- dal regime storico.

Modalità supportate:

```
`window\_mean\_range`

`pattern\_mean\_range`

`atr`
```

Questo permette al motore di lavorare su:

```
`strutture relative`
```

piuttosto che su:

```
`tick assoluti rigidi`
```


# Similarity Logic

## Il vero cuore matematico del motore

Il modulo:

```
`similarity/similarity\_engine.py`
```

rappresenta uno dei componenti più importanti dell’intera architettura.

Qui avviene:

```
`la misurazione quantitativa della somiglianza tra due pattern`
```


# Come funziona la similarità

Ogni pattern viene convertito in:

```
`vettore numerico`
```

Il similarity engine confronta:

```
`reference vector`

`VS`

`candidate vector`
```

tramite metriche matematiche.

Attualmente il sistema supporta:

```
`euclidean distance`

`cosine distance`
```


# Similarity Score

Il risultato finale è:

```
`similarity\_score ∈ \[0,1\]`
```

Dove:

```
`1.0  → pattern praticamente identico`

`0.0  → pattern completamente differente`
```


# Perché è importante

Questo approccio permette di superare completamente:

- pattern rigidi;

- matching discrezionale;

- configurazioni binarie;

- riconoscimento “visivo”.

Il sistema lavora invece tramite:

```
`similarità graduale`
```

che è molto più realistica nei mercati finanziari.


# Channel-Based Similarity

Il motore non confronta tutto in blocco.

Divide il pattern in:

- price channel;

- volume channel;

- delta channel.

Ogni canale:

- ha pesi dedicati;

- ha caps dedicate;

- contribuisce separatamente al punteggio finale.

Questo rende il matching:

```
`molto più controllabile e interpretabile`
```


# Sliding Matching Engine

## Historical Retrieval Engine

Il modulo:

```
`matching/sliding\_matcher.py`
```

implementa:

```
`la scansione storica delle finestre OHLCV`
```

Il sistema prende:

```
`reference pattern`
```

ed effettua:

```
`sliding window matching`
```

sull’intero dataset storico.


# Come funziona lo sliding matcher

Esempio:

```
`pattern length = 4 barre`
```

Il motore scorre:

```
`4 barre alla volta`
```

sull’intero storico.

Per ogni finestra:

```
`feature extraction`

`→ similarity computation`

`→ tolerance filtering`
```


# Perché è importante

Questo approccio permette di trasformare:

```
`dataset OHLCV storico`
```

in:

```
`database ricercabile di contesti di mercato`
```

Il modulo diventa quindi:

```
`un motore di retrieval storico`
```

più che un semplice “pattern detector”.


# Manual Template Engine

## Il nuovo percorso architetturale

Una delle evoluzioni più importanti del progetto è:

```
`manual\_template\_engine`
```

Questo percorso introduce:

```
`template-driven pattern definition`
```


# Filosofia del manual template engine

In questo approccio:

```
`l’utente descrive direttamente le candele`
```

tramite:

- body;

- wick;

- direction;

- close position;

- volume;

- delta.

Il sistema NON usa:

- feature vector globali;

- similarity vectoriale completa;

- distance engine classico.

Lavora invece tramite:

```
`scoring deterministico candle-by-candle`
```


# Perché è importante

Questo approccio è:

- molto interpretabile;

- altamente controllabile;

- intuitivo;

- leggibile;

- semplice da auditare.

È anche:

```
`molto vicino al ragionamento umano del trader discrezionale`
```


# Deterministic Candle Scoring

Il modulo:

```
`manual/manual\_template\_matcher.py`
```

trasforma ogni candela in:

```
`feature descrittive leggibili`
```

come:

- bullish/bearish;

- body ticks;

- wick size;

- close position;

- volume;

- delta.

Ogni candela riceve quindi:

```
`uno score indipendente`
```

che contribuisce al:

```
`pattern score finale`
```


# Outcome Engine

## Cosa succedeva dopo?

Il modulo:

```
`outcomes/outcome\_engine.py`
```

è responsabile della parte:

```
`probabilistica/statistica`
```

Una volta trovati i pattern simili:

```
`il sistema misura cosa accadeva successivamente`
```


# Metriche principali

Il motore calcola:

- MFE;

- MAE;

- hit rates;

- follow through;

- ATR multiples.

Questo permette di trasformare:

```
`pattern storici`
```

in:

```
`contestualizzazione statistica`
```


# Export Engine

Il modulo:

```
`export/export\_engine.py`
```

è responsabile della:

```
`riproducibilità completa dei risultati`
```

Il sistema esporta:

- matches;

- stats;

- OHLC dataset;

- config snapshot;

- schema JSON;

- manifest SHA256.


# Filosofia dell’export

L’export non è un dettaglio secondario.

È parte centrale dell’architettura.

Perché il progetto è stato costruito per essere:

- auditabile;

- versionabile;

- deterministicamente riproducibile;

- ricostruibile nel tempo.


# Bar Loader

Il modulo:

```
`bar\_loader.py`
```

rappresenta il layer di accesso ai dati.

Gestisce:

- validazione schema;

- timezone;

- OHLC sanity;

- duplicate timestamps;

- data source abstraction.


# Filosofia del loader

Il Pattern Engine NON crea nuovi formati dati.

Si integra invece con:

```
`central market data pipeline`
```

oppure:

```
`raw txt datasets`
```

in modalità development.


# Determinismo e Auditabilità

Una caratteristica fondamentale del progetto è:

```
`la riproducibilità deterministica`
```

Il motore cerca di mantenere:

- stessi input;

- stessi output;

- stessi score;

- stessi export.

Questo è fondamentale per:

- studio futuro;

- validazione;

- auditing;

- ricerca quantitativa.


# Filosofia Generale del Sistema

Il Pattern Engine NON cerca di prevedere il futuro.

Cerca invece di:

```
`contestualizzare statisticamente il presente`
```

Questa differenza è molto importante.

Il sistema non lavora su:

```
`predizione magica`
```

ma su:

```
`analogia storica misurabile`
```


# Evoluzioni Future

## Live Runtime Pattern Retrieval

Una delle evoluzioni più importanti già previste è:

```
`live retrieval engine`
```


# L’idea

Invece di:

```
`cercare pattern statici nello storico`
```

il sistema potrebbe:

```
`prendere le ultime N barre live`
```

trasformarle automaticamente in:

```
`runtime pattern`
```

ed effettuare:

```
`ricerca storica realtime`
```


# Workflow futuro possibile

```
`live bars`

`→ runtime feature extraction`

`→ similarity retrieval`

`→ historical analog search`

`→ live probabilistic statistics`
```


# Perché l’architettura attuale è già compatibile

Molti componenti esistenti sono già:

```
`runtime-safe`
```

In particolare:

- feature extraction;

- similarity engine;

- outcome engine;

- sliding matcher.

Il vero cambiamento futuro diventerebbe:

```
`chi genera il pattern`
```


# Prima

```
`utente definisce pattern`
```


# Dopo

```
`mercato live genera pattern runtime`
```


# Closed-Bar Runtime Philosophy

La prima implementazione live prevista è:

```
`closed-bar mode`
```

ovvero:

```
`analisi solo a chiusura candela`
```

Questo approccio è preferibile rispetto al tick-by-tick perché:

- evita repaint;

- mantiene stabilità feature;

- mantiene determinismo;

- riduce rumore runtime;

- semplifica la similarity logic.


# Possibili evoluzioni avanzate

Futuri sviluppi potrebbero includere:

- realtime retrieval;

- vector indexing;

- ANN search;

- live similarity dashboard;

- probabilistic live context;

- multi-pattern retrieval;

- orderflow runtime analysis;

- microstructure patterning.


# Stato attuale del progetto

Attualmente il modulo è già:

- architetturalmente modulare;

- altamente estendibile;

- runtime-oriented;

- deterministicamente auditabile;

- coerente con il resto del progetto.


# Conclusione

`pattern\_engine` rappresenta uno dei moduli più avanzati dell’intero ecosistema.

Perché unisce:

- pattern recognition;

- feature engineering;

- statistical retrieval;

- similarity analysis;

- probabilistic contextualization.

in un’unica pipeline coerente.

L’aspetto più importante è che:

```
`non lavora come un indicatore rigido`
```

ma come:

```
`motore di analogia storica quantitativa`
```

capace di trasformare:

```
`strutture di mercato`
```

in:

```
`contesto statistico interpretabile`
```

mantenendo:

- trasparenza;

- auditabilità;

- modularità;

- coerenza architetturale.

Questo rende il Pattern Engine:

```
`non solo un modulo di pattern matching`
```

ma:

```
`una vera infrastruttura di ricerca probabilistica sui comportamenti storici del mercato`
```

