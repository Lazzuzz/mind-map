# mind_map/frontend/graph.py
import base64

from nicegui import ui
from pyvis.network import Network

class Graph:
    """Pure rendering of a node/edge graph. Holds no state of its own —
    the caller (controller) is responsible for supplying current data.
    """

    def build_graph_html(self, nodes: list[dict], edges: list[tuple[int, int]]) -> str:
        net = Network(notebook=False, height="400px", width="100%")

        for node in nodes:
            node_x = node.get("x", None)
            node_y = node.get("y", None)

            net.add_node(
                node["id"],
                label=node["label"],
                color=node["color"],
                shape=node.get("shape", "box"),
                widthConstraint={"maximum": 150},
                font={"color": "white", "size": 14, "face": "Arial"},
                margin={"top": 12, "bottom": 12, "left": 16, "right": 16},
                shapeProperties={
                    "borderRadius": 6,
                    "useImageSize": False,
                    "interpolation": False,
                },
                x=node_x,
                y=node_y,
            )

        # Security check: if there are no edges, add an invisible one.
        # This tricks pyvis/vis.js into rendering the graph without errors.
        if not edges and nodes:
            first_node_id = nodes[0]["id"]
            net.add_edge(
                first_node_id,
                first_node_id,
                color="rgba(0,0,0,0)",
                physics=False,
            )
        else:
            for source, target in edges:
                net.add_edge(source, target)

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

        # Script that tracks selected node(s) and drag events inside the iframe
        node_selector = """
               <script type="text/javascript">
               setTimeout(function() {
                   if (typeof network !== 'undefined') {
                       var clickedNodes = [];

                       network.on("dragEnd", function(params) {
                           if (params.nodes.length > 0) {
                               var nodeId = params.nodes[0];
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
    def render_graph_ui(self, nodes: list[dict], edges: list[tuple[int, int]]) -> None:
        """Renders the graph inside an isolated iframe to support <script> tags.

        Call `.refresh(nodes, edges)` with fresh data any time the graph
        needs to be redrawn.
        """
        with ui.card().classes("w-full h-[500px] p-0 overflow-hidden"):
            html_content = self.build_graph_html(nodes, edges)

            import base64
            b64_html = base64.b64encode(html_content.encode("utf-8")).decode("utf-8")
            src_data = f"data:text/html;base64,{b64_html}"

            ui.element("iframe").props(f'src="{src_data}"').classes(
                "w-full h-full border-none"
            )
