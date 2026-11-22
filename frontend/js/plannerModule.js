/**
 * Member 4 Module (Frontend JS): Multi-Stop / Multi-Hop Planner & Route Assembler
 */

import { runDijkstra } from './dijkstraEngine.js';

export function getPermutations(arr) {
  if (arr.length <= 1) return [arr];
  const result = [];
  for (let i = 0; i < arr.length; i++) {
    const current = arr[i];
    const remaining = [...arr.slice(0, i), ...arr.slice(i + 1)];
    for (const p of getPermutations(remaining)) {
      result.push([current, ...p]);
    }
  }
  return result;
}

export function assembleRoute(graph, startId, orderedStops, destId, cache) {
  const waypoints = [startId, ...orderedStops, destId];
  const fullRoute = [];
  const legs = [];
  let totalDistance = 0;

  for (let i = 0; i < waypoints.length - 1; i++) {
    const u = waypoints[i];
    const v = waypoints[i + 1];
    const key = `${u}->${v}`;
    const res = cache.get(key) || runDijkstra(graph, u, v);
    if (res.status !== 'SUCCESS' && res.status !== 'ZERO_DISTANCE') {
      return { status: 'UNREACHABLE', orderedStops, fullRoute: [], legs: [], totalDistance: Infinity };
    }
    totalDistance += res.distance;
    if (fullRoute.length === 0) {
      fullRoute.push(...res.path);
    } else {
      fullRoute.push(...res.path.slice(1));
    }
    legs.push({
      legIndex: i + 1,
      from: u,
      to: v,
      path: res.path,
      distance: res.distance,
      steps: res.steps
    });
  }

  return {
    status: 'SUCCESS',
    orderedStops,
    waypoints,
    fullRoute,
    legs,
    totalDistance
  };
}
