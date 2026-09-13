from nicegui import ui
from mind_map.front_end.graph import Graph

# ----------------------------------------
# Application Layout
# ----------------------------------------
ui.label("Callable & Refreshable Pyvis Graph").classes("text-xl font-bold")

# 1. Initial call to render the UI component
my_graph = Graph()
my_graph.render_network_ui()
ui.button("Add Connected Node", on_click=my_graph.add_new_node).classes("mt-4")

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(port=8080, reload=False)
