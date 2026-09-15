#!/usr/bin/env python3
"""Check published catalog artifacts (catalog.json + schema.json + meta.json)."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

MONEY_INT_RE = re.compile(r'"(?:priceUsd|monthlyUsd)": -?\d+(?=[,\n])')


def main() -> int:
    catalog_path = Path(sys.argv[1] if len(sys.argv) > 1 else "dist/v1/catalog.json")
    schema_path = catalog_path.parent / "schema.json"
    meta_path = catalog_path.parent / "meta.json"
    errors: list[str] = []

    raw = catalog_path.read_text()
    catalog = json.loads(raw)
    if MONEY_INT_RE.search(raw):
        errors.append("catalog.json: priceUsd/monthlyUsd must be JSON floats (69.0), not ints (69)")

    for svc in catalog.get("services", []):
        sid = svc.get("id", "?")
        if "logo" in svc:
            errors.append(f"{sid}: unexpected relative logo in published dump")
        if "plans" in svc:
            errors.append(f"{sid}: unexpected plans in published dump")
        for key in ("priceUsd", "monthlyUsd"):
            if not isinstance(svc.get(key), float):
                errors.append(f"{sid}: {key} is {type(svc.get(key)).__name__}, expected float")
        if not svc.get("logoUrl"):
            errors.append(f"{sid}: missing logoUrl")
        if not svc.get("url"):
            errors.append(f"{sid}: missing url")
        if not svc.get("sourceUrl"):
            errors.append(f"{sid}: missing sourceUrl")
        if not svc.get("plan"):
            errors.append(f"{sid}: missing plan")

    if catalog.get("schemaVersion") != 1:
        errors.append("catalog.json: schemaVersion must be 1")

    schema = json.loads(schema_path.read_text())
    if schema.get("$id") != "https://subdrop.repruv.com/v1/schema.json":
        errors.append("schema.json: unexpected $id")
    if "service" not in schema.get("$defs", {}):
        errors.append("schema.json: missing $defs.service")

    meta = json.loads(meta_path.read_text())
    for key in ("schemaVersion", "generatedAt", "count", "catalogUrl", "schemaUrl", "note"):
        if key not in meta:
            errors.append(f"meta.json: missing {key}")
    if meta.get("count") != catalog.get("count"):
        errors.append("meta.json: count does not match catalog.json")
    if meta.get("generatedAt") != catalog.get("generatedAt"):
        errors.append("meta.json: generatedAt does not match catalog.json")

    if errors:
        print("Published catalog check failed:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print(
        f"OK: {catalog['count']} services, "
        f"schema + meta present, money fields are JSON floats"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
