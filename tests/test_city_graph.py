import json
from pathlib import Path

from backend.graph.city_graph import CityGraph


DATA_FILE = Path(__file__).resolve().parents[1] / "backend" / "data" / "seed_data.json"


def test_city_graph_builds_from_seed_data():
    payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    graph = CityGraph.from_seed_data(payload)

    assert graph.node_count() >= 50
    assert graph.edge_count() >= 30
    assert "ROAD_R1" in graph.graph.nodes
    assert "HOSPITAL_H1" in graph.graph.nodes
    assert "BUS_B1" in graph.graph.nodes


def test_city_graph_finds_nearby_and_connected_entities():
    payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    graph = CityGraph.from_seed_data(payload)

    nearby = graph.find_nearby_entities("ROAD_R1", radius_km=1.5)
    nearby_ids = {entity["id"] for entity in nearby}
    assert "HOSPITAL_H1" in nearby_ids
    assert "SCHOOL_S1" in nearby_ids
    assert "BUS_B1" in nearby_ids

    connected = graph.find_connected_entities("ROAD_R1", max_depth=2)
    connected_ids = {entity_id for entity_id in connected}
    assert "HOSPITAL_H1" in connected_ids
    assert "SCHOOL_S1" in connected_ids
    assert "BUS_B1" in connected_ids


def test_city_graph_identifies_critical_services():
    payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    graph = CityGraph.from_seed_data(payload)

    critical = graph.find_affected_critical_services("ROAD_R1", max_depth=3)
    assert any(entity_id == "HOSPITAL_H1" for entity_id in critical)
