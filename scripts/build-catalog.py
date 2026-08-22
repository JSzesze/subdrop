#!/usr/bin/env python3
"""Build catalog.json from Subdrop source YAML files."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from yaml_lite import load  # noqa: E402


def build(host: str | None) -> dict:
    catalog = load((ROOT / "catalog.yaml").read_text())
    categories = load((ROOT / "categories.yaml").read_text())

    services: list[dict] = []
    for path in sorted((ROOT / "services").glob("*.yaml")):
        svc = load(path.read_text())
        entry = dict(svc)
        entry["aliases"] = list(entry.get("aliases") or [])
        if host:
            logo = entry.get("logo")
            if logo:
                entry["logoUrl"] = f"{host.rstrip('/')}/{logo}"
        services.append(entry)

    services.sort(key=lambda s: (-int(s.get("rank", 0)), s.get("id", "")))

    return {
        "schemaVersion": catalog.get("schemaVersion", 1),
        "name": catalog.get("name"),
        "description": catalog.get("description"),
        "region": catalog.get("region"),
        "currency": catalog.get("currency"),
        "license": catalog.get("license"),
        "licenseNote": catalog.get("licenseNote"),
        "generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "count": len(services),
        "categories": categories,
        "services": services,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Subdrop catalog.json")
    parser.add_argument(
        "-o",
        "--output",
        default=str(ROOT / "dist" / "catalog.json"),
        help="Output path (default: dist/catalog.json)",
    )
    parser.add_argument(
        "--host",
        default=None,
        help="CDN host prefix; when set, adds logoUrl to each service",
    )
    args = parser.parse_args()

    payload = build(args.host)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {out} ({payload['count']} services)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
