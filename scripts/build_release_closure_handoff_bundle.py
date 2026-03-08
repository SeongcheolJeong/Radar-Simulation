#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tarfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

DEFAULT_FILES = [
    "docs/294_release_closure_handoff_2026_03_08.md",
    "docs/295_release_closure_handoff_2026_03_08_ko.md",
    "docs/296_release_closure_final_announcement_2026_03_08.md",
    "docs/297_release_closure_final_announcement_2026_03_08_ko.md",
    "docs/291_release_candidate_snapshot_2026_03_08.md",
    "docs/292_release_candidate_snapshot_2026_03_08_ko.md",
    "docs/293_hf1_release_requirement_decision_2026_03_08.md",
    "docs/298_release_closure_freeze_note_2026_03_08.md",
    "docs/299_release_closure_freeze_note_2026_03_08_ko.md",
    "docs/reports/README.md",
    "docs/reports/canonical_release_candidate_subset_latest.json",
    "docs/reports/release_announcement_pack_latest.json",
    "docs/reports/release_announcement_pack_latest.md",
]


def _git(repo_root: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return ""
    return proc.stdout.strip()



def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()



def _resolve(repo_root: Path, raw: str) -> Path:
    path = Path(raw)
    if path.is_absolute():
        return path.resolve()
    return (repo_root / path).resolve()



def main() -> None:
    p = argparse.ArgumentParser(description="Build a frozen release-closure handoff bundle archive.")
    p.add_argument(
        "--output-tar",
        default="docs/reports/release_closure_handoff_bundle_latest.tar.gz",
        help="Output tar.gz path relative to repo root.",
    )
    p.add_argument(
        "--output-manifest",
        default="docs/reports/release_closure_handoff_bundle_latest_manifest.json",
        help="Output manifest JSON path relative to repo root.",
    )
    p.add_argument(
        "--bundle-version",
        default="release_closure_handoff_bundle_v1",
        help="Manifest bundle version.",
    )
    args = p.parse_args()

    repo_root = Path.cwd().resolve()
    out_tar = _resolve(repo_root, args.output_tar)
    out_manifest = _resolve(repo_root, args.output_manifest)

    files: List[Path] = []
    manifest_files: List[Dict[str, Any]] = []
    for raw in DEFAULT_FILES:
        path = _resolve(repo_root, raw)
        if not path.exists():
            raise FileNotFoundError(f"missing handoff bundle file: {raw}")
        rel = path.relative_to(repo_root)
        files.append(path)
        manifest_files.append(
            {
                "path": rel.as_posix(),
                "size_bytes": path.stat().st_size,
                "sha256": _sha256(path),
            }
        )

    out_tar.parent.mkdir(parents=True, exist_ok=True)
    out_manifest.parent.mkdir(parents=True, exist_ok=True)

    with tarfile.open(out_tar, "w:gz") as tar:
        for path in files:
            rel = path.relative_to(repo_root)
            tar.add(path, arcname=rel.as_posix(), recursive=False)

    tar_sha256 = _sha256(out_tar)
    manifest: Dict[str, Any] = {
        "version": args.bundle_version,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(repo_root),
        "git": {
            "head_commit": _git(repo_root, "rev-parse", "HEAD"),
            "head_commit_short": _git(repo_root, "rev-parse", "--short", "HEAD"),
            "branch": _git(repo_root, "rev-parse", "--abbrev-ref", "HEAD"),
            "status_porcelain": _git(repo_root, "status", "--short"),
        },
        "bundle_archive": {
            "path": out_tar.relative_to(repo_root).as_posix(),
            "size_bytes": out_tar.stat().st_size,
            "sha256": tar_sha256,
        },
        "file_count": len(manifest_files),
        "files": manifest_files,
    }
    out_manifest.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(json.dumps({
        "output_tar": out_tar.relative_to(repo_root).as_posix(),
        "output_manifest": out_manifest.relative_to(repo_root).as_posix(),
        "file_count": len(manifest_files),
        "bundle_sha256": tar_sha256,
    }, indent=2))


if __name__ == "__main__":
    main()
