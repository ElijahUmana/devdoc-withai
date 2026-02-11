# TaskFlow API

A lightweight REST API for task management. Built with Flask.

## Quick Start

```bash
pip install -r requirements.txt
python src/app.py
```

## API Endpoints

- `GET /health` — Health check
- `GET /api/v1/tasks` — List all tasks
- `POST /api/v1/tasks` — Create a task
- `GET /api/v1/tasks/:id` — Get a task
- `PATCH /api/v1/tasks/:id` — Update a task
- `DELETE /api/v1/tasks/:id` — Delete a task
- `GET /api/v1/tasks/stats` — Task statistics
