# AI-Powered Seed Data Generator Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let users generate research-backed seed data from just a topic idea, using Perplexity Sonar for live web research, eliminating the need to prepare documents manually.

**Architecture:** New `SeedGenerator` service calls gpt-4.1-mini to analyze topics into categories, then Perplexity Sonar (sonar-pro/sonar-deep-research) to generate web-grounded research files. New `seed_bp` blueprint exposes 4 endpoints. Frontend adds a `SeedGeneratorModal.vue` component triggered when user launches with no files.

**Tech Stack:** Python/Flask (backend), Perplexity API via OpenAI SDK, Vue 3 (frontend), existing TaskManager for async progress.

**Spec:** `docs/superpowers/specs/2026-03-17-ai-seed-generator-design.md`

---

## Chunk 1: Backend Config & Service

### Task 1: Add Perplexity config

**Files:**
- Modify: `backend/app/config.py`
- Modify: `.env`

- [ ] **Step 1: Add Perplexity config to Config class**

In `backend/app/config.py`, add after the `OUTPUT_LANGUAGE` line:

```python
# Perplexity API (for seed data generation with web search)
PERPLEXITY_API_KEY = os.environ.get('PERPLEXITY_API_KEY')
PERPLEXITY_MODEL = os.environ.get('PERPLEXITY_MODEL', 'sonar-pro')
PERPLEXITY_MODEL_DEEP = os.environ.get('PERPLEXITY_MODEL_DEEP', 'sonar-deep-research')
```

- [ ] **Step 2: Add PERPLEXITY_API_KEY to `.env`**

```env
# Perplexity API (for AI seed data generation)
PERPLEXITY_API_KEY=your_perplexity_api_key
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/config.py .env
git commit -m "feat(seed): add Perplexity API config for seed generation"
```

---

### Task 2: Add seed generation prompts

**Files:**
- Modify: `backend/app/i18n/prompts.py`

- [ ] **Step 1: Add `seed_analyze_prompt` to PROMPTS dict**

Add to the end of the PROMPTS dict in `backend/app/i18n/prompts.py`:

```python
# ═══════════════════════════════════════════════════════════════════════════
# 5. SEED DATA GENERATOR
# ═══════════════════════════════════════════════════════════════════════════

'seed_analyze_prompt': {
    'en': """\
You are an expert research strategist. Given a simulation topic, suggest 3-5 categories of background research that would produce the most realistic social media simulation.

Consider these dimensions:
- Historical precedents (similar events that happened before)
- Key stakeholders and their positions
- Social media dynamics and public sentiment patterns
- Political/regulatory landscape
- Economic data and impact analysis

For each category, provide:
- id: short snake_case identifier
- name: human-readable category name
- description: one sentence explaining what this research covers
- recommended: true if essential, false if optional

Return a JSON object: {"categories": [...]}

Tailor categories to the specific topic — a political event needs different research than a product launch or natural disaster.""",

    'ms': """\
Anda adalah pakar strategi penyelidikan. Diberikan topik simulasi, cadangkan 3-5 kategori penyelidikan latar belakang yang akan menghasilkan simulasi media sosial yang paling realistik.

Pertimbangkan dimensi ini:
- Preseden sejarah (peristiwa serupa yang pernah berlaku)
- Pihak berkepentingan utama dan pendirian mereka
- Dinamik media sosial dan corak sentimen awam
- Landskap politik/peraturan
- Data ekonomi dan analisis impak

Untuk setiap kategori, berikan:
- id: pengecam snake_case pendek
- name: nama kategori yang boleh dibaca
- description: satu ayat menerangkan apa yang diliputi penyelidikan ini
- recommended: true jika penting, false jika pilihan

Kembalikan objek JSON: {"categories": [...]}""",
},

'seed_generate_prompt': {
    'en': """\
You are a research analyst preparing comprehensive background material for a social media public-opinion simulation engine called ARUS.

Your task: Write a detailed research document about the specified category related to the given topic.

Requirements:
- Include real events, statistics, named individuals/organizations, and timelines
- Quote specific numbers, dates, and facts
- Describe key actors: their roles, positions, motivations, and likely social media behavior
- Cover social media reactions and public sentiment patterns where relevant
- Include multiple perspectives (government, opposition, public, media, international)
- Cite your sources with URLs where possible
- Write in markdown format with clear headers and sections
- Be comprehensive: 2,000-5,000 words
- Focus on information that helps create realistic simulated agents with distinct personalities and viewpoints

This document will be used as "seed data" to generate AI agents who will simulate social media discussions about this topic.""",

    'ms': """\
Anda adalah penganalisis penyelidikan yang menyediakan bahan latar belakang komprehensif untuk enjin simulasi pendapat awam media sosial dipanggil ARUS.

Tugas anda: Tulis dokumen penyelidikan terperinci tentang kategori yang dinyatakan berkaitan dengan topik yang diberikan.

Keperluan:
- Sertakan peristiwa sebenar, statistik, individu/organisasi yang dinamakan, dan garis masa
- Petik nombor, tarikh, dan fakta tertentu
- Terangkan aktor utama: peranan, pendirian, motivasi, dan tingkah laku media sosial mereka yang mungkin
- Liputi reaksi media sosial dan corak sentimen awam di mana berkaitan
- Sertakan pelbagai perspektif (kerajaan, pembangkang, awam, media, antarabangsa)
- Petik sumber anda dengan URL di mana mungkin
- Tulis dalam format markdown dengan tajuk dan bahagian yang jelas
- Jadilah komprehensif: 2,000-5,000 patah perkataan""",
},
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/i18n/prompts.py
git commit -m "feat(seed): add seed analysis and generation prompts"
```

---

### Task 3: Create SeedGenerator service

**Files:**
- Create: `backend/app/services/seed_generator.py`

- [ ] **Step 1: Create the service**

```python
"""
Seed data generator service.

Uses gpt-4.1-mini to analyze topics into research categories,
then Perplexity Sonar to generate web-grounded research files.
"""

import os
import json
import uuid
import threading
from typing import Optional
from openai import OpenAI

from ..config import Config
from ..utils.llm_client import LLMClient
from ..utils.logger import get_logger
from ..i18n import get_prompt

logger = get_logger('arus.seed')


class SeedTask:
    """Tracks progress of a seed generation task."""

    def __init__(self, task_id: str, categories: list, depth: str):
        self.task_id = task_id
        self.categories = categories
        self.depth = depth
        self.status = 'running'
        self.progress = 0
        self.current_file = ''
        self.completed_files = []
        self.error = None

    def to_dict(self):
        return {
            'task_id': self.task_id,
            'status': self.status,
            'progress': self.progress,
            'current_file': self.current_file,
            'completed_files': self.completed_files,
            'error': self.error,
        }


class SeedGenerator:
    """Generates research-backed seed data using Perplexity Sonar."""

    # In-memory task store
    _tasks: dict[str, SeedTask] = {}

    def __init__(self):
        self.llm = LLMClient()

        if not Config.PERPLEXITY_API_KEY:
            raise ValueError('PERPLEXITY_API_KEY is not configured')

        self.perplexity = OpenAI(
            api_key=Config.PERPLEXITY_API_KEY,
            base_url='https://api.perplexity.ai',
        )

        self.output_dir = os.path.join(Config.UPLOAD_FOLDER, 'seed')
        os.makedirs(self.output_dir, exist_ok=True)

    def analyze_topic(self, prompt: str) -> list[dict]:
        """Use gpt-4.1-mini to suggest research categories for a topic."""
        logger.info(f'Analyzing topic: {prompt[:100]}...')

        system_prompt = get_prompt('seed_analyze_prompt')
        result = self.llm.chat_json(
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': prompt},
            ],
            temperature=0.7,
            max_tokens=2048,
        )

        categories = result.get('categories', [])
        logger.info(f'Suggested {len(categories)} categories')
        return categories

    def generate_file(self, prompt: str, category: dict, depth: str) -> str:
        """Use Perplexity Sonar to generate one seed file with live web research."""
        model = Config.PERPLEXITY_MODEL_DEEP if depth == 'thorough' else Config.PERPLEXITY_MODEL
        system_prompt = get_prompt('seed_generate_prompt')

        user_message = (
            f"Topic: {prompt}\n\n"
            f"Category: {category['name']}\n"
            f"Description: {category.get('description', '')}\n\n"
            f"Write a comprehensive research document about this category "
            f"as it relates to the topic above."
        )

        logger.info(f'Generating seed file: {category["name"]} (model={model})')

        response = self.perplexity.chat.completions.create(
            model=model,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_message},
            ],
        )

        content = response.choices[0].message.content
        logger.info(f'Generated {len(content)} chars for {category["name"]}')
        return content

    def start_generation(self, prompt: str, categories: list, depth: str) -> str:
        """Start async seed generation. Returns task_id."""
        task_id = str(uuid.uuid4())[:12]
        task = SeedTask(task_id, categories, depth)
        self._tasks[task_id] = task

        task_dir = os.path.join(self.output_dir, task_id)
        os.makedirs(task_dir, exist_ok=True)

        thread = threading.Thread(
            target=self._generate_all,
            args=(prompt, categories, depth, task),
            daemon=True,
        )
        thread.start()

        return task_id

    def _generate_all(self, prompt: str, categories: list, depth: str, task: SeedTask):
        """Generate all seed files in background thread."""
        total = len(categories)
        task_dir = os.path.join(self.output_dir, task.task_id)

        try:
            for i, category in enumerate(categories):
                cat_name = category.get('name', f'category_{i+1}')
                task.current_file = cat_name
                task.progress = int((i / total) * 100)

                # Generate content via Perplexity
                content = self.generate_file(prompt, category, depth)

                # Save to disk
                filename = f"{category.get('id', f'cat_{i+1}')}.md"
                filepath = os.path.join(task_dir, filename)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"# {cat_name}\n\n{content}")

                task.completed_files.append({
                    'name': filename,
                    'display_name': cat_name,
                    'path': filepath,
                    'size': len(content),
                })

            task.status = 'completed'
            task.progress = 100
            task.current_file = ''
            logger.info(f'Seed generation complete: {task.task_id}, {len(task.completed_files)} files')

        except Exception as e:
            task.status = 'failed'
            task.error = str(e)
            logger.error(f'Seed generation failed: {task.task_id}: {e}')

    def get_task(self, task_id: str) -> Optional[SeedTask]:
        """Get task by ID."""
        return self._tasks.get(task_id)

    def get_file_content(self, task_id: str, filename: str) -> Optional[str]:
        """Read content of a generated seed file."""
        filepath = os.path.join(self.output_dir, task_id, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        return None

    def get_file_path(self, task_id: str, filename: str) -> Optional[str]:
        """Get absolute path of a generated seed file."""
        filepath = os.path.join(self.output_dir, task_id, filename)
        if os.path.exists(filepath):
            return filepath
        return None
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/services/seed_generator.py
git commit -m "feat(seed): create SeedGenerator service with Perplexity integration"
```

---

### Task 4: Create seed API blueprint

**Files:**
- Create: `backend/app/api/seed.py`
- Modify: `backend/app/api/__init__.py`
- Modify: `backend/app/__init__.py`

- [ ] **Step 1: Create the API blueprint**

Create `backend/app/api/seed.py`:

```python
"""
Seed data generation API endpoints.
"""

import os
from flask import Blueprint, request, jsonify, send_file

from ..utils.logger import get_logger
from ..services.seed_generator import SeedGenerator

logger = get_logger('arus.api.seed')

seed_bp = Blueprint('seed', __name__)

# Lazy-initialized generator (avoids error if PERPLEXITY_API_KEY not set)
_generator = None


def _get_generator():
    global _generator
    if _generator is None:
        _generator = SeedGenerator()
    return _generator


@seed_bp.route('/analyze', methods=['POST'])
def analyze_topic():
    """Analyze a topic and suggest research categories."""
    try:
        data = request.get_json()
        prompt = data.get('prompt', '').strip()

        if not prompt:
            return jsonify(success=False, error='Prompt is required'), 400

        generator = _get_generator()
        categories = generator.analyze_topic(prompt)

        return jsonify(success=True, categories=categories)

    except ValueError as e:
        return jsonify(success=False, error=str(e)), 400
    except Exception as e:
        logger.error(f'Topic analysis failed: {e}')
        return jsonify(success=False, error=str(e)), 500


@seed_bp.route('/generate', methods=['POST'])
def generate_seed():
    """Start seed data generation."""
    try:
        data = request.get_json()
        prompt = data.get('prompt', '').strip()
        categories = data.get('categories', [])
        depth = data.get('depth', 'quick')

        if not prompt:
            return jsonify(success=False, error='Prompt is required'), 400
        if not categories:
            return jsonify(success=False, error='At least one category is required'), 400
        if depth not in ('quick', 'thorough'):
            return jsonify(success=False, error='Depth must be "quick" or "thorough"'), 400
        if len(categories) > 5:
            return jsonify(success=False, error='Maximum 5 categories allowed'), 400

        generator = _get_generator()
        task_id = generator.start_generation(prompt, categories, depth)

        return jsonify(success=True, task_id=task_id)

    except ValueError as e:
        return jsonify(success=False, error=str(e)), 400
    except Exception as e:
        logger.error(f'Seed generation start failed: {e}')
        return jsonify(success=False, error=str(e)), 500


@seed_bp.route('/task/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """Poll seed generation progress."""
    try:
        generator = _get_generator()
        task = generator.get_task(task_id)

        if not task:
            return jsonify(success=False, error='Task not found'), 404

        return jsonify(success=True, **task.to_dict())

    except Exception as e:
        logger.error(f'Task status check failed: {e}')
        return jsonify(success=False, error=str(e)), 500


@seed_bp.route('/file/<task_id>/<filename>', methods=['GET'])
def get_seed_file(task_id, filename):
    """Get content of a generated seed file."""
    try:
        generator = _get_generator()
        content = generator.get_file_content(task_id, filename)

        if content is None:
            return jsonify(success=False, error='File not found'), 404

        return jsonify(success=True, content=content, filename=filename)

    except Exception as e:
        logger.error(f'File retrieval failed: {e}')
        return jsonify(success=False, error=str(e)), 500
```

- [ ] **Step 2: Export seed_bp from `backend/app/api/__init__.py`**

Add to the existing imports:

```python
from .seed import seed_bp
```

- [ ] **Step 3: Register seed_bp in `backend/app/__init__.py`**

Add after the existing blueprint registrations:

```python
app.register_blueprint(seed_bp, url_prefix='/api/seed')
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/seed.py backend/app/api/__init__.py backend/app/__init__.py
git commit -m "feat(seed): add seed API blueprint with analyze/generate/poll endpoints"
```

---

## Chunk 2: Frontend

### Task 5: Add seed API client

**Files:**
- Create: `frontend/src/api/seed.js`

- [ ] **Step 1: Create the API client**

```javascript
import service from './index.js';

/**
 * Analyze a topic and get suggested research categories.
 */
export const analyzeTopicAPI = (prompt) => {
  return service.post('/api/seed/analyze', { prompt });
};

/**
 * Start seed data generation.
 */
export const generateSeedAPI = (prompt, categories, depth) => {
  return service.post('/api/seed/generate', { prompt, categories, depth });
};

/**
 * Poll seed generation progress.
 */
export const getSeedTaskAPI = (taskId) => {
  return service.get(`/api/seed/task/${taskId}`);
};

/**
 * Get content of a generated seed file.
 */
export const getSeedFileAPI = (taskId, filename) => {
  return service.get(`/api/seed/file/${taskId}/${filename}`);
};
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/api/seed.js
git commit -m "feat(seed): add seed API client functions"
```

---

### Task 6: Create SeedGeneratorModal component

**Files:**
- Create: `frontend/src/components/SeedGeneratorModal.vue`

- [ ] **Step 1: Create the modal component**

This component handles the full seed generation flow:
- Phase 0: "No seed data" prompt with "Generate" button
- Phase 1: Category checklist + depth selector
- Phase 2: Progress bar during generation
- Phase 3: Complete — files ready

The component should:
1. Accept `prompt` as a prop (the simulation requirement text)
2. Emit `'files-ready'` with array of `{ name, displayName, taskId, filename }` when complete
3. Emit `'close'` when dismissed

Key UI elements:
- Category checklist with checkboxes (pre-checked for recommended ones)
- Depth toggle: Quick / Thorough with descriptions
- Progress bar showing current file being generated
- List of completed files with preview buttons

Style: Match existing ARUS monochrome design (black/white, JetBrains Mono font, minimal borders)

Size: ~300 lines. Full implementation with template, script setup, and scoped styles.

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/SeedGeneratorModal.vue
git commit -m "feat(seed): create SeedGeneratorModal component"
```

---

### Task 7: Integrate into Home.vue

**Files:**
- Modify: `frontend/src/views/Home.vue`

- [ ] **Step 1: Import and wire up SeedGeneratorModal**

In Home.vue:

1. Import the modal and seed API
2. Add a `showSeedModal` ref
3. Modify `startSimulation()`: if no files uploaded, show the seed modal instead of navigating
4. Add handler for `files-ready` event: convert generated files into File objects and add to `files` array
5. Add the `<SeedGeneratorModal>` to the template

Key changes:
- In `startSimulation()`, check `files.value.length === 0` → set `showSeedModal.value = true` instead of navigating
- When seed files are ready, fetch each file's content, create File objects, push to `files.value`
- User can then click "Launch Engine" again with the generated files in the upload zone

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/Home.vue
git commit -m "feat(seed): integrate seed generator into Home.vue launch flow"
```

---

## Chunk 3: Integration & Polish

### Task 8: Add i18n strings for seed generator

**Files:**
- Modify: `frontend/src/i18n/en.js`
- Modify: `frontend/src/i18n/ms.js`

- [ ] **Step 1: Add English strings**

Add to `frontend/src/i18n/en.js`:

```javascript
// Seed Generator
'seed.banner': 'No seed data uploaded. Want ARUS to research and generate it for you?',
'seed.generate': 'Generate Research Data',
'seed.selectCategories': 'Select research categories',
'seed.depth': 'Research depth',
'seed.quick': 'Quick',
'seed.quickDesc': 'Broader web search, concise reports (~1 min)',
'seed.thorough': 'Thorough',
'seed.thoroughDesc': 'Exhaustive research, hundreds of sources (~3 min)',
'seed.startResearch': 'Start Research',
'seed.researching': 'Researching',
'seed.complete': 'Research complete!',
'seed.filesReady': 'files ready. Review and launch when ready.',
'seed.preview': 'Preview',
'seed.cancel': 'Cancel',
'seed.error': 'Research generation failed',
```

- [ ] **Step 2: Add Malay strings**

Add equivalent translations to `frontend/src/i18n/ms.js`.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/i18n/en.js frontend/src/i18n/ms.js
git commit -m "feat(seed): add i18n strings for seed generator"
```

---

### Task 9: Test end-to-end

- [ ] **Step 1: Set PERPLEXITY_API_KEY in .env**

Get a key from https://www.perplexity.ai/settings/api and add to `.env`.

- [ ] **Step 2: Start dev server and test the flow**

1. Go to http://localhost:3000
2. Type a simulation prompt (e.g., "What happens after Malaysia fuel subsidy cut?")
3. Click "Launch Engine" with no files uploaded
4. Verify the seed generator modal appears
5. Verify categories are suggested
6. Select categories, choose depth, click "Start Research"
7. Verify progress bar updates
8. Verify completed files appear in upload zone
9. Click "Launch Engine" again — verify normal ARUS flow starts

- [ ] **Step 3: Test with existing files**

1. Upload 1 file manually
2. Click "Launch Engine"
3. Verify it proceeds normally (no seed modal shown)

- [ ] **Step 4: Push to remote and deploy**

```bash
git push origin main
railway up --detach
```

- [ ] **Step 5: Update Railway env vars**

```bash
railway variables set PERPLEXITY_API_KEY=your_key
```
