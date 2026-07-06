# Running the Project

This document describes the minimum setup required to run the clean public version of the Market Analysis Engine.

The repository is a portable reconstruction of the original project.
It preserves the same core logic, conceptual architecture, engine structure and artifact-based workflow, while simplifying imports, namespaces, runtime paths and workspace configuration for easier local setup.

---

## Project Structure
```text
engines/        Analytical engines
backend/        Orchestrator and API layer
apps/           Frontend application host
packages/       Shared GUI packages
datasets/       Local datasets
```

## Python Setup
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Frontend Setup
```powershell
npm install
```

## Dataset Setup
Datasets must be placed under:
```text
datasets/market_data/
```
Example:
```text
datasets/market_data/MNQ/5m/data_2025.txt
```

## Start the Backend
```powershell
$env:MARKET_DATA_ROOT="./datasets/market_data"

uvicorn backend.orchestrator.src.api.http.app_factory:create_app --factory --port 8000
```

Backend URL:
`http://localhost:8000`

## Start the GUI
```powershell
cd apps/gui-web
npm run dev
```

GUI URL:
`http://localhost:5173`

## Notes
This public repository keeps the same:
- analytical logic
- pipeline concept
- engine responsibilities
- artifact flow
- conceptual architecture

The public version only adapts:
- imports
- namespaces
- runtime paths
- minimal workspace structure
- portability-related configuration

## Current Status
This project is under active development.
It is intended to demonstrate the architecture, modular workflow and engineering approach of the Market Analysis Engine.
