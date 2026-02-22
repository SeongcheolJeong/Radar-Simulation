#!/usr/bin/env python3
import argparse
from pathlib import Path

from avxsim.web_e2e_api import WebE2EOrchestrator, serve_web_e2e_http_api


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[1]
    default_store_root = repo_root / "data" / "web_e2e"

    p = argparse.ArgumentParser(description="Run web-based E2E orchestration API (phase-0)")
    p.add_argument("--host", default="127.0.0.1", help="Bind host")
    p.add_argument("--port", type=int, default=8099, help="Bind port")
    p.add_argument(
        "--repo-root",
        default=str(repo_root),
        help="Repository root used to resolve relative scene paths",
    )
    p.add_argument(
        "--store-root",
        default=str(default_store_root),
        help="Store root for run records and artifacts",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    orchestrator = WebE2EOrchestrator(repo_root=args.repo_root, store_root=args.store_root)

    print("web e2e orchestrator api starting")
    print(f"  host: {args.host}")
    print(f"  port: {args.port}")
    print(f"  repo_root: {Path(args.repo_root).resolve()}")
    print(f"  store_root: {Path(args.store_root).resolve()}")
    print("  endpoints:")
    print("    GET  /health")
    print("    GET  /api/profiles")
    print("    GET  /api/runs")
    print("    GET  /api/runs/{run_id}")
    print("    GET  /api/runs/{run_id}/summary")
    print("    POST /api/runs?async=1|0")
    print("    GET  /api/comparisons")
    print("    GET  /api/comparisons/{comparison_id}")
    print("    POST /api/compare")
    print("    GET  /api/baselines")
    print("    GET  /api/baselines/{baseline_id}")
    print("    POST /api/baselines")
    print("    GET  /api/policy-evals")
    print("    GET  /api/policy-evals/{policy_eval_id}")
    print("    POST /api/compare/policy")
    print("    GET  /api/regression-sessions")
    print("    GET  /api/regression-sessions/{session_id}")
    print("    POST /api/regression-sessions")

    serve_web_e2e_http_api(host=args.host, port=args.port, orchestrator=orchestrator)


if __name__ == "__main__":
    main()
