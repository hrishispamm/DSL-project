"""
Member 2 Module: Network Topology / City Data, Graph & Hash Map Lookup
Implements:
- Hash Map (O(1) node lookup by unique ID)
- Adjacency List representation for weighted directed/bidirectional edges
- Validation of node existence, non-negative edge weights, and link status
- Default topology matching Section 10 of the Project Plan (Nodes A-G, plus optional H-J)
"""

from typing import Dict, List, Optional, Any
import copy


DEFAULT_TOPOLOGY_DATA: Dict[str, Any] = {
    "locations": [
        {
            "id": "A",
            "name": "Central Junction",
            "router_name": "Core-Router-A",
            "ip": "10.0.1.1",
            "role": "Core Gateway",
            "zone": "Central Core",
            "x": 140,
            "y": 240,
            "core": True
        },
        {
            "id": "B",
            "name": "City Hospital",
            "router_name": "Edge-Router-B",
            "ip": "10.0.2.1",
            "role": "Priority Medical Node",
            "zone": "North District",
            "x": 340,
            "y": 120,
            "core": True
        },
        {
            "id": "C",
            "name": "College",
            "router_name": "Campus-Switch-C",
            "ip": "10.0.3.1",
            "role": "Academic Backbone",
            "zone": "University Park",
            "x": 340,
            "y": 360,
            "core": True
        },
        {
            "id": "D",
            "name": "Shopping Centre",
            "router_name": "Metro-Hub-D",
            "ip": "10.0.4.1",
            "role": "Commercial Aggregator",
            "zone": "Midtown Plaza",
            "x": 570,
            "y": 160,
            "core": True
        },
        {
            "id": "E",
            "name": "Fuel Station",
            "router_name": "Relay-Node-E",
            "ip": "10.0.5.1",
            "role": "Telemetry Relay",
            "zone": "South Corridor",
            "x": 570,
            "y": 360,
            "core": True
        },
        {
            "id": "F",
            "name": "Railway Station",
            "router_name": "Transit-Gateway-F",
            "ip": "10.0.6.1",
            "role": "External Uplink",
            "zone": "East Terminal",
            "x": 800,
            "y": 240,
            "core": True
        },
        {
            "id": "G",
            "name": "Isolated Substation",
            "router_name": "Airgap-Node-G",
            "ip": "10.0.7.1",
            "role": "Offline / Disconnected",
            "zone": "Remote Outpost",
            "x": 800,
            "y": 430,
            "core": True
        },
        {
            "id": "H",
            "name": "Tech Park Data Center",
            "router_name": "Cloud-Core-H",
            "ip": "10.0.8.1",
            "role": "High-Speed Cloud Node",
            "zone": "Innovation Hub",
            "x": 150,
            "y": 90,
            "core": False
        },
        {
            "id": "I",
            "name": "Airport Control Tower",
            "router_name": "Aero-Relay-I",
            "ip": "10.0.9.1",
            "role": "Redundant Uplink",
            "zone": "Aviation Sector",
            "x": 790,
            "y": 80,
            "core": False
        },
        {
            "id": "J",
            "name": "Industrial Smart Grid",
            "router_name": "SCADA-Switch-J",
            "ip": "10.0.10.1",
            "role": "IoT Sensor Gateway",
            "zone": "West Logistics",
            "x": 150,
            "y": 420,
            "core": False
        }
    ],
    "roads": [
        {"from": "A", "to": "B", "distance": 4, "speed_kmh": 60, "bandwidth_mbps": 1000, "bidirectional": True, "active": True, "core": True},
        {"from": "A", "to": "C", "distance": 2, "speed_kmh": 50, "bandwidth_mbps": 1000, "bidirectional": True, "active": True, "core": True},
        {"from": "B", "to": "C", "distance": 1, "speed_kmh": 40, "bandwidth_mbps": 2500, "bidirectional": True, "active": True, "core": True},
        {"from": "B", "to": "D", "distance": 5, "speed_kmh": 60, "bandwidth_mbps": 1000, "bidirectional": True, "active": True, "core": True},
        {"from": "C", "to": "D", "distance": 8, "speed_kmh": 50, "bandwidth_mbps": 500, "bidirectional": True, "active": True, "core": True},
        {"from": "C", "to": "E", "distance": 10, "speed_kmh": 60, "bandwidth_mbps": 500, "bidirectional": True, "active": True, "core": True},
        {"from": "D", "to": "E", "distance": 2, "speed_kmh": 45, "bandwidth_mbps": 2500, "bidirectional": True, "active": True, "core": True},
        {"from": "D", "to": "F", "distance": 6, "speed_kmh": 70, "bandwidth_mbps": 1000, "bidirectional": True, "active": True, "core": True},
        {"from": "E", "to": "F", "distance": 3, "speed_kmh": 60, "bandwidth_mbps": 1000, "bidirectional": True, "active": True, "core": True},
        # Extended optional links for 10-node smart city / network mode (disabled in strict 7-node test mode if needed)
        {"from": "A", "to": "H", "distance": 3, "speed_kmh": 65, "bandwidth_mbps": 1000, "bidirectional": True, "active": True, "core": False},
        {"from": "H", "to": "B", "distance": 2, "speed_kmh": 60, "bandwidth_mbps": 1000, "bidirectional": True, "active": True, "core": False},
        {"from": "D", "to": "I", "distance": 4, "speed_kmh": 80, "bandwidth_mbps": 2500, "bidirectional": True, "active": True, "core": False},
        {"from": "I", "to": "F", "distance": 3, "speed_kmh": 75, "bandwidth_mbps": 2500, "bidirectional": True, "active": True, "core": False},
        {"from": "A", "to": "J", "distance": 5, "speed_kmh": 55, "bandwidth_mbps": 500, "bidirectional": True, "active": True, "core": False},
        {"from": "J", "to": "C", "distance": 4, "speed_kmh": 50, "bandwidth_mbps": 500, "bidirectional": True, "active": True, "core": False}
    ]
}


class NetworkGraph:
    """
    Represents the Router Network / Smart City Road Graph using:
    1. Hash Map (`self.location_map`) for O(1) node record lookup and validation
    2. Adjacency List (`self.adjacency_list`) for efficient neighbour traversal
    """

    def __init__(self, dataset: Optional[Dict[str, Any]] = None, core_only: bool = True):
        self.location_map: Dict[str, Dict[str, Any]] = {}
        self.adjacency_list: Dict[str, List[Dict[str, Any]]] = {}
        self.roads: List[Dict[str, Any]] = []
        self.core_only = core_only
        raw = copy.deepcopy(dataset if dataset is not None else DEFAULT_TOPOLOGY_DATA)
        self.load_dataset(raw, core_only=core_only)

    def load_dataset(self, data: Dict[str, Any], core_only: bool = True) -> None:
        self.location_map.clear()
        self.adjacency_list.clear()
        self.roads.clear()

        for loc in data.get("locations", []):
            if core_only and not loc.get("core", True):
                continue
            node_id = str(loc["id"]).strip()
            if not node_id:
                raise ValueError("Location ID cannot be empty.")
            if node_id in self.location_map:
                raise ValueError(f"Duplicate location ID detected: {node_id}")
            self.location_map[node_id] = loc
            self.adjacency_list[node_id] = []

        for road in data.get("roads", []):
            if core_only and not road.get("core", True):
                continue
            if not road.get("active", True):
                continue
            u = str(road["from"]).strip()
            v = str(road["to"]).strip()
            weight = float(road["distance"])
            if weight < 0:
                raise ValueError(f"Negative edge weight ({weight}) not allowed on {u} -> {v}.")
            if u not in self.location_map or v not in self.location_map:
                raise ValueError(f"Road references unknown location ID: {u} -> {v}")

            bidirectional = road.get("bidirectional", True)
            speed_kmh = float(road.get("speed_kmh", 60.0))
            bandwidth_mbps = float(road.get("bandwidth_mbps", 1000.0))

            self.roads.append(road)
            self.adjacency_list[u].append({
                "to": v,
                "weight": weight,
                "speed_kmh": speed_kmh,
                "bandwidth_mbps": bandwidth_mbps,
                "bidirectional": bidirectional
            })
            if bidirectional:
                self.adjacency_list[v].append({
                    "to": u,
                    "weight": weight,
                    "speed_kmh": speed_kmh,
                    "bandwidth_mbps": bandwidth_mbps,
                    "bidirectional": bidirectional
                })

    def has_location(self, node_id: str) -> bool:
        """O(1) Hash Map existence check."""
        return node_id in self.location_map

    def get_location(self, node_id: str) -> Optional[Dict[str, Any]]:
        """O(1) Hash Map lookup returning full location/router metadata."""
        return self.location_map.get(node_id)

    def get_neighbours(self, node_id: str) -> List[Dict[str, Any]]:
        """Adjacency List lookup for all outgoing links/roads from node_id."""
        if node_id not in self.adjacency_list:
            raise KeyError(f"Location '{node_id}' not found in graph.")
        return self.adjacency_list[node_id]

    def get_edge_info(self, u: str, v: str) -> Optional[Dict[str, Any]]:
        """Return edge metadata between u and v if connected."""
        for edge in self.adjacency_list.get(u, []):
            if edge["to"] == v:
                return edge
        return None

    def get_all_ids(self) -> List[str]:
        return list(self.location_map.keys())
