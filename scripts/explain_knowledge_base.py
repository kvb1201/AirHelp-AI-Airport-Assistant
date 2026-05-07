#!/usr/bin/env python3
"""
Print a structured explanation of the project's knowledge base:
what files exist, record counts, and how layers fit together.

Usage (from repo root):
  python scripts/explain_knowledge_base.py
  python scripts/explain_knowledge_base.py --json
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _len_json_array(path: Path) -> int | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return len(data) if isinstance(data, list) else None


def _len_json_dict_keys(path: Path) -> int | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return len(data) if isinstance(data, dict) else None


def _airport_data_summary(path: Path) -> dict[str, int | str]:
    out: dict[str, int | str] = {}
    if not path.is_file():
        out["missing"] = str(path)
        return out
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        out["error"] = str(e)
        return out
    if not isinstance(data, dict):
        return out
    for k, v in data.items():
        if isinstance(v, list):
            out[k] = len(v)
        elif isinstance(v, dict):
            out[k] = len(v)
        else:
            out[k] = 1
    return out


def _graph_bundle_counts(path: Path) -> tuple[int | None, int | None]:
    if not path.is_file():
        return None, None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None, None
    nodes = data.get("nodes")
    edges = data.get("edges")
    n = len(nodes) if isinstance(nodes, dict) else None
    e = len(edges) if isinstance(edges, list) else None
    return n, e


def _csv_rows(path: Path) -> int | None:
    if not path.is_file():
        return None
    try:
        with path.open(encoding="utf-8", newline="") as f:
            return sum(1 for _ in csv.DictReader(f))
    except OSError:
        return None


def _rag_map_count(path: Path) -> int | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    m = data.get("rag_to_graph")
    return len(m) if isinstance(m, dict) else None


def build_report() -> dict[str, object]:
    raw = ROOT / "data" / "raw"
    airport = ROOT / "data" / "airport"
    rag = ROOT / "data" / "rag"
    mock = ROOT / "data" / "mock"
    app_data = ROOT / "backend" / "app" / "data"

    layer_a = {
        "description": "Compiled KB: raw seeds normalized to places, chunks, terminal shell, flights from mock.",
        "raw_food_n": _len_json_array(raw / "food.json"),
        "raw_shops_n": _len_json_array(raw / "shops.json"),
        "raw_services_n": _len_json_array(raw / "services.json"),
        "compiled_places_n": _len_json_array(airport / "places.json"),
        "compiled_flights_n": _len_json_array(airport / "flights.json"),
        "compiled_offers_n": _len_json_array(airport / "offers.json"),
        "compiled_raw_docs_n": _len_json_array(airport / "raw_documents.json"),
        "knowledge_chunks_n": _len_json_array(rag / "knowledge_chunks.json"),
        "mock_flights_seed_n": _len_json_array(mock / "flights.json"),
    }

    layer_b_path = ROOT / "backend" / "app" / "core" / "rag" / "airport_data.json"
    layer_b = {
        "description": "RAG pipeline (Chroma): flattened sections from airport_data.json.",
        "file": str(layer_b_path.relative_to(ROOT)),
        "sections": _airport_data_summary(layer_b_path),
    }

    graph_path = app_data / "mumbai_t2_level02_graph.json"
    gn, ge = _graph_bundle_counts(graph_path)
    layer_c = {
        "description": "Walking graph + CSV POI overlays (coordinates 0-100, graph_node_id).",
        "graph_file": str(graph_path.relative_to(ROOT)),
        "node_count": gn,
        "edge_count": ge,
        "shops_csv_rows": _csv_rows(app_data / "shops_t2_l02.csv"),
        "facilities_csv_rows": _csv_rows(app_data / "facilities_bom.csv"),
        "rag_to_graph_mappings": _rag_map_count(app_data / "rag_to_graph_node_map.json"),
        "gate_policy_file": str((app_data / "mumbai_t2_gate_segregation.json").relative_to(ROOT)),
    }

    travel_path = app_data / "travel_documents.json"
    layer_d = {
        "description": "Offline travel document rules per country + city to country map.",
        "countries_with_rules": _len_json_dict_keys(travel_path),
        "city_mapping_entries": _len_json_dict_keys(app_data / "city_country_mapping.json"),
    }

    staging = {
        "description": "Scraped / optional assets not always wired to runtime.",
        "airport_services_detailed_n": _len_json_array(raw / "airport_services_detailed.json"),
        "mumbai_t2_catalog": str((app_data / "mumbai_t2_catalog.json").relative_to(ROOT)),
        "catalog_meta_note": "Mock demo catalog (flights + sample outlets) for orchestrator paths.",
    }

    narrative = "\n".join(
        [
            "KNOWLEDGE BASE OVERVIEW",
            "========================",
            "",
            "Layer A - Compiled airport KB",
            "  Source: data/raw/{food,shops,services}.json",
            "  Built by: backend/app/core/knowledge_base/repository.py (on startup if outputs missing)",
            "  Outputs: data/airport/*.json, data/rag/knowledge_chunks.json",
            "  Purpose: structured Place records + lexical chunks for search_places / get_relevant_chunks.",
            "",
            "Layer B - Semantic RAG",
            "  Source: backend/app/core/rag/airport_data.json",
            "  Pipeline: backend/app/core/rag/pipeline.py -> Chroma embeddings",
            "  Purpose: dense retrieval for recommendations / chat; IDs may use node-* prefix.",
            "",
            "Layer C - Navigation",
            "  Graph: backend/app/data/mumbai_t2_level02_graph.json (nodes + edges, minutes weights)",
            "  POIs: shops_t2_l02.csv, facilities_bom.csv - tie names to graph_node_id + map x_norm/y_norm",
            "  Bridge: rag_to_graph_node_map.json maps RAG node-* ids to t2_* graph ids",
            "",
            "Layer D - Travel documents",
            "  backend/app/data/travel_documents.json + city_country_mapping.json",
            "",
            "Timing / alerts - not static KB files: user flight times in StateManager + orchestrator nudges",
            "  (Head to security T-120 min, Go to gate T-45 min, Final call T-10 min vs boarding).",
            "",
            "Full prose reference: docs/knowledge_base_full_reference.md",
            "",
        ]
    )

    return {
        "root": str(ROOT),
        "narrative": narrative,
        "layer_a_compiled": layer_a,
        "layer_b_rag_file": layer_b,
        "layer_c_navigation": layer_c,
        "layer_d_travel": layer_d,
        "staging_and_catalog": staging,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Explain the project knowledge base layout and counts.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON only.")
    args = parser.parse_args()

    report = build_report()

    if args.json:
        # narrative is long; still useful for tooling
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0

    print(report["narrative"])

    def block(title: str, d: object) -> None:
        print(title)
        print("-" * len(title))
        if isinstance(d, dict):
            for k, v in d.items():
                print(f"  {k}: {v}")
        else:
            print(f"  {d}")
        print()

    block("Paths & counts - Layer A (compiled)", report["layer_a_compiled"])
    block("Layer B (airport_data.json sections)", report["layer_b_rag_file"])
    block("Layer C (graph + CSV)", report["layer_c_navigation"])
    block("Layer D (travel)", report["layer_d_travel"])
    block("Staging / catalog", report["staging_and_catalog"])
    print(f"Repository root: {report['root']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
