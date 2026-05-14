# Market Analysis Engine

Replica pulita e funzionante del progetto originale.
Questo documento descrive il setup minimo per il run pulito.

## Struttura

```text
engines/        -> engine analitici
backend/        -> orchestrator + API
apps/           -> frontend host
packages/       -> GUI shared package
datasets/       -> dataset locali
```

## Setup Python

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Setup Frontend

```powershell
npm install
```

## Dataset

Il dataset deve essere presente in:

```text
datasets/market_data/
```

Esempio:

```text
datasets/market_data/MNQ/5m/data_2025.txt
```

## Backend Start

```powershell
$env:MARKET_DATA_ROOT="./datasets/market_data"

uvicorn backend.orchestrator.src.api.http.app_factory:create_app --factory --port 8000
```

## GUI Start

```powershell
cd apps/gui-web
npm run dev
```

## GUI URL

```text
http://localhost:5173
```

## Note

Questa copia mantiene:

- stessa logica;
- stessa pipeline;
- stessa architettura concettuale;
- stessi engine;
- stesso artifact flow;

del progetto originale.

Sono stati modificati solamente:

- import;
- namespace;
- path runtime;
- struttura workspace minima;
- configurazioni necessarie alla portabilità.