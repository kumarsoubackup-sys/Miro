# i18n: English & Malay Language Support

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace all hardcoded Chinese LLM prompts and UI strings with configurable English/Malay support so that MiroFish generates all output (agent profiles, ontology, reports, progress messages) in the user's chosen language.

**Architecture:** Add an `OUTPUT_LANGUAGE` env var (`en` or `ms`) to `config.py`. Create a `backend/app/i18n/` module with prompt templates and UI string translations for both languages. Each service reads its prompts from the i18n module instead of hardcoding Chinese. The frontend adds a language toggle that sends the language preference to the backend via API and switches its own UI strings.

**Tech Stack:** Python (backend prompts/strings), Vue 3 (frontend i18n), env var config

---

## Chunk 1: Backend Language Configuration & i18n Module

### Task 1: Add language config to `backend/app/config.py`

**Files:**
- Modify: `backend/app/config.py`

- [ ] **Step 1: Add OUTPUT_LANGUAGE to Config class**

Add after `ZEP_API_KEY` (around line 37):

```python
# Language configuration
OUTPUT_LANGUAGE = os.environ.get('OUTPUT_LANGUAGE', 'en')  # 'en' or 'ms'
```

- [ ] **Step 2: Add validation for OUTPUT_LANGUAGE**

In the `validate()` method, add:

```python
if cls.OUTPUT_LANGUAGE not in ('en', 'ms'):
    errors.append("OUTPUT_LANGUAGE must be 'en' or 'ms'")
```

- [ ] **Step 3: Add `OUTPUT_LANGUAGE=en` to `.env`**

- [ ] **Step 4: Commit**

```bash
git add backend/app/config.py .env
git commit -m "feat(i18n): add OUTPUT_LANGUAGE config (en/ms)"
```

---

### Task 2: Create i18n module structure

**Files:**
- Create: `backend/app/i18n/__init__.py`
- Create: `backend/app/i18n/prompts.py`
- Create: `backend/app/i18n/strings.py`

- [ ] **Step 1: Create `backend/app/i18n/__init__.py`**

```python
from .prompts import get_prompt
from .strings import get_string
```

- [ ] **Step 2: Create `backend/app/i18n/prompts.py`**

This is the core file. It holds all LLM prompt templates keyed by `(prompt_name, language)`. Each prompt has an `en` and `ms` version.

Structure:

```python
from ..config import Config

PROMPTS = {
    'ontology_system': {
        'en': """You are a professional knowledge graph ontology design expert...""",
        'ms': """Anda adalah pakar reka bentuk ontologi graf pengetahuan profesional...""",
    },
    'profile_system': {
        'en': ...,
        'ms': ...,
    },
    # ... all other prompts
}

def get_prompt(name: str, lang: str = None, **kwargs) -> str:
    lang = lang or Config.OUTPUT_LANGUAGE
    template = PROMPTS[name][lang]
    return template.format(**kwargs) if kwargs else template
```

- [ ] **Step 3: Create `backend/app/i18n/strings.py`**

For user-facing progress messages, error messages, and agent action descriptions:

```python
from ..config import Config

STRINGS = {
    'building_graph': {
        'en': 'Building graph...',
        'ms': 'Membina graf...',
    },
    'graph_created': {
        'en': 'Graph created: {graph_id}',
        'ms': 'Graf dicipta: {graph_id}',
    },
    # ... all other user-facing strings
}

def get_string(name: str, lang: str = None, **kwargs) -> str:
    lang = lang or Config.OUTPUT_LANGUAGE
    template = STRINGS[name][lang]
    return template.format(**kwargs) if kwargs else template
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/i18n/
git commit -m "feat(i18n): create i18n module with prompt and string templates"
```

---

## Chunk 2: Translate LLM Prompts (HIGH priority)

These are the prompts that directly control what language the LLM outputs. This is why agent profiles appear in Chinese.

### Task 3: Translate ontology generator prompts

**Files:**
- Modify: `backend/app/services/ontology_generator.py`
- Modify: `backend/app/i18n/prompts.py`

The entire `ONTOLOGY_SYSTEM_PROMPT` constant (lines 12-155) is a ~145-line Chinese prompt. The user prompt template (lines 228-255) is also Chinese.

- [ ] **Step 1: Add `ontology_system` prompt to `i18n/prompts.py`**

Translate the full system prompt (lines 12-155 of `ontology_generator.py`) to English and Malay. Key sections to translate:
- Core task background (lines 18-37): what entities can/cannot be
- Output format (lines 39-71): JSON schema instructions
- Design guidelines (lines 73-155): entity/relationship type rules, reference types

Important: Keep all JSON field names, PascalCase/snake_case conventions, and structural requirements identical. Only translate the instructional Chinese text.

- [ ] **Step 2: Add `ontology_user` prompt template to `i18n/prompts.py`**

Translate the user message template (lines 228-255) with `{document_text}`, `{simulation_requirement}`, `{truncation_notice}` placeholders.

- [ ] **Step 3: Update `ontology_generator.py` to use i18n prompts**

Replace the hardcoded `ONTOLOGY_SYSTEM_PROMPT` constant with:

```python
from ..i18n import get_prompt
```

In the method that builds messages, replace direct use of `ONTOLOGY_SYSTEM_PROMPT` with `get_prompt('ontology_system')` and the user prompt with `get_prompt('ontology_user', ...)`.

- [ ] **Step 4: Test that ontology generation produces English output**

Run the app, upload a test document, trigger graph building, verify entity types and analysis_summary come back in English.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/ontology_generator.py backend/app/i18n/prompts.py
git commit -m "feat(i18n): translate ontology generator prompts to en/ms"
```

---

### Task 4: Translate profile generator prompts

**Files:**
- Modify: `backend/app/services/oasis_profile_generator.py`
- Modify: `backend/app/i18n/prompts.py`

Three Chinese prompts to translate:

1. **System prompt** (line 673): `"你是社交媒体用户画像生成专家...使用中文。"`
2. **Individual persona prompt** (lines 689-723): Full prompt with field descriptions
3. **Group persona prompt** (lines 738-771): Full prompt with field descriptions

- [ ] **Step 1: Add `profile_system`, `profile_individual`, `profile_group` prompts to `i18n/prompts.py`**

Translate all three prompts. Key changes:
- Remove `"使用中文"` instruction, replace with `"Use English"` / `"Gunakan Bahasa Melayu"`
- Change `country` field guidance from `"中国"` to `"Malaysia"` (for `ms`) or appropriate default
- Translate all field descriptions and instructions
- Keep JSON field names unchanged (`bio`, `persona`, `age`, `gender`, `mbti`, etc.)

- [ ] **Step 2: Update `oasis_profile_generator.py` to use i18n prompts**

In `_get_system_prompt()` (line 671): replace hardcoded Chinese with `get_prompt('profile_system')`.

In `_build_individual_persona_prompt()` (line 676): replace with `get_prompt('profile_individual', entity_name=..., ...)`.

In `_build_group_persona_prompt()` (line 725): replace with `get_prompt('profile_group', entity_name=..., ...)`.

- [ ] **Step 3: Update fallback rule-based generation**

Check `_generate_profile_rule_based()` (line 773+) — this uses English templates already but verify.

Also fix the fallback on line 668: `f"{entity_name}是一个{entity_type}。"` → use English/Malay.

- [ ] **Step 4: Test profile generation produces English output**

Run a simulation prepare step, verify agent bios and personas are in English.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/oasis_profile_generator.py backend/app/i18n/prompts.py
git commit -m "feat(i18n): translate profile generator prompts to en/ms"
```

---

### Task 5: Translate report agent prompts

**Files:**
- Modify: `backend/app/services/report_agent.py`
- Modify: `backend/app/i18n/prompts.py`

Three large prompt blocks to translate:

1. **PLAN_SYSTEM_PROMPT** (lines 551-588): ~38 lines — report planning instructions
2. **PLAN_USER_PROMPT_TEMPLATE** (lines 590-610): ~21 lines — with placeholders for simulation data
3. **SECTION_SYSTEM_PROMPT_TEMPLATE** (lines 614-714): ~100 lines — section writing instructions including formatting rules, tool usage guidance

- [ ] **Step 1: Add `report_plan_system`, `report_plan_user`, `report_section_system` prompts to `i18n/prompts.py`**

Translate all three. Key changes:
- Line 656: Replace conditional Chinese language rule with appropriate English/Malay instruction
- Keep the formatting rules (no markdown headers in sections, use bold/quotes/lists)
- Keep tool names unchanged (`insight_forge`, `panorama_search`, `quick_search`, `interview_agents`)
- Translate the correct/incorrect formatting examples

- [ ] **Step 2: Translate tool descriptions (lines 476-547)**

These are `TOOL_DESC_*` constants describing each tool for the LLM. Add to `i18n/prompts.py` as `tool_desc_insight_forge`, `tool_desc_panorama_search`, etc.

- [ ] **Step 3: Update `report_agent.py` to use i18n prompts**

Replace all hardcoded prompt constants with `get_prompt(...)` calls.

- [ ] **Step 4: Test report generation produces English output**

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/report_agent.py backend/app/i18n/prompts.py
git commit -m "feat(i18n): translate report agent prompts to en/ms"
```

---

### Task 6: Translate simulation config generator prompts

**Files:**
- Modify: `backend/app/services/simulation_config_generator.py`
- Modify: `backend/app/i18n/prompts.py`

Three LLM prompts to translate:

1. **Time config prompt** (lines 542-587): System prompt for generating time-based simulation config. Remove `"符合中国人作息习惯"` (Chinese daily routine pattern) reference.
2. **Event config prompt** (lines 674-703): System prompt for generating events and hot topics.
3. **Agent config prompt** (lines 830-866): System prompt for agent activity patterns. Remove `"符合中国人作息习惯"` reference.

- [ ] **Step 1: Add `sim_time_config`, `sim_event_config`, `sim_agent_config` prompts to `i18n/prompts.py`**

Translate all three. Key changes:
- Replace "Chinese daily routine" references with locale-appropriate defaults (e.g., Malaysian timezone, general activity patterns)
- Translate the default time config docstring (line 596) and reasoning text (line 606)

- [ ] **Step 2: Update `simulation_config_generator.py` to use i18n prompts**

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/simulation_config_generator.py backend/app/i18n/prompts.py
git commit -m "feat(i18n): translate simulation config prompts to en/ms"
```

---

## Chunk 3: Translate User-Facing Strings (MEDIUM priority)

### Task 7: Translate progress/error messages in backend services

**Files:**
- Modify: `backend/app/i18n/strings.py`
- Modify: `backend/app/services/graph_builder.py`
- Modify: `backend/app/services/simulation_runner.py`
- Modify: `backend/app/services/simulation_config_generator.py`

- [ ] **Step 1: Add all user-facing strings to `i18n/strings.py`**

Catalog from exploration results — approximately 30+ strings across:
- `graph_builder.py`: ~15 progress messages (lines 112-395)
- `simulation_runner.py`: ~5 error/status messages (lines 336, 343, etc.)
- `simulation_config_generator.py`: ~8 progress messages (lines 295-376)

- [ ] **Step 2: Update each service to use `get_string()`**

Replace each Chinese string literal with `get_string('key_name', param=value)`.

- [ ] **Step 3: Commit**

```bash
git add backend/app/i18n/strings.py backend/app/services/graph_builder.py backend/app/services/simulation_runner.py backend/app/services/simulation_config_generator.py
git commit -m "feat(i18n): translate user-facing progress and error messages"
```

---

### Task 8: Translate agent action descriptions in zep_graph_memory_updater.py

**Files:**
- Modify: `backend/app/services/zep_graph_memory_updater.py`
- Modify: `backend/app/i18n/strings.py`

~40 Chinese action description strings (lines 25-198) that describe what agents did in the simulation (e.g., `"发布了一条帖子"` → "Published a post" / "Menerbitkan siaran"). These are written to Zep graph memory and later read by the report agent.

- [ ] **Step 1: Add all action description strings to `i18n/strings.py`**

- [ ] **Step 2: Update `zep_graph_memory_updater.py` to use `get_string()`**

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/zep_graph_memory_updater.py backend/app/i18n/strings.py
git commit -m "feat(i18n): translate agent action descriptions to en/ms"
```

---

### Task 9: Translate display text in zep_tools.py

**Files:**
- Modify: `backend/app/services/zep_tools.py`
- Modify: `backend/app/i18n/strings.py`

~30 Chinese display strings in `to_text()` methods (lines 46-280) — section headers like `"相关事实:"`, relationship display formats, search result formatting. These are shown in report tool results.

- [ ] **Step 1: Add display strings to `i18n/strings.py`**

- [ ] **Step 2: Update `zep_tools.py` `to_text()` methods to use `get_string()`**

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/zep_tools.py backend/app/i18n/strings.py
git commit -m "feat(i18n): translate zep tools display text to en/ms"
```

---

## Chunk 4: Frontend Language Toggle

### Task 10: Add language toggle to frontend

**Files:**
- Modify: `frontend/src/App.vue`
- Create: `frontend/src/i18n/en.js`
- Create: `frontend/src/i18n/ms.js`
- Create: `frontend/src/i18n/index.js`
- Modify: `frontend/src/views/Home.vue`
- Modify: All component files that have user-facing text

The frontend is currently in English (from PR #176). We need to:

1. Extract all English strings into `i18n/en.js`
2. Create Malay translations in `i18n/ms.js`
3. Add a simple reactive i18n provider in `i18n/index.js`
4. Add a language toggle (EN/MS) in the navbar
5. When language changes, also call the backend API to set `OUTPUT_LANGUAGE`

- [ ] **Step 1: Create `frontend/src/i18n/index.js`**

Simple reactive i18n using Vue's `reactive`:

```javascript
import { reactive } from 'vue';
import en from './en.js';
import ms from './ms.js';

const state = reactive({
  locale: localStorage.getItem('mirofish_lang') || 'en',
});

const messages = { en, ms };

export function t(key) {
  return messages[state.locale]?.[key] || messages['en'][key] || key;
}

export function setLocale(lang) {
  state.locale = lang;
  localStorage.setItem('mirofish_lang', lang);
}

export function getLocale() {
  return state.locale;
}
```

- [ ] **Step 2: Create `frontend/src/i18n/en.js`**

Extract all English strings from Home.vue and other components into a flat key-value object.

- [ ] **Step 3: Create `frontend/src/i18n/ms.js`**

Malay translations for all keys.

- [ ] **Step 4: Add language toggle to App.vue navbar**

Small EN | MS toggle button in the top nav bar.

- [ ] **Step 5: Update Home.vue and all components to use `t()` function**

Replace hardcoded English strings with `t('key_name')` calls.

- [ ] **Step 6: Add API call to sync language with backend**

When language changes, POST to a new `/api/config/language` endpoint (or include `language` param in existing API calls).

- [ ] **Step 7: Add backend endpoint for language setting**

Add a simple endpoint that updates `Config.OUTPUT_LANGUAGE` at runtime:

```python
@app.route('/api/config/language', methods=['POST'])
def set_language():
    lang = request.json.get('language', 'en')
    if lang in ('en', 'ms'):
        Config.OUTPUT_LANGUAGE = lang
        return jsonify(success=True)
    return jsonify(success=False, error='Invalid language'), 400
```

- [ ] **Step 8: Commit**

```bash
git add frontend/src/i18n/ frontend/src/App.vue frontend/src/views/ frontend/src/components/ backend/app/api/
git commit -m "feat(i18n): add EN/MS language toggle to frontend and backend sync"
```

---

## Chunk 5: Final Integration & Testing

### Task 11: End-to-end testing

- [ ] **Step 1: Test full flow in English**

Set `OUTPUT_LANGUAGE=en`, run the complete pipeline:
1. Upload seed document → verify ontology entities are in English
2. Generate agent profiles → verify bios/personas are in English
3. Run simulation → verify action descriptions are in English
4. Generate report → verify report content is in English
5. Interact with agents → verify responses are in English

- [ ] **Step 2: Test full flow in Malay**

Switch to MS via UI toggle, repeat the same pipeline and verify all output is in Bahasa Melayu.

- [ ] **Step 3: Test language switching mid-session**

Verify that changing language doesn't break an in-progress simulation.

- [ ] **Step 4: Update `.env.example` with `OUTPUT_LANGUAGE` documentation**

- [ ] **Step 5: Final commit**

```bash
git add .env.example
git commit -m "feat(i18n): complete EN/MS language support with documentation"
```
