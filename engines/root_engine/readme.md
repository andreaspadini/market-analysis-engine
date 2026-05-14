# ROOT ENGINE — Market Structure Detection Engine

Il `root\_engine` è il primo motore strutturale del progetto `market\_analysis\_engine`.

Il suo compito è trasformare barre grezze di mercato in una lettura organizzata della struttura prezzo/volume:

```
`dataset → bars → rotations → balances → breakouts → output`
```

In pratica, il Root Engine prende dati OHLCV, li converte in rotazioni direzionali, raggruppa queste rotazioni in aree di equilibrio chiamate balance, e infine cerca eventuali breakout da quelle aree.

Il risultato principale è:

```
`root\_engine\_result.json`
```

In modalità estesa può produrre anche:

```
`root\_output\_dataset.csv`
```

arricchito con feature di market levels.


# Obiettivo del Root Engine

Il Root Engine non prova a “prevedere” il mercato.

Il suo obiettivo è più concreto: leggere la struttura.

Cerca di rispondere a domande come:

- il mercato sta ruotando dentro un range?

- quella zona è abbastanza compatta da essere una balance?

- il prezzo ha rotto il range?

- il breakout è stato forte o debole?

- dopo il breakout c’è stato follow-through?

- il breakout è pulito, fallito, con retest o in accumulazione?

Questa impostazione rende il Root Engine una base utile per analisi successive, perché trasforma dati grezzi in eventi strutturati.


# Pipeline Root

La pipeline principale parte da un payload JSON.

L’entrypoint è:

```
`market\_analysis\_engine/root\_engine/\_\_main\_\_.py`
```

Il motore riceve:

```
`\{`

`  "tool\_id": "root\_engine",`

`  "config": \{\},`

`  "dataset": \{\}`

`\}`
```

Il dataset viene caricato da filesystem tramite:

```
`dataset\_loader.py`
```

La struttura attesa è:

```
`MARKET\_DATA\_ROOT / instrument / timeframe / data\_\<year\>.txt`
```

Ogni riga viene trasformata in una barra con:

```
`time`

`open`

`high`

`low`

`close`

`volume`

`delta`
```

Da qui parte la pipeline vera:

```
`bars`

`  → rotations`

`  → balances`

`  → breakouts`

`  → root\_engine\_result.json`
```


# Rotation Logic

La rotation logic è il primo livello di astrazione.

Il motore non costruisce balance direttamente dalle candele. Prima trasforma le barre in rotazioni.

Una rotazione è un movimento direzionale continuo.

La logica è semplice ma potente:

- se l’high corrente supera l’high precedente, la direzione è `up`;

- se il low corrente scende sotto il low precedente, la direzione è `down`;

- se non succede nulla, viene mantenuta la direzione precedente.

Quando la direzione cambia, la rotazione corrente viene chiusa e ne viene aperta una nuova.

Ogni rotazione contiene:

```
`direction`

`start\_time`

`end\_time`

`start\_price`

`end\_price`

`amplitude`

`volume`

`delta`

`validity\_flag`

`rotation\_type`
```

La rotazione viene poi classificata come:

```
`micro`

`standard`

`structural`

`invalid`
```

La classificazione dipende dall’ampiezza del movimento.

Una rotazione non è automaticamente valida. Deve superare i filtri configurabili:

```
`min\_rotation\_amplitude`

`min\_rotation\_bars`
```

Questo passaggio è fondamentale perché determina la sensibilità dell’intero engine.

Se le rotazioni sono troppo sensibili, il sistema trova molte balance rumorose.  
Se sono troppo filtrate, il sistema trova meno strutture ma più pulite.


# Balance Detection

Una balance è una zona di equilibrio del mercato.

Nel Root Engine una balance nasce da un cluster di rotazioni valide.

Il sistema prende le rotazioni e prova a raggrupparle progressivamente. Un cluster rimane valido finché rispetta tre condizioni principali:

```
`numero minimo di rotazioni`

`distanza temporale massima`

`ampiezza massima del range`
```

Il parametro più importante è:

```
`max\_width`
```

La width del cluster viene calcolata come:

```
`cluster\_high - cluster\_low`
```

Se la width supera `max\_width`, il cluster viene chiuso.

Questo significa che il sistema non usa una regola rigida del tipo:

```
`se il prezzo rompe il massimo precedente di X tick, invalida`
```

La logica reale è più strutturale:

```
`finché il range totale resta entro max\_width,`

`il cluster può restare una balance`
```

Quindi piccoli overshoot o leggere espansioni possono essere accettati, purché il range complessivo rimanga coerente.

Una balance valida contiene:

```
`high`

`low`

`midpoint`

`range\_size`

`rotations`

`volume\_profile`

`vpoc`

`hvn`

`lvn`

`volatility`

`compression\_ratio`

`stability\_score`
```

Questo rende la balance non solo un range di prezzo, ma una struttura completa con informazioni direzionali, volumetriche e di compressione.


# Volume Profile della Balance

Per ogni balance il motore costruisce un volume profile interno.

Le barre della balance vengono aggregate per livelli di prezzo. Da questa distribuzione vengono calcolati:

```
`POC / VPOC`

`HVN`

`LVN`

`total\_volume`

`total\_delta`

`skewness`

`kurtosis`

`concentration`

`asymmetry`

`density\_around\_mid`
```

Il volume profile serve a capire dove il mercato ha accettato il prezzo e dove invece ha scambiato poco.

Queste informazioni vengono poi riutilizzate nella fase di breakout, soprattutto per misurare:

- distanza dal VPOC;

- relazione con HVN/LVN;

- qualità della rottura.


# Breakout Detection

Dopo aver costruito le balance, il Root Engine cerca breakout.

Il `BreakoutDetector` riceve:

```
`bars`

`balances`

`config`

`eventuali lower\_tf\_bars`
```

Per ogni balance il motore:

1. trova le barre appartenenti alla balance;

2. individua la fine della balance;

3. osserva le barre successive;

4. verifica se una barra rompe il range.

Il breakout viene cercato rispetto a:

```
`balance\_high`

`balance\_low`
```

La modalità di breakout è configurabile.

## Strict

La modalità più severa.

Per breakout up:

```
`low \> balance\_high`
```

Per breakout down:

```
`high \< balance\_low`
```

La barra deve stare completamente fuori dal range.

## Close Only

Modalità più permissiva.

Per breakout up:

```
`close \> balance\_high`
```

Per breakout down:

```
`close \< balance\_low`
```

Conta solo la chiusura.

## Body 50

Modalità intermedia.

Almeno il 50% del corpo della candela deve stare fuori dalla balance.

Questa modalità cerca di evitare rotture marginali, ma senza essere rigida come `strict`.


# Pre-Breakout Logic

Il Root Engine può valutare una balance prima della rottura effettiva.

Il modulo:

```
`pre\_breakout\_detector.py`
```

calcola un segnale usando quattro componenti:

```
`compression\_score`

`lvn\_proximity\_score`

`volatility\_score`

`delta\_bias\_score`
```

Questi score vengono pesati tramite config.

Se il totale supera:

```
`min\_score`
```

la balance viene marcata come candidata pre-breakout.

Questo dato non sostituisce il breakout reale. È un’informazione aggiuntiva che entra nel `BreakoutModel`.


# Early Breakout

Il motore supporta anche una logica di early breakout su timeframe inferiore.

Se configurato, il Root Engine può caricare barre lower timeframe tramite:

```
`load\_dataset\_for\_timeframe`
```

Esempio:

```
`timeframe principale: 5m`

`lower timeframe: 1m`
```

Il motore cerca se sul timeframe inferiore esiste una rottura anticipata coerente con il breakout principale.

Se viene trovata, salva:

```
`early\_time`

`early\_price`

`early\_bar\_index`

`early\_timeframe`

`minutes\_of\_anticipation`
```

Questa informazione è utile per capire se il breakout era visibile prima sul timeframe più piccolo.


# Strength Analysis

Quando viene trovato un breakout, il motore non si limita a dire “breakout sì/no”.

Calcola anche la forza della rottura.

La strength analysis combina:

```
`momentum`

`delta imbalance`

`volume spike`

`volatility`

`distance from VPOC`

`HVN/LVN relation`
```

Ogni componente produce uno score.

Il risultato finale contiene:

```
`overall\_strength\_score`

`overall\_strength\_normalized`
```

Il primo è lo score grezzo.  
Il secondo è la versione normalizzata.

Questa parte è importante perché permette di distinguere breakout tecnicamente simili ma qualitativamente diversi.

Un breakout con volume, delta, distanza dal VPOC e buon momentum ha un profilo molto diverso da una semplice chiusura marginale fuori range.


# Follow-Through

Il follow-through è una delle parti più importanti del Root Engine.

Dopo la barra di breakout, il motore osserva cosa succede nelle barre successive.

Calcola:

```
`max\_excursion`

`max\_excursion\_bars`

`close\_after\_n\_bars`

`retracement\_depth`

`retracement\_bars`

`time\_to\_retest\_boundary`

`failure\_price`

`failure\_bars\_from\_breakout`

`post\_breakout\_volatility`

`post\_breakout\_volume\_mean`
```

Questa analisi serve a capire se la rottura ha avuto prosecuzione reale.

Un breakout può essere strutturalmente valido ma fallire subito dopo.  
Oppure può rompere, ritestare il boundary e poi continuare.  
Oppure può restare in accumulazione.

Per questo il follow-through è fondamentale: non guarda solo la rottura, ma anche la qualità del movimento successivo.


# Classificazione del Breakout

Dopo il follow-through, il breakout viene classificato.

Le classificazioni principali sono:

```
`clean`

`false\_breakout`

`failed\_follow\_through`

`with\_retest`

`accumulation`
```

Un breakout `clean` è una rottura pulita.

Un `false\_breakout` indica una rottura che rientra o fallisce rispetto al boundary.

Un `failed\_follow\_through` indica una rottura senza sufficiente prosecuzione.

Un breakout `with\_retest` indica che il prezzo è tornato sul boundary dopo la rottura.

Un breakout `accumulation` indica una permanenza prolungata dopo la rottura.

Questa classificazione rende l’output molto più utile di un semplice elenco di breakout.


# Parametri Configurabili

Il Root Engine è fortemente guidato dalla configurazione.

I parametri più importanti sono quelli che controllano:

```
`rotations`

`balance`

`breakout`

`confirmation`

`follow\_through`

`strength`

`pre\_breakout`

`early\_detection`
```

## Rotations

Parametri principali:

```
`min\_rotation\_amplitude`

`min\_rotation\_bars`

`min\_rotation\_amplitude\_micro`

`min\_rotation\_amplitude\_standard`

`min\_rotation\_amplitude\_structural`

`merge\_same\_direction`

`whipsaw\_bars`
```

Questi parametri decidono quanto il sistema è sensibile al movimento del prezzo.

## Balance

Parametri principali:

```
`min\_rotations`

`max\_gap\_bars`

`min\_width`

`max\_width`
```

Questi decidono cosa può diventare una balance.

Esempio:

```
`max\_width = 5`
```

su MNQ significa:

```
`5 punti = 20 tick`
```

Quindi il cluster resta valido finché il range totale non supera 20 tick.

## Breakout

Parametri principali:

```
`mode`

`post\_balance\_bars`

`debug\_force\_first\_breakout`
```

`mode` controlla la modalità di rottura:

```
`strict`

`close\_only`

`body\_50`
```

`post\_balance\_bars` controlla quante barre dopo la balance vengono osservate per cercare il breakout.

## Confirmation

Parametri principali:

```
`enabled`

`max\_bars`

`closes\_required`

`delta\_confirmation`

`delta\_min\_abs`
```

Se la conferma è attiva, il breakout deve dimostrare continuità oltre il boundary.

## Follow-Through

Parametri principali:

```
`observation\_bars`

`retracement\_factor`
```

Questi controllano quante barre osservare dopo il breakout e come misurare ritracciamento/failure.

## Strength

Parametri principali:

```
`momentum\_weight`

`delta\_weight`

`volume\_spike\_weight`

`volatility\_weight`

`distance\_from\_vpoc\_weight`

`hvn\_lvn\_break\_weight`
```

Questi pesi decidono quale componente conta di più nello strength score.

## Pre-Breakout

Parametri principali:

```
`enabled`

`min\_score`

`max\_lvn\_distance`

`min\_volatility\_increase`

`min\_delta\_bias`

`weights`
```

Servono a riconoscere balance potenzialmente pronte a rompere.

## Early Detection

Parametri principali:

```
`enabled`

`lower\_timeframe`

`reference\_timeframe`

`max\_lead\_minutes`

`trigger`
```

Servono a cercare rotture anticipate su timeframe più basso.


# Output Root

L’output principale è:

```
`root\_engine\_result.json`
```

Contiene:

```
`tool\_id`

`balances`

`breakouts`

`counts`
```

I `counts` includono:

```
`balances`

`bars`

`lower\_tf\_bars`

`breakouts`
```

Ogni balance viene serializzata da `BalanceModel`.

Ogni breakout viene serializzato da `BreakoutModel`.

Le colonne principali dei breakout sono:

```
`breakout\_id`

`parent\_balance\_id`

`instrument`

`timeframe`

`breakout\_time`

`breakout\_bar\_index`

`direction`

`breakout\_type`

`confirmation\_status`

`breakout\_price`

`boundary\_price`

`boundary\_type`

`balance\_high`

`balance\_low`

`balance\_midpoint`

`balance\_range\_size`

`balance\_vpoc`

`initial\_volume`

`initial\_delta`

`atr\_before`

`atr\_after`

`strength\_components`

`follow\_through`

`rotation\_context`

`pre\_breakout\_signal`

`tags`
```

In modalità export estesa viene prodotto anche:

```
`root\_output\_dataset.csv`
```

Questo CSV può includere feature market levels:

```
`ml\_nearest\_support`

`ml\_nearest\_resistance`

`ml\_distance\_to\_level`

`ml\_cluster\_strength`

`ml\_density`

`ml\_alignment\_score`

`schema\_version`
```


# Market Levels Extension

Il Root Engine può usare un’estensione chiamata `market\_levels`.

Questa parte non è necessaria per produrre `root\_engine\_result.json`.

Serve invece per arricchire il CSV dei breakout.

Il flusso esteso è:

```
`breakouts`

`  → breakout\_export`

`  → enrich\_breakouts\_with\_levels`

`  → SessionLevelsEngine`

`  → root\_output\_dataset.csv`
```

Il modulo `market\_levels` calcola:

```
`session\_high`

`session\_low`

`session\_poc`

`session\_vah`

`session\_val`

`session\_vwap`

`day\_high`

`day\_low`

`prev\_day\_high`

`prev\_day\_low`

`weekly\_high`

`weekly\_low`

`monthly\_high`

`monthly\_low`
```

Poi il Root Engine usa questi livelli per calcolare feature come supporto/resistenza vicini e densità dei livelli intorno al breakout.


# Differenza tra Core Mode ed Extended Mode

Il Root Engine ha due modalità pratiche.

## Core Mode

È la modalità essenziale.

Produce:

```
`root\_engine\_result.json`
```

Usa:

```
`dataset\_loader`

`BalanceDetector`

`BreakoutDetector`
```

Non richiede `market\_levels`.

## Extended Mode

È la modalità arricchita.

Produce anche:

```
`root\_output\_dataset.csv`
```

Usa:

```
`breakout\_export`

`enrichments/market\_levels`

`market\_levels`

`pandas`
```

Questa modalità è utile per costruire dataset analitici più completi.


# File Principali

I file core sono:

```
`root\_engine/\_\_main\_\_.py`

`root\_engine/dataset\_loader.py`

`root\_engine/processing/balance/balance\_detector.py`

`root\_engine/processing/balance/mixins/rotations\_mixin.py`

`root\_engine/processing/balance/mixins/balance\_mixin.py`

`root\_engine/processing/balance/schema.py`

`root\_engine/processing/breakout/breakout\_detector.py`

`root\_engine/processing/breakout/schema.py`

`root\_engine/processing/breakout/pre\_breakout\_detector.py`

`root\_engine/models/balance\_info.py`

`root\_engine/models/volume\_profile\_stats.py`

`root\_engine/utils/logger.py`
```

I file extended/export sono:

```
`root\_engine/processing/breakout/breakout\_export.py`

`root\_engine/enrichments/market\_levels/\*`

`market\_levels/session\_levels\_engine.py`

`market\_levels/session\_levels\_schema.py`

`market\_levels/market\_levels\_export.py`
```


# Dipendenze Importanti

Il Root Engine richiede:

```
`pydantic`

`numpy`
```

La modalità export richiede anche:

```
`pandas`
```

Il loader richiede la variabile ambiente:

```
`MARKET\_DATA\_ROOT`
```

Senza questa variabile, il dataset non può essere caricato.


# Considerazioni Tecniche

Il Root Engine è una pipeline chiara e leggibile.

La sua forza è che ogni passaggio aggiunge struttura:

```
`barre grezze`

`→ movimento direzionale`

`→ area di equilibrio`

`→ rottura`

`→ qualità della rottura`

`→ comportamento post-rottura`
```

Il motore non lavora come un semplice detector di segnali.

Lavora come un interprete strutturale del mercato.

Questo rende l’output adatto sia allo studio manuale sia a elaborazioni successive, perché ogni breakout porta con sé il contesto della balance da cui nasce, la forza iniziale e il comportamento successivo.

