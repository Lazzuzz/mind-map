
import json
import sqlite3


class MindMapRepository:

    def __init__(self, db_file: str = "mindmaps.db"):
        self.db_file = db_file
        self._create_table()

    def _create_table(self) -> None:
        """Create a table if one does not already exist."""
        with sqlite3.connect(self.db_file) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS maps (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE,
                    graph_json TEXT
                )
            """)

    def save_map(self, name: str, nodes: list, edges: list) -> None:
        """Package the node and edges to JSON, and store or update the SQLite."""
        payload = {"nodes": nodes, "edges": edges}
        json_string = json.dumps(payload)

        with sqlite3.connect(self.db_file) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO maps (name, graph_json)
                VALUES (?, ?)
            """,
                (name, json_string),
            )

    def load_map(self, name: str) -> dict | None:
        """Loads a mind-map from db and return a dictionary for nodes and edges."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.execute(
                "SELECT graph_json FROM maps WHERE name = ?", (name,)
            )
            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
            return None

    def get_all_map_names(self) -> list[str]:
        """Fetch a list of all stored map names."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.execute("SELECT name FROM maps")
            return [row[0] for row in cursor.fetchall()]

    def delete_map(self, name: str) -> None:
        """Delete a specific map from the database."""
        with sqlite3.connect(self.db_file) as conn:
            conn.execute("DELETE FROM maps WHERE name = ?", (name,))
