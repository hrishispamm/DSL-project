"""
Automated Verification Suite for all 10 Official Test Cases (Section 10, Page 9)
and the Final Project Demonstration Scenario (Section 11, Page 9-10).
"""

from typing import List, Dict, Any
from graph_module import NetworkGraph
from dijkstra_engine import benchmark_implementations
from multistop_planner import plan_journey


def run_all_tests() -> List[Dict[str, Any]]:
    graph = NetworkGraph(core_only=True)
    results: List[Dict[str, Any]] = []

    # Test 1: Basic shortest path A -> C
    r1 = plan_journey(graph, "A", "C", [])
    results.append({
        "id": 1,
        "name": "Basic shortest path",
        "input": "Start: A, Dest: C",
        "expected": "A -> C; 2 km",
        "actual": f"{' -> '.join(r1['full_route'])}; {r1['total_distance']:g} km",
        "passed": r1["status"] == "SUCCESS" and r1["full_route"] == ["A", "C"] and r1["total_distance"] == 2.0,
        "notes": "Direct link A->C (2 km / 2 ms) verified via Min-Heap."
    })

    # Test 2: Alternative paths A -> D
    r2 = plan_journey(graph, "A", "D", [])
    results.append({
        "id": 2,
        "name": "Alternative paths",
        "input": "Start: A, Dest: D",
        "expected": "A -> B -> D (9 km) / Dijkstra optimal: A -> C -> B -> D (8 km)",
        "actual": f"{' -> '.join(r2['full_route'])}; {r2['total_distance']:g} km",
        "passed": r2["status"] == "SUCCESS" and r2["total_distance"] == 8.0,
        "notes": "Dijkstra discovers A->C(2)->B(1)->D(5) = 8 km, beating A->B(4)->D(5) = 9 km and A->C(2)->D(8) = 10 km."
    })

    # Test 3: Multi-stop journey Start A; stops C and D; destination F
    r3 = plan_journey(graph, "A", "F", ["C", "D"], strategy="nearest_neighbour")
    results.append({
        "id": 3,
        "name": "Multi-stop journey",
        "input": "Start: A; Stops: C, D; Dest: F",
        "expected": "Order C then D: A -> C -> B -> D -> E -> F (13 km) / Direct D->F leg: 14 km",
        "actual": f"Order {','.join(r3['ordered_stops'])}: {' -> '.join(r3['full_route'])}; {r3['total_distance']:g} km",
        "passed": r3["status"] == "SUCCESS" and r3["ordered_stops"] == ["C", "D"],
        "notes": "Visits C then D (B is transit junction); leg D->F takes shortest path D->E(2)->F(3)=5 km (total 13 km vs 14 km direct D->F)."
    })

    # Test 4: Unknown location A -> Z
    r4 = plan_journey(graph, "A", "Z", [])
    results.append({
        "id": 4,
        "name": "Unknown location",
        "input": "Start: A, Dest: Z",
        "expected": "Validation error: location not found.",
        "actual": r4["message"],
        "passed": r4["status"] == "UNKNOWN_LOCATION",
        "notes": "O(1) Hash Map lookup catches unknown ID 'Z' before graph traversal."
    })

    # Test 5: Disconnected location A -> G
    r5 = plan_journey(graph, "A", "G", [])
    results.append({
        "id": 5,
        "name": "Disconnected location",
        "input": "Start: A, Dest: G",
        "expected": "No route exists.",
        "actual": r5["message"],
        "passed": r5["status"] == "UNREACHABLE",
        "notes": "Node G has 0 edges in Adjacency List; Dijkstra terminates with distance = infinity."
    })

    # Test 6: Unreachable required stop Start A; stop G; destination F
    r6 = plan_journey(graph, "A", "F", ["G"])
    results.append({
        "id": 6,
        "name": "Unreachable required stop",
        "input": "Start: A; Stop: G; Dest: F",
        "expected": "No feasible complete route.",
        "actual": r6["message"],
        "passed": r6["status"] == "UNREACHABLE",
        "notes": "Multi-stop planner detects unreachable leg A->G and aborts assembly cleanly."
    })

    # Test 7: Duplicate stop Stops C and C
    r7 = plan_journey(graph, "A", "F", ["C", "C"], deduplicate_stops=False)
    results.append({
        "id": 7,
        "name": "Duplicate stop",
        "input": "Start: A; Stops: C, C; Dest: F",
        "expected": "Reject or deduplicate with a clear message.",
        "actual": r7["message"],
        "passed": r7["status"] == "DUPLICATE_STOP",
        "notes": "Input validator rejects duplicate stop 'C' with explicit message (auto-deduplicate also supported)."
    })

    # Test 8: Start also a stop Start A; stop A
    r8 = plan_journey(graph, "A", "F", ["A"])
    results.append({
        "id": 8,
        "name": "Start also a stop",
        "input": "Start: A; Stop: A; Dest: F",
        "expected": "Validation error in version one.",
        "actual": r8["message"],
        "passed": r8["status"] == "START_IN_STOPS",
        "notes": "Input validator prevents start node 'A' from being added as an intermediate stop."
    })

    # Test 9: Same start/destination A -> A, no stops
    r9 = plan_journey(graph, "A", "A", [])
    results.append({
        "id": 9,
        "name": "Same start/destination",
        "input": "Start: A, Dest: A, No stops",
        "expected": "Zero-distance journey.",
        "actual": f"{r9['message']} ({r9['total_distance']:g} km)",
        "passed": r9["status"] == "ZERO_DISTANCE" and r9["total_distance"] == 0.0,
        "notes": "Returns immediate 0 km / 0 ms loopback route [A]."
    })

    # Test 10: Compare stop orders Start A; stops C and E; destination F
    r10 = plan_journey(graph, "A", "F", ["C", "E"], strategy="exact_search")
    perms = r10.get("comparison", {}).get("all_permutations", [])
    perm_summary = "; ".join([f"{'->'.join(p['order'])} = {p['total_distance']:g} km" for p in perms])
    results.append({
        "id": 10,
        "name": "Compare stop orders",
        "input": "Start: A; Stops: C, E; Dest: F",
        "expected": "Prefer C then E over E then C",
        "actual": f"Selected {' then '.join(r10['ordered_stops'])} ({perm_summary})",
        "passed": r10["status"] == "SUCCESS" and r10["ordered_stops"] == ["C", "E"],
        "notes": "Both Nearest-Neighbour and Exact (k!) search prefer C then E (13 km) over E then C (21 km)."
    })

    return results


if __name__ == "__main__":
    suite = run_all_tests()
    passed_count = sum(1 for t in suite if t["passed"])
    print(f"=== TEST SUITE RESULTS ({passed_count}/{len(suite)} PASSED) ===")
    for t in suite:
        status_str = "PASS" if t["passed"] else "FAIL"
        print(f"[{status_str}] Test {t['id']}: {t['name']} | Input: {t['input']} -> {t['actual']}")
    bench = benchmark_implementations(NetworkGraph(core_only=False), "A", "F", runs=500)
    print("\n=== BENCHMARK (Min-Heap vs Linear Scan) ===")
    print(bench)
