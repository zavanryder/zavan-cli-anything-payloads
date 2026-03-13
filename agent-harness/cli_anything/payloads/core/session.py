"""Stateful session management for interactive REPL use."""

import json
import os
import time
from pathlib import Path


class Session:
    """Manages persistent session state for the payloads CLI.

    Tracks current category, search history, favorites, and recent commands.
    State is stored as a JSON file.
    """

    def __init__(self, session_file: str | None = None):
        if session_file is None:
            session_dir = Path.home() / ".cli-anything-payloads"
            session_dir.mkdir(parents=True, exist_ok=True)
            self.session_file = str(session_dir / "session.json")
        else:
            self.session_file = session_file

        self._state = {
            "current_category": None,
            "favorites": [],
            "search_history": [],
            "command_history": [],
            "last_accessed": None,
        }
        self._load()

    def _load(self):
        if os.path.isfile(self.session_file):
            try:
                with open(self.session_file, "r") as f:
                    saved = json.load(f)
                self._state.update(saved)
            except (json.JSONDecodeError, OSError):
                pass

    def _save(self):
        self._state["last_accessed"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        try:
            with open(self.session_file, "w") as f:
                json.dump(self._state, f, indent=2)
        except OSError:
            pass

    @property
    def current_category(self) -> str | None:
        return self._state["current_category"]

    @current_category.setter
    def current_category(self, value: str | None):
        self._state["current_category"] = value
        self._save()

    @property
    def favorites(self) -> list[str]:
        return list(self._state["favorites"])

    def add_favorite(self, category: str):
        if category not in self._state["favorites"]:
            self._state["favorites"].append(category)
            self._save()

    def remove_favorite(self, category: str):
        if category in self._state["favorites"]:
            self._state["favorites"].remove(category)
            self._save()

    def add_search(self, query: str):
        history = self._state["search_history"]
        # Remove old duplicate
        history = [h for h in history if h["query"] != query]
        history.append({"query": query, "time": time.strftime("%Y-%m-%dT%H:%M:%S")})
        # Keep last 50
        self._state["search_history"] = history[-50:]
        self._save()

    @property
    def search_history(self) -> list[dict]:
        return list(self._state["search_history"])

    def add_command(self, command: str):
        history = self._state["command_history"]
        history.append({"command": command, "time": time.strftime("%Y-%m-%dT%H:%M:%S")})
        self._state["command_history"] = history[-100:]
        self._save()

    def clear(self):
        self._state = {
            "current_category": None,
            "favorites": [],
            "search_history": [],
            "command_history": [],
            "last_accessed": None,
        }
        self._save()

    def to_dict(self) -> dict:
        return dict(self._state)
