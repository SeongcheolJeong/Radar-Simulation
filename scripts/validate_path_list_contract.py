#!/usr/bin/env python3
import json
import tempfile
from pathlib import Path

from avxsim.io import save_paths_by_chirp_json
from avxsim.path_contract import validate_paths_by_chirp, validate_paths_payload_json
from avxsim.types import Path as RadarPath


def main() -> None:
    good_paths = [
        [
            RadarPath(
                delay_s=1.0e-6,
                doppler_hz=0.0,
                unit_direction=(1.0, 0.0, 0.0),
                amp=1.0 + 0.0j,
                path_id="path_c0000_p0000",
                material_tag="metal",
                reflection_order=1,
            )
        ],
        [
            RadarPath(
                delay_s=1.5e-6,
                doppler_hz=150.0,
                unit_direction=(0.0, 1.0, 0.0),
                amp=0.5 + 0.2j,
                path_id="path_c0001_p0000",
                material_tag="asphalt",
                reflection_order=2,
            )
        ],
    ]

    inmem_summary = validate_paths_by_chirp(
        paths_by_chirp=good_paths,
        n_chirps=2,
        require_metadata=True,
    )
    assert inmem_summary["chirp_count"] == 2
    assert inmem_summary["path_count"] == 2

    with tempfile.TemporaryDirectory(prefix="validate_path_list_contract_") as td:
        out_json = Path(td) / "path_list.json"
        save_paths_by_chirp_json(good_paths, str(out_json))
        payload = json.loads(out_json.read_text(encoding="utf-8"))
        file_summary = validate_paths_payload_json(
            payload=payload,
            expected_n_chirps=2,
            require_metadata=True,
        )
        assert file_summary["chirp_count"] == 2
        assert file_summary["path_count"] == 2

    bad_paths = [
        [
            RadarPath(
                delay_s=1.0e-6,
                doppler_hz=0.0,
                unit_direction=(1.0, 0.0, 0.0),
                amp=1.0 + 0.0j,
                path_id="",
                material_tag="metal",
                reflection_order=1,
            )
        ]
    ]
    try:
        validate_paths_by_chirp(
            paths_by_chirp=bad_paths,
            n_chirps=1,
            require_metadata=True,
        )
    except ValueError as exc:
        assert "path_id" in str(exc)
    else:
        raise AssertionError("expected metadata validation error for empty path_id")

    print("validate_path_list_contract: pass")


if __name__ == "__main__":
    main()
