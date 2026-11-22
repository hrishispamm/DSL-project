/**
 * Member 2 Module (Frontend JS): Topology Data, Graph, Adjacency List & Hash Map Lookup
 * Supports both Network Packet Router Mode (Routers/Links/ms) and Smart City Route Mode (Locations/Roads/km).
 */

export const DEFAULT_TOPOLOGY = {
  locations: [
    { id: 'A', name: 'Central Junction', routerName: 'Core-Router-A', ip: '10.0.1.1', role: 'Core Gateway', x: 130, y: 230, core: true },
    { id: 'B', name: 'City Hospital', routerName: 'Edge-Router-B', ip: '10.0.2.1', role: 'Priority Medical Node', x: 330, y: 110, core: true },
    { id: 'C', name: 'College', routerName: 'Campus-Switch-C', ip: '10.0.3.1', role: 'Academic Backbone', x: 330, y: 350, core: true },
    { id: 'D', name: 'Shopping Centre', routerName: 'Metro-Hub-D', ip: '10.0.4.1', role: 'Commercial Aggregator', x: 560, y: 145, core: true },
    { id: 'E', name: 'Fuel Station', routerName: 'Relay-Node-E', ip: '10.0.5.1', role: 'Telemetry Relay', x: 560, y: 350, core: true },
    { id: 'F', name: 'Railway Station', routerName: 'Transit-Gateway-F', ip: '10.0.6.1', role: 'External Uplink', x: 785, y: 230, core: true },
    { id: 'G', name: 'Isolated Node G', routerName: 'Airgap-Subnet-G', ip: '10.0.7.1', role: 'Disconnected Node', x: 785, y: 410, core: true },
    { id: 'H', name: 'Tech Park DC', routerName: 'Cloud-Core-H', ip: '10.0.8.1', role: 'Cloud Data Center', x: 140, y: 80, core: false },
    { id: 'I', name: 'Airport Tower', routerName: 'Aero-Relay-I', ip: '10.0.9.1', role: 'Redundant Uplink', x: 775, y: 75, core: false },
    { id: 'J', name: 'Smart Grid Hub', routerName: 'SCADA-Switch-J', ip: '10.0.10.1', role: 'IoT Gateway', x: 140, y: 405, core: false }
  ],
  roads: [
    { id: 'A-B', from: 'A', to: 'B', distance: 4, speedKmh: 60, bandwidthMbps: 1000, bidirectional: true, active: true, core: true },
    { id: 'A-C', from: 'A', to: 'C', distance: 2, speedKmh: 50, bandwidthMbps: 1000, bidirectional: true, active: true, core: true },
    { id: 'B-C', from: 'B', to: 'C', distance: 1, speedKmh: 40, bandwidthMbps: 2500, bidirectional: true, active: true, core: true },
    { id: 'B-D', from: 'B', to: 'D', distance: 5, speedKmh: 60, bandwidthMbps: 1000, bidirectional: true, active: true, core: true },
    { id: 'C-D', from: 'C', to: 'D', distance: 8, speedKmh: 50, bandwidthMbps: 500, bidirectional: true, active: true, core: true },
    { id: 'C-E', from: 'C', to: 'E', distance: 10, speedKmh: 60, bandwidthMbps: 500, bidirectional: true, active: true, core: true },
    { id: 'D-E', from: 'D', to: 'E', distance: 2, speedKmh: 45, bandwidthMbps: 2500, bidirectional: true, active: true, core: true },
    { id: 'D-F', from: 'D', to: 'F', distance: 6, speedKmh: 70, bandwidthMbps: 1000, bidirectional: true, active: true, core: true },
    { id: 'E-F', from: 'E', to: 'F', distance: 3, speedKmh: 60, bandwidthMbps: 1000, bidirectional: true, active: true, core: true },
    { id: 'A-H', from: 'A', to: 'H', distance: 3, speedKmh: 65, bandwidthMbps: 1000, bidirectional: true, active: true, core: false },
    { id: 'H-B', from: 'H', to: 'B', distance: 2, speedKmh: 60, bandwidthMbps: 1000, bidirectional: true, active: true, core: false },
    { id: 'D-I', from: 'D', to: 'I', distance: 4, speedKmh: 80, bandwidthMbps: 2500, bidirectional: true, active: true, core: false },
    { id: 'I-F', from: 'I', to: 'F', distance: 3, speedKmh: 75, bandwidthMbps: 2500, bidirectional: true, active: true, core: false },
    { id: 'A-J', from: 'A', to: 'J', distance: 5, speedKmh: 55, bandwidthMbps: 500, bidirectional: true, active: true, core: false },
    { id: 'J-C', from: 'J', to: 'C', distance: 4, speedKmh: 50, bandwidthMbps: 500, bidirectional: true, active: true, core: false }
  ]
};

export class NetworkGraph {
  constructor(topologyData = DEFAULT_TOPOLOGY, includeExtended = false) {
    this.locationMap = new Map();
    this.adjacencyList = new Map();
    this.includeExtended = includeExtended;
    this.load(topologyData, includeExtended);
  }

  load(data, includeExtended = false) {
    this.locationMap.clear();
    this.adjacencyList.clear();
    for (const loc of data.locations) {
      if (!includeExtended && !loc.core) continue;
      this.locationMap.set(loc.id, { ...loc });
      this.adjacencyList.set(loc.id, []);
    }
    for (const road of data.roads) {
      if (!includeExtended && !road.core) continue;
      if (!road.active) continue;
      if (!this.locationMap.has(road.from) || !this.locationMap.has(road.to)) continue;
      const weight = Number(road.distance);
      if (weight < 0) continue;
      this.adjacencyList.get(road.from).push({
        to: road.to,
        weight,
        speedKmh: road.speedKmh || 60,
        bandwidthMbps: road.bandwidthMbps || 1000,
        bidirectional: road.bidirectional !== false,
        edgeId: road.id
      });
      if (road.bidirectional !== false) {
        this.adjacencyList.get(road.to).push({
          to: road.from,
          weight,
          speedKmh: road.speedKmh || 60,
          bandwidthMbps: road.bandwidthMbps || 1000,
          bidirectional: true,
          edgeId: road.id
        });
      }
    }
  }

  hasLocation(id) {
    return this.locationMap.has(id);
  }

  getLocation(id) {
    return this.locationMap.get(id) || null;
  }

  getNeighbours(id) {
    return this.adjacencyList.get(id) || [];
  }

  getAllIds() {
    return Array.from(this.locationMap.keys());
  }
}
