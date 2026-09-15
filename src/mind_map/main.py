# mind_map/main.py

from nicegui import ui

from mind_map.controllers.mind_map_controller import (
    ControllerError,
    MindMapController,
    SelectionRequiredError,
)
from mind_map.db.mind_map_repository import MindMapRepository
from mind_map.domain.nodes import Nodes
from mind_map.frontend.graph import Graph

BRIDGE_SCRIPT = """
<script>
window.addEventListener('message', function(event) {
    if (!event.data) return;
    if (event.data.event === 'nodes_tracked') {
        emitEvent('nodes_tracked', {list: event.data.list});
    }
    if (event.data.event === 'toggle_edge_request') {
        emitEvent('toggle_edge_request', {n1: event.data.node1, n2: event.data.node2});
    }
    if (event.data.event === 'node_moved') {
        emitEvent('node_moved', {id: event.data.id, x: event.data.x, y: event.data.y});
    }
});
</script>
"""


@ui.page("/")
def main_page() -> None:
    ui.label("Mind map graph").classes("text-xl font-bold")
    ui.add_head_html(BRIDGE_SCRIPT)

    # Fresh state per browser session/tab
    nodes = Nodes()
    graph = Graph()
    repo = MindMapRepository()
    controller = MindMapController(nodes, graph, repo)

    graph.render_graph_ui(nodes.get_nodes(), nodes.get_edges())  # initial draw

    status_label = ui.label("No node chosen as reference.").classes(
        "text-amber-600 font-mono"
    )

    node_name = ui.textarea(
        label="Create new mind node",
        placeholder="name of mind node",
        validation={"Input too long": lambda value: len(value) <= 200},
    ).props("clearable autogrow").classes("w-96 mt-4")

    # -- Event handlers: thin translation between UI events and controller --

    def handle_nodes_tracked(e) -> None:
        selection = e.args.get("list", [])
        if len(selection) == 1:
            label = controller.select_node(selection[0])
            status_label.set_text(
                f"Chosen node: ID {controller.selected_node_id}. "
                "(Click a new node to connect/disconnect)"
            )
            status_label.classes(replace="text-blue-600 font-mono")
            node_name.set_value(label)
        elif len(selection) == 0:
            controller.clear_selection()
            status_label.set_text("No node is chosen.")
            status_label.classes(replace="text-amber-600 font-mono")
            node_name.set_value("")

    def handle_toggle_edge(e) -> None:
        n1, n2 = e.args.get("n1"), e.args.get("n2")
        result = controller.toggle_edge(n1, n2)
        if result == "added":
            ui.notify(f"Created new edge: {n1} -> {n2}!")
        else:
            ui.notify(f"Removed edge: {n1} -> {n2}.", type="warning")

    def handle_node_moved(e) -> None:
        controller.move_node(e.args.get("id"), e.args.get("x"), e.args.get("y"))

    def add_node_and_connect() -> None:
        label = node_name.value
        try:
            controller.add_node_and_connect(label)
        except SelectionRequiredError as err:
            ui.notify(str(err), type="negative")
            return
        except ControllerError as err:
            ui.notify(str(err), type="warning")
            return
        ui.notify(f"Added '{label}', connected from node {controller.selected_node_id}!")
        node_name.set_value("")

    def save_node_edits() -> None:
        try:
            controller.save_node_edits(node_name.value)
        except ControllerError as err:
            ui.notify(str(err), type="warning")
            return
        ui.notify("Node text updated!")

    def delete_selected_node() -> None:
        try:
            controller.delete_selected_node()
        except ControllerError as err:
            ui.notify(str(err), type="warning")
            return
        status_label.set_text("No node selected.")
        status_label.classes(replace="text-amber-600 font-mono")
        node_name.set_value("")
        ui.notify("Node has been removed. Any child nodes remain independent.")

    def clear_active_map() -> None:
        controller.clear_map()
        status_label.set_text("No node chosen as reference.")
        status_label.classes(replace="text-amber-600 font-mono")
        node_name.set_value("")
        map_name_input.set_value("")
        ui.notify("Active map has been cleared!")

    def save_current_map() -> None:
        name = map_name_input.value.strip()
        try:
            controller.save_map(name)
        except ControllerError as err:
            ui.notify(str(err), type="warning")
            return
        ui.notify(f"Mind-map '{name}' has been stored!")
        map_selector.options = controller.get_map_names()
        map_selector.update()

    def load_selected_map(e) -> None:
        if not e.value:
            return
        try:
            controller.load_map(e.value)
        except ControllerError as err:
            ui.notify(str(err), type="warning")
            return
        map_name_input.set_value(e.value)
        ui.notify(f"Loaded '{e.value}'!")

    ui.on("nodes_tracked", handle_nodes_tracked)
    ui.on("toggle_edge_request", handle_toggle_edge)
    ui.on("node_moved", handle_node_moved)

    with ui.row().classes("gap-2 mt-2 items-center"):
        ui.button(
            "Add & Connect", on_click=add_node_and_connect, color="primary"
        ).props("icon=add")

        ui.button(
            "Save Changes", on_click=save_node_edits, color="orange"
        ).props("icon=edit")

        ui.button(
            "Delete Node", on_click=delete_selected_node, color="red"
        ).props("icon=delete").classes("ml-4")

    # -- Database Admin UI --------------------------------------------------
    ui.label("Database-admin").classes("text-md font-semibold mt-6")

    with ui.row().classes("items-end gap-4 p-4 bg-slate-50 rounded-lg w-full"):
        map_name_input = ui.input(
            label="Name of current map", placeholder="example. Project X"
        ).classes("w-48")

        ui.button("Save map", on_click=save_current_map, color="green").props(
            "icon=save"
        )

        map_selector = ui.select(
            options=controller.get_map_names(),
            label="Load existing map",
            on_change=load_selected_map,
        ).classes("w-48")

        ui.button(
            "New Map", on_click=clear_active_map, color="grey-7"
        ).props("icon=brightness_low").classes("ml-auto")


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(port=8080, reload=False)
