from nicegui import ui
from mind_map.front_end.graph import Graph

# ----------------------------------------
# Application Layout
# ----------------------------------------
ui.label("Mind map graph").classes("text-xl font-bold")

# 1. Initial call to render the UI component
mind_map_graph = Graph()
mind_map_graph.render_graph_ui()

#2. Button to add a new node for testing purposes
ui.button("Add Connected Node", on_click=mind_map_graph.add_new_node).classes("mt-4")

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(port=8080, reload=False)
