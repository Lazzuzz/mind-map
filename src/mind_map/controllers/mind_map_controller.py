# mind_map/controllers/mind_map_controller.py

from mind_map.db.mind_map_repository import MindMapRepository
from mind_map.domain.nodes import Nodes
from mind_map.frontend.graph import Graph


class ControllerError(Exception):
    """Validation failure that the UI layer should show as a soft warning."""


class SelectionRequiredError(ControllerError):
    """Raised when an action needs a selected node but none is selected."""


class MindMapController:
    """Orchestrates domain state, rendering, and persistence for one session.

    Owns no UI code. Methods either succeed (optionally returning a value
    the caller can use for feedback) or raise a ControllerError with a
    human-readable message the UI layer can display as-is.
    """

    def __init__(self, nodes: Nodes, graph: Graph, repo: MindMapRepository) -> None:
        self.nodes = nodes
        self.graph = graph
        self.repo = repo
        self.selected_node_id: int | None = None

    # -- Rendering -----------------------------------------------------

    def render_graph(self) -> None:
        """(Re)renders the graph with the current node/edge state."""
        self.graph.render_graph_ui.refresh(
            self.nodes.get_nodes(), self.nodes.get_edges()
        )

    # -- Selection -------------------------------------------------------

    def select_node(self, node_id: int | None) -> str:
        """Marks a node as selected and returns its current label ("" if none)."""
        self.selected_node_id = node_id
        if node_id is None:
            return ""

        node = next((n for n in self.nodes.get_nodes() if n["id"] == node_id), None)
        return node["label"] if node else ""

    def clear_selection(self) -> None:
        self.selected_node_id = None

    # -- Node editing ------------------------------------------------------

    def add_node_and_connect(self, label: str) -> int:
        """Creates a new node connected to the selected reference node.

        Returns the new node's id. Raises ControllerError / SelectionRequiredError
        on invalid input.
        """
        if not label.strip():
            raise ControllerError("Enter the name of new node.")
        if self.selected_node_id is None:
            raise SelectionRequiredError("You need to select a reference node!")

        new_id = self.nodes.add_node(self.selected_node_id, label)
        self.render_graph()
        return new_id

    def save_node_edits(self, new_label: str) -> None:
        """Updates the label of the currently selected node."""
        if self.selected_node_id is None:
            raise ControllerError("No node is chosen for edit")
        if not new_label.strip():
            raise ControllerError("Text cannot be empty.")

        self.nodes.update_node_label(self.selected_node_id, new_label)
        self.render_graph()

    def delete_selected_node(self) -> None:
        """Deletes the currently selected node, if allowed."""
        if self.selected_node_id is None:
            raise ControllerError("No node selected for removal")
        if self.nodes.get_node_count() <= 1:
            raise ControllerError("You can not remove the last remaining node from the map.")

        self.nodes.delete_node(self.selected_node_id)
        self.clear_selection()
        self.render_graph()

    def toggle_edge(self, node1: int, node2: int) -> str:
        """Toggles an edge between two nodes. Returns 'added' or 'removed'."""
        result = self.nodes.toggle_edge(node1, node2)
        self.render_graph()
        return result

    def move_node(self, node_id: int, x: int, y: int) -> None:
        """Persists a node's dragged position. Does not trigger a re-render."""
        self.nodes.update_node_position(node_id, x, y)

    # -- Map-level operations ------------------------------------------

    def clear_map(self) -> None:
        """Resets the active map to a single starter node."""
        self.nodes.clear_map()
        self.clear_selection()
        self.render_graph()

    def save_map(self, name: str) -> None:
        """Saves the current map under the given name."""
        if not name.strip():
            raise ControllerError("You need to supply a name for the map!")

        self.repo.save_map(name, self.nodes.get_nodes(), self.nodes.get_edges())

    def load_map(self, name: str) -> None:
        """Loads a previously saved map by name and replaces the active state."""
        data = self.repo.load_map(name)
        if data is None:
            raise ControllerError(f"No saved map named '{name}' was found.")

        self.nodes.set_raw_data(data["nodes"], data["edges"])
        self.clear_selection()
        self.render_graph()

    def get_map_names(self) -> list[str]:
        return self.repo.get_all_map_names()
