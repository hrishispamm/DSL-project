"""
Member 4 Module: Multi-Stop / Multi-Hop Planner & Route Assembler
Implements:
- Input validation according to Section 5 Error Handling Rules
- Pre-cached pairwise Dijkstra matrix for relevant locations (Section 4 Implementation Note)
- Nearest-Neighbour heuristic stop ordering
- Exact Permutation Search (k!) for optimal stop ordering comparison
- Route Assembler that joins individual path legs, removes duplicate junction nodes,
  distinguishes required stops from pass-through junctions, and calculates total distance & travel/transmission time.
"""

from typing import Dict, List, Optional, Any, Tuple
import itertools
import math
from graph_module import NetworkGraph
from dijkstra_engine import dijkstra_shortest_path


def validate_route_request(
    graph: NetworkGraph,
    start_id: Optional[str],
    dest_id: Optional[str],
    stops: Optional[List[str]],
    deduplicate_stops: bool = False
) -> Dict[str, Any]:
    """
    Validates start, destination, and intermediate stops against all Section 5 rules:
    1. Missing required input -> MISSING_INPUT
    2. Unknown location ID -> UNKNOWN_LOCATION ("Location not found.")
    3. Duplicate stops -> DUPLICATE_STOP (reject in v1 or deduplicate if requested)
    4. Start (or destination) included as an intermediate stop -> START_IN_STOPS
    """
    start = (start_id or "").strip()
    dest = (dest_id or "").strip()
    raw_stops = [str(s).strip() for s in (stops or []) if str(s).strip()]

    if not start or not dest:
        return {
            "valid": False,
            "status": "MISSING_INPUT",
            "message": "Missing required input: please select both a start location and a destination."
        }

    # Check existence of all IDs in Hash Map
    for loc_id in [start, dest] + raw_stops:
        if not graph.has_location(loc_id):
            return {
                "valid": False,
                "status": "UNKNOWN_LOCATION",
                "unknown_id": loc_id,
                "message": f"Validation error: Location '{loc_id}' not found."
            }

    # Check if start is included as a required stop (Test Case 8)
    if start in raw_stops:
        return {
            "valid": False,
            "status": "START_IN_STOPS",
            "message": f"Validation error: Start location '{start}' cannot also be listed as an intermediate stop."
        }

    # Check duplicate stops (Test Case 7)
    seen = set()
    deduped = []
    duplicates = []
    for s in raw_stops:
        if s in seen:
            duplicates.append(s)
        else:
            seen.add(s)
            deduped.append(s)

    if duplicates and not deduplicate_stops:
        dup_str = ", ".join(duplicates)
        return {
            "valid": False,
            "status": "DUPLICATE_STOP",
            "duplicates": duplicates,
            "message": f"Validation error: Duplicate intermediate stop(s) detected ({dup_str}). Remove duplicates or enable auto-deduplication."
        }

    return {
        "valid": True,
        "status": "VALID",
        "start": start,
        "destination": dest,
        "stops": deduped,
        "message": "Input validated."
    }


def build_pairwise_cache(
    graph: NetworkGraph,
    relevant_nodes: List[str]
) -> Dict[Tuple[str, str], Dict[str, Any]]:
    """
    Implementation Note (Page 4):
    Run Dijkstra between relevant selected locations and cache shortest paths/distances
    so the multi-stop planner can compare candidate stop orders without re-running Dijkstra.
    """
    cache: Dict[Tuple[str, str], Dict[str, Any]] = {}
    unique_nodes = list(dict.fromkeys(relevant_nodes))
    for u in unique_nodes:
        for v in unique_nodes:
            if u != v:
                cache[(u, v)] = dijkstra_shortest_path(graph, u, v, record_trace=True)
            else:
                cache[(u, v)] = {
                    "status": "ZERO_DISTANCE",
                    "path": [u],
                    "distance": 0.0,
                    "steps": []
                }
    return cache


def assemble_route(
    graph: NetworkGraph,
    start_id: str,
    ordered_stops: List[str],
    dest_id: str,
    cache: Dict[Tuple[str, str], Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Joins path legs in the chosen visiting order, avoids double-counting join nodes,
    and calculates individual leg distances, total distance, and travel/transmission estimates.
    """
    waypoints = [start_id] + list(ordered_stops) + [dest_id]
    full_node_sequence: List[str] = []
    legs: List[Dict[str, Any]] = []
    edge_segments: List[Dict[str, Any]] = []
    total_distance = 0.0
    total_time_minutes = 0.0

    for i in range(len(waypoints) - 1):
        u = waypoints[i]
        v = waypoints[i + 1]
        leg_res = cache.get((u, v)) or dijkstra_shortest_path(graph, u, v, record_trace=True)

        if leg_res["status"] not in ("SUCCESS", "ZERO_DISTANCE") or math.isinf(leg_res["distance"]):
            return {
                "status": "UNREACHABLE",
                "ordered_stops": ordered_stops,
                "full_route": [],
                "legs": [],
                "edge_segments": [],
                "total_distance": math.inf,
                "message": f"No feasible complete route: '{v}' is unreachable from '{u}'."
            }

        leg_path = leg_res["path"]
        leg_dist = leg_res["distance"]
        total_distance += leg_dist

        # Assemble without duplicating join nodes
        if not full_node_sequence:
            full_node_sequence.extend(leg_path)
        else:
            full_node_sequence.extend(leg_path[1:])

        # Break leg into individual road/link hops for detailed display
        hop_details = []
        leg_time_min = 0.0
        for j in range(len(leg_path) - 1):
            a, b = leg_path[j], leg_path[j + 1]
            edge = graph.get_edge_info(a, b)
            w = edge["weight"] if edge else 0.0
            spd = edge["speed_kmh"] if edge else 60.0
            bw = edge["bandwidth_mbps"] if edge else 1000.0
            hop_time_min = (w / spd) * 60.0 if spd > 0 else 0.0
            leg_time_min += hop_time_min
            seg = {
                "from": a,
                "to": b,
                "from_name": graph.get_location(a)["name"],
                "to_name": graph.get_location(b)["name"],
                "distance": w,
                "speed_kmh": spd,
                "bandwidth_mbps": bw,
                "travel_time_min": round(hop_time_min, 2)
            }
            hop_details.append(seg)
            edge_segments.append(seg)

        total_time_minutes += leg_time_min
        legs.append({
            "leg_index": i + 1,
            "from": u,
            "to": v,
            "from_name": graph.get_location(u)["name"],
            "to_name": graph.get_location(v)["name"],
            "path": leg_path,
            "distance": leg_dist,
            "travel_time_min": round(leg_time_min, 2),
            "hops": hop_details,
            "dijkstra_steps": leg_res.get("steps", [])
        })

    # Identify pass-through road junctions vs required stops
    required_set = set(ordered_stops)
    junction_nodes = [
        n for n in full_node_sequence[1:-1]
        if n not in required_set
    ]

    return {
        "status": "SUCCESS",
        "ordered_stops": ordered_stops,
        "waypoint_sequence": waypoints,
        "full_route": full_node_sequence,
        "junction_nodes": junction_nodes,
        "legs": legs,
        "edge_segments": edge_segments,
        "total_distance": round(total_distance, 4),
        "estimated_travel_time_min": round(total_time_minutes, 2),
        "message": "Complete route assembled."
    }


def plan_journey(
    graph: NetworkGraph,
    start_id: str,
    dest_id: str,
    stops: Optional[List[str]] = None,
    strategy: str = "nearest_neighbour",
    deduplicate_stops: bool = False
) -> Dict[str, Any]:
    """
    Coordinates validation, pairwise Dijkstra caching, multi-stop ordering
    (Nearest-Neighbour, Exact Search k!, and Requested Order comparison), and route assembly.
    """
    validation = validate_route_request(graph, start_id, dest_id, stops, deduplicate_stops=deduplicate_stops)
    if not validation["valid"]:
        return {
            "status": validation["status"],
            "message": validation["message"],
            "ordered_stops": [],
            "full_route": [],
            "legs": [],
            "total_distance": None
        }

    start = validation["start"]
    dest = validation["destination"]
    valid_stops = validation["stops"]

    # Case: Same start and destination with no intermediate stops (Test Case 9)
    if start == dest and len(valid_stops) == 0:
        return {
            "status": "ZERO_DISTANCE",
            "message": "Zero-distance journey: start and destination are identical with no intermediate stops.",
            "start": start,
            "destination": dest,
            "ordered_stops": [],
            "waypoint_sequence": [start],
            "full_route": [start],
            "junction_nodes": [],
            "legs": [],
            "edge_segments": [],
            "total_distance": 0.0,
            "estimated_travel_time_min": 0.0,
            "comparison": None
        }

    relevant_nodes = [start] + valid_stops + [dest]
    cache = build_pairwise_cache(graph, relevant_nodes)

    # Check if no intermediate stops: direct shortest-path query
    if len(valid_stops) == 0:
        direct_res = cache[(start, dest)]
        if direct_res["status"] == "UNREACHABLE":
            return {
                "status": "UNREACHABLE",
                "message": f"No route exists between {start} and {dest}.",
                "ordered_stops": [],
                "full_route": [],
                "legs": [],
                "total_distance": None
            }
        assembled = assemble_route(graph, start, [], dest, cache)
        assembled["strategy_used"] = "direct_dijkstra"
        assembled["comparison"] = None
        return assembled

    # 1. Evaluate User's Requested Order
    requested_assembled = assemble_route(graph, start, valid_stops, dest, cache)

    # 2. Nearest-Neighbour Heuristic Order
    unvisited = list(valid_stops)
    nn_order: List[str] = []
    current = start
    nn_reachable = True
    while unvisited:
        best_stop = None
        best_dist = math.inf
        for candidate in unvisited:
            d = cache[(current, candidate)]["distance"]
            if d < best_dist:
                best_dist = d
                best_stop = candidate
        if best_stop is None or math.isinf(best_dist):
            nn_reachable = False
            break
        nn_order.append(best_stop)
        unvisited.remove(best_stop)
        current = best_stop

    nn_assembled = (
        assemble_route(graph, start, nn_order, dest, cache)
        if nn_reachable
        else {"status": "UNREACHABLE", "total_distance": math.inf, "ordered_stops": nn_order, "full_route": []}
    )

    # 3. Exact Search (k! permutations) when stop count <= 7
    exact_assembled = None
    candidate_orders_evaluated: List[Dict[str, Any]] = []
    if len(valid_stops) <= 7:
        best_perm_dist = math.inf
        best_perm_assembled = None
        for perm in itertools.permutations(valid_stops):
            perm_list = list(perm)
            res = assemble_route(graph, start, perm_list, dest, cache)
            if res["status"] == "SUCCESS":
                candidate_orders_evaluated.append({
                    "order": perm_list,
                    "full_route": res["full_route"],
                    "total_distance": res["total_distance"]
                })
                if res["total_distance"] < best_perm_dist:
                    best_perm_dist = res["total_distance"]
                    best_perm_assembled = res
        exact_assembled = best_perm_assembled

    # Check if any feasible complete route exists
    if (
        nn_assembled["status"] != "SUCCESS"
        and requested_assembled["status"] != "SUCCESS"
        and (exact_assembled is None or exact_assembled["status"] != "SUCCESS")
    ):
        return {
            "status": "UNREACHABLE",
            "message": "No feasible complete route exists visiting all required stops.",
            "ordered_stops": valid_stops,
            "full_route": [],
            "legs": [],
            "total_distance": None
        }

    # Select result based on requested strategy
    if strategy == "requested_order" and requested_assembled["status"] == "SUCCESS":
        chosen = requested_assembled
    elif strategy == "exact_search" and exact_assembled is not None and exact_assembled["status"] == "SUCCESS":
        chosen = exact_assembled
    elif nn_assembled["status"] == "SUCCESS":
        chosen = nn_assembled
    elif exact_assembled is not None and exact_assembled["status"] == "SUCCESS":
        chosen = exact_assembled
    else:
        chosen = requested_assembled

    chosen["strategy_used"] = strategy
    chosen["comparison"] = {
        "requested_order": {
            "order": valid_stops,
            "full_route": requested_assembled.get("full_route", []),
            "total_distance": requested_assembled.get("total_distance")
        },
        "nearest_neighbour": {
            "order": nn_order,
            "full_route": nn_assembled.get("full_route", []),
            "total_distance": nn_assembled.get("total_distance")
        },
        "exact_search": {
            "order": exact_assembled.get("ordered_stops", []) if exact_assembled else [],
            "full_route": exact_assembled.get("full_route", []) if exact_assembled else [],
            "total_distance": exact_assembled.get("total_distance") if exact_assembled else None
        },
        "all_permutations": candidate_orders_evaluated
    }
    return chosen
