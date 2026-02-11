"""Tests for TaskFlow API."""

import pytest
from app import create_app


@pytest.fixture
def client():
    app = create_app({'TESTING': True})
    with app.test_client() as client:
        yield client


def test_health_check(client):
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'


def test_create_task(client):
    response = client.post('/api/v1/tasks', json={
        'title': 'Write tests',
        'description': 'Add unit tests for all endpoints',
        'priority': 'high',
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data['title'] == 'Write tests'
    assert data['priority'] == 'high'
    assert data['status'] == 'todo'


def test_create_task_missing_title(client):
    response = client.post('/api/v1/tasks', json={
        'description': 'No title provided',
    })
    assert response.status_code == 400


def test_list_tasks(client):
    # Create two tasks
    client.post('/api/v1/tasks', json={'title': 'Task 1'})
    client.post('/api/v1/tasks', json={'title': 'Task 2'})

    response = client.get('/api/v1/tasks')
    assert response.status_code == 200
    data = response.get_json()
    assert data['total'] == 2


def test_get_task_not_found(client):
    response = client.get('/api/v1/tasks/nonexistent')
    assert response.status_code == 404


def test_delete_task(client):
    # Create then delete
    create_resp = client.post('/api/v1/tasks', json={'title': 'To delete'})
    task_id = create_resp.get_json()['id']

    delete_resp = client.delete(f'/api/v1/tasks/{task_id}')
    assert delete_resp.status_code == 200
