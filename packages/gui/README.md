# GUI — Visual Orchestration Layer

## Overview

La GUI del progetto non nasce come semplice frontend React.

Non è stata progettata come dashboard indipendente, né come applicazione business-logic centrica.

La GUI rappresenta invece un:

```
`Visual Orchestration Layer`
```

sopra l’orchestrator artifact-driven.

Il suo compito principale non è “calcolare”, ma:

- guidare l’utente;

- coordinare visivamente gli stage;

- costruire pipeline operative;

- mostrare artifact e manifest;

- accompagnare l’esecuzione runtime;

- rendere leggibile il chaining tra engine.

L’interfaccia è quindi costruita attorno alla pipeline reale del sistema:

```
`Root`

`→ Statistical`

`→ Query`
```

Dove ogni stage produce artifact che possono essere immediatamente riutilizzati dal successivo.


# Filosofia della GUI

La GUI segue una filosofia molto precisa:

```
`thin frontend`

`artifact-centric`

`workspace-driven`

`contract-driven`
```

Questo significa che:

- la logica reale vive nel backend;

- gli engine non vengono eseguiti nel frontend;

- la GUI non “interpreta” semanticamente gli artifact;

- il frontend preserva il contratto dell’orchestrator;

- il chaining viene costruito usando artifact ref reali.

Il frontend non tenta mai di sostituire il runtime backend.

Al contrario:

rende il runtime:

- visibile;

- navigabile;

- leggibile;

- operativo.


# Workflow UX

Uno degli aspetti più importanti della GUI è il workflow operativo percepito dall’utente.

L’interfaccia non è stata organizzata come semplice raccolta di pagine separate.

È stata progettata per accompagnare progressivamente la pipeline.

L’utente percepisce chiaramente:

- dove si trova;

- quale stage sta eseguendo;

- quale artifact sta usando;

- quale risultato è stato prodotto;

- come proseguire nello stage successivo.

Questo crea una UX molto più “pipeline-oriented” rispetto a una dashboard tradizionale.

La GUI cerca continuamente di ridurre attrito operativo.

L’obiettivo non è riempire schermate di controlli.

L’obiettivo è:

```
`rendere leggibile la pipeline reale`
```


# Configurazione Pipeline

## Dataset come punto di partenza

Ogni esecuzione parte dalla definizione del dataset.

La GUI permette di configurare:

- strumenti;

- timeframe;

- date range.

Questa fase rappresenta il contesto globale della pipeline.

L’utente costruisce il perimetro operativo prima ancora di scegliere gli engine.

Dal punto di vista UX, questo rende subito chiaro che:

```
`gli stage lavorano tutti sullo stesso universo dati`
```


## Configurazione Root

Lo stage Root rappresenta il primo livello operativo reale.

Dal frontend l’utente configura:

- rotazioni;

- balance;

- breakout;

- follow-through;

- ranking;

- export;

- session levels.

La GUI espone il contratto canonico dell’engine.

Non introduce semantiche alternative.

Questo è un aspetto architetturale fondamentale:

```
`la GUI non reinventa il backend`
```

ma ne riflette direttamente la struttura.

Dal punto di vista dell’utente, questo crea una sensazione molto “diretta”.

Si percepisce chiaramente che:

```
`la configurazione mostrata è quella reale del runtime`
```

non una versione “semplificata artificialmente”.


## Configurazione Statistical

Una volta prodotto un artifact Root, la GUI permette di passarlo direttamente allo stage Statistical.

Qui l’esperienza utente cambia.

Il frontend smette di essere solamente “configurazione”.

Diventa:

```
`workspace operativo`
```

L’utente vede:

- artifact disponibili;

- stato dello stage;

- collegamenti tra output e input;

- continuità della pipeline.

Statistical lavora quindi come naturale prosecuzione di Root.

La GUI accompagna questa transizione in modo molto fluido.

Esempio operativo:

```
`L’utente completa Root.`

`La GUI riceve:`

`- run\_id`

`- artifact ref`


`Il workspace salva automaticamente il riferimento.`


`Statistical viene precompilato.`


`L’utente vede immediatamente:`

`- artifact disponibile`

`- badge identificativo`

`- possibilità di continuare la pipeline`
```

Questo rende il sistema estremamente tangibile.


## Configurazione Query

La parte Query rende la pipeline ancora più concreta.

L’utente non lavora più solo su configurazioni runtime.

Lavora direttamente su:

```
`risultati statistici già materializzati`
```

La GUI rende molto evidente questa transizione.

L’esperienza percepita diventa:

```
`analisi iterativa`
```

più che semplice submit di job.

La pipeline evolve quindi da:

```
`execution flow`
```

verso:

```
`exploration flow`
```


# Artifact Visualization

## Artifact come elemento centrale

La GUI ruota completamente attorno agli artifact.

Gli artifact non vengono trattati come semplici file.

Sono invece:

- output ufficiali della pipeline;

- punti di collegamento tra stage;

- identità operative persistenti;

- riferimenti runtime.

Ogni artifact viene mostrato usando:

```
`tool\_id`

`fingerprint`
```

che rappresentano il contratto reale dell’orchestrator.

Questo rende molto chiaro all’utente che:

```
`gli output non sono “temporanei”`
```

ma rappresentano elementi reali della pipeline.


## Chaining visuale

Uno degli aspetti più riusciti della GUI è il chaining visuale.

Esempio reale:

```
`L’utente esegue Root.`

`La GUI riceve:`

`- run\_id`

`- artifact ref`


`Lo stato workspace salva il riferimento.`


`Statistical viene automaticamente precompilato.`


`L’utente vede immediatamente:`

`- artifact disponibile`

`- badge identificativo`

`- possibilità di aprire risultati`

`- possibilità di continuare la pipeline`
```

Questa esperienza rende il sistema molto più concreto e leggibile.

L’utente percepisce chiaramente che:

```
`uno stage sta alimentando il successivo`
```


## Artifact Selector

L’Artifact Selector è il punto in cui il chaining diventa esplicito.

L’utente può:

- usare artifact appena prodotti;

- inserire manualmente artifact ref;

- ricollegare stage precedenti;

- lavorare su pipeline diverse.

La GUI quindi non impone un flusso rigido.

Permette una vera orchestrazione visuale.

Questo è particolarmente importante perché il frontend non “risolve semanticamente” gli artifact.

Passa semplicemente:

```
`tool\_id + fingerprint`
```

all’orchestrator.

Ed è il backend a risolvere il riferimento reale.


# Workspace UX

## Workspace come centro della GUI

Il vero cuore del frontend non è la pagina Results.

È il Workspace.

Il workspace rappresenta:

```
`la pipeline viva`
```

L’utente non percepisce più stage isolati.

Percepisce invece:

- continuità;

- propagazione artifact;

- avanzamento operativo;

- coordinazione runtime.

Questo è il motivo per cui il progetto definisce la GUI come:

```
`Visual Orchestration Layer`
```

più che semplice frontend.


## Root → Statistical

Uno dei flow più importanti è:

```
`Root → Statistical`
```

Flow operativo percepito:

```
`1. L’utente configura Root`

`2. Esegue la run`

`3. La GUI mostra stato runtime`

`4. Root produce artifact`

`5. Lo stato workspace salva artifact ref`

`6. Statistical viene precompilato`

`7. L’utente continua senza reinserire dati`
```

Questo riduce enormemente attrito operativo.

La pipeline appare continua.


## Statistical → Query

Il passaggio Query è ancora più interessante.

Qui la GUI accompagna una trasformazione concettuale:

```
`da execution pipeline`

`a exploration pipeline`
```

L’utente comincia a lavorare direttamente sui risultati statistici.

La GUI rende questa transizione molto naturale.

Esempio:

```
`Statistical produce aggregazioni.`

`Query riceve automaticamente l’artifact.`

`L’utente può immediatamente:`

`- lanciare ranking`

`- confrontare gruppi`

`- iterare query`

`- leggere insight`
```


# Results System

## Polling Runtime

La pagina Results utilizza polling runtime.

La GUI controlla periodicamente lo stato della run.

Esempio:

```
`RUNNING`

`→ RUNNING`

`→ SUCCEEDED`
```

Questo permette all’utente di percepire:

- avanzamento;

- stato runtime;

- successo/fallimento;

- disponibilità dei risultati.

L’esperienza è molto più “runtime-aware” rispetto a una semplice pagina statica.


## Snapshot Results

I risultati vengono mostrati tramite snapshot aggregati.

La GUI non ricostruisce il runtime internamente.

Mostra semplicemente:

```
`lo snapshot prodotto dall’orchestrator`
```

Questo mantiene frontend e backend semanticamente allineati.


## Root Results

La sezione Root visualizza:

- eventi;

- breakout;

- balance;

- dettagli nested;

- summary cards.

L’esperienza è molto più vicina a:

```
`navigazione runtime`
```

che a semplice rendering JSON.

La GUI cerca continuamente di trasformare output tecnici in:

```
`navigazione leggibile`
```


## Statistical Results

La parte Statistical enfatizza:

- distribuzioni;

- aggregazioni;

- summary;

- nested blocks;

- visualizzazione tabellare.

Qui la GUI rende il lato quantitativo molto leggibile.

L’utente percepisce chiaramente:

- densità dati;

- bucket;

- ranking;

- distribuzioni;

- differenze statistiche.


## Query Results

La sezione Query trasforma il risultato in:

- ranking;

- insight;

- differenze tra gruppi;

- overview operative.

La GUI accompagna l’utente nella lettura del risultato.

Non si limita a mostrare dati grezzi.

Esempio percepito:

```
`“quale gruppo performa meglio?”`

`“quale configurazione è più debole?”`

`“quanto cambia il risultato?”`
```

La lettura diventa molto più intuitiva.


# API Layer

## Thin Typed Client

La GUI usa un client tipizzato sopra l’orchestrator.

Questo layer:

- centralizza endpoint;

- centralizza DTO;

- preserva i contratti;

- evita fetch sparsi.

La GUI si comporta quindi come:

```
`thin typed client`
```

sopra il backend.


## DTO Contract

I payload frontend rispettano il contratto reale backend.

Questo è estremamente importante.

Il frontend:

- non rinomina campi;

- non normalizza semantiche;

- non aggiunge runtime logic;

- non altera gli artifact.

Preserva la struttura canonica del sistema.

Questo mantiene:

```
`frontend e orchestrator semanticamente allineati`
```


# Architettura Frontend

## packages/gui

Contiene la logica reale del frontend:

- workspace;

- routing;

- API;

- results;

- componenti;

- orchestration flow.

È il cuore dell’interfaccia.


## apps/gui-web

Host app dedicata al runtime browser.

Serve principalmente a:

- montare la GUI;

- avviare Vite;

- configurare runtime web.


## apps/gui-dev

Host dedicato allo sviluppo locale.

Permette:

- test veloci;

- preview;

- sviluppo isolato;

- debug frontend.


# Filosofia Visuale

La GUI non cerca di apparire “enterprise dashboard”.

L’obiettivo reale è:

```
`rendere leggibile la pipeline`
```

Per questo l’interfaccia enfatizza:

- flow verticale;

- continuità stage;

- artifact chaining;

- stato runtime;

- navigazione operativa.

L’utente percepisce chiaramente che il sistema sta:

```
`costruendo una pipeline reale`
```

non semplicemente compilando form.


# Conclusione

La GUI rappresenta uno dei layer più importanti del progetto perché rende tangibile l’intera architettura artifact-driven.

Senza il frontend:

- gli artifact rimarrebbero invisibili;

- il chaining sarebbe astratto;

- il runtime sarebbe opaco;

- la pipeline sarebbe difficile da seguire.

La GUI trasforma invece:

```
`engine + orchestrator`
```

in un workflow operativo leggibile.

Per questo la definizione corretta del frontend non è:

```
`“semplice frontend React”`
```

ma:

```
`Visual Orchestration Layer`
```

sopra un sistema runtime artifact-driven.

