#!/usr/bin/env python3
"""Build published catalog JSON from Subdrop source YAML files."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from yaml_lite import load  # noqa: E402

DEFAULT_HOST = "https://subdrop.repruv.com"
CATALOG_SCHEMA_SRC = ROOT / "schema" / "catalog.schema.json"
MONEY_KEYS = ("priceUsd", "monthlyUsd")
MONEY_INT_RE = re.compile(r'"(?:priceUsd|monthlyUsd)": -?\d+(?=[,\n])')


def git_commit(explicit: str | None) -> str | None:
    if explicit:
        return explicit
    env_sha = os.environ.get("GITHUB_SHA") or os.environ.get("GIT_COMMIT")
    if env_sha:
        return env_sha
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def as_money(value: Any) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise TypeError(f"money field must be a number, got {type(value).__name__}")
    return float(value)


def normalize_service(svc: dict[str, Any], host: str | None) -> dict[str, Any]:
    """Shape one service for the public dump (not source YAML)."""
    entry = dict(svc)
    entry["aliases"] = list(entry.get("aliases") or [])
    for key in MONEY_KEYS:
        if key in entry:
            entry[key] = as_money(entry[key])

    logo = entry.pop("logo", None)
    if host and logo:
        entry["logoUrl"] = f"{host.rstrip('/')}/{logo}"

    plans = entry.get("plans")
    if not plans:
        entry.pop("plans", None)

    return entry


def build_meta(
    *,
    schema_version: int,
    generated_at: str,
    count: int,
    host: str | None,
    commit: str | None,
) -> dict[str, Any]:
    base = (host or DEFAULT_HOST).rstrip("/")
    meta: dict[str, Any] = {
        "schemaVersion": schema_version,
        "generatedAt": generated_at,
        "count": count,
        "catalogUrl": f"{base}/v1/catalog.json",
        "schemaUrl": f"{base}/v1/schema.json",
        "note": (
            "Advertised US list prices (snapshot, not live billing). "
            "Poll /v1/meta.json or send If-None-Match against /v1/catalog.json."
        ),
    }
    if commit:
        meta["commit"] = commit
    return meta


def build(host: str | None, commit: str | None = None) -> tuple[dict, dict]:
    catalog = load((ROOT / "catalog.yaml").read_text())
    categories = load((ROOT / "categories.yaml").read_text())

    services: list[dict] = []
    for path in sorted((ROOT / "services").glob("*.yaml")):
        svc = load(path.read_text())
        services.append(normalize_service(svc, host))

    services.sort(key=lambda s: (-int(s.get("rank", 0)), s.get("id", "")))

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    schema_version = int(catalog.get("schemaVersion", 1))
    payload = {
        "schemaVersion": schema_version,
        "name": catalog.get("name"),
        "description": catalog.get("description"),
        "region": catalog.get("region"),
        "currency": catalog.get("currency"),
        "license": catalog.get("license"),
        "licenseNote": catalog.get("licenseNote"),
        "generatedAt": generated_at,
        "count": len(services),
        "categories": categories,
        "services": services,
    }
    meta = build_meta(
        schema_version=schema_version,
        generated_at=generated_at,
        count=len(services),
        host=host,
        commit=git_commit(commit),
    )
    return payload, meta


def dumps_catalog(payload: dict) -> str:
    text = json.dumps(payload, indent=2, ensure_ascii=False)
    if MONEY_INT_RE.search(text):
        raise SystemExit("money fields must be JSON floats (e.g. 69.0), not integers")
    return text + "\n"


def assert_published_shape(payload: dict, host: str | None) -> None:
    if payload.get("schemaVersion") != 1:
        raise SystemExit("published catalog schemaVersion must be 1")
    for svc in payload["services"]:
        sid = svc.get("id", "?")
        if "logo" in svc:
            raise SystemExit(f"{sid}: published dump must omit relative logo")
        if "plans" in svc:
            raise SystemExit(f"{sid}: published dump must omit unused plans")
        for key in MONEY_KEYS:
            value = svc.get(key)
            if not isinstance(value, float) or isinstance(value, bool):
                raise SystemExit(f"{sid}: {key} must be a float, got {type(value).__name__}")
        if host and not svc.get("logoUrl"):
            raise SystemExit(f"{sid}: published dump with --host must include logoUrl")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Subdrop catalog.json")
    parser.add_argument(
        "-o",
        "--output",
        default=str(ROOT / "dist" / "v1" / "catalog.json"),
        help="Catalog JSON path (default: dist/v1/catalog.json)",
    )
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help="CDN host prefix for logoUrl (default: https://subdrop.repruv.com)",
    )
    parser.add_argument(
        "--commit",
        default=None,
        help="Git SHA to record in meta.json (default: GITHUB_SHA or git rev-parse)",
    )
    args = parser.parse_args()

    host = args.host.strip() or None
    payload, meta = build(host, args.commit)
    assert_published_shape(payload, host)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(dumps_catalog(payload))

    schema_out = out.parent / "schema.json"
    schema_out.write_text(CATALOG_SCHEMA_SRC.read_text())

    meta_out = out.parent / "meta.json"
    meta_out.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n")

    print(f"Wrote {out} ({payload['count']} services)")
    print(f"Wrote {schema_out}")
    print(f"Wrote {meta_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
