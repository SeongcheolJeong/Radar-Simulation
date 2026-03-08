#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
from pathlib import Path
from typing import Any, Dict, List, Tuple


def _resolve(repo_root: Path, raw: str) -> Path:
    path = Path(raw)
    if path.is_absolute():
        return path.resolve()
    return (repo_root / path).resolve()


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_manifest(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("manifest root must be an object")
    return payload


def _validate_required_keys(payload: Dict[str, Any]) -> None:
    required = ["version", "bundle_archive", "file_count", "files"]
    for key in required:
        if key not in payload:
            raise ValueError(f"manifest missing key: {key}")
    archive = payload["bundle_archive"]
    if not isinstance(archive, dict):
        raise ValueError("manifest bundle_archive must be object")
    for key in ["path", "size_bytes", "sha256"]:
        if key not in archive:
            raise ValueError(f"manifest bundle_archive missing key: {key}")
    files = payload["files"]
    if not isinstance(files, list):
        raise ValueError("manifest files must be list")
    for idx, item in enumerate(files):
        if not isinstance(item, dict):
            raise ValueError(f"manifest file entry {idx} must be object")
        for key in ["path", "size_bytes", "sha256"]:
            if key not in item:
                raise ValueError(f"manifest file entry {idx} missing key: {key}")


def _validate_archive_members(archive_path: Path, expected_members: List[str]) -> Tuple[bool, List[str]]:
    with tarfile.open(archive_path, "r:gz") as tar:
        members = sorted(
            member.name for member in tar.getmembers() if member.isfile()
        )
    expected_sorted = sorted(expected_members)
    return members == expected_sorted, members


def main() -> None:
    p = argparse.ArgumentParser(description="Validate the frozen release-closure handoff bundle.")
    p.add_argument(
        "--manifest-json",
        default="docs/reports/release_closure_handoff_bundle_latest_manifest.json",
        help="Manifest JSON path relative to repo root.",
    )
    args = p.parse_args()

    repo_root = Path.cwd().resolve()
    manifest_path = _resolve(repo_root, args.manifest_json)
    payload = _load_manifest(manifest_path)
    _validate_required_keys(payload)

    archive_rel = str(payload["bundle_archive"]["path"])
    archive_path = _resolve(repo_root, archive_rel)
    if not archive_path.exists():
        raise FileNotFoundError(f"bundle archive missing: {archive_rel}")

    archive_size = archive_path.stat().st_size
    expected_archive_size = int(payload["bundle_archive"]["size_bytes"])
    if archive_size != expected_archive_size:
        raise ValueError(
            f"bundle archive size mismatch: actual={archive_size} expected={expected_archive_size}"
        )

    archive_sha = _sha256(archive_path)
    expected_archive_sha = str(payload["bundle_archive"]["sha256"])
    if archive_sha != expected_archive_sha:
        raise ValueError("bundle archive sha256 mismatch")

    files = payload["files"]
    expected_file_count = int(payload["file_count"])
    if len(files) != expected_file_count:
        raise ValueError(
            f"manifest file_count mismatch: len(files)={len(files)} file_count={expected_file_count}"
        )

    file_results: List[Dict[str, Any]] = []
    expected_members: List[str] = []
    for item in files:
        rel = str(item["path"])
        path = _resolve(repo_root, rel)
        if not path.exists():
            raise FileNotFoundError(f"bundle file missing in repo: {rel}")
        size_bytes = path.stat().st_size
        sha256 = _sha256(path)
        expected_size = int(item["size_bytes"])
        expected_sha = str(item["sha256"])
        if size_bytes != expected_size:
            raise ValueError(
                f"bundle file size mismatch for {rel}: actual={size_bytes} expected={expected_size}"
            )
        if sha256 != expected_sha:
            raise ValueError(f"bundle file sha256 mismatch for {rel}")
        expected_members.append(rel)
        file_results.append(
            {
                "path": rel,
                "size_bytes": size_bytes,
                "sha256": sha256,
            }
        )

    archive_members_match, archive_members = _validate_archive_members(archive_path, expected_members)
    if not archive_members_match:
        raise ValueError("bundle archive members do not match manifest files")

    result = {
        "status": "pass",
        "manifest_json": manifest_path.relative_to(repo_root).as_posix(),
        "bundle_archive": archive_rel,
        "file_count": expected_file_count,
        "archive_size_bytes": archive_size,
        "archive_sha256": archive_sha,
        "archive_members_match": archive_members_match,
        "archive_members": archive_members,
        "version": payload["version"],
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
