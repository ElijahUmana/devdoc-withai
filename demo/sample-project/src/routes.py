"""
Route definitions for TaskFlow API.
Registers all endpoint blueprints with the Flask app.
"""

from flask import Blueprint, jsonify, request, current_app
from models import Task, Status, Priority

api = Blueprint('api', __name__, url_prefix='/api/v1')


def register_routes(app):
    """Register all route blueprints with the Flask application."""
    app.register_blueprint(api)


@api.route('/tasks', methods=['GET'])
def list_tasks():
    """List all tasks with optional filtering."""
    store = current_app.extensions['task_store']

    status_filter = request.args.get('status')
    priority_filter = request.args.get('priority')

    status = Status(status_filter) if status_filter else None
    priority = Priority(priority_filter) if priority_filter else None

    tasks = store.list_all(status=status, priority=priority)
    return jsonify({
        'tasks': [t.to_dict() for t in tasks],
        'total': len(tasks),
    })


@api.route('/tasks', methods=['POST'])
def create_task():
    """Create a new task."""
    store = current_app.extensions['task_store']
    data = request.get_json()

    if not data or 'title' not in data:
        return jsonify({'error': 'Title is required'}), 400

    task = Task.from_dict(data)
    store.create(task)
    return jsonify(task.to_dict()), 201


@api.route('/tasks/<task_id>', methods=['GET'])
def get_task(task_id):
    """Get a single task by ID."""
    store = current_app.extensions['task_store']
    task = store.get(task_id)

    if not task:
        return jsonify({'error': 'Task not found'}), 404

    return jsonify(task.to_dict())


@api.route('/tasks/<task_id>', methods=['PATCH'])
def update_task(task_id):
    """Update a task's fields."""
    store = current_app.extensions['task_store']
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No update data provided'}), 400

    task = store.update(task_id, data)
    if not task:
        return jsonify({'error': 'Task not found'}), 404

    return jsonify(task.to_dict())


@api.route('/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Delete a task."""
    store = current_app.extensions['task_store']

    if store.delete(task_id):
        return jsonify({'message': 'Task deleted'}), 200

    return jsonify({'error': 'Task not found'}), 404


@api.route('/tasks/stats', methods=['GET'])
def task_stats():
    """Get task statistics."""
    store = current_app.extensions['task_store']
    all_tasks = store.list_all()

    stats = {
        'total': len(all_tasks),
        'by_status': {},
        'by_priority': {},
    }

    for status in Status:
        count = len([t for t in all_tasks if t.status == status])
        stats['by_status'][status.value] = count

    for priority in Priority:
        count = len([t for t in all_tasks if t.priority == priority])
        stats['by_priority'][priority.value] = count

    return jsonify(stats)
