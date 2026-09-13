import base64
from nicegui import ui
from pyvis.network import Network

# State to simulate dynamic data
nodes_data = [
    {"id": 1, "label": "NiceGUI", "color": "#3b82f6"},
    {"id": 2, "label": "Pyvis", "color": "#ef4444"},
]
edges_data = [(1, 2)]

class Graph:
    def build_graph_html(self) -> str:
        """Generates the raw HTML from the current state data."""
        net = Network(notebook=False, height="450px", width="100%")

        # Add current nodes
        for node in nodes_data:
            net.add_node(node["id"], label=node["label"], color=node["color"])

        # Add current edges
        for source, target in edges_data:
            net.add_edge(source, target)

        return net.generate_html()


    # ---- This is your callable UI method ----
    @ui.refreshable_method
    def render_network_ui(self) -> None:
        """Renders the graph inside an isolated iframe to support <script> tags."""
        with ui.card().classes("w-full h-[500px] p-0 overflow-hidden"):
            # 1. Generer rå HTML fra Pyvis
            html_content = self.build_graph_html()

            # 2. Konverter HTML til en trygg base64-streng som en iframe kan lese direkte
            b64_html = base64.b64encode(html_content.encode('utf-8')).decode('utf-8')
            src_data = f"data:text/html;base64,{b64_html}"

            # 3. LØSNING: Bruk en iframe i stedet for ui.html
            ui.element('iframe').props(f'src="{src_data}"').classes("w-full h-full border-none")


    # 2. Controls to demonstrate modifying data and calling a refresh
    def add_new_node(self):
        new_id = len(nodes_data) + 1

        # Update state
        nodes_data.append(
            {"id": new_id, "label": f"Node {new_id}", "color": "#10b981"}
        )
        edges_data.append((1, new_id))  # Connect it to the NiceGUI node

        # Call the refresh method built into the decorated function
        self.render_network_ui.refresh()
