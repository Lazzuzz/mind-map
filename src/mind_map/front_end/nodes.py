nodes_data = [
    {"id": 1, "label": "My new Mind-map", "color": "#3b82f6", "shape": "box"},
]

edges_data = [ ]

class Nodes:

    def getNodes(self):
        return nodes_data

    def getEdges(self):
        return edges_data

    def getNrOfNodes(self) -> int:
        return len(nodes_data)

    def addNode(self, source_node_id, label):
        new_id = len(nodes_data) + 1

        # Update state
        nodes_data.append(
            {
                "id": new_id,
                "label": f"{label}",
                "color": "#10b981",
                "shape": "box",
            }
        )
        edges_data.append((source_node_id, new_id))

    def updateNodeLabel(self, node_id: int, new_label: str) -> None:
            """Finds a node by ID and updates the label."""
            for node in nodes_data:
                if node["id"] == node_id:
                    node["label"] = new_label
                    break
