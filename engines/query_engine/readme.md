# 📘 Query Engine — WORK IN PROGRESS

Il Query Engine è il layer interpretativo e interrogativo del progetto.

Non è solamente un motore di “analisi statistica”.

Il suo obiettivo reale è trasformare dataset quantitativi complessi in:

- query leggibili

- aggregazioni strutturate

- ranking comparativi

- report canonici

- insight interpretabili

Il modulo nasce sopra lo Statistical Engine e lavora principalmente sul dataset:

```
`statistical\_dataset.parquet`
```

prodotto dalla pipeline statistica.


# ⚠️ WORK IN PROGRESS

Il Query Engine è attualmente uno dei moduli più stratificati dell’intero progetto.

Esistono infatti:

- path moderni verificati

- componenti legacy

- layer opzionali

- runtime frozen

- sezioni NL/WIP

Per questo motivo il modulo viene mantenuto marcato come:

```
`WORK IN PROGRESS`
```

Il path moderno realmente verificato durante audit è:

```
`core`

`intent`

`report`

`insight`
```

Mentre:

```
`nl\_layer`

`frozen`
```

restano:

```
`legacy / opzionali / non completamente consolidati`
```


# 🎯 OBIETTIVO DEL QUERY ENGINE

Il Query Engine esiste per rispondere a domande.

Non domande generiche, ma domande quantitative costruite sopra eventi di mercato già processati.

Esempi reali:

```
`Quale weekday produce il miglior true breakout rate?`


`Quale sessione mostra maggiore max excursion?`


`Qual è la probabilità di true breakout in ATR\_HIGH?`


`Quale gruppo domina una distribuzione?`


`Quale segmento ha il ranking peggiore?`
```

Il motore non esegue semplicemente aggregazioni numeriche.

Costruisce un flusso completo:

```
`semantica`

`→ validazione`

`→ pianificazione`

`→ esecuzione`

`→ report`

`→ insight`
```

Ed è proprio questa stratificazione che lo rende molto diverso da un semplice script pandas.


# 🧠 SEMANTICS LAYER

Una delle caratteristiche più importanti del Query Engine è la presenza di un vero livello semantico.

Il sistema non lavora solamente con funzioni tecniche dirette.

Esiste infatti un layer intent che permette di descrivere il significato della query.

Per esempio:

```
`true\_breakout\_rate by weekday`
```

oppure:

```
`ranking by mean(max\_excursion)`
```

Il motore trasforma progressivamente queste richieste in una forma eseguibile.

Questa separazione tra:

```
`cosa voglio ottenere`
```

e:

```
`come il sistema lo calcola`
```

è uno degli elementi architetturali più importanti del Query Engine.


# 🔍 FILTERING

Il sistema è costruito attorno a un filtering molto strutturato.

Le query non lavorano quasi mai sull’intero dataset.

Prima dell’aggregazione il motore può restringere il contesto usando:

- weekday

- session\_calc

- ATR bucket

- breakout outcome

- instrument

- hour

- time bucket

- condizioni personalizzate

Esempi:

```
`weekday == monday`


`session\_calc == RTH`


`atr\_bucket in \[LOW, MEDIUM\]`
```

Questo rende il Query Engine molto più vicino a un sistema analitico segmentato piuttosto che a una semplice pipeline batch.


# 📊 AGGREGATIONS

Il cuore computazionale del Query Engine è rappresentato dalle aggregazioni.

Le aggregazioni trasformano migliaia di righe del dataset in risultati leggibili.

Metriche supportate:

```
`count`

`mean`

`median`

`std`

`success\_rate`

`true\_breakout\_rate`

`non\_failed\_rate`

`probability`

`distribution`

`ranking`
```

Ogni aggregazione possiede:

- validazione dedicata

- comportamento specifico

- gestione NaN

- struttura output coerente

Il sistema separa volutamente:

```
`query execution`
```

from:

```
`aggregation logic`
```

Questo permette al core di rimanere relativamente stabile mentre le metriche evolvono separatamente.


# 📈 TRUE BREAKOUT RATE

Una delle metriche più importanti del motore è:

```
`true\_breakout\_rate`
```

Questa rappresenta la semantica moderna del successo breakout.

Durante l’evoluzione del progetto è emersa una distinzione importante tra:

```
`non failed`
```

and:

```
`true breakout`
```

Per questo motivo:

```
`success\_rate`
```

è stato mantenuto principalmente come alias/deprecated compatibility layer.

Mentre:

```
`true\_breakout\_rate`
```

è diventato il riferimento canonico moderno.


# 📦 DISTRIBUTION ANALYSIS

Il Query Engine non si limita a metriche scalar.

Può anche lavorare con distribuzioni.

Le distribution query permettono di capire:

- composizione del dataset

- concentrazione categorie

- dominanza segmenti

- squilibri statistici

Esempio:

```
`distribution of breakout\_type`
```

Il sistema può successivamente trasformare queste distribuzioni in insight come:

```
`dominant\_segment`

`imbalanced\_distribution`
```


# 🧮 PROBABILITY ENGINE

Una parte importante del motore è il supporto a probabilità condizionate.

Forma generale:

```
`P(event | condition)`
```

Esempi:

```
`P(true\_breakout | weekday == monday)`


`P(failed\_breakout | atr\_bucket == HIGH)`
```

Questa logica permette al Query Engine di lavorare come un vero motore di analisi comportamentale e non solamente come un aggregatore tabellare.


# 🏆 RANKING

Il ranking è uno dei layer più interessanti del sistema.

Il motore non si limita a calcolare metriche.

Può anche confrontare gruppi e ordinarli.

Esempio:

```
`best weekday by true\_breakout\_rate`
```

oppure:

```
`worst session by mean(max\_excursion)`
```

Il ranking viene costruito sopra metriche già esistenti.

Questo significa che il sistema:

1. calcola la metrica

2. confronta i gruppi

3. genera score

4. ordina i risultati

Questo approccio rende il Query Engine molto più vicino a un layer decisionale piuttosto che a una semplice analisi statica.


# 🧱 EXECUTION PLAN

Il Query Engine separa:

```
`semantica`
```

ed:

```
`esecuzione`
```

Questa separazione avviene tramite l’ExecutionPlan.

L’ExecutionPlan rappresenta una query:

- validata

- normalizzata

- pronta per l’executor

In pratica il planner risolve:

- alias

- mapping

- configurazioni metriche

- default impliciti

prima che il core esecutivo inizi il lavoro.


# 📄 REPORT GENERATION

Uno degli aspetti più importanti del Query Engine è la generazione report.

Il sistema non restituisce solamente numeri grezzi.

Costruisce una struttura canonica composta da:

```
`meta`

`summary`

`data`

`ranking`
```

Questo rende il motore molto più stabile e interoperabile.

I report vengono:

- normalizzati

- validati

- ordinati

- uniformati

prima di essere restituiti.


# 💡 INSIGHT GENERATION

Dopo il report entra in gioco l’insight layer.

Questo layer prova a interpretare automaticamente il risultato.

Esempi:

```
`top\_performer`

`bottom\_performer`

`range\_gap`

`dominant\_segment`

`imbalanced\_distribution`
```

Gli insight servono a trasformare numeri in segnali leggibili.

Il sistema:

- estrae insight grezzi

- valuta il segnale

- rimuove rumore

- assegna priorità

- classifica gli insight

Questo è uno dei motivi per cui il Query Engine non può essere considerato solamente una pipeline pandas.


# 🔄 PIPELINE MODERNA

Il path moderno verificato segue questo flusso:

```
`statistical\_dataset.parquet`

`        ↓`

`load\_statistical\_dataset`

`        ↓`

`public intent / query spec`

`        ↓`

`plan\_query`

`        ↓`

`execute\_query`

`        ↓`

`dispatch\_aggregation`

`        ↓`

`build\_report`

`        ↓`

`build\_insight`
```

Questo rappresenta il runtime principale realmente auditato.


# 🧩 STRUTTURA DEL MODULO

## CORE

Responsabile di:

- dataset loading

- query planning

- query execution

- aggregazioni

- ranking


## INTENT

Responsabile di:

- parsing

- validazione

- alias mapping

- public intents

- query semantics


## REPORT

Responsabile di:

- normalizzazione output

- validazione struttura

- serializzazione logica report


## INSIGHT

Responsabile di:

- interpretazione automatica

- classificazione segnali

- scoring

- refinement

- prioritizzazione


## NL\_LAYER (WIP)

Layer opzionale dedicato al Natural Language.

Attualmente non considerato parte del runtime moderno consolidato.


## FROZEN (LEGACY)

Runtime storico separato.

Mantenuto principalmente per:

- compatibilità

- audit

- path precedenti


# 🧠 PERCHÉ IL QUERY ENGINE È DIVERSO DAGLI ALTRI MODULI

Root Engine e Statistical Engine lavorano principalmente sulla produzione del dato.

Il Query Engine invece lavora sull’interpretazione.

Questo significa che il modulo deve gestire contemporaneamente:

- semantica

- validazione

- pianificazione

- aggregazione

- ranking

- reporting

- insight generation

È proprio questa stratificazione che rende il Query Engine uno dei layer più complessi dell’intera architettura.


# 📌 STATO ATTUALE

Attualmente il Query Engine può essere considerato:

```
`funzionante sul path moderno verificato`
```

ma ancora:

```
`WORK IN PROGRESS`
```

sull’intero perimetro storico/legacy/NL.

Durante audit sono stati verificati principalmente:

```
`core`

`intent`

`report`

`insight`
```

mentre:

```
`nl\_layer`

`frozen`

`runner legacy`
```

restano aree da considerare:

```
`opzionali / legacy / parzialmente consolidate`
```


# 📘 CONCLUSIONE

Il Query Engine rappresenta il layer analitico e interpretativo del progetto.

Non è solamente un motore di query.

È un sistema che prova a trasformare:

```
`dati strutturati`
```

in:

```
`lettura quantitativa`

`segmentazione`

`ranking`

`probabilità`

`insight`

`interpretazione automatica`
```

Ed è proprio questa combinazione tra:

- semantics

- filtering

- aggregations

- ranking

- report generation

- insight generation

che lo rende uno dei moduli più interessanti dell’intera architettura.

