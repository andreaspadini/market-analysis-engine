# Engineering Decisions

This document summarizes the main engineering decisions behind the Market Analysis Engine (MAE).

Rather than documenting implementation details, it explains the architectural reasoning that guided the project.

---

# Why a Modular Architecture?

The platform has been designed as a collection of independent analytical engines rather than a monolithic application.

### Benefits

- clear separation of responsibilities
- independent evolution of each engine
- improved maintainability
- easier testing
- extensibility

### Trade-off

The architecture introduces additional coordination complexity compared to a single monolithic application.

---

# Why Runtime Orchestration?

A dedicated Orchestrator coordinates the execution of analytical engines.

Instead of allowing engines to invoke each other directly, the Orchestrator controls the execution pipeline.

### Benefits

- engines remain independent
- execution order can evolve
- easier pipeline extension
- centralized runtime coordination

### Trade-off

An additional orchestration layer increases implementation complexity.

---

# Why Artifact-Based Processing?

Intermediate analytical results are intentionally persisted as artifacts.

Artifacts are considered first-class engineering objects rather than temporary implementation details.

### Benefits

- reproducibility
- debugging
- historical comparison
- statistical experimentation
- independent validation
- easier future extensions

### Trade-off

Disk I/O introduces additional execution overhead compared to pure in-memory processing.

This trade-off was considered acceptable because MAE prioritizes analytical reproducibility over maximum execution speed.

---

# Why Contract-Driven Communication?

Analytical engines never communicate through internal implementation details.

Instead, every engine exchanges standardized artifacts acting as contracts.

### Benefits

- low coupling
- engine replacement
- independent development
- clear interfaces

### Trade-off

Contracts require careful versioning as the platform evolves.

---

# Why Independent Engines?

Every analytical engine owns a specific business responsibility.

Examples include:

- market event detection
- statistical enrichment
- historical pattern analysis
- analytical reporting

This keeps business logic isolated and improves long-term maintainability.

---

# Why a Separate Pattern Engine?

Historical pattern analysis represents a different analytical problem compared to statistical enrichment.

For this reason, the Pattern Engine has been implemented as an independent analytical module rather than extending the primary execution pipeline.

### Benefits

- isolated responsibility
- independent evolution
- reusable analytical workflow
- future extensibility

---

# Why External YAML Configuration?

Analytical parameters are intentionally stored outside the source code.

### Benefits

- reproducible experiments
- easier parameter comparison
- configurable analytical workflows
- no code changes required

### Trade-off

External configuration requires validation and documentation.

---

# Why AI-Assisted Development?

Artificial Intelligence has been used throughout the project as an engineering assistant.

AI supported:

- software design discussions
- architectural exploration
- implementation refinement
- documentation
- learning

Final design decisions always remain human-driven.

The goal has never been automatic code generation, but accelerated software engineering and continuous learning.

---

# Why FastAPI?

FastAPI provides a modern backend framework based on explicit contracts through Pydantic models.

This naturally aligns with MAE's contract-driven architecture.

Benefits include:

- request validation
- response validation
- automatic documentation
- clear API contracts

---

# Why React?

The graphical interface has been intentionally separated from the backend.

This allows independent evolution of:

- frontend
- backend
- runtime orchestration

without introducing unnecessary coupling.

---

# Why Low Coupling and High Cohesion?

One of the primary architectural goals has been to maximize cohesion while minimizing coupling.

Each component focuses exclusively on its own responsibility.

Examples:

- GUI handles user interaction.
- FastAPI exposes APIs.
- Services implement business logic.
- Orchestrator coordinates execution.
- Engines perform analytical processing.

This organization simplifies maintenance and future expansion.

---

# Why This Architecture Instead of a Monolith?

For a small real-time application a monolithic architecture might have been preferable.

MAE, however, is a long-term analytical platform where:

- reproducibility
- maintainability
- experimentation
- extensibility

are considered more important than raw execution speed.

For this reason, the project intentionally accepts architectural complexity in exchange for long-term flexibility.

---

# Lessons Learned

Developing MAE has reinforced several software engineering principles.

Among the most important:

- architecture is about trade-offs
- contracts reduce coupling
- modularity simplifies evolution
- artifacts improve reproducibility
- orchestration improves scalability
- AI is most valuable as an engineering assistant rather than an autonomous developer

These principles continue to guide the evolution of the project.
