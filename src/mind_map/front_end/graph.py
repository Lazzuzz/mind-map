import base64
from nicegui import ui
from pyvis.network import Network
from mind_map.front_end.nodes import Nodes

nodes = Nodes()

class Graph:

    def build_graph_html(self) -> str:
            current_nodes = nodes.getNodes()
            current_edges = nodes.getEdges()

            net = Network(notebook=False, height="400px", width="100%")

            # Generate starter node
            for node in current_nodes:
                # Check if a node has stored coordinate state
                node_x = node.get("x", None)
                node_y = node.get("y", None)

                net.add_node(
                    node["id"],
                    label=node["label"],
                    color=node["color"],
                    shape=node.get("shape", "box"),
                    widthConstraint={"maximum": 150},
                    font={"color": "white", "size": 14, "face": "Arial"},
                    margin={
                        "top": 12,
                        "bottom": 12,
                        "left": 16,
                        "right": 16,
                    },  # Gir god plass på sidene
                    shapeProperties={
                        "borderRadius": 6,  # Avrunder hjørnene på boksen (box)
                        "useImageSize": False,
                        "interpolation": False,  # Sikrer stabil tekst-padding
                    },
                    x=node_x,
                    y=node_y
                )

            # 2. Security check SIKKERHETS-SJEKK FOR EDGES:
            # If nodes does not contain any edges we add a invisible edge.
            # This tricks pyvis/vis.js to render the graph without any errors
            if not current_edges and current_nodes:
                first_node_id = current_nodes[0]["id"]
                net.add_edge(
                    first_node_id,
                    first_node_id,
                    color="rgba(0,0,0,0)",
                    physics=False,
                )
            else:
                # If we have a real edge, add as normal
                for s, t in current_edges:
                    net.add_edge(s, t)

            # Disable physics to avoid unintentional scrambling
            net.set_options(
                        """
                    {
                      "physics": {"enabled": false},
                      "interaction": {
                        "dragNodes": true,
                        "multiselect": true,
                        "hover": true
                      }
                    }
                    """
                    )

            html = net.generate_html()

            # Script that tracks what node(s) is selected by iframe
            node_selector = """
                   <script type="text/javascript">
                   setTimeout(function() {
                       if (typeof network !== 'undefined') {
                           var clickedNodes = [];

                           // Listen for when a user is done moving a node
                           network.on("dragEnd", function(params) {
                               if (params.nodes.length > 0) {
                                   var nodeId = params.nodes[0];
                                   // Retrieve the exact coordinates via vis.js canvaset
                                   var positions = network.getPositions([nodeId]);
                                   var pos = positions[nodeId];

                                   window.parent.postMessage({
                                       event: 'node_moved',
                                       id: nodeId,
                                       x: Math.round(pos.x),
                                       y: Math.round(pos.y)
                                   }, '*');
                               }
                           });

                           network.on("click", function(params) {
                               var node_id = network.getNodeAt(params.pointer.DOM);
                               if (node_id !== undefined) {
                                   var index = clickedNodes.indexOf(node_id);
                                   if (index > -1) {
                                       clickedNodes.splice(index, 1);
                                   } else {
                                       clickedNodes.push(node_id);
                                   }

                                   window.parent.postMessage({event: 'nodes_tracked', list: clickedNodes}, '*');

                                   if (clickedNodes.length === 2) {
                                       window.parent.postMessage({
                                           event: 'toggle_edge_request',
                                           node1: clickedNodes[0],
                                           node2: clickedNodes[1]
                                       }, '*');
                                       clickedNodes = [];
                                       network.unselectAll();
                                   }
                               } else {
                                   clickedNodes = [];
                                   network.unselectAll();
                                   window.parent.postMessage({event: 'nodes_tracked', list: []}, '*');
                               }
                           });
                       }
                   }, 400);
                   </script>
                   """
            return html.replace("</body>", f"{node_selector}</body>")


    @ui.refreshable_method
    def render_graph_ui(self) -> None:
        """Renders the graph inside an isolated iframe to support <script> tags."""
        with ui.card().classes("w-full h-[500px] p-0 overflow-hidden"):
            html_content = self.build_graph_html()

            b64_html = base64.b64encode(html_content.encode("utf-8")).decode(
                "utf-8"
            )
            src_data = f"data:text/html;base64,{b64_html}"

            ui.element("iframe").props(f'src="{src_data}"').classes(
                "w-full h-full border-none"
            )
