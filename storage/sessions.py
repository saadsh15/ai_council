import json
import os
from typing import List, Optional
from pathlib import Path
from utils.models import Session
from pydantic import TypeAdapter

SESSIONS_DIR = Path("storage/sessions")

class SessionManager:
    def __init__(self, sessions_dir: Path = SESSIONS_DIR):
        self.sessions_dir = sessions_dir
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def save_session(self, session: Session):
        session_path = self.sessions_dir / f"{session.session_id}.json"
        with open(session_path, "w") as f:
            f.write(session.model_dump_json(indent=2))

    def load_session(self, session_id: str) -> Optional[Session]:
        session_path = self.sessions_dir / f"{session_id}.json"
        if not session_path.exists():
            return None
        with open(session_path, "r") as f:
            return Session.model_validate_json(f.read())

    def list_sessions(self) -> List[Session]:
        sessions = []
        for file in self.sessions_dir.glob("*.json"):
            with open(file, "r") as f:
                try:
                    session = Session.model_validate_json(f.read())
                    sessions.append(session)
                except Exception as e:
                    print(f"Error loading session {file}: {e}")
        return sorted(sessions, key=lambda s: s.created_at, reverse=True)

    def clear_sessions(self):
        for file in self.sessions_dir.glob("*.json"):
            file.unlink()
