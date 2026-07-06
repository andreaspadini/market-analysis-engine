# Market Analysis Engine (MAE)

Market Analysis Engine (MAE) is a modular software platform designed for quantitative and statistical market analysis.

Rather than focusing on automated trading, MAE is built as a research-oriented environment that allows analysts to detect market structures, perform statistical analysis, compare historical behaviours, and progressively enrich analytical datasets through independent processing engines.

The project has been developed following a strongly iterative and AI-assisted software engineering workflow, with particular emphasis on software architecture, modularity, contract-driven development and maintainability.

---

# Why this project exists

Most market analysis software focuses on generating trading signals.

MAE follows a different philosophy.

The objective is to build an extensible analytical platform where every processing step is reproducible, inspectable and independently evolvable.

The system has been designed around software engineering principles such as:

- Separation of Responsibilities
- Low Coupling
- High Cohesion
- Contract-Driven Development
- Artifact-Based Processing
- Modular Architecture
- Reproducible Analysis Pipelines

---

# Key Features

- Modular multi-engine architecture
- Breakout detection engine
- Statistical enrichment engine
- Pattern recognition engine
- Query engine
- Runtime orchestration layer
- Artifact-based workflow
- Dataset processing pipeline
- External configuration support
- React/TypeScript graphical interface
- AI-assisted development workflow

---

# Architecture Overview

The platform is organized as independent software components coordinated by a runtime orchestrator.

```text
GUI
    │
    ▼
FastAPI Backend
    │
    ▼
Orchestrator
    │
    ├───────────────► Root Engine
    │                     │
    │                     ▼
    │               Root Artifact
    │                     │
    │                     ▼
    │            Statistical Engine
    │                     │
    │                     ▼
    │           Statistical Artifact
    │                     │
    │                     ▼
    │              Query Engine
    │                     │
    │                     ▼
    │              Final Results
```

Each engine has a single responsibility and communicates through versioned artifacts rather than direct implementation dependencies.

---

# Technology Stack

Backend

- Python
- FastAPI
- Pydantic

Frontend

- React
- TypeScript

Architecture

- Contract-Driven Design
- Artifact-Based Processing
- Runtime Orchestration
- Modular Engines
- Dataset Pipelines

Development

- Git
- GitHub
- AI-Assisted Development

---

# Project Structure

```text
market-analysis-engine/

├── Root Engine
├── Statistical Engine
├── Pattern Engine
├── Query Engine
├── Orchestrator
├── GUI
├── Documentation
├── Configurations
└── Runtime Artifacts
```

---

# Running the Project

A complete setup guide is available here:

**RUNNING.md**

The document includes:

- installation
- project setup
- environment configuration
- execution examples
- GUI startup
- development workflow

---

# What I Learned While Building This Project

Building MAE has been an opportunity to deepen several software engineering concepts beyond programming itself.

Main topics explored include:

- modular software architecture
- separation of responsibilities
- orchestration systems
- API design
- contract-driven development
- artifact lifecycle management
- software scalability
- architectural trade-offs
- iterative software design
- AI-assisted software development

---

# Current Status

MAE is an active long-term project currently under continuous development.

The platform continues to evolve through incremental improvements, architectural refinements and new analytical engines.

Future work includes:

- additional analytical modules
- improved dataset management
- expanded statistical capabilities
- advanced reporting
- further GUI evolution

---

# Repository

This repository represents an ongoing engineering project focused on software architecture, modular backend systems and quantitative analysis workflows.

Suggestions, discussions and constructive feedback are always welcome.
