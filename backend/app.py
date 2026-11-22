"""
Backend Application Server (Layer 2: Application Logic & REST API)
Coordinates:
- Member 2: Graph, Adjacency List & Hash Map (`graph_module.py`)
- Member 3: Shortest-Path Engine with Min-Heap (`dijkstra_engine.py`)
- Member 4: Multi-Stop Planner & Route Assembler (`multistop_planner.py`)
- Automated 10-Case Test Suite (`test_suite.py`)
Zero external dependencies required — uses Python's standard `http.server` and `json`.
"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import os
import time
from urllib.parse import urlparse
from graph_module import NetworkGraph, DEFAULT_TOPOLOGY_DATA
from dijkstra_engine import dijkstra_shortest_path, benchmark_implementations
from multistop_planner import plan_journey
from test_suite import run_all_tests


FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))


class RouterSimulatorAPIHandler(SimpleHTTPRequestHandler):
    """Serves both the Frontend Web App and the JSON REST API endpoints."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=FRONTEND_DIR, **kwargs)

    def _send_json(self, payload: dict, status_code: int = 200) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self._send_json({"ok": True})

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/topology":
            self._send_json({
                "status": "SUCCESS",
                "topology": DEFAULT_TOPOLOGY_DATA
            })
        elif parsed.path == "/api/test-suite":
            results = run_all_tests()
            self._send_json({
                "status": "SUCCESS",
                "total": len(results),
                "passed": sum(1 for r in results if r["passed"]),
                "results": results
            })
        elif parsed.path == "/api/benchmark":
            graph = NetworkGraph(core_only=False)
            bench = benchmark_implementations(graph, "A", "F", runs=500)
            self._send_json({
                "status": "SUCCESS",
                "benchmark": bench
            })
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        content_len = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_len).decode("utf-8") if content_len > 0 else "{}"
        try:
            data = json.loads(raw_body)
        except json.JSONDecodeError:
            self._send_json({"status": "INVALID_JSON", "message": "Malformed JSON request body."}, 400)
            return

        if parsed.path == "/api/route":
            custom_topology = data.get("topology")
            core_only = bool(data.get("core_only", True))
            graph = NetworkGraph(dataset=custom_topology, core_only=core_only)
            start_id = data.get("start", "")
            dest_id = data.get("destination", "")
            stops = data.get("stops", [])
            strategy = data.get("strategy", "nearest_neighbour")
            dedup = bool(data.get("deduplicate_stops", False))

            t0 = time.perf_counter()
            result = plan_journey(
                graph=graph,
                start_id=start_id,
                dest_id=dest_id,
                stops=stops,
                strategy=strategy,
                deduplicate_stops=dedup
            )
            result["compute_time_ms"] = round((time.perf_counter() - t0) * 1000.0, 4)
            self._send_json(result)

        elif parsed.path == "/api/dijkstra":
            custom_topology = data.get("topology")
            core_only = bool(data.get("core_only", True))
            graph = NetworkGraph(dataset=custom_topology, core_only=core_only)
            source_id = data.get("source", "A")
            dest_id = data.get("destination", "F")
            res = dijkstra_shortest_path(graph, source_id, dest_id, record_trace=True)
            self._send_json(res)

        else:
            self._send_json({"status": "NOT_FOUND", "message": f"Unknown endpoint {parsed.path}"}, 404)


def run_server(port: int = 8080) -> None:
    server = HTTPServer(("0.0.0.0", port), RouterSimulatorAPIHandler)
    print(f"Realtime Network Packet Router & Smart City Route Optimizer running at http://localhost:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
