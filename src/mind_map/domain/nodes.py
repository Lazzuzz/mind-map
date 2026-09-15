# mind_map/domain/nodes.py

def _default_node() -> dict:
    """Factory for the single starter node a fresh/empty map begins with."""
    return {
        "id": 1,
        "label": "My new mind-map",
        "color": "#3b82f6",
        "shape": "box",
    }


class Nodes:
    """Holds and mutates the node/edge state for a single mind map session.

    Instance-scoped on purpose: each NiceGUI page/session should create its
    own Nodes() so that separate browser tabs never share state.
    """

    def __init__(self) -> None:
        self.nodes: list[dict] = [_default_node()]
        self.edges: list[tuple[int, int]] = []
        self._next_id: int = 2  # next free id after the starter node (id=1)

    def get_nodes(self) -> list[dict]:
        return self.nodes

    def get_edges(self) -> list[tuple[int, int]]:
        return self.edges

    def get_node_count(self) -> int:
        return len(self.nodes)

    def set_raw_data(self, nodes: list[dict], edges: list[tuple[int, int]]) -> None:
        """Overwrite the active state (used when loading a saved map)."""
        self.nodes = nodes
        self.edges = edges
        # Keep the id counter ahead of anything we just loaded, so newly
        # added nodes can't collide with ids coming from the loaded map.
        existing_ids = [n["id"] for n in self.nodes if isinstance(n.get("id"), int)]
        self._next_id = max(existing_ids, default=0) + 1

    def add_node(self, source_node_id: int, label: str) -> int:
        """Adds a new node connected to source_node_id. Returns the new node's id."""
        new_id = self._next_id
        self._next_id += 1

        self.nodes.append(
            {
                "id": new_id,
                "label": label,
                "color": "#10b981",
                "shape": "box",
            }
        )
        self.edges.append((source_node_id, new_id))
        return new_id

    def update_node_label(self, node_id: int, new_label: str) -> None:
        """Finds a node by id and updates its label."""
        for node in self.nodes:
            if node["id"] == node_id:
                node["label"] = new_label
                break

    def update_node_position(self, node_id: int, x: int, y: int) -> None:
        """Updates the x & y coordinates of a node."""
        try:
            node_id, x, y = int(node_id), int(x), int(y)
        except (TypeError, ValueError):
            return

        for node in self.nodes:
            if node["id"] == node_id:
                node["x"] = x
                node["y"] = y
                break

    def toggle_edge(self, node1: int, node2: int) -> str:
        """Adds an edge between two nodes if none exists, otherwise removes it.

        Returns a status: 'added' or 'removed'.
        """
        node1, node2 = int(node1), int(node2)
        edge_forward = (node1, node2)
        edge_backward = (node2, node1)

        if edge_forward in self.edges:
            self.edges.remove(edge_forward)
            return "removed"
        elif edge_backward in self.edges:
            self.edges.remove(edge_backward)
            return "removed"
        else:
            self.edges.append(edge_forward)
            return "added"

    def delete_node(self, node_id: int) -> None:
        """Deletes a node and any edges directly connected to it.

        Child nodes remain and become independent of the deleted node.
        """
        try:
            node_id = int(node_id)
        except (TypeError, ValueError):
            return

        self.edges = [
            (s, t) for s, t in self.edges if s != node_id and t != node_id
        ]
        self.nodes = [n for n in self.nodes if n["id"] != node_id]

    def clear_map(self) -> None:
        """Resets the map back to a single starter node with no edges."""
        self.nodes = [_default_node()]
        self.edges = []
        self._next_id = 2
