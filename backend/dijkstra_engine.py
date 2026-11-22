"""
Member 3 Module: Shortest-Path Engine (Dijkstra's Algorithm & Custom Binary Min-Heap)
Implements:
- Custom MinHeap Priority Queue class with step-by-step operation logging
- Dijkstra's Shortest-Path Algorithm using the Min-Heap (O((V + E) log V))
- Linear Scan Dijkstra comparator (O(V^2)) for performance benchmarking (Section 4 Optional Extension)
"""

from typing import Dict, List, Optional, Tuple, Any
import math
import time
from graph_module import NetworkGraph


class MinHeap:
    """
    Explicit binary Min-Heap priority queue storing tuples of (priority_distance, node_id).
    Retrieves the node with the smallest known distance in O(log V) time.
    """

    def __init__(self):
        self.heap: List[Tuple[float, str]] = []
        self.operations_count: int = 0

    def push(self, priority: float, node_id: str) -> None:
        self.heap.append((priority, node_id))
        self.operations_count += 1
        self._sift_up(len(self.heap) - 1)

    def pop(self) -> Tuple[float, str]:
        if not self.heap:
            raise IndexError("pop from an empty MinHeap")
        self.operations_count += 1
        smallest = self.heap[0]
        last = self.heap.pop()
        if self.heap:
            self.heap[0] = last
            self._sift_down(0)
        return smallest

    def is_empty(self) -> bool:
        return len(self.heap) == 0

    def size(self) -> int:
        return len(self.heap)

    def snapshot(self) -> List[Dict[str, Any]]:
        return [{"node": item[1], "distance": item[0]} for item in sorted(self.heap)]

    def _sift_up(self, idx: int) -> None:
        while idx > 0:
            parent = (idx - 1) // 2
            if self.heap[idx] < self.heap[parent]:
                self.heap[idx], self.heap[parent] = self.heap[parent], self.heap[idx]
                idx = parent
            else:
                break

    def _sift_down(self, idx: int) -> None:
        n = len(self.heap)
        while True:
            smallest = idx
            left = 2 * idx + 1
            right = 2 * idx + 2
            if left < n and self.heap[left] < self.heap[smallest]:
                smallest = left
            if right < n and self.heap[right] < self.heap[smallest]:
                smallest = right
            if smallest != idx:
                self.heap[idx], self.heap[smallest] = self.heap[smallest], self.heap[idx]
                idx = smallest
            else:
                break


def dijkstra_shortest_path(
    graph: NetworkGraph,
    source_id: str,
    dest_id: str,
    record_trace: bool = True
) -> Dict[str, Any]:
    """
    Runs Dijkstra's shortest-path algorithm with a custom Min-Heap.
    Returns structured status, path, total distance/latency, and step-by-step trace.
    """
    if not graph.has_location(source_id) or not graph.has_location(dest_id):
        return {
            "status": "INVALID_NODE",
            "path": [],
            "distance": math.inf,
            "steps": [],
            "heap_ops": 0,
            "message": "Location not found."
        }

    if source_id == dest_id:
        return {
            "status": "ZERO_DISTANCE",
            "path": [source_id],
            "distance": 0.0,
            "steps": [{
                "step": 1,
                "action": "Source equals destination (zero-distance journey)",
                "current": source_id,
                "popped_distance": 0.0,
                "relaxations": [],
                "heap_snapshot": []
            }],
            "heap_ops": 0,
            "message": "Zero-distance journey."
        }

    distances: Dict[str, float] = {node: math.inf for node in graph.get_all_ids()}
    predecessors: Dict[str, Optional[str]] = {node: None for node in graph.get_all_ids()}
    visited: set = set()

    distances[source_id] = 0.0
    pq = MinHeap()
    pq.push(0.0, source_id)

    steps: List[Dict[str, Any]] = []
    step_num = 0

    while not pq.is_empty():
        current_dist, u = pq.pop()

        if u in visited:
            continue
        visited.add(u)
        step_num += 1

        relaxations: List[Dict[str, Any]] = []

        if u == dest_id:
            if record_trace:
                steps.append({
                    "step": step_num,
                    "action": f"Reached destination {dest_id} with optimal distance {current_dist}",
                    "current": u,
                    "popped_distance": current_dist,
                    "relaxations": [],
                    "heap_snapshot": pq.snapshot()
                })
            break

        for edge in graph.get_neighbours(u):
            v = edge["to"]
            weight = edge["weight"]
            if v in visited:
                continue
            candidate_dist = current_dist + weight
            updated = False
            old_dist = distances[v]
            if candidate_dist < distances[v]:
                distances[v] = candidate_dist
                predecessors[v] = u
                pq.push(candidate_dist, v)
                updated = True

            if record_trace:
                relaxations.append({
                    "neighbour": v,
                    "edge_weight": weight,
                    "old_distance": None if math.isinf(old_dist) else old_dist,
                    "new_distance": candidate_dist if updated else (None if math.isinf(old_dist) else old_dist),
                    "updated": updated
                })

        if record_trace:
            steps.append({
                "step": step_num,
                "action": f"Popped {u} (dist={current_dist}) and inspected neighbours",
                "current": u,
                "popped_distance": current_dist,
                "relaxations": relaxations,
                "heap_snapshot": pq.snapshot()
            })

    if math.isinf(distances[dest_id]):
        return {
            "status": "UNREACHABLE",
            "path": [],
            "distance": math.inf,
            "steps": steps,
            "heap_ops": pq.operations_count,
            "message": f"No route exists between {source_id} and {dest_id}."
        }

    # Reconstruct shortest path from predecessors
    path: List[str] = []
    curr: Optional[str] = dest_id
    while curr is not None:
        path.append(curr)
        curr = predecessors[curr]
    path.reverse()

    return {
        "status": "SUCCESS",
        "path": path,
        "distance": distances[dest_id],
        "steps": steps,
        "heap_ops": pq.operations_count,
        "message": "Shortest path found."
    }


def dijkstra_linear_scan(graph: NetworkGraph, source_id: str, dest_id: str) -> Dict[str, Any]:
    """
    Simpler O(V^2) Dijkstra implementation that scans all unprocessed vertices
    instead of using a Min-Heap (for Section 4 Optional Advanced Extension comparison).
    """
    nodes = graph.get_all_ids()
    distances: Dict[str, float] = {n: math.inf for n in nodes}
    predecessors: Dict[str, Optional[str]] = {n: None for n in nodes}
    unprocessed = set(nodes)
    distances[source_id] = 0.0
    scan_comparisons = 0

    while unprocessed:
        best_node = None
        best_dist = math.inf
        for n in unprocessed:
            scan_comparisons += 1
            if distances[n] < best_dist:
                best_dist = distances[n]
                best_node = n

        if best_node is None or math.isinf(best_dist):
            break

        unprocessed.remove(best_node)
        if best_node == dest_id:
            break

        for edge in graph.get_neighbours(best_node):
            v = edge["to"]
            if v in unprocessed:
                cand = best_dist + edge["weight"]
                if cand < distances[v]:
                    distances[v] = cand
                    predecessors[v] = best_node

    if math.isinf(distances.get(dest_id, math.inf)):
        return {"status": "UNREACHABLE", "path": [], "distance": math.inf, "scan_comparisons": scan_comparisons}

    path: List[str] = []
    curr: Optional[str] = dest_id
    while curr is not None:
        path.append(curr)
        curr = predecessors[curr]
    path.reverse()
    return {
        "status": "SUCCESS",
        "path": path,
        "distance": distances[dest_id],
        "scan_comparisons": scan_comparisons
    }


def benchmark_implementations(graph: NetworkGraph, source_id: str = "A", dest_id: str = "F", runs: int = 200) -> Dict[str, Any]:
    """Compare Min-Heap Dijkstra vs Linear Scan Dijkstra execution time and operation counts."""
    t0 = time.perf_counter()
    heap_res = {}
    for _ in range(runs):
        heap_res = dijkstra_shortest_path(graph, source_id, dest_id, record_trace=False)
    heap_ms = (time.perf_counter() - t0) * 1000.0

    t1 = time.perf_counter()
    scan_res = {}
    for _ in range(runs):
        scan_res = dijkstra_linear_scan(graph, source_id, dest_id)
    scan_ms = (time.perf_counter() - t1) * 1000.0

    return {
        "runs": runs,
        "min_heap_total_ms": round(heap_ms, 3),
        "linear_scan_total_ms": round(scan_ms, 3),
        "min_heap_ops_per_run": heap_res.get("heap_ops", 0),
        "linear_scan_comparisons_per_run": scan_res.get("scan_comparisons", 0),
        "complexity_explanation": (
            "Min-Heap Priority Queue selects the next vertex in O(log V) giving O((V + E) log V), "
            "whereas scanning all unprocessed vertices takes O(V) per step giving O(V^2)."
        )
    }
