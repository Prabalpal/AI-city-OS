from __future__ import annotations

import math
from collections import deque
from typing import Any

import networkx as nx

from backend.models.entity import CityEntity, EntityRelationship


class CityGraph:
    def __init__(self) -> None:
        self.graph: nx.Graph = nx.Graph()

    @classmethod
    def from_seed_data(cls, payload: dict[str, Any]) -> "CityGraph":
        graph = cls()

        for item in payload.get("entities", []):
            graph.add_entity(
                CityEntity(
                    id=item["id"],
                    name=item["name"],
                    type=item["type"],
                    latitude=item["latitude"],
                    longitude=item["longitude"],
                    zone=item["zone"],
                    status=item["status"],
                    metadata=item.get("metadata", {}),
                )
            )

        for item in payload.get("relationships", []):
            graph.add_relationship(
                EntityRelationship(
                    source_id=item["source_id"],
                    target_id=item["target_id"],
                    relationship=item["relationship"],
                    metadata=item.get("metadata", {}),
                )
            )

        return graph

    def add_entity(self, entity: CityEntity) -> None:
        self.graph.add_node(
            entity.id,
            **entity.model_dump(),
        )

    def add_relationship(self, relationship: EntityRelationship) -> None:
        if relationship.source_id not in self.graph.nodes or relationship.target_id not in self.graph.nodes:
            raise ValueError(
                f"Cannot add relationship between unknown entities: {relationship.source_id} -> {relationship.target_id}"
            )

        self.graph.add_edge(
            relationship.source_id,
            relationship.target_id,
            relationship=relationship.relationship,
            metadata=relationship.metadata,
        )

    def node_count(self) -> int:
        return self.graph.number_of_nodes()

    def edge_count(self) -> int:
        return self.graph.number_of_edges()

    def get_entity(self, entity_id: str) -> dict[str, Any] | None:
        if entity_id not in self.graph.nodes:
            return None
        return dict(self.graph.nodes[entity_id])

    def find_nearby_entities(self, entity_id: str, radius_km: float = 3.0) -> list[dict[str, Any]]:
        if entity_id not in self.graph.nodes:
            return []

        reference = self.graph.nodes[entity_id]
        nearby: list[dict[str, Any]] = []

        for other_id, attrs in self.graph.nodes(data=True):
            if other_id == entity_id:
                continue
            distance = self._haversine_km(reference["latitude"], reference["longitude"], attrs["latitude"], attrs["longitude"])
            if distance <= radius_km:
                nearby.append({"id": other_id, **attrs})

        return sorted(nearby, key=lambda item: item["id"])

    def find_connected_entities(self, entity_id: str, max_depth: int = 3) -> list[str]:
        if entity_id not in self.graph.nodes:
            return []

        seen: set[str] = {entity_id}
        queue: deque[tuple[str, int]] = deque([(entity_id, 0)])
        connected: list[str] = []

        while queue:
            current, depth = queue.popleft()
            for neighbor in self.graph.neighbors(current):
                if neighbor in seen:
                    continue
                seen.add(neighbor)
                connected.append(neighbor)
                if depth + 1 < max_depth:
                    queue.append((neighbor, depth + 1))

        return connected

    def find_affected_critical_services(self, entity_id: str, max_depth: int = 3) -> list[str]:
        connected = self.find_connected_entities(entity_id, max_depth=max_depth)
        critical: list[str] = []

        for entity in connected:
            attrs = self.graph.nodes[entity]
            if attrs.get("type") in {"hospital", "power_station", "government_office", "drainage_zone"}:
                critical.append(entity)

        return critical

    def traverse_relationships(self, root_id: str, max_depth: int = 3) -> list[dict[str, Any]]:
        if root_id not in self.graph.nodes:
            return []

        visited: set[str] = set()
        queue: deque[tuple[str, int]] = deque([(root_id, 0)])
        chain: list[dict[str, Any]] = []

        while queue:
            current, depth = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            chain.append({"entity_id": current, "depth": depth})
            if depth >= max_depth:
                continue
            for neighbor in self.graph.neighbors(current):
                if neighbor not in visited:
                    queue.append((neighbor, depth + 1))

        return chain

    def impact_chain(self, root_id: str, max_depth: int = 3) -> list[str]:
        return [step["entity_id"] for step in self.traverse_relationships(root_id, max_depth=max_depth)]

    def find_entity_connections(self, entity_id: str) -> list[dict[str, Any]]:
        if entity_id not in self.graph.nodes:
            return []

        results: list[dict[str, Any]] = []
        for neighbor in self.graph.neighbors(entity_id):
            edge_data = self.graph.get_edge_data(entity_id, neighbor)
            results.append(
                {
                    "neighbor_id": neighbor,
                    "relationship": edge_data.get("relationship", "connected"),
                    "metadata": edge_data.get("metadata", {}),
                }
            )
        return results

    @staticmethod
    def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        radius_km = 6371.0
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        a = (
            math.sin(d_lat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(d_lon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return radius_km * c
