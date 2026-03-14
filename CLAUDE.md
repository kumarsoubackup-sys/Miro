# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MiroFish is a multi-agent AI prediction engine. It takes text documents (PDF, Markdown, TXT), builds knowledge graphs via Zep Cloud, generates thousands of autonomous agents with distinct personalities, runs social media simulations (Twitter/Reddit via OASIS framework), and produces prediction reports through an Agent-based system. Users can then chat with simulated agents and refine reports interactively.

## Commands

```bash
# Install everything (Node + Python)
npm run setup:all

# Start both frontend (port 3000) and backend (port 5001) concurrently
npm run dev

# Start individually
npm run frontend    # Vite dev server
npm run backend     # Flask via uv

# Build frontend for production
npm run build

# Backend Python dependency management (uses uv, not pip)
cd backend && uv sync

# Run backend tests (pytest available as dev dependency)
cd backend && uv run pytest
```

No linter or formatter is configured.

## Architecture

**Monorepo** with two independent apps connected via REST API:

```
MiroFish/
├── frontend/    # Vue 3 + Vite SPA (port 3000, proxies /api to backend)
├── backend/     # Flask API (port 5001, Python 3.11+)
└── package.json # Root orchestration via concurrently
```

### 5-Step Workflow Pipeline

1. **Graph Build** - Upload docs, LLM extracts entities/relationships, builds Zep knowledge graph
2. **Env Setup** - Generate OASIS agent personas from graph entities
3. **Simulation** - Run social platform simulation (Twitter/Reddit-like)
4. **Report** - ReportAgent generates prediction reports via tool-calling LLM
5. **Interaction** - Chat with simulated agents or refine reports

### Frontend (`frontend/src/`)

- **Framework**: Vue 3 Composition API (`<script setup>` throughout)
- **Routing**: Vue Router with params `:projectId`, `:simulationId`
- **HTTP**: Axios with 5-minute timeout, exponential backoff retry in `api/index.js`
- **Visualization**: D3.js for knowledge graph rendering in `GraphPanel.vue`
- **State**: Minimal - route props, no Vuex/Pinia (just a small `store/pendingUpload.js`)
- **Components**: Numbered Step1-Step5 components map to the workflow pipeline
- **API layer**: Centralized in `api/` folder (graph.js, simulation.js, report.js)

### Backend (`backend/app/`)

- **Blueprints**: `graph_bp`, `simulation_bp`, `report_bp` in `api/`
- **Service layer**: Each feature has a dedicated service class in `services/`
  - `ontology_generator.py` - LLM entity/relationship extraction
  - `graph_builder.py` - Zep graph construction
  - `oasis_profile_generator.py` - Agent persona generation
  - `simulation_runner.py` - OASIS execution with IPC progress
  - `report_agent.py` - ReportAgent with tool-calling (largest file ~2570 LOC)
- **Models**: `ProjectManager` (in-memory session state), `TaskManager` (async task tracking with progress 0-100)
- **Utils**: `LLMClient` wraps OpenAI SDK, `file_parser.py` handles uploads, per-module loggers via `get_logger()`
- **Config**: `config.py` loads `.env` from project root

### Data Storage

No traditional database. All state managed via:
- **Zep Cloud** - Graph storage, entity memory, relationships (REST API)
- **File system** - Project state via ProjectManager, uploads in `backend/uploads/`
- **In-memory** - Task tracking via TaskManager (lost on restart)

### API Response Format

```json
{
  "success": true,
  "data": {},
  "error": "message on failure"
}
```

Long-running operations return a `task_id`; frontend polls for progress.

## Environment Variables

Create `.env` in project root (loaded by both frontend proxy and backend):

```env
# Required
LLM_API_KEY=              # OpenAI-compatible API key
ZEP_API_KEY=              # Zep Cloud API key

# Optional (defaults shown)
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL_NAME=gpt-4o-mini
FLASK_DEBUG=True
FLASK_PORT=5001
OASIS_DEFAULT_MAX_ROUNDS=10
REPORT_AGENT_MAX_TOOL_CALLS=5
REPORT_AGENT_MAX_REFLECTION_ROUNDS=2
REPORT_AGENT_TEMPERATURE=0.5
```

## Key Conventions

- **Python**: snake_case, type hints, docstrings. Comments and some variable names are in Chinese.
- **Vue/JS**: ES6 modules, Composition API, no TypeScript, no explicit linting.
- **LLM integration**: All providers must support OpenAI API format. Single `LLMClient` wrapper.
- **Package managers**: `uv` for Python (not pip), `npm` for Node at root level.
- **Git commits**: Semantic format (`feat(graph):`, `fix:`, `docs(readme):`).
- **Deployment**: Docker multi-stage build, GitHub Actions CI pushes to ghcr.io on tag.
