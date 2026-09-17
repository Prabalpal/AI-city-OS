import json
from pathlib import Path


DATA_FILE = Path(__file__).resolve().parents[1] / "backend" / "data" / "seed_data.json"


def test_seed_data_has_required_entity_counts():
    payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    entities = payload["entities"]

    counts = {}
    for item in entities:
        counts[item["type"]] = counts.get(item["type"], 0) + 1

    assert counts["road"] == 10
    assert counts["hospital"] == 5
    assert counts["school"] == 10
    assert counts["government_office"] == 5
    assert counts["power_station"] == 5
    assert counts["drainage_zone"] == 5
    assert counts["bus_route"] == 5
    assert counts["city_zone"] == 10


def test_seed_data_has_relationships_between_entities():
    payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    relationships = payload["relationships"]

    assert len(relationships) >= 30
    assert any(r["source_id"] == "ROAD_R1" and r["target_id"] == "HOSPITAL_H1" for r in relationships)
    assert any(r["source_id"] == "POWER_P2" and r["target_id"] == "HOSPITAL_H1" for r in relationships)
    assert any(r["source_id"] == "DRAIN_D2" and r["target_id"] == "ZONE_A" for r in relationships)
    assert any(r["source_id"] == "BUS_B1" and r["target_id"] == "ZONE_A" for r in relationships)
