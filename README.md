![Python](https://img.shields.io/badge/Python-3.x-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green)
![React](https://img.shields.io/badge/React-Frontend-blue)
![Status](https://img.shields.io/badge/Status-Active-success)

# Market Analysis Engine (MAE)

A modular, artifact-driven software platform for quantitative market analysis.

Market Analysis Engine (MAE) is a long-term software engineering project designed to support reproducible market research through independent analytical engines rather than automated trading.

Instead of producing trading signals, MAE focuses on identifying market structures, enriching them with statistical information, discovering historical similarities, and exposing the resulting knowledge through dedicated analytical services.

The project has been developed following an iterative AI-assisted engineering workflow, with a strong emphasis on software architecture, modularity, maintainability and long-term scalability.

---

# Project Goals

MAE has been designed around a simple idea:

**Build an analytical platform where every processing step is reproducible, inspectable and independently evolvable.**

The architecture intentionally prioritizes:

- Separation of Responsibilities
- High Cohesion
- Low Coupling
- Contract-Driven Development
- Artifact-Based Processing
- Runtime Orchestration
- Reproducible Analytical Pipelines

rather than maximizing raw execution speed.

---

# Architecture Overview

The platform is composed of independent software components coordinated by a runtime orchestrator.

```text
                         GUI
                          │
                          ▼
                   FastAPI Backend
                          │
                          ▼
                    Orchestrator
                          │
          ┌───────────────┼────────────────┐
          │               │                │
          ▼               ▼                ▼

     Root Engine    Statistical Engine   Query Engine
          │               │                │
          ▼               ▼                ▼

   Root Artifact  Statistical Artifact  Final Report


                  Independent Workflow
                          │
                          ▼

                  Pattern Engine
                          │
                          ▼

                  Pattern Matches
```

The Root → Statistical → Query pipeline represents the primary analytical workflow.

The Pattern Engine is an independent analytical module dedicated to historical similarity analysis, allowing current market structures to be compared with historical datasets without affecting the primary pipeline.

Each engine owns a single responsibility and communicates through versioned artifacts instead of direct implementation dependencies.

---

# Main Components

## Root Engine

Detects analytical market events such as balances, breakouts and other market structures starting from raw market data.

---

## Statistical Engine

Consumes Root artifacts and enriches detected events with statistical information and derived analytical features.

---

## Query Engine

Provides analytical reporting capabilities over generated datasets, allowing structured exploration of statistical results.

---

## Pattern Engine

Dedicated historical similarity engine.

Its purpose is to compare current market structures with historical datasets in order to identify similar market behaviour and support exploratory market analysis.

Unlike the primary execution pipeline, the Pattern Engine operates as an independent analytical workflow.

---

## Orchestrator

Coordinates engine execution.

Responsibilities include:

- pipeline orchestration
- engine registration
- runtime coordination
- artifact routing
- dependency management

Individual engines never know which component will consume their output.

---

## GUI

React-based graphical interface exposing the platform through a user-friendly frontend.

---

# Key Features

- Modular multi-engine architecture
- Runtime orchestration
- Contract-driven communication
- Artifact-based analytical workflow
- Historical pattern similarity analysis
- Statistical enrichment pipeline
- External YAML configuration
- Dataset-driven analysis
- React + FastAPI architecture
- AI-assisted software engineering workflow

---

# Technology Stack

## Backend

- Python
- FastAPI
- Pydantic

## Frontend

- React
- TypeScript

## Architecture

- Modular Design
- Contract-Driven Development
- Runtime Orchestration
- Artifact-Based Processing
- Independent Analytical Engines

## Configuration

- YAML
- External runtime configuration

## Development

- Git
- GitHub
- AI-Assisted Development

---

# Project Structure

```text
market-analysis-engine/

├── backend/
├── engines/
│   ├── Root Engine
│   ├── Statistical Engine
│   ├── Pattern Engine
│   └── Query Engine
├── apps/
├── packages/
├── datasets/
├── documentation/
└── runtime artifacts/
```

---

# Running the Project

Complete setup instructions are available in:

**RUNNING.md**

The document includes:

- environment setup
- Python installation
- frontend installation
- dataset configuration
- backend startup
- GUI startup
- development workflow

---

# What I Learned While Building MAE

MAE has been much more than a programming project.

It has been an opportunity to study and apply software engineering principles in a real-world architectural context.

Key topics explored during development include:

- modular software architecture
- separation of responsibilities
- contract-driven development
- runtime orchestration
- artifact lifecycle management
- scalable backend systems
- API design
- historical data processing
- architectural trade-offs
- AI-assisted software engineering

Above all, the project taught me how architectural decisions influence maintainability, extensibility and long-term software evolution.

---

---

# Documentation

Additional documentation is available in the **docs** folder.

| Document | Description |
|----------|-------------|
| **ARCHITECTURE.md** | High-level architecture, design principles and system organization. |
| **ENGINEERING_DECISIONS.md** | Main architectural decisions, design trade-offs and engineering rationale. |
| **RUNNING.md** | English setup and execution guide. |
| **RUNNING.it.md** | Italian setup and execution guide. |
| **ROADMAP.md** | Planned features and project evolution. |
| **CHANGELOG.md** | Project history and version changes. |

# Current Status

MAE is an active long-term project under continuous development.

Current work focuses on:

- architectural refinement
- analytical engine evolution
- GUI improvements
- runtime enhancements
- statistical capabilities
- future analytical modules

---

# Repository

This repository showcases an ongoing software engineering project focused on modular backend architecture, quantitative analysis and AI-assisted software development.

Suggestions, discussions and constructive feedback are always welcome.
