import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence


DEFAULT_CANDIDATE_GLOBS = ["candidates/*.npz"]


def discover_candidate_npz_paths(
    pack_root: str,
    candidate_globs: Sequence[str] = DEFAULT_CANDIDATE_GLOBS,
    exclude_globs: Optional[Sequence[str]] = None,
) -> List[Path]:
    root = Path(pack_root)
    if not root.exists() or not root.is_dir():
        raise ValueError(f"pack_root must be existing directory: {pack_root}")

    excluded = set()
    if exclude_globs is not None:
        for pattern in exclude_globs:
            for p in root.glob(str(pattern)):
                excluded.add(p.resolve())

    found: Dict[str, Path] = {}
    for pattern in candidate_globs:
        for p in root.glob(str(pattern)):
            if not p.is_file():
                continue
            rp = p.resolve()
            if rp in excluded:
                continue
            found[str(rp)] = p

    return [found[k] for k in sorted(found.keys())]


def resolve_profile_json(pack_root: str, profile_json: Optional[str] = None) -> Path:
    root = Path(pack_root)
    if profile_json is not None:
        p = Path(profile_json)
        if not p.is_absolute():
            p = root / p
        if not p.exists() or not p.is_file():
            raise ValueError(f"profile_json not found: {p}")
        return p

    candidates = [
        root / "scenario_profile.locked.json",
        root / "scenario_profile.json",
        root / "profile.json",
    ]
    for c in candidates:
        if c.exists() and c.is_file():
            return c

    found = sorted(root.glob("*profile*.json"))
    if len(found) == 1:
        return found[0]
    if len(found) > 1:
        raise ValueError(
            "multiple profile json files found; specify --profile-json explicitly"
        )
    raise ValueError("no profile json found; specify --profile-json")


def build_replay_manifest_case(
    pack_root: str,
    scenario_id: Optional[str],
    profile_json: str,
    candidate_paths: Sequence[str],
    reference_estimation_npz: Optional[str] = None,
    include_sidecar_metadata: bool = False,
    candidate_name_mode: str = "stem",
) -> Dict[str, Any]:
    root = Path(pack_root)
    sid = str(scenario_id).strip() if scenario_id is not None else root.name
    if sid == "":
        sid = "scenario"

    cands: List[Dict[str, Any]] = []
    for cp in candidate_paths:
        p = Path(cp)
        name = _candidate_name(p, mode=candidate_name_mode)
        row: Dict[str, Any] = {
            "name": name,
            "estimation_npz": str(p),
        }
        if include_sidecar_metadata:
            meta = _load_sidecar_metadata(p)
            if meta is not None:
                row["metadata"] = meta
        cands.append(row)

    case: Dict[str, Any] = {
        "scenario_id": sid,
        "profile_json": str(profile_json),
        "candidates": cands,
    }
    if reference_estimation_npz is not None:
        case["reference_estimation_npz"] = str(reference_estimation_npz)
    return case


def build_replay_manifest_payload(cases: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    return {
        "version": 1,
        "cases": [dict(c) for c in cases],
    }


def save_replay_manifest_json(path: str, payload: Mapping[str, Any]) -> None:
    Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _candidate_name(path: Path, mode: str) -> str:
    if mode == "stem":
        return path.stem
    if mode == "name":
        return path.name
    if mode == "relative":
        return str(path)
    raise ValueError(f"unsupported candidate_name_mode: {mode}")


def _load_sidecar_metadata(candidate_npz: Path) -> Optional[Dict[str, Any]]:
    sidecars = [candidate_npz.with_suffix(".json"), candidate_npz.with_suffix(".meta.json")]
    for sp in sidecars:
        if sp.exists() and sp.is_file():
            payload = json.loads(sp.read_text(encoding="utf-8"))
            if not isinstance(payload, Mapping):
                raise ValueError(f"metadata sidecar must be object: {sp}")
            return dict(payload)
    return None
