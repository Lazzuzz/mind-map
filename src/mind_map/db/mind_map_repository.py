# mind_map/db/mind_map_repository.py

import json
import sqlite3
from contextlib import closing


class MindMapRepository:
    """Persists and retrieves mind maps as JSON blobs in SQLite.

    Responsible for translating between the storage format (JSON, which has
    no tuple type) and the shapes the domain layer expects (edges as
    list[tuple[int, int]]) — that translation belongs here, not upstream.
    """

    def __init__(self, db_file: str = "mindmaps.db") -> None:
        self.db_file = db_file
        self._create_table()

    def _create_table(self) -> None:
        """Create the maps table if it does not already exist."""
        with closing(sqlite3.connect(self.db_file)) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS maps (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE,
                    graph_json TEXT
                )
                """
            )

    def save_map(
        self, name: str, nodes: list[dict], edges: list[tuple[int, int]]
    ) -> None:
        """Serializes nodes and edges to JSON and stores/updates the row."""
        payload = {"nodes": nodes, "edges": edges}
        json_string = json.dumps(payload)

        with closing(sqlite3.connect(self.db_file)) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO maps (name, graph_json)
                VALUES (?, ?)
                """,
                (name, json_string),
            )

    def load_map(self, name: str) -> dict | None:
        """Loads a mind map and returns {"nodes": [...], "edges": [...]}.

        Edges are converted back to tuples here, since JSON only knows
        lists — callers should never have to worry about that distinction.
        """
        with closing(sqlite3.connect(self.db_file)) as conn:
            cursor = conn.execute(
                "SELECT graph_json FROM maps WHERE name = ?", (name,)
            )
            row = cursor.fetchone()

        if row is None:
            return None

        data = json.loads(row[0])
        data["edges"] = [tuple(edge) for edge in data["edges"]]
        return data

    def get_all_map_names(self) -> list[str]:
        """Fetch a list of all stored map names."""
        with closing(sqlite3.connect(self.db_file)) as conn:
            cursor = conn.execute("SELECT name FROM maps")
            return [row[0] for row in cursor.fetchall()]

    def delete_map(self, name: str) -> None:
        """Delete a specific map from the database."""
        with closing(sqlite3.connect(self.db_file)) as conn:
            conn.execute("DELETE FROM maps WHERE name = ?", (name,))
