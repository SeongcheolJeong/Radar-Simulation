#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path


DEFAULT_TEMPLATE = "docs/ci/radarsimpy-integration-smoke.workflow.yml"
DEFAULT_OUTPUT = ".github/workflows/radarsimpy-integration-smoke.yml"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Install/sync the RadarSimPy CI workflow from template into "
            ".github/workflows for environments with workflow write permission."
        )
    )
    p.add_argument("--template", default=DEFAULT_TEMPLATE)
    p.add_argument("--output", default=DEFAULT_OUTPUT)
    p.add_argument(
        "--check",
        action="store_true",
        help="Check-only mode: fail when output is missing or differs from template.",
    )
    return p.parse_args()


def _resolve_path(raw: str, repo_root: Path) -> Path:
    p = Path(str(raw)).expanduser()
    if p.is_absolute():
        return p.resolve()
    return (repo_root / p).resolve()


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]

    template_path = _resolve_path(args.template, repo_root=repo_root)
    output_path = _resolve_path(args.output, repo_root=repo_root)

    if not template_path.exists():
        raise FileNotFoundError(f"template not found: {template_path}")

    template_text = template_path.read_text(encoding="utf-8")
    output_exists = output_path.exists()
    output_text = output_path.read_text(encoding="utf-8") if output_exists else None
    is_synced = bool(output_exists and (output_text == template_text))

    if args.check:
        print("RadarSimPy CI workflow template check completed.")
        print(f"  template_path: {template_path}")
        print(f"  output_path: {output_path}")
        print(f"  output_exists: {output_exists}")
        print(f"  synced: {is_synced}")
        if is_synced:
            sys.exit(0)
        sys.exit(2)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not is_synced:
        output_path.write_text(template_text, encoding="utf-8")

    print("RadarSimPy CI workflow template install completed.")
    print(f"  template_path: {template_path}")
    print(f"  output_path: {output_path}")
    print(f"  wrote: {not is_synced}")
    print(f"  synced: True")


if __name__ == "__main__":
    main()
