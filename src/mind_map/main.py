from mind_map.db.mind_map_repository import MindMapRepository
from mind_map.front_end.graph import Graph
from mind_map.front_end.nodes import Nodes
from nicegui import ui

ui.label("Mind map graph").classes("text-xl font-bold")

ui.add_head_html(
    """
    <script>
    window.addEventListener('message', function(event) {
        if (!event.data) return;
        if (event.data.event === 'nodes_tracked') {
            emitEvent('nodes_tracked', {list: event.data.list});
        }
        if (event.data.event === 'toggle_edge_request') {
            emitEvent('toggle_edge_request', {n1: event.data.node1, n2: event.data.node2});
        }
    });
    </script>
"""
)

# 1. Create and render graph-component
mind_map_graph = Graph()
mind_map_graph.render_graph_ui()

status_label = ui.label("No node chosen as reference.").classes(
    "text-amber-600 font-mono"
)

selected_node_id = None
nodes = Nodes()
db_repo = MindMapRepository()

# Methods to save the state of the current map
def save_current_map():
    name = map_name_input.value.strip()
    if not name:
        ui.notify("You need to supply a name for the map!", type="warning")
        return

    # Hent nåværende tilstand og send til repoet
    db_repo.save_map(name, nodes.getNodes(), nodes.getEdges())
    ui.notify(f"Mind-map '{name}' has been stored!")

    # Oppdater dropdown-menyen live
    map_selector.options = db_repo.get_all_map_names()
    map_selector.update()


def load_selected_map(e):
    if not e.value:
        return

    # Hent data fra dedikert klasse
    data = db_repo.load_map(e.value)
    if data:
        # Oppdater tilstanden i nodes.py
        nodes.setRawData(data["nodes"], data["edges"])

        # Synkroniser input-feltet og oppdater skjermen
        map_name_input.set_value(e.value)
        mind_map_graph.render_graph_ui.refresh()
        ui.notify(f"Lastet inn '{e.value}'!")


def handle_node_selection(e):
    global selected_node_id
    raw_id = e.args.get("id")

    # Pyvis returns ID as a list, extract the id
    selected_node_id = raw_id[0] if isinstance(raw_id, list) else raw_id

    if selected_node_id:
        # Extract a nodes label
        node_info = next(
            (n for n in nodes.getNodes() if n["id"] == selected_node_id), None
        )
        current_label = node_info["label"] if node_info else ""

        status_label.set_text(f"Valgt node ID: {selected_node_id}")
        status_label.classes(replace="text-green-600 font-mono")

        # Fill node with it's current label
        node_name.set_value(current_label)
    else:
        status_label.set_text("Ingen node valgt som referanse.")
        status_label.classes(replace="text-amber-600 font-mono")
        node_name.set_value("")  # Tøm feltet hvis brukeren klikker i tomrommet

def add_node_and_connect(new_label: str):
    """Create a new node and connect it to the selected reference (selected_node_id)."""
    global selected_node_id
    if not new_label.strip():
        ui.notify("Enter the name of new node.", type="warning")
        return

    if selected_node_id is None:
        ui.notify(
            "You need to select a reference node!",
            type="negative",
        )
        return

    # Add a node to the shared nodes state
    nodes.addNode(selected_node_id, new_label)

    # Re-render graph to update with new node values
    mind_map_graph.render_graph_ui.refresh()

    node_name.set_value("")  # Clears input field automatically after successfull update
    ui.notify(f"Added '{new_label}', connected from node {selected_node_id}!")

def save_node_edits(new_label: str):
    global selected_node_id
    if selected_node_id is None:
        ui.notify("No node is chose for edit", type="warning")
        return
    if not new_label.strip():
        ui.notify("Text cannot be empty.", type="warning")
        return

    # Update the label of selected node
    nodes.updateNodeLabel(selected_node_id, new_label)

    # Refresh graph to render the updated node state
    mind_map_graph.render_graph_ui.refresh()
    ui.notify("Node-tekst oppdatert!")

def delete_selected_node():
    global selected_node_id
    if selected_node_id is None:
        ui.notify("No node selected for removal", type="warning")
        return

    # Sikkerhetssjekk: Ikke slett hvis det er den absolutt siste noden i kartet
    if len(nodes.getNodes()) <= 1:
        ui.notify("You can not remove the last remaining node from the map.", type="warning")
        return

    # Slett noden og dens direkte linjer fra datamodellen
    nodes.deleteNode(selected_node_id)

    # NULLSTILL VALG-POINTEREN: Siden noden er borte, må vi tømme utvalget
    selected_node_id = None
    status_label.set_text("No node selected.")
    status_label.classes(replace="text-amber-600 font-mono")
    node_name.set_value("")

    # Refresh grafen for å fjerne noden fra skjermen
    mind_map_graph.render_graph_ui.refresh()
    ui.notify("Noden has been removed. Any child nodes remain independent.")

def handle_nodes_tracked(e):
    """Updated the text-field showing the users selected node."""
    global selected_node_id
    current_selection = e.args.get("list", [])

    if len(current_selection) == 1:
        selected_node_id = current_selection[0]
        status_label.set_text(
            f"Chosen node: ID {selected_node_id}. (Click a new node to connect/disconnect)"
        )
        status_label.classes(replace="text-blue-600 font-mono")

        # Fyll textarea for redigering (valgfritt, bevarer din gamle flyt)
        node_info = next(
            (n for n in nodes.getNodes() if n["id"] == selected_node_id), None
        )
        if node_info:
            node_name.set_value(node_info["label"])
    elif len(current_selection) == 0:
        selected_node_id = None
        status_label.set_text("Ingen node valgt.")
        status_label.classes(replace="text-amber-600 font-mono")
        node_name.set_value("")


def handle_toggle_edge(e):
    """Received the two nodes from JavaScript and runs the Toggle-logic."""
    n1 = e.args.get("n1")
    n2 = e.args.get("n2")

    # Kjør logikken i nodes.py
    result = nodes.toggleEdge(n1, n2)

    if result == "added":
        ui.notify(f"Created new edge: {n1} -> {n2}!")
    else:
        ui.notify(
            f"Removed edge: {n1} -> {n2}.", type="warning"
        )

    # Refresh grafen umiddelbart for å vise endringen live
    mind_map_graph.render_graph_ui.refresh()

# 2. Input fields and event listeners
node_name = ui.textarea(
    label="Create new mind node",
    placeholder="name of mind node",
    validation={
        "Input too long": lambda value: len(value) <= 200
    },
).props("clearable autogrow").classes("w-96 mt-4")

ui.on("node_selected", handle_node_selection)
ui.on("nodes_tracked", handle_nodes_tracked)
ui.on("toggle_edge_request", handle_toggle_edge)

with ui.row().classes("gap-2 mt-2 items-center"):
    ui.button(
        "Add & Connect",
        on_click=lambda: add_node_and_connect(node_name.value),
        color="primary",
    ).props("icon=add")

    ui.button(
        "Save Changes",
        on_click=lambda: save_node_edits(node_name.value),
        color="orange",
    ).props("icon=edit")

    ui.button(
        "Delete Node", on_click=delete_selected_node, color="red"
    ).props("icon=delete").classes("ml-4")

# ==============================================================================
# 3. Database Admin UI
# ==============================================================================
ui.label("Database-admin").classes("text-md font-semibold mt-6")

with ui.row().classes("items-end gap-4 p-4 bg-slate-50 rounded-lg w-full"):
    map_name_input = ui.input(
        label="Name of current map", placeholder="example. Project X"
    ).classes("w-48")

    ui.button(
        "Save map", on_click=save_current_map, color="green"
    ).props("icon=save")

    # Dropdown henter nå alternativer fra db_repo
    map_selector = ui.select(
        options=db_repo.get_all_map_names(),
        label="Load existing map",
        on_change=load_selected_map,
    ).classes("w-48")

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(port=8080, reload=False)
