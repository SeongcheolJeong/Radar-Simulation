#!/usr/bin/env python3
"""Pull RadarSimPy order downloads and run production gate when license is found."""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sqlite3
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen


def _timestamp_tag() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Read RadarSimPy order downloads from an order-received URL (or saved HTML), "
            "download selected assets, extract license files, and optionally run strict "
            "production readiness gate."
        )
    )
    p.add_argument("--order-received-url", default="")
    p.add_argument("--order-html-file", default="")
    p.add_argument(
        "--download-label",
        action="append",
        default=[],
        help="Download only this label from order page (repeatable).",
    )
    p.add_argument(
        "--download-label-regex",
        default="",
        help="Download only labels matching this regex.",
    )
    p.add_argument("--max-downloads", type=int, default=0)
    p.add_argument(
        "--output-root",
        default=f"external/radarsimpy_order_pull_{_timestamp_tag()}",
    )
    p.add_argument(
        "--output-json",
        default=f"docs/reports/radarsimpy_production_gate_from_order_{_timestamp_tag()}.json",
    )
    p.add_argument("--python-bin", default="")
    p.add_argument(
        "--production-gate-json",
        default="",
        help="Optional output JSON path for nested run_radarsimpy_production_release_gate.py",
    )
    p.add_argument("--run-production-gate", action="store_true")
    p.add_argument("--allow-blocked", action="store_true")
    p.add_argument(
        "--user-agent",
        default=(
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0 Safari/537.36"
        ),
    )
    p.add_argument(
        "--cookie-header",
        default="",
        help="Optional raw Cookie header string for authenticated order access.",
    )
    p.add_argument(
        "--firefox-cookie-db",
        default="",
        help="Optional Firefox cookies.sqlite path for loading radarsimx.com cookies.",
    )
    p.add_argument(
        "--use-firefox-radarsimx-cookies",
        action="store_true",
        help="Auto-load radarsimx.com cookies from default Firefox profile.",
    )
    p.set_defaults(extract_zips=True)
    p.add_argument("--no-extract-zips", dest="extract_zips", action="store_false")
    return p.parse_args()


def _resolve_path(raw: str, *, repo_root: Path) -> Path:
    p = Path(str(raw)).expanduser()
    if p.is_absolute():
        return p.resolve()
    return (repo_root / p).resolve()


def _resolve_python_bin(raw: str, *, repo_root: Path) -> str:
    text = str(raw).strip()
    if text != "":
        p = Path(text).expanduser()
        if p.exists():
            if p.is_absolute():
                return str(p.resolve())
            return str((repo_root / p).resolve())
        return text

    for candidate in (
        repo_root / ".venv" / "bin" / "python",
        repo_root / ".venv-po-sbr" / "bin" / "python",
    ):
        if candidate.exists():
            return str(candidate)
    return str(sys.executable)


def _tail(text: str, n: int = 80) -> str:
    lines = str(text).splitlines()
    return "\n".join(lines[-n:])


def _fetch_text(url: str, *, user_agent: str) -> str:
    req = Request(url, headers={"User-Agent": user_agent})
    with urlopen(req, timeout=120) as resp:
        data = resp.read()
        charset = resp.headers.get_content_charset() or "utf-8"
    return data.decode(charset, errors="replace")


def _fetch_text_safe(url: str, *, user_agent: str) -> Tuple[bool, str, str]:
    try:
        return True, _fetch_text(url, user_agent=user_agent), ""
    except Exception as exc:
        return False, "", str(exc)


def _fetch_text_with_cookie_header(url: str, *, user_agent: str, cookie_header: str) -> str:
    headers = {"User-Agent": user_agent}
    if str(cookie_header).strip() != "":
        headers["Cookie"] = str(cookie_header).strip()
    req = Request(url, headers=headers)
    with urlopen(req, timeout=120) as resp:
        data = resp.read()
        charset = resp.headers.get_content_charset() or "utf-8"
    return data.decode(charset, errors="replace")


def _fetch_text_safe_with_cookie_header(
    url: str,
    *,
    user_agent: str,
    cookie_header: str,
) -> Tuple[bool, str, str]:
    try:
        return True, _fetch_text_with_cookie_header(url, user_agent=user_agent, cookie_header=cookie_header), ""
    except Exception as exc:
        return False, "", str(exc)


_DL_LINK_RE = re.compile(
    r"""<a\s+href=["'](?P<href>[^"']+)["'][^>]*class=["'][^"']*woocommerce-MyAccount-downloads-file[^"']*["'][^>]*>(?P<label>[^<]+)</a>""",
    re.IGNORECASE,
)


def _contains_any(text: str, phrases: Sequence[str]) -> bool:
    lower = str(text).lower()
    return any(str(p).lower() in lower for p in phrases)


def _detect_login_gate(order_html: str) -> bool:
    return _contains_any(
        order_html,
        (
            "username or email address",
            "lost your password?",
            "register",
            "my account",
        ),
    )


def _detect_invalid_order(order_html: str) -> bool:
    return _contains_any(
        order_html,
        (
            "sorry, this order is invalid and cannot be paid for",
            "invalid order",
            "order not found",
        ),
    )


def _extract_order_id_and_key(order_url: str) -> Tuple[str, str]:
    parsed = urlparse(str(order_url))
    order_id = ""
    m = re.search(r"/(?:checkout/)?order-(?:received|pay)/([0-9]+)/?", parsed.path)
    if m:
        order_id = m.group(1)
    qs = parse_qs(parsed.query)
    key = str((qs.get("key") or [""])[0]).strip()
    return order_id, key


def _probe_related_endpoints(
    *,
    order_url: str,
    user_agent: str,
    cookie_header: str,
) -> Dict[str, Any]:
    info: Dict[str, Any] = {
        "order_id": "",
        "order_key": "",
        "probed": False,
        "my_account_view_order_url": "",
        "order_pay_url": "",
        "my_account_view_order_fetch_ok": False,
        "order_pay_fetch_ok": False,
        "my_account_login_required": False,
        "order_pay_invalid": False,
        "errors": [],
    }
    order_id, key = _extract_order_id_and_key(order_url)
    info["order_id"] = order_id
    info["order_key"] = key
    if order_id == "" or key == "":
        info["errors"].append("unable to derive order_id/key from order URL")
        return info

    info["probed"] = True
    my_account_url = f"https://radarsimx.com/my-account/view-order/{order_id}/?key={key}"
    order_pay_url = f"https://radarsimx.com/checkout/order-pay/{order_id}/?key={key}&pay_for_order=true"
    info["my_account_view_order_url"] = my_account_url
    info["order_pay_url"] = order_pay_url

    ok, text, err = _fetch_text_safe_with_cookie_header(
        my_account_url, user_agent=user_agent, cookie_header=cookie_header
    )
    info["my_account_view_order_fetch_ok"] = ok
    if ok:
        info["my_account_login_required"] = _detect_login_gate(text)
    elif err:
        info["errors"].append(f"my_account_view_order fetch failed: {err}")

    ok, text, err = _fetch_text_safe_with_cookie_header(
        order_pay_url, user_agent=user_agent, cookie_header=cookie_header
    )
    info["order_pay_fetch_ok"] = ok
    if ok:
        info["order_pay_invalid"] = _detect_invalid_order(text)
    elif err:
        info["errors"].append(f"order_pay fetch failed: {err}")

    return info


def _extract_download_rows(order_html: str) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for m in _DL_LINK_RE.finditer(str(order_html)):
        href = html.unescape(m.group("href")).strip()
        label = html.unescape(m.group("label")).strip()
        if href == "" or label == "":
            continue
        rows.append({"label": label, "url": href})
    return rows


def _safe_file_name(raw: str) -> str:
    text = str(raw).strip().replace("\\", "_").replace("/", "_")
    text = re.sub(r"[^A-Za-z0-9._-]+", "_", text)
    return text.strip("._") or "download.bin"


def _file_name_from_headers(headers: Mapping[str, str]) -> str:
    cd = str(headers.get("Content-Disposition", headers.get("content-disposition", "")))
    if cd == "":
        return ""
    m_star = re.search(r"filename\\*=UTF-8''([^;]+)", cd, re.IGNORECASE)
    if m_star:
        return _safe_file_name(m_star.group(1))
    m = re.search(r'filename="?([^";]+)"?', cd, re.IGNORECASE)
    if m:
        return _safe_file_name(m.group(1))
    return ""


def _download_file(
    *,
    url: str,
    dst_dir: Path,
    fallback_name: str,
    user_agent: str,
    cookie_header: str,
) -> Dict[str, Any]:
    headers = {"User-Agent": user_agent}
    if str(cookie_header).strip() != "":
        headers["Cookie"] = str(cookie_header).strip()
    req = Request(url, headers=headers)
    with urlopen(req, timeout=180) as resp:
        headers = {str(k): str(v) for k, v in resp.headers.items()}
        name = _file_name_from_headers(headers)
        if name == "":
            parsed = urlparse(url)
            base = Path(parsed.path).name
            name = _safe_file_name(base if base != "" else fallback_name)
        dst_path = dst_dir / name
        with dst_path.open("wb") as f:
            shutil.copyfileobj(resp, f, length=1024 * 1024)
    return {
        "url": str(url),
        "path": str(dst_path),
        "name": str(name),
        "size_bytes": int(dst_path.stat().st_size),
        "headers": headers,
    }


def _default_firefox_cookie_db() -> Path:
    return Path(
        "/home/seongcheoljeong/snap/firefox/common/.mozilla/firefox/45ma06ij.default/cookies.sqlite"
    )


def _load_firefox_radarsimx_cookie_header(db_path: Path) -> Tuple[str, List[str], List[str]]:
    errors: List[str] = []
    names: List[str] = []
    if (not db_path.exists()) or (not db_path.is_file()):
        errors.append(f"cookie db missing: {db_path}")
        return "", names, errors

    tmp = Path("/tmp") / f"radarsimx_firefox_cookie_copy_{os.getpid()}.sqlite"
    try:
        shutil.copy2(str(db_path), str(tmp))
        con = sqlite3.connect(str(tmp))
        cur = con.cursor()
        cur.execute(
            "select name, value from moz_cookies where host like '%radarsimx.com%' order by name"
        )
        rows = cur.fetchall()
        con.close()
    except Exception as exc:
        errors.append(f"failed to read firefox cookie db: {exc}")
        rows = []
    finally:
        try:
            if tmp.exists():
                tmp.unlink()
        except Exception:
            pass

    pairs: List[str] = []
    for name, value in rows:
        n = str(name).strip()
        if n == "":
            continue
        names.append(n)
        pairs.append(f"{n}={value}")
    header = "; ".join(pairs)
    return header, sorted(set(names)), errors


def _select_rows(
    rows: Sequence[Mapping[str, str]],
    *,
    labels: Sequence[str],
    label_regex: str,
    max_downloads: int,
) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    wanted = {str(x).strip() for x in labels if str(x).strip() != ""}
    pattern = re.compile(str(label_regex), re.IGNORECASE) if str(label_regex).strip() != "" else None
    for row in rows:
        label = str(row.get("label", "")).strip()
        url = str(row.get("url", "")).strip()
        if label == "" or url == "":
            continue
        if wanted and label not in wanted:
            continue
        if pattern is not None and pattern.search(label) is None:
            continue
        out.append({"label": label, "url": url})
    if not wanted and pattern is None:
        out = [{"label": str(r.get("label", "")).strip(), "url": str(r.get("url", "")).strip()} for r in rows]
        out = [r for r in out if r["label"] != "" and r["url"] != ""]
    if int(max_downloads) > 0:
        out = out[: int(max_downloads)]
    return out


def _extract_zip_files(downloaded: Sequence[Mapping[str, Any]], *, extracted_root: Path) -> List[Dict[str, Any]]:
    extracted: List[Dict[str, Any]] = []
    for item in downloaded:
        path_text = str(item.get("path", "")).strip()
        if path_text == "":
            continue
        path = Path(path_text)
        if path.suffix.lower() != ".zip":
            continue
        out_dir = extracted_root / path.stem
        out_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(path, "r") as zf:
            zf.extractall(out_dir)
        extracted.append(
            {
                "archive_path": str(path),
                "extract_dir": str(out_dir),
                "file_count": int(len(zf.namelist())),
            }
        )
    return extracted


def _find_license_files(root: Path) -> List[str]:
    candidates: List[Path] = []
    for p in root.rglob("license_RadarSimPy*.lic"):
        if p.is_file():
            candidates.append(p.resolve())
    for p in root.rglob("*.lic"):
        if p.is_file():
            candidates.append(p.resolve())
    dedup = sorted({str(p) for p in candidates})
    return dedup


def _run_cmd(cmd: List[str], *, cwd: Path, env: Mapping[str, str]) -> Dict[str, Any]:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        env=dict(env),
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "cmd": list(cmd),
        "returncode": int(proc.returncode),
        "pass": bool(proc.returncode == 0),
        "stdout_tail": _tail(proc.stdout),
        "stderr_tail": _tail(proc.stderr),
    }


def _load_json_if_exists(path: Path) -> Optional[Dict[str, Any]]:
    if (not path.exists()) or (not path.is_file()):
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return None
    return payload


def main() -> None:
    args = parse_args()
    repo_root = Path.cwd().resolve()

    output_root = _resolve_path(str(args.output_root), repo_root=repo_root)
    output_root.mkdir(parents=True, exist_ok=True)
    output_json = _resolve_path(str(args.output_json), repo_root=repo_root)
    output_json.parent.mkdir(parents=True, exist_ok=True)

    blockers: List[str] = []
    fetch_errors: List[str] = []
    endpoint_probe: Dict[str, Any] = {}
    cookie_load_errors: List[str] = []
    cookie_name_list: List[str] = []
    cookie_source = ""
    order_html = ""
    order_source = ""

    order_html_file = str(args.order_html_file).strip()
    order_url = str(args.order_received_url).strip()
    cookie_header = str(args.cookie_header).strip()
    firefox_cookie_db = str(args.firefox_cookie_db).strip()
    if bool(args.use_firefox_radarsimx_cookies) or firefox_cookie_db != "":
        db_path = _default_firefox_cookie_db() if firefox_cookie_db == "" else _resolve_path(
            firefox_cookie_db, repo_root=repo_root
        )
        loaded_header, loaded_names, load_errors = _load_firefox_radarsimx_cookie_header(db_path)
        cookie_load_errors.extend(load_errors)
        if loaded_header != "":
            if cookie_header == "":
                cookie_header = loaded_header
                cookie_source = f"firefox:{db_path}"
            cookie_name_list = loaded_names
        else:
            if cookie_source == "":
                cookie_source = f"firefox:{db_path}"
    if cookie_source == "" and cookie_header != "":
        cookie_source = "arg:cookie_header"

    if order_html_file != "":
        html_path = _resolve_path(order_html_file, repo_root=repo_root)
        if not html_path.exists() or (not html_path.is_file()):
            raise FileNotFoundError(f"order HTML not found: {html_path}")
        order_html = html_path.read_text(encoding="utf-8")
        order_source = str(html_path)
    elif order_url != "":
        try:
            order_html = _fetch_text_with_cookie_header(
                order_url,
                user_agent=str(args.user_agent),
                cookie_header=cookie_header,
            )
        except Exception as exc:
            order_html = ""
            fetch_errors.append(f"{order_url}: {exc}")
            blockers.append("order_fetch_error")
        order_source = str(order_url)
    else:
        raise ValueError("provide --order-received-url or --order-html-file")

    rows = _extract_download_rows(order_html)
    login_gate = _detect_login_gate(order_html)
    invalid_order = _detect_invalid_order(order_html)
    if login_gate:
        blockers.append("order_login_required")
    if invalid_order:
        blockers.append("order_invalid")
    selected = _select_rows(
        rows,
        labels=list(args.download_label),
        label_regex=str(args.download_label_regex),
        max_downloads=int(args.max_downloads),
    )
    if len(rows) == 0:
        blockers.append("no_download_rows_detected")
        if order_url != "":
            endpoint_probe = _probe_related_endpoints(
                order_url=order_url,
                user_agent=str(args.user_agent),
                cookie_header=cookie_header,
            )
            if bool(endpoint_probe.get("my_account_login_required", False)):
                blockers.append("my_account_login_required")
            if bool(endpoint_probe.get("order_pay_invalid", False)):
                blockers.append("order_pay_invalid")
    if len(selected) == 0:
        blockers.append("no_download_rows_selected")

    downloads_dir = output_root / "downloads"
    downloads_dir.mkdir(parents=True, exist_ok=True)
    downloaded: List[Dict[str, Any]] = []
    download_errors: List[str] = []
    for row in selected:
        label = str(row.get("label", ""))
        url = str(row.get("url", ""))
        fallback_name = f"{_safe_file_name(label)}.bin"
        try:
            item = _download_file(
                url=url,
                dst_dir=downloads_dir,
                fallback_name=fallback_name,
                user_agent=str(args.user_agent),
                cookie_header=cookie_header,
            )
            item["label"] = label
            downloaded.append(item)
        except Exception as exc:
            download_errors.append(f"{label}: {exc}")
    if len(download_errors) > 0:
        blockers.append("download_error")

    extracted: List[Dict[str, Any]] = []
    if bool(args.extract_zips):
        extracted_root = output_root / "extracted"
        extracted_root.mkdir(parents=True, exist_ok=True)
        extracted = _extract_zip_files(downloaded, extracted_root=extracted_root)

    license_files = _find_license_files(output_root)
    selected_license = license_files[0] if len(license_files) > 0 else ""
    if selected_license == "":
        blockers.append("license_file_not_found_in_order_assets")

    production_gate_run: Dict[str, Any] = {"skipped": True}
    production_gate_payload: Dict[str, Any] = {}
    production_gate_json = ""
    if bool(args.run_production_gate):
        production_gate_json_text = str(args.production_gate_json).strip()
        if production_gate_json_text == "":
            production_gate_json_path = output_json.parent / f"{output_json.stem}_production_gate.json"
        else:
            production_gate_json_path = _resolve_path(production_gate_json_text, repo_root=repo_root)
        production_gate_json_path.parent.mkdir(parents=True, exist_ok=True)
        production_gate_json = str(production_gate_json_path.resolve())
        py_bin = _resolve_python_bin(str(args.python_bin), repo_root=repo_root)
        cmd = [
            py_bin,
            "scripts/run_radarsimpy_production_release_gate.py",
            "--output-json",
            str(production_gate_json_path),
        ]
        if selected_license != "":
            cmd.extend(["--license-file", selected_license])
        if bool(args.allow_blocked):
            cmd.append("--allow-blocked")
        env = dict(os.environ)
        env["PYTHONPATH"] = f"src{os.pathsep}{env['PYTHONPATH']}" if "PYTHONPATH" in env else "src"
        production_gate_run = _run_cmd(cmd, cwd=repo_root, env=env)
        production_gate_payload = _load_json_if_exists(production_gate_json_path) or {}
        if production_gate_payload.get("production_gate_status") != "ready":
            blockers.append("production_gate_not_ready")
        if not bool(production_gate_run.get("pass", False)):
            blockers.append("production_gate_returncode_nonzero")

    blockers = sorted(set(blockers))
    status = "ready" if len(blockers) == 0 else "blocked"

    summary: Dict[str, Any] = {
        "version": 1,
        "report_name": "radarsimpy_production_gate_from_order",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "workspace_root": str(repo_root),
        "status": status,
        "allow_blocked": bool(args.allow_blocked),
        "order_source": order_source,
        "cookie_source": cookie_source,
        "cookie_name_count": int(len(cookie_name_list)),
        "cookie_name_list": sorted(set(cookie_name_list)),
        "cookie_load_errors": cookie_load_errors,
        "fetch_errors": fetch_errors,
        "order_download_row_count": int(len(rows)),
        "order_login_required": bool(login_gate),
        "order_invalid": bool(invalid_order),
        "order_download_rows": rows,
        "related_endpoint_probe": endpoint_probe,
        "selected_download_count": int(len(selected)),
        "selected_download_rows": selected,
        "downloaded_count": int(len(downloaded)),
        "downloaded": downloaded,
        "download_errors": download_errors,
        "extract_zips": bool(args.extract_zips),
        "extracted": extracted,
        "license_files": license_files,
        "selected_license_file": selected_license,
        "run_production_gate": bool(args.run_production_gate),
        "production_gate_json": production_gate_json,
        "production_gate_status": str(production_gate_payload.get("production_gate_status", "")),
        "production_gate_run": production_gate_run,
        "blockers": blockers,
        "output_root": str(output_root),
    }
    output_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("RadarSimPy production gate-from-order runner completed.")
    print(f"  status: {status}")
    print(f"  selected_license_file: {selected_license or '(none)'}")
    print(f"  downloaded_count: {len(downloaded)}")
    print(f"  output_root: {output_root}")
    print(f"  output_json: {output_json}")

    if (status != "ready") and (not bool(args.allow_blocked)):
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
