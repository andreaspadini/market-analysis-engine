# ORCHESTRATOR BACKEND CORE

## Overview

L’Orchestrator rappresenta il kernel backend dell’intero sistema.

Non è un semplice wrapper runtime e non è soltanto un layer che “lancia” gli engine.

È il componente che coordina:

- pipeline execution;

- artifact lifecycle;

- runtime orchestration;

- deterministic planning;

- storage management;

- manifest semantics;

- lineage tracking;

- API execution flow.

L’architettura è costruita con una filosofia fortemente:

- artifact-driven;

- deterministic-first;

- contract-oriented;

- execution-separation oriented.

Questo significa che il backend non tratta le esecuzioni come operazioni temporanee, ma come processi tracciabili che producono artifact persistenti identificabili tramite fingerprint deterministici.

Ogni run importante genera:

- artifact;

- manifest;

- lineage;

- execution metadata;

che possono essere:

- riutilizzati downstream;

- verificati;

- riaperti;

- concatenati in pipeline successive.


# Architettura Generale

L’orchestrator separa chiaramente:

- engine layer;

- orchestration layer;

- runtime layer;

- storage layer;

- API layer.

Gli engine analitici:

- Root;

- Statistical;

- Query;

- Pattern;

rimangono responsabili della logica computazionale.

L’orchestrator invece coordina:

- quando eseguire;

- come eseguire;

- quali dipendenze rispettare;

- come salvare gli artifact;

- come validare manifest;

- come propagare lineage;

- come riutilizzare risultati esistenti.

Questo approccio evita che gli engine diventino direttamente responsabili di:

- runtime execution;

- filesystem management;

- caching;

- orchestration;

- artifact tracking.

Il risultato è una struttura molto più leggibile e stabile nel tempo.


# Filosofia Artifact-Driven

Uno dei principi centrali dell’intero backend è che ogni risultato importante deve diventare un artifact persistente.

L’obiettivo non è semplicemente “ottenere un output”, ma costruire una catena computazionale tracciabile.

Per questo motivo il sistema utilizza:

- fingerprint deterministici;

- manifest strict;

- checksum;

- lineage;

- canonical JSON;

- deterministic hashing.

Un artifact rappresenta:

- una specifica esecuzione;

- una specifica configurazione;

- uno specifico input set;

- una precisa identità computazionale.

Questo permette al backend di supportare:

- cache reuse;

- reproducibility;

- downstream chaining;

- auditabilità;

- deterministic rebuild.


# Runtime Flow

Il runtime è costruito come una pipeline separata in più fasi.

Questa separazione è uno dei punti architetturali più importanti del sistema.

Il backend distingue infatti:

1. Planning

2. Scheduling

3. Execution

4. Materialization

## Planning

Il planner riceve il DAG e decide:

- quali nodi servono;

- quali dipendenze devono essere rispettate;

- quali artifact sono già presenti;

- quali nodi devono essere ricostruiti.

Il planner è volutamente puro e separato dal runtime concreto.

Non accede a:

- filesystem;

- engine;

- worker;

- API state.

Questo garantisce deterministic planning.


## Scheduling

Lo scheduler coordina l’ordine operativo del runtime.

Una volta generato il piano, lo scheduler decide:

- quali task possono partire;

- quali dipendenze sono soddisfatte;

- quali worker possono eseguire.

Il sistema supporta sia:

- runtime seriale;

- runtime concorrente.


## Execution

L’esecuzione reale avviene tramite worker e adapter.

Gli adapter fungono da anti-corruption layer tra orchestrator ed engine.

Il runtime non conosce direttamente la logica interna degli engine.

Conosce soltanto:

- input;

- output attesi;

- artifact semantics;

- execution contract.

Questo mantiene separati:

- orchestration;

- analytics;

- runtime infrastructure.


## Materialization

Quando un task produce un risultato, il backend entra nella fase di materialization.

Qui il sistema:

- costruisce il manifest;

- valida checksum;

- salva gli output;

- registra lineage;

- promuove atomicamente l’artifact nello storage.

La materialization è una delle componenti più importanti dell’intero backend perché trasforma output temporanei in artifact persistenti e tracciabili.


# DAG Execution Model

L’orchestrator utilizza un modello DAG-based.

Ogni pipeline viene rappresentata come un grafo orientato aciclico.

Questo permette di modellare:

- dipendenze;

- ordine di esecuzione;

- propagazione rebuild;

- scheduling;

- cache reuse.

Esempio:

```
`Root → Statistical → Query`
```

Statistical può partire solo dopo Root.

Query può partire solo dopo Statistical.

Il planner utilizza:

- topological sort deterministico;

- closure dependency resolution;

- rebuild propagation.

per costruire execution plan coerenti.


# Deterministic-First Design

L’intero backend è progettato per preservare comportamento prevedibile.

Questo principio attraversa:

- planner;

- hashing;

- manifest;

- storage;

- DAG ordering;

- canonical JSON.

A parità di:

- input;

- configurazione;

- engine version;

il sistema tende a produrre:

- stesso fingerprint;

- stesso artifact;

- stessa identity semantics.

Questo è fondamentale per:

- caching affidabile;

- artifact reuse;

- debugging;

- audit;

- reproducibility.


# Artifact Identity

Ogni artifact viene identificato tramite fingerprint deterministico.

Il fingerprint deriva dalla combinazione di:

- input\_hash;

- config\_hash;

- engine\_version.

Formula concettuale:

```
`fingerprint = sha256(input\_hash + config\_hash + engine\_version)`
```

Questo permette al sistema di trattare gli artifact come unità computazionali stabili.


# Manifest System

Ogni artifact viene accompagnato da un manifest strict.

Il manifest descrive:

- producer;

- outputs;

- checksum;

- bytes;

- lineage.

Il manifest è trattato come source of truth dell’artifact.

Il backend valida rigorosamente:

- canonical JSON;

- relpath;

- checksum;

- bytes;

- schema.

Questo rende il sistema molto più sicuro e tracciabile.


# Lineage

La lineage rappresenta la genealogia computazionale degli artifact.

Il sistema mantiene esplicitamente relazioni come:

```
`Root Artifact`

`    ↓`

`Statistical Artifact`

`    ↓`

`Query Artifact`
```

Questo permette di ricostruire:

- origine dei risultati;

- dipendenze upstream;

- chain computazionale.


# Storage Layer

Lo storage layer è filesystem-based ma fortemente strutturato.

Il backend utilizza:

- staging directories;

- atomic promotion;

- strict relpath validation;

- checksum verification;

- manifest validation.

Il filesystem store non è una semplice directory di output.

È un vero artifact repository locale.


# Adapter Layer

Gli adapter rappresentano il punto di contatto tra orchestrator ed engine.

Ogni adapter conosce:

- come invocare un engine;

- come convertire input/output;

- come produrre artifact compatibili.

Questo layer protegge il runtime da coupling eccessivo con implementazioni concrete.


# API Layer

L’API layer è costruito con FastAPI.

Espone:

- endpoint runtime;

- DTO validation;

- contract enforcement;

- execution services.

L’API non esegue direttamente gli engine.

Invoca invece:

- orchestrator services;

- runtime flows;

- execution pipelines.


# Contracts e DTO

Il backend utilizza contract Pydantic strict.

Esistono DTO dedicati per:

- Root;

- Statistical;

- Query;

- Pattern;

- Pipeline;

- ArtifactRef.

Questo permette di mantenere:

- API stabili;

- validation forte;

- semantiche prevedibili.


# Runtime Modes

Il backend contiene più modalità runtime.

Sono presenti:

- runtime seriale;

- scheduler concorrente;

- worker pool;

- execution queue;

- runtime state in-memory.

L’architettura mostra già una direzione evolutiva verso orchestration più avanzata, pur restando principalmente single-process.


# Observability

L’orchestrator include un layer di observability.

Il sistema registra eventi runtime come:

- RunStarted;

- NodeStarted;

- NodeSucceeded;

- RunFailed.

Gli eventi vengono salvati in formato JSONL.

L’observability è best-effort e serve principalmente per:

- debugging;

- tracing;

- runtime inspection.


# Pipeline Flow

## Root → Statistical → Query

La pipeline principale del sistema segue una chain artifact-driven.

### Root

Il Root Engine produce dataset di breakout e strutture market profile.

### Statistical

Statistical consuma artifact Root e produce:

- aggregazioni;

- distribuzioni;

- metriche;

- parquet statistical.

### Query

Query utilizza artifact Statistical per:

- ranking;

- filtering;

- semantic query;

- report generation.

Ogni layer utilizza artifact upstream tramite lineage e artifact resolution.


## Pattern Standalone

Pattern è più standalone rispetto alla chain Root → Statistical → Query.

Supporta:

- manual\_template mode;

- historical\_reference mode.

Pattern utilizza adapter dedicati e configura pipeline indipendenti.


# Punti di Forza Architetturali

L’orchestrator mostra diversi aspetti di maturità architetturale:

- separazione planning/execution;

- artifact-driven lifecycle;

- deterministic-first design;

- manifest strict;

- lineage esplicita;

- anti-corruption adapters;

- storage abstraction;

- DAG orchestration;

- canonical hashing;

- runtime layering.

La parte più importante è che il sistema possiede una vera identità architetturale coerente.

Non è una semplice collezione di script.


# Stato Attuale dell’Architettura

Il backend reale mostra una combinazione di:

- componenti molto maturi;

- componenti evolutivi;

- layer già fortemente strutturati;

- runtime ancora in crescita.

I layer più solidi risultano:

- artifact management;

- manifest validation;

- storage semantics;

- planner;

- deterministic hashing.

I layer più evolutivi risultano:

- API runtime integration;

- runtime persistence;

- concurrency modes;

- observability;

- runtime orchestration path unification.

Questo è normale in sistemi sviluppati incrementalmente.


# Filosofia del Sistema

L’idea centrale dell’orchestrator può essere riassunta così:

```
`Ogni computation significativa deve produrre`

`artifact deterministici, tracciabili e riutilizzabili.`
```

Questa filosofia attraversa:

- planner;

- runtime;

- storage;

- manifest;

- lineage;

- adapters;

- API.

Ed è ciò che definisce la vera identità del backend.


# Conclusioni

L’Orchestrator Backend Core rappresenta il layer infrastrutturale centrale dell’intero sistema.

Coordina:

- engine;

- runtime;

- storage;

- artifact lifecycle;

- manifest semantics;

- lineage;

- API execution.

La sua architettura è costruita attorno a:

- deterministic execution;

- artifact persistence;

- execution separation;

- orchestration semantics.

Il backend non tratta le run come semplici operazioni temporanee.

Le tratta come processi computazionali tracciabili e riproducibili.

Questo approccio dà al sistema:

- maturità architetturale;

- coerenza runtime;

- riutilizzabilità;

- capacità evolutiva;

- controllo semantico degli artifact.

Nel complesso, l’orchestrator rappresenta una struttura backend avanzata orientata alla coordinazione di pipeline analitiche deterministic-first basate su artifact persistenti.

