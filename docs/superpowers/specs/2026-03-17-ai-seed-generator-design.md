# AI-Powered Seed Data Generator

## Problem

ARUS requires users to upload seed data files (PDF/MD/TXT) before running simulations. Most users don't have pre-prepared documents — they just have a topic idea or a question they want to simulate. This friction blocks adoption.

## Solution

When a user types a simulation prompt but uploads no files, ARUS offers to automatically research and generate seed data using **Perplexity Sonar** — an LLM with native web search built in. One API call per seed file: Sonar searches the live web, synthesizes findings, and returns a comprehensive research document with citations. No separate scraping or search orchestration needed.

## Provider Architecture

- **Perplexity Sonar** (`sonar`) — used ONLY for seed data generation (web-grounded research)
- **OpenAI gpt-4.1-mini** — used for everything else (ontology, profiles, reports, simulation config)

Perplexity uses the OpenAI SDK format, so we reuse the existing `LLMClient` class with different `base_url` and `model` parameters. Two providers, each doing what they're best at.

## User Flow

1. User types prompt in the simulation requirement box (e.g., "What happens if Malaysia removes RON95 subsidy?")
2. User clicks "Launch Engine" with no files uploaded
3. Banner appears: "No seed data uploaded. Want ARUS to research and generate it for you?"
4. User clicks "Generate" → gpt-4.1-mini analyzes prompt and returns 3-5 suggested data categories as a checklist:
   - ☑ Historical Precedents
   - ☑ Policy & Stakeholder Analysis
   - ☑ Social Media Dynamics
   - ☑ Political Landscape
   - ☐ Economic Data & Statistics (optional)
5. User toggles categories on/off and selects depth:
   - **Quick** (~1 min) — broader web search, concise reports (~2,000-3,000 words per file, uses `sonar-pro`)
   - **Thorough** (~3 min) — exhaustive research, hundreds of sources, comprehensive reports (~5,000 words per file, uses `sonar-deep-research`)
6. User clicks "Start Research"
7. Progress bar shows per-file status: `Researching historical precedents... ████████░░ 80%`
8. Completed files appear in the upload zone as they finish — user can preview, edit, or remove
9. When all files are ready, user clicks "Launch Engine" → normal ARUS flow continues

## Alternative entry: User has some files

If user uploads 1-2 files but the LLM detects gaps (e.g., has policy analysis but no historical context), offer: "Want to supplement with AI-generated research on [missing categories]?"

## Backend

### New Config

Add to `backend/app/config.py`:
```python
PERPLEXITY_API_KEY = os.environ.get('PERPLEXITY_API_KEY')
PERPLEXITY_MODEL = os.environ.get('PERPLEXITY_MODEL', 'sonar-pro')
PERPLEXITY_MODEL_DEEP = os.environ.get('PERPLEXITY_MODEL_DEEP', 'sonar-deep-research')
```

### New API Endpoints

New blueprint: `seed_bp` in `backend/app/api/seed.py`

**`POST /api/seed/analyze`**
- Input: `{ prompt: string }`
- Uses gpt-4.1-mini to analyze the topic and suggest research categories
- Output: `{ categories: [{ id: string, name: string, description: string, recommended: boolean }] }`

**`POST /api/seed/generate`**
- Input: `{ prompt: string, categories: string[], depth: "quick" | "thorough" }`
- Creates async task, generates files sequentially using Perplexity Sonar
- Output: `{ task_id: string }`

**`GET /api/seed/task/{taskId}`**
- Polls generation progress
- Output: `{ status: "running" | "completed" | "failed", progress: number, current_file: string, completed_files: [{ name: string, path: string, size: number }] }`

**`GET /api/seed/file/{taskId}/{filename}`**
- Returns content of a generated seed file for preview
- Output: file content as text

### New Service: `SeedGenerator`

Location: `backend/app/services/seed_generator.py`

```python
class SeedGenerator:
    def __init__(self):
        # Primary LLM for category analysis
        self.llm = LLMClient()  # gpt-4.1-mini (existing)

        # Perplexity client for web-grounded research
        self.perplexity = OpenAI(
            api_key=Config.PERPLEXITY_API_KEY,
            base_url="https://api.perplexity.ai"
        )

    def analyze_topic(self, prompt: str) -> list[dict]:
        """Use gpt-4.1-mini to suggest research categories."""
        ...

    def generate_file(self, prompt: str, category: dict, depth: str) -> str:
        """Use Perplexity Sonar to generate one seed file."""
        model = Config.PERPLEXITY_MODEL_DEEP if depth == "thorough" else Config.PERPLEXITY_MODEL
        response = self.perplexity.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SEED_SYSTEM_PROMPT},
                {"role": "user", "content": f"Research: {category['name']} for topic: {prompt}"}
            ]
        )
        return response.choices[0].message.content

    def generate_all(self, prompt: str, categories: list, depth: str, task_id: str):
        """Generate all seed files, updating progress per file."""
        ...
```

### LLM Prompts

Add to `backend/app/i18n/prompts.py`:

1. **`seed_analyze_prompt`** — System prompt for gpt-4.1-mini:
   "Given this simulation topic, suggest 3-5 categories of background research that would create the most realistic simulation. Consider: historical precedents, stakeholder analysis, social media dynamics, political/economic context. Return JSON array."

2. **`seed_generate_prompt`** — System prompt for Perplexity Sonar:
   "You are a research analyst preparing background material for a social media simulation. Write a comprehensive research document about [category] related to [topic]. Include: real events, statistics, key actors, timelines, social media reactions. Cite your sources with URLs. Write 2,000-5,000 words in markdown format."

### Data Flow

```
User prompt
    ↓
POST /api/seed/analyze (gpt-4.1-mini)
    ↓
Returns 3-5 suggested categories
    ↓
User selects categories + depth
    ↓
POST /api/seed/generate
    ↓
For each category (sequential):
    → Perplexity Sonar: one API call
      (searches web + synthesizes + cites sources)
    → Save .md file to disk
    → Update progress
    ↓
Files ready in upload zone
    ↓
User clicks "Launch Engine"
    ↓
Normal ARUS flow (ontology → graph → simulation → report)
```

### Dependencies

- `openai` (already installed) — Perplexity uses the same SDK
- Existing `TaskManager` pattern for async progress tracking
- New env var: `PERPLEXITY_API_KEY`

## Frontend

### Home.vue Changes

1. **Seed generation banner** — shown when user clicks "Launch Engine" with no files:
   - Appears as a modal/overlay
   - Contains category checklist + depth selector (Quick/Thorough)
   - "Start Research" button

2. **Progress display** — replaces/overlays the upload zone during generation:
   - Per-file progress bar with current status text
   - Files appear in upload zone as they complete

3. **Preview** — clicking a generated file shows its content in a read-only modal

### New Components

- `SeedGeneratorModal.vue` — category checklist + depth selector + progress display
- No other new components needed; generated files reuse existing file list UI

## Constraints

- Max 5 categories per generation
- Each seed file: 2,000-5,000 words depending on depth
- Total generation time: ~1 min (quick), ~3 min (thorough)
- Files saved as `.md` in `backend/uploads/seed/{task_id}/`
- Cleanup: seed files deleted after 24 hours or when simulation starts

## Cost

- **Quick mode** (sonar-pro): ~$0.01 per seed file
- **Thorough mode** (sonar-deep-research): ~$0.04 per seed file
- **Category analysis** (gpt-4.1-mini): ~$0.001 per request
- Total per simulation: $0.02-0.25 depending on depth and number of categories

## Success Criteria

- User can go from "just a topic idea" to a running simulation without preparing any documents
- Generated seed data includes real, recent information with source citations
- Generated data produces realistic, diverse agent profiles
- User maintains control: can preview, edit, remove, or add their own files alongside generated ones
