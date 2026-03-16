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
