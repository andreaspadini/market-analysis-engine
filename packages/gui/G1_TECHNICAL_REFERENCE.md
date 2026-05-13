GUI — G1 Technical Reference

Design System & Layout Foundation

1️⃣ Scopo del Documento

Questo documento definisce:

Terminologia ufficiale adottata in G1

Struttura tecnica della foundation

Pattern architetturali utilizzati

Boundary applicati

Convenzioni di naming

Serve come riferimento per micro-capitoli successivi (G2+), senza introdurre linee guida implementative.

2️⃣ Terminologia Ufficiale
App Layer
Termine	Definizione
App Shell	Struttura globale layout (Header + Sidebar + Content)
AppLayout	Componente che definisce la shell applicativa
PageShell	Wrapper standard per ogni pagina
ContentContainer	Wrapper per max-width e padding coerente
Router	Configurazione rotte GUI
Route	Percorso navigabile
Navigation
Termine	Definizione
SidebarNav	Navigazione primaria
NotFoundPage	Pagina fallback
routes.ts	Mappa centralizzata delle rotte
UI Layer (Design System)
Termine	Definizione
UI Component	Componente atomico riutilizzabile
Layout Component	Componente per gestione layout
Feedback Component	Componente per stati UX
UI Components
Nome	Tipo
Button	UI
Card	UI
Tabs	UI
Table	UI
Modal	UI
Toast	UI
Collapsible	UI
Skeleton	UI
Layout Components
Nome	Tipo
Grid	Layout
Stack	Layout
Divider	Layout
Feedback Components
Nome	Tipo
ErrorBoundary	UI-level error isolation
ErrorState	Stato errore
EmptyState	Stato vuoto
3️⃣ Pattern Tecnici Utilizzati
3.1 Composizione

Struttura component-based

Nessun componente monolitico

Layout separato da UI atomica

3.2 Routing Pattern

createBrowserRouter

Configurazione centralizzata in app/router.tsx

Rotte definite in app/routes.ts

NotFound catch-all

3.3 Layout Pattern

Struttura a griglia CSS:

Header
Sidebar | Content

Con:

CSS Grid per macro layout

Flexbox per micro layout

Container centralizzato

3.4 Theming Pattern

CSS variables (tokens.css)

data-theme attribute

Nessuna libreria esterna

Dark/Light support

3.5 Print Pattern

print.css

Classi:

.no-print

.print-only

.print-section

.print-table

Rimozione header/sidebar in stampa

3.6 Table Architecture

Div-based rendering

Header/body separati

No <table> rigid structure

Virtualization-compatible

3.7 Modal Pattern

React Portal

ESC close

Overlay click close

UI-only behavior

3.8 Toast Pattern

Provider locale (UI scope)

Nessuna persistenza

Nessuna integrazione backend

3.9 Error Isolation

ErrorBoundary livello UI

No logging esterno

No retry logic

UI fallback only

4️⃣ Struttura Cartelle
packages/gui/
  src/
    app/
    pages/
    components/
      ui/
      layout/
      feedback/
    features/
    state/
    api/
5️⃣ Boundary Tecnici Applicati in G1

G1 non contiene:

API calls

Fetch logic

Engine integration

Orchestrator integration

Global state manager

Data fetching libraries

Business logic

Artifact handling

G1 è esclusivamente:

Struttura + Layout + UI + Routing

6️⃣ Dependency Model

packages/gui è progettato come:

UI library interna

React peer dependency

Router peer dependency

No runtime engine dependency

Il runtime è fornito dal runner esterno.

7️⃣ Naming Conventions
File Naming

PascalCase per componenti (NewRunPage.tsx)

camelCase per funzioni

kebab-case per classi CSS

.ts per logica

.tsx per componenti React

Component Naming

Layout components → prefisso neutro (Grid, Stack)

UI components → nome atomico (Button, Card)

Pages → suffisso Page

Providers → suffisso Provider

8️⃣ Stato Foundation

G1 rappresenta:

Stable base layer

Neutral architecture

Extensible without refactor

Isolated from engine

9️⃣ Ruolo del DEV Harness

apps/gui-dev:

Ambiente preview

Non parte della GUI foundation

Non definisce stack finale

10️⃣ Invarianti Strutturali (Non Modificabili Senza Review)

Struttura cartelle

PageShell pattern

Table div-based

Print CSS foundation

No external state manager

No compute logic

Conclusione

G1 stabilisce:

Terminologia ufficiale

Pattern strutturali

Foundation visiva

Boundary architetturali

Micro-capitoli successivi devono rispettare:

nomenclature

isolamento

separazione UI / domain

neutralità runtime