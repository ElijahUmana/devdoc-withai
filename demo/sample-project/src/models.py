"""
Data models for TaskFlow API.
Implements an in-memory task store with CRUD operations.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum
import uuid


class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Status(Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    ARCHIVED = "archived"


@dataclass
class Task:
    """Represents a single task in the system."""
    title: str
    description: str = ""
    priority: Priority = Priority.MEDIUM
    status: Status = Status.TODO
    assignee: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'priority': self.priority.value,
            'status': self.status.value,
            'assignee': self.assignee,
            'tags': self.tags,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Task':
        return cls(
            title=data['title'],
            description=data.get('description', ''),
            priority=Priority(data.get('priority', 'medium')),
            status=Status(data.get('status', 'todo')),
            assignee=data.get('assignee'),
            tags=data.get('tags', []),
        )


class TaskStore:
    """In-memory task storage with CRUD operations."""

    def __init__(self, db_url: str = "sqlite:///tasks.db"):
        self.db_url = db_url
        self._tasks: dict[str, Task] = {}

    def create(self, task: Task) -> Task:
        """Add a new task to the store."""
        self._tasks[task.id] = task
        return task

    def get(self, task_id: str) -> Optional[Task]:
        """Retrieve a task by ID."""
        return self._tasks.get(task_id)

    def list_all(self, status: Optional[Status] = None,
                 priority: Optional[Priority] = None) -> list[Task]:
        """List tasks with optional filters."""
        tasks = list(self._tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        if priority:
            tasks = [t for t in tasks if t.priority == priority]
        return sorted(tasks, key=lambda t: t.created_at, reverse=True)

    def update(self, task_id: str, updates: dict) -> Optional[Task]:
        """Update a task's fields."""
        task = self._tasks.get(task_id)
        if not task:
            return None

        for key, value in updates.items():
            if key == 'priority':
                value = Priority(value)
            elif key == 'status':
                value = Status(value)
            if hasattr(task, key):
                setattr(task, key, value)

        task.updated_at = datetime.now()
        return task

    def delete(self, task_id: str) -> bool:
        """Delete a task by ID."""
        if task_id in self._tasks:
            del self._tasks[task_id]
            return True
        return False

    def count(self) -> int:
        """Return total number of tasks."""
        return len(self._tasks)
