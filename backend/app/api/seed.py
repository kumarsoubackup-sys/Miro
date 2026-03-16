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
