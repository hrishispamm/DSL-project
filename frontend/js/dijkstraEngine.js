/**
 * Member 3 Module (Frontend JS): Binary Min-Heap Priority Queue & Dijkstra Shortest-Path Engine
 */

export class MinHeap {
  constructor() {
    this.heap = [];
    this.opsCount = 0;
  }

  push(priority, node) {
    this.heap.push({ priority, node });
    this.opsCount++;
    this._siftUp(this.heap.length - 1);
  }

  pop() {
    if (this.heap.length === 0) return null;
    this.opsCount++;
    const top = this.heap[0];
    const last = this.heap.pop();
    if (this.heap.length > 0) {
      this.heap[0] = last;
      this._siftDown(0);
    }
    return top;
  }

  isEmpty() {
    return this.heap.length === 0;
  }

  snapshot() {
    return [...this.heap].sort((a, b) => a.priority - b.priority);
  }

  _siftUp(idx) {
    while (idx > 0) {
      const parent = Math.floor((idx - 1) / 2);
      if (
        this.heap[idx].priority < this.heap[parent].priority ||
        (this.heap[idx].priority === this.heap[parent].priority &&
          this.heap[idx].node < this.heap[parent].node)
      ) {
        [this.heap[idx], this.heap[parent]] = [this.heap[parent], this.heap[idx]];
        idx = parent;
      } else {
        break;
      }
    }
  }

  _siftDown(idx) {
    const n = this.heap.length;
    while (true) {
      let smallest = idx;
      const left = 2 * idx + 1;
      const right = 2 * idx + 2;
      if (
        left < n &&
        (this.heap[left].priority < this.heap[smallest].priority ||
          (this.heap[left].priority === this.heap[smallest].priority &&
            this.heap[left].node < this.heap[smallest].node))
      ) {
        smallest = left;
      }
      if (
        right < n &&
        (this.heap[right].priority < this.heap[smallest].priority ||
          (this.heap[right].priority === this.heap[smallest].priority &&
            this.heap[right].node < this.heap[smallest].node))
      ) {
        smallest = right;
      }
      if (smallest !== idx) {
        [this.heap[idx], this.heap[smallest]] = [this.heap[smallest], this.heap[idx]];
        idx = smallest;
      } else {
        break;
      }
    }
  }
}

export function runDijkstra(graph, sourceId, destId) {
  if (!graph.hasLocation(sourceId) || !graph.hasLocation(destId)) {
    return { status: 'INVALID_NODE', path: [], distance: Infinity, steps: [], heapOps: 0 };
  }
  if (sourceId === destId) {
    return { status: 'ZERO_DISTANCE', path: [sourceId], distance: 0, steps: [], heapOps: 0 };
  }

  const distances = {};
  const predecessors = {};
  const visited = new Set();
  for (const id of graph.getAllIds()) {
    distances[id] = Infinity;
    predecessors[id] = null;
  }

  distances[sourceId] = 0;
  const pq = new MinHeap();
  pq.push(0, sourceId);
  const steps = [];

  while (!pq.isEmpty()) {
    const { priority: currentDist, node: u } = pq.pop();
    if (visited.has(u)) continue;
    visited.add(u);

    const relaxations = [];
    if (u === destId) {
      steps.push({
        step: steps.length + 1,
        current: u,
        poppedDistance: currentDist,
        action: `Destination ${destId} settled at optimal cost ${currentDist}`,
        relaxations: [],
        heapSnapshot: pq.snapshot()
      });
      break;
    }

    for (const edge of graph.getNeighbours(u)) {
      const v = edge.to;
      if (visited.has(v)) continue;
      const cand = currentDist + edge.weight;
      const oldDist = distances[v];
      let updated = false;
      if (cand < distances[v]) {
        distances[v] = cand;
        predecessors[v] = u;
        pq.push(cand, v);
        updated = true;
      }
      relaxations.push({
        neighbour: v,
        weight: edge.weight,
        oldDistance: oldDist,
        newDistance: distances[v],
        updated
      });
    }

    steps.push({
      step: steps.length + 1,
      current: u,
      poppedDistance: currentDist,
      action: `Popped ${u} (cost ${currentDist}), inspected ${relaxations.length} neighbour(s)`,
      relaxations,
      heapSnapshot: pq.snapshot()
    });
  }

  if (!Number.isFinite(distances[destId])) {
    return { status: 'UNREACHABLE', path: [], distance: Infinity, steps, heapOps: pq.opsCount };
  }

  const path = [];
  let curr = destId;
  while (curr !== null) {
    path.push(curr);
    curr = predecessors[curr];
  }
  path.reverse();

  return {
    status: 'SUCCESS',
    path,
    distance: distances[destId],
    steps,
    heapOps: pq.opsCount
  };
}
