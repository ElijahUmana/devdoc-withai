"""
TaskFlow API — A lightweight task management REST API.
Built with Flask for demonstration purposes.
"""

from flask import Flask, jsonify, request
from models import TaskStore, Task
from routes import register_routes
from utils import setup_logging, validate_config

import os
import logging

app = Flask(__name__)
logger = setup_logging()


def create_app(config=None):
    """Application factory pattern."""
    app = Flask(__name__)

    # Load configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    app.config['DATABASE_URL'] = os.environ.get('DATABASE_URL', 'sqlite:///tasks.db')
    app.config['MAX_TASKS_PER_USER'] = int(os.environ.get('MAX_TASKS', '100'))

    if config:
        app.config.update(config)

    validate_config(app.config)

    # Initialize task store
    store = TaskStore(app.config['DATABASE_URL'])
    app.extensions['task_store'] = store

    # Register route blueprints
    register_routes(app)

    # Health check endpoint
    @app.route('/health')
    def health():
        return jsonify({'status': 'healthy', 'version': '1.0.0'})

    logger.info(f"TaskFlow API initialized (DB: {app.config['DATABASE_URL']})")
    return app


if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
