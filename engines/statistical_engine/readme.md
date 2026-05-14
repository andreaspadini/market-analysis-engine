# 📘 Statistical Engine

## Pipeline di Arricchimento Quantitativo per Eventi di Market Structure

Lo `statistical\_engine` rappresenta il layer di interpretazione quantitativa dell’intero progetto.

Mentre il ROOT engine ha il compito di individuare e strutturare gli eventi di mercato:

- balance

- breakout

- follow-through

- contesto strutturale

…lo statistical engine trasforma questi eventi in un dataset completamente arricchito dal punto di vista analitico.

Riceve eventi breakout “raw” e li converte progressivamente in:

- feature statistiche

- rapporti contestuali

- classificazioni di stato del mercato

- target quantitativi

- segmentazione temporale

- distribuzioni

- dataset parquet pronti per ricerca e aggregazioni

In termini semplici:

ROOT risponde alla domanda:

> “È avvenuto un breakout.”

STATISTICAL prova invece a rispondere a domande molto più profonde:

> “Che tipo di breakout era?”  
“Quanto era forte?”  
“Quanto era compresso il mercato?”  
“Il movimento ha davvero funzionato?”  
“Il movimento era pulito o instabile?”  
“In quali condizioni questi breakout funzionano meglio?”


# 🔹 Filosofia del Modulo

Lo statistical engine NON è un generatore di segnali.

Non:

- apre trade

- decide ingressi

- esegue strategie

- produce operatività

Il suo ruolo è completamente diverso.

È:

👉 una pipeline di arricchimento quantitativo.

Il suo obiettivo è trasformare eventi strutturali di mercato in oggetti statistici misurabili.

Questo significa che:

- ogni breakout diventa analizzabile

- ogni contesto diventa segmentabile

- ogni movimento diventa misurabile

- ogni outcome diventa classificabile

Il risultato finale è un dataset progettato per:

- ricerca quantitativa

- aggregazioni

- analisi probabilistiche

- studi comportamentali

- distribuzioni statistiche

- futuri layer di modeling


# 🔹 Posizione nella Pipeline Generale

Lo statistical engine si trova immediatamente dopo il ROOT engine.

Il flusso globale del progetto è:

```
`Market Data`

`    ↓`

`ROOT Engine`

`    ↓`

`ROOT Dataset (CSV)`

`    ↓`

`STATISTICAL Engine`

`    ↓`

`Dataset Quantitativo Arricchito (Parquet)`

`    ↓`

`Query / Dashboard / Research / Modeling`
```

Questa posizione è fondamentale.

Lo statistical engine dipende completamente dallo schema prodotto dal ROOT.

ROOT produce:

- informazioni strutturali

- metadata dei breakout

- payload follow-through

- metriche balance

- contesto di volatilità

- informazioni market-level

STATISTICAL arricchisce questi elementi in:

- feature

- distribuzioni

- categorie

- target

- statistiche comportamentali

Il modulo agisce quindi come ponte tra:

👉 interpretazione strutturale del mercato

e

👉 analisi quantitativa del comportamento del mercato.


# 🔹 Cosa Produce Realmente il Modulo

La pipeline statistical trasforma progressivamente il dataset originale.

All’inizio:

il ROOT dataset contiene principalmente informazioni grezze sugli eventi.

Alla fine:

il parquet finale contiene:

- feature contestuali

- ratio normalizzati

- classificazioni breakout

- segmentazione della volatilità

- segmentazione delta

- segmentazione volume

- target quantitativi

- classificazioni clean

- scansioni multi-target

- distribuzioni temporali

- metriche quantitative pronte per ricerca

Il sistema converte quindi:

```
`eventi breakout grezzi`
```

in:

```
`oggetti comportamentali quantitativi`
```


# 🔹 Architettura Sequenziale di Enrichment

Lo statistical engine è volutamente sequenziale.

Questo è uno dei principi architetturali più importanti del modulo.

La pipeline è:

👉 order-dependent.

Questo significa che:

molte trasformazioni dipendono da colonne generate in precedenza.

Esempio:

```
`range\_atr\_ratio`

`    ↓`

`compression\_bucket`
```

Il bucket non può esistere prima del ratio.

La stessa logica vale per:

- delta bucket

- volume bucket

- target labeling

- clean target

- time bucket

- metriche di efficienza

Il sistema funziona quindi come una catena progressiva di arricchimento.

Ogni step:

- legge colonne esistenti

- deriva nuove informazioni

- aggiunge nuovi layer analitici

- passa il dataset allo stage successivo

Durante la pipeline il DataFrame evolve continuamente.


# 🔹 Quantitative Enrichment

Una delle responsabilità principali del modulo è l’arricchimento quantitativo.

Il ROOT dataset contiene già market structure.

Ma la struttura, da sola, non è sufficiente per la ricerca.

Lo statistical engine aggiunge:

- normalizzazione

- ratio

- contesto di volatilità

- misure di pressione

- efficienza breakout

- target quantitativi

- analisi clean

- segmentazione temporale

Questo processo trasforma eventi statici in comportamenti misurabili.


# 🔹 Feature Engineering

Il layer di feature engineering costruisce metriche derivate.

Queste feature non sono indicatori casuali.

Sono progettate specificamente per descrivere:

- compressione

- espansione

- qualità del movimento

- pressione direzionale

- volatilità contestuale

- partecipazione di mercato

- efficienza post-breakout

Esempi:

- `range\_atr\_ratio`

- `balance\_pressure`

- `breakout\_location\_ratio`

- `volume\_atr\_ratio`

- `volume\_range\_ratio`

- `breakout\_efficiency`

- `ml\_distance\_atr`

Queste metriche permettono di confrontare breakout in regimi di mercato differenti.


# 🔹 Analisi della Compressione

Uno dei concetti più importanti dello statistical engine è la compressione.

La compressione prova a rispondere alla domanda:

> “Quanto era contratto il mercato prima del breakout?”

Il sistema misura principalmente questo aspetto tramite:

```
`balance\_range\_size / atr\_before`
```

che diventa:

```
`range\_atr\_ratio`
```

Successivamente il ratio viene trasformato in:

- ultra\_compressed

- compressed

- balanced

- expanded

- ultra\_expanded

Questa segmentazione è estremamente importante perché permette di studiare:

- come si comportano i breakout dopo compressione

- se i mercati compressi generano movimenti più forti

- come la volatilità modifica la qualità del breakout

Il sistema trasforma quindi la struttura della volatilità in categorie statistiche.


# 🔹 Interpretazione di Volume e Delta

Il modulo arricchisce i breakout anche con metriche di partecipazione.

Le due dimensioni principali sono:

- volume

- delta

Le feature legate al volume includono:

- `initial\_volume\_feature`

- `volume\_atr\_ratio`

- `volume\_range\_ratio`

- `volume\_bucket`

Le feature legate al delta includono:

- `abs\_initial\_delta`

- `delta\_bucket`

Queste metriche aiutano a capire:

- il breakout era aggressivo?

- esisteva forte partecipazione?

- il movimento è nato con convinzione?

- era presente squilibrio importante durante il breakout?

Il sistema cerca quindi di misurare non solo il movimento del prezzo, ma anche l’intensità della partecipazione di mercato.


# 🔹 Breakout Efficiency

Un breakout che si muove molto non è automaticamente un breakout di qualità.

Lo statistical engine introduce il concetto di efficienza.

L’efficienza viene calcolata tramite:

```
`max\_excursion / atr\_before`
```

che produce:

```
`breakout\_efficiency`
```

Questa metrica misura:

👉 quanto efficientemente il mercato si è mosso rispetto alla volatilità.

Un movimento di:

- 2 punti in bassa volatilità  
può essere estremamente importante,

mentre:

- 2 punti in alta volatilità  
può essere relativamente debole.

La normalizzazione ATR permette confronti coerenti tra ambienti di mercato differenti.


# 🔹 Analisi dei Target

Il sistema di target è una delle parti più importanti dell’intero engine.

Questo layer cerca di formalizzare:

👉 cosa significa realmente “successo”.

Il modulo supporta più filosofie di target.


## Target ATR-Based

I target ATR-based si adattano alla volatilità.

Esempio:

```
`success if:`

`max\_excursion \>= 1 ATR`
```

Questi target scalano dinamicamente in base alle condizioni di mercato.

Sono utili per:

- ricerca normalizzata sulla volatilità

- confronto tra regimi

- analisi adattive


## Target Tick-Based

I target tick-based utilizzano distanza assoluta.

Esempio:

```
`success if:`

`max\_excursion \>= 20 ticks`
```

Questi target sono fissi.

Sono utili per:

- studi orientati all’esecuzione

- analisi operative

- confronti a rischio fisso


## Multi-Target Scans

Il modulo supporta anche la generazione automatica di scan multipli.

Invece di creare un solo target:

il sistema può generare intere scale di target.

Esempio:

```
`0.5 ATR`

`1.0 ATR`

`1.5 ATR`

`2.0 ATR`
```

oppure:

```
`10 ticks`

`20 ticks`

`30 ticks`

`40 ticks`
```

Questo rende il dataset molto più ricco quantitativamente.

Il progetto può quindi studiare:

- quanto lontano tendono ad arrivare i breakout

- dove le distribuzioni iniziano a decadere

- quali condizioni favoriscono movimenti estesi

Questa è una delle capacità quantitative più forti dell’intero modulo.


# 🔹 Analisi dei Clean Move

Lo statistical engine non studia soltanto la distanza del movimento.

Studia anche:

👉 la qualità del movimento.

Alcuni breakout:

- si muovono molto

- ma retracciano violentemente

Altri:

- si muovono progressivamente

- mantengono integrità direzionale

- retracciano pochissimo

Il sistema cerca di separare questi comportamenti.

Questa logica viene implementata tramite:

- retracement depth

- clean threshold

- clean target logic

Le colonne generate includono:

- `is\_clean\_quant`

- `clean\_quant\_label`

- `t2\_clean\_\*ticks`

Questo permette di studiare:

- movimenti direzionali efficienti

- movimenti instabili

- mercati rumorosi

- qualità della persistenza direzionale

La logica clean non riguarda quindi solo il successo.

Riguarda:

👉 la qualità strutturale del movimento.


# 🔹 Bucket e Stati di Mercato

Il sistema di bucket è uno dei meccanismi statistici più potenti del modulo.

I valori numerici continui sono difficili da aggregare direttamente.

Esempio:

```
`0.91`

`0.97`

`1.02`

`1.08`
```

sono valori molto simili, ma difficili da interpretare velocemente.

I bucketizer trasformano questi valori in:

- stati di mercato

- regimi di volatilità

- classi di partecipazione

- categorie strutturali

Esempi:

- compressed

- balanced

- expanded

- low volume

- extreme volume

- high ATR

- low ATR

Questo migliora enormemente:

- aggregazioni

- grouping

- filtraggio

- leggibilità statistica

- costruzione dashboard

I bucket convertono quindi:

```
`numeri`
```

in:

```
`condizioni di mercato interpretabili`
```


# 🔹 Aggregazioni e Ricerca Statistica

Il dataset finale è progettato specificamente per l’aggregazione.

Una volta generato il parquet, il progetto può studiare domande come:

- Quali stati di compressione producono i migliori risultati?

- Quali sessioni generano i movimenti più clean?

- Come la volatilità influenza il successo dei breakout?

- In quali ambienti delta il follow-through è migliore?

- Quali target sono realisticamente raggiungibili?

- Come si distribuiscono i breakout nel tempo?

Lo statistical engine rappresenta quindi:

👉 la base quantitativa dell’intero progetto.


# 🔹 Distribuzioni

Il dataset arricchito permette analisi distributive.

Questo è estremamente importante quantitativamente.

Il progetto può analizzare:

- distribuzioni target

- distribuzioni excursion

- distribuzioni retracement

- distribuzioni session

- distribuzioni volatilità

- distribuzioni efficienza breakout

- distribuzioni clean move

Invece di osservare singoli esempi:

il sistema studia:

👉 popolazioni comportamentali.

Questo rappresenta un enorme cambio concettuale.

L’analisi passa da:

```
`interpretazione del singolo breakout`
```

ad:

```
`analisi statistica di grandi popolazioni di comportamento`
```


# 🔹 Analisi Temporale del Mercato

Il modulo costruisce anche feature temporali.

Il comportamento del mercato cambia enormemente in base a:

- sessione

- orario

- weekday

- regime temporale

Lo statistical engine estrae:

- hour

- session\_calc

- weekday

- day\_of\_month

- week\_of\_month

- year

- time\_bucket

Questo permette di studiare:

- comportamento intraday

- performance per sessione

- cambiamenti temporali della volatilità

- pattern ricorrenti

Il tempo diventa quindi una dimensione analitica misurabile.


# 🔹 Metriche Prodotte dal Sistema

Il modulo genera diverse classi di metriche.


## Metriche Strutturali

Esempi:

- range\_atr\_ratio

- balance\_pressure

- breakout\_location\_ratio

Descrivono:

- compressione

- espansione

- geometria del balance

- posizionamento del breakout


## Metriche di Partecipazione

Esempi:

- volume\_atr\_ratio

- volume\_range\_ratio

- abs\_initial\_delta

Descrivono:

- partecipazione di mercato

- aggressività direzionale

- intensità dell’attività


## Metriche di Outcome

Esempi:

- breakout\_outcome

- success targets

- clean targets

Descrivono:

- successo del movimento

- fallimento breakout

- qualità del movimento


## Metriche Temporali

Esempi:

- session\_calc

- weekday

- time\_bucket

Descrivono:

- timing di mercato

- comportamento delle sessioni

- struttura intraday


## Metriche di Efficienza

Esempi:

- breakout\_efficiency

- clean\_quant\_label

Descrivono:

- qualità del movimento

- consistenza direzionale

- performance normalizzata sulla volatilità


# 🔹 Flow Reale dei Dati

Il flusso reale della pipeline è:

```
`ROOT CSV`

`    ↓`

`Schema Validation`

`    ↓`

`Outcome Labeling`

`    ↓`

`Feature Engineering`

`    ↓`

`Bucketization`

`    ↓`

`Target Labeling`

`    ↓`

`Clean Move Analysis`

`    ↓`

`Temporal Enrichment`

`    ↓`

`Parquet Export`
```

Ogni stage arricchisce progressivamente il dataset.

Il parquet finale non è quindi un semplice export.

È:

👉 il risultato cumulativo dell’intera pipeline di interpretazione quantitativa.


# 🔹 Caratteristiche Architetturali

Lo statistical engine è:

- deterministico

- sequenziale

- enrichment-oriented

- data-coupled

- schema-dependent

- research-focused

- aggregation-friendly

- config-parameterized

È progettato per produrre:

- dataset analitici stabili

- output riproducibili

- interpretazione statistica configurabile

senza modificare la struttura architetturale della pipeline.


# 🔹 Perché il Modulo è Importante

Senza lo statistical engine:

il progetto saprebbe soltanto:

> “È avvenuto un breakout.”

Con lo statistical engine:

il progetto può studiare:

- come il breakout si è formato

- in quali condizioni è nato

- come il mercato si è comportato dopo

- quanto il movimento è stato efficiente

- quanto il movimento è stato pulito

- come la volatilità ha influenzato il risultato

- come evolvono le distribuzioni statistiche

Questo è ciò che trasforma il progetto da:

```
`rilevazione di eventi di mercato`
```

in:

```
`analisi quantitativa comportamentale del mercato`
```


# 🔹 Visione Finale

Lo statistical engine non è semplicemente un modulo di post-processing.

È il layer che dà significato quantitativo all’intera architettura.

ROOT rileva.

STATISTICAL interpreta.

Insieme trasformano la market structure grezza in:

- comportamento misurabile

- contesto statistico

- dataset pronti per ricerca

- ambienti analitici configurabili

Il parquet finale non è quindi solo un file.

È:

👉 una mappa strutturata del comportamento dinamico dei breakout di mercato.

