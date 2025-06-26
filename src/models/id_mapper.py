from typing import Dict, Optional

class IDMapper:
    def __init__(self):
        self._node_names = {}
        self._node_ids = set()

    def register_node(self, node_id: str, name: str) -> None:
        self._node_ids.add(node_id)
        self._node_names[node_id] = name

    def get_dash_id(self, node_id: str) -> Dict:
        return {"type": "node", "index": node_id}

    def get_html_id(self, node_id: str) -> str:
        return f"node-{node_id}"

    def get_node_name(self, node_id: str) -> str:
        return self._node_names.get(node_id, "")

    def get_node_id_from_dash(self, dash_id: Dict) -> Optional[str]:
        if isinstance(dash_id, dict) and dash_id.get("type") == "node":
            return dash_id.get("index")
        return None

    def update_node_name(self, node_id: str, new_name: str) -> None:
        if node_id in self._node_ids:
            self._node_names[node_id] = new_name 