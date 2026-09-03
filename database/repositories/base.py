from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4


def new_id() -> str:
    return str(uuid4())


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def to_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


def from_json(value: str | None, default: object = None) -> object:
    return json.loads(value) if value else default
