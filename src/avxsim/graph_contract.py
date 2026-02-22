from __future__ import annotations

import copy
import re
from typing import Any, Dict, Iterable, Mapping, Optional


GRAPH_SCHEMA_VERSION = "web_e2e_graph_schema_v1"
GRAPH_VALIDATION_VERSION = "web_e2e_graph_validation_v1"

ALLOWED_NODE_TYPES = {
    "SceneSource",
    "RadarConfig",
    "Propagation",
    "AntennaPattern",
    "SynthFMCW",
    "RadarMap",
    "ComparePolicy",
    "RegressionGate",
    "ReportExport",
}

_ID_PATTERN = re.compile(r"^[A-Za-z0-9_.:-]+$")


def build_default_graph_templates() -> list[dict[str, Any]]:
    return [
        {
            "template_id": "radar_minimal_v1",
            "title": "Radar Minimal Pipeline",
            "description": "Scene -> propagation -> synth -> map",
            "graph": {
                "version": GRAPH_SCHEMA_VERSION,
                "graph_id": "radar_minimal_v1",
                "profile": "fast_debug",
                "nodes": [
                    {"id": "scene_1", "type": "SceneSource", "params": {}},
                    {"id": "prop_1", "type": "Propagation", "params": {"backend": "analytic_targets"}},
                    {"id": "synth_1", "type": "SynthFMCW", "params": {}},
                    {"id": "map_1", "type": "RadarMap", "params": {}},
                ],
                "edges": [
                    {"id": "e1", "source": "scene_1", "target": "prop_1", "contract": "scene_payload"},
                    {"id": "e2", "source": "prop_1", "target": "synth_1", "contract": "path_list"},
                    {"id": "e3", "source": "synth_1", "target": "map_1", "contract": "adc_cube"},
                ],
            },
        }
    ]


def validate_graph_contract_payload(
    payload: Mapping[str, Any],
    *,
    allowed_profiles: Optional[Iterable[str]] = None,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(payload, Mapping):
        return {
            "version": GRAPH_VALIDATION_VERSION,
            "valid": False,
            "errors": ["request body must be a JSON object"],
            "warnings": [],
            "stats": {"node_count": 0, "edge_count": 0, "source_count": 0, "sink_count": 0},
            "normalized": None,
        }

    version = str(payload.get("version", GRAPH_SCHEMA_VERSION)).strip() or GRAPH_SCHEMA_VERSION
    if version != GRAPH_SCHEMA_VERSION:
        errors.append(
            f"version must be '{GRAPH_SCHEMA_VERSION}' (received: {version!r})"
        )

    graph_id = str(payload.get("graph_id", "")).strip()
    if not graph_id:
        errors.append("graph_id is required")
    elif not _ID_PATTERN.fullmatch(graph_id):
        errors.append("graph_id has invalid characters")

    profile = str(payload.get("profile", "balanced_dev")).strip() or "balanced_dev"
    allowed_profile_set = set(str(x).strip() for x in (allowed_profiles or []))
    if allowed_profile_set and profile not in allowed_profile_set:
        errors.append(
            f"profile must be one of {sorted(allowed_profile_set)!r} (received: {profile!r})"
        )

    nodes_raw = payload.get("nodes", [])
    edges_raw = payload.get("edges", [])

    if not isinstance(nodes_raw, list):
        errors.append("nodes must be a list")
        nodes_raw = []
    if not isinstance(edges_raw, list):
        errors.append("edges must be a list")
        edges_raw = []

    node_ids: set[str] = set()
    nodes_norm: list[dict[str, Any]] = []
    for idx, node in enumerate(nodes_raw):
        if not isinstance(node, Mapping):
            errors.append(f"nodes[{idx}] must be object")
            continue
        node_id = str(node.get("id", "")).strip()
        node_type = str(node.get("type", "")).strip()
        params = node.get("params", {})
        ui = node.get("ui", {})

        if not node_id:
            errors.append(f"nodes[{idx}].id is required")
            continue
        if not _ID_PATTERN.fullmatch(node_id):
            errors.append(f"nodes[{idx}].id has invalid characters: {node_id!r}")
            continue
        if node_id in node_ids:
            errors.append(f"duplicate node id: {node_id!r}")
            continue
        node_ids.add(node_id)

        if not node_type:
            errors.append(f"nodes[{idx}].type is required")
        elif node_type not in ALLOWED_NODE_TYPES:
            errors.append(
                f"nodes[{idx}].type must be one of {sorted(ALLOWED_NODE_TYPES)!r}"
            )

        if not isinstance(params, Mapping):
            warnings.append(f"nodes[{idx}].params is not object; coercing to empty object")
            params = {}
        if not isinstance(ui, Mapping):
            warnings.append(f"nodes[{idx}].ui is not object; coercing to empty object")
            ui = {}

        nodes_norm.append(
            {
                "id": node_id,
                "type": node_type,
                "params": copy.deepcopy(dict(params)),
                "ui": copy.deepcopy(dict(ui)),
            }
        )

    if len(nodes_norm) == 0:
        errors.append("nodes must include at least one node")

    indegree: Dict[str, int] = {nid: 0 for nid in node_ids}
    adjacency: Dict[str, list[str]] = {nid: [] for nid in node_ids}
    edges_norm: list[dict[str, Any]] = []

    for idx, edge in enumerate(edges_raw):
        if not isinstance(edge, Mapping):
            errors.append(f"edges[{idx}] must be object")
            continue
        edge_id = str(edge.get("id", f"e{idx+1}")).strip() or f"e{idx+1}"
        source = str(edge.get("source", "")).strip()
        target = str(edge.get("target", "")).strip()
        contract = str(edge.get("contract", "generic")).strip() or "generic"
        if not source:
            errors.append(f"edges[{idx}].source is required")
        if not target:
            errors.append(f"edges[{idx}].target is required")
        if source and source not in node_ids:
            errors.append(f"edges[{idx}].source not found in nodes: {source!r}")
        if target and target not in node_ids:
            errors.append(f"edges[{idx}].target not found in nodes: {target!r}")

        edges_norm.append(
            {
                "id": edge_id,
                "source": source,
                "target": target,
                "contract": contract,
            }
        )
        if source in node_ids and target in node_ids:
            adjacency[source].append(target)
            indegree[target] = int(indegree.get(target, 0)) + 1

    source_nodes = [nid for nid, deg in indegree.items() if int(deg) == 0]
    sink_nodes = [nid for nid in node_ids if len(adjacency.get(nid, [])) == 0]
    isolated_nodes = [
        nid
        for nid in node_ids
        if int(indegree.get(nid, 0)) == 0 and len(adjacency.get(nid, [])) == 0 and len(node_ids) > 1
    ]

    if len(source_nodes) == 0 and len(node_ids) > 0:
        errors.append("graph must have at least one source node")
    if len(sink_nodes) == 0 and len(node_ids) > 0:
        errors.append("graph must have at least one sink node")
    if len(isolated_nodes) > 0:
        warnings.append(f"isolated nodes detected: {isolated_nodes!r}")

    # Kahn topological ordering.
    indegree_tmp = dict(indegree)
    queue = sorted(source_nodes)
    topo: list[str] = []
    while len(queue) > 0:
        nid = queue.pop(0)
        topo.append(nid)
        for nxt in adjacency.get(nid, []):
            indegree_tmp[nxt] = int(indegree_tmp.get(nxt, 0)) - 1
            if indegree_tmp[nxt] == 0:
                queue.append(nxt)
        queue.sort()

    if len(node_ids) > 0 and len(topo) != len(node_ids):
        errors.append("graph contains cycle(s); DAG is required for execution planning")

    valid = len(errors) == 0
    normalized = {
        "version": GRAPH_SCHEMA_VERSION,
        "graph_id": graph_id or "invalid_graph",
        "profile": profile,
        "nodes": nodes_norm,
        "edges": edges_norm,
        "topological_order": topo,
    }

    return {
        "version": GRAPH_VALIDATION_VERSION,
        "valid": valid,
        "errors": errors,
        "warnings": warnings,
        "stats": {
            "node_count": len(nodes_norm),
            "edge_count": len(edges_norm),
            "source_count": len(source_nodes),
            "sink_count": len(sink_nodes),
        },
        "normalized": normalized,
    }
