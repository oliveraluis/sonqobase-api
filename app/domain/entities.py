from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class Database:
    name: str
    expires_at: datetime

@dataclass(frozen=True)
class Project:
    id: str
    name: str
    description: str | None
    status: str
    expires_at: datetime
    database: Database

