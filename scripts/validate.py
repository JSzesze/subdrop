#!/usr/bin/env python3
"""Validate Subdrop catalog source files."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from yaml_lite import load  # noqa: E402

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
LOGO_RE = re.compile(r"^logos/[a-z0-9._-]+\.(svg|png|webp)$")
FORBIDDEN_KEYS = {"logoUrl", "homepage"}
URL_PREFIXES = ("http://", "https://", "//")


def load_json_schema() -> dict:
    return json.loads((ROOT / "schema" / "service.schema.json").read_text())


def monthly_expected(price_usd: float, billing: str) -> float:
    if billing == "month":
        return price_usd
    if billing == "year":
        return price_usd / 12.0
    if billing == "week":
        return price_usd * 52.0 / 12.0
    raise ValueError(f"Unknown billing: {billing}")


def validate_catalog(catalog: dict, errors: list[str]) -> None:
    if catalog.get("schemaVersion") != 1:
        errors.append("catalog.yaml: schemaVersion must be 1")
    if catalog.get("region") != "US":
        errors.append("catalog.yaml: region must be US")
    if catalog.get("currency") != "USD":
        errors.append("catalog.yaml: currency must be USD")
    if not catalog.get("name"):
        errors.append("catalog.yaml: name is required")
    if not catalog.get("description"):
        errors.append("catalog.yaml: description is required")


def validate_categories(categories: list, errors: list[str]) -> set[str]:
    ids: set[str] = set()
    if not categories:
        errors.append("categories.yaml: must contain at least one category")
        return ids
    for i, cat in enumerate(categories):
        if not isinstance(cat, dict):
            errors.append(f"categories.yaml[{i}]: expected object")
            continue
        cid = cat.get("id")
        label = cat.get("label")
        if not cid:
            errors.append(f"categories.yaml[{i}]: missing id")
        elif cid in ids:
            errors.append(f"categories.yaml: duplicate category id {cid!r}")
        else:
            ids.add(cid)
        if not label:
            errors.append(f"categories.yaml[{i}]: missing label")
    return ids


def validate_service(
    path: Path,
    data: dict,
    schema: dict,
    category_ids: set[str],
    seen_ids: set[str],
    errors: list[str],
) -> None:
    required = set(schema.get("required", []))
    props = schema.get("properties", {})
    billing_enum = set(props.get("billing", {}).get("enum", []))

    for key in FORBIDDEN_KEYS:
        if key in data:
            errors.append(f"{path}: forbidden field {key!r}")

    for key in data:
        if key not in props:
            errors.append(f"{path}: unknown field {key!r}")

    for key in required:
        if key not in data or data[key] in (None, ""):
            errors.append(f"{path}: missing required field {key!r}")

    sid = data.get("id")
    if sid:
        if sid in seen_ids:
            errors.append(f"{path}: duplicate id {sid!r}")
        seen_ids.add(sid)
        if path.stem != sid:
            errors.append(f"{path}: filename must match id ({path.stem!r} != {sid!r})")

    category = data.get("category")
    if category and category not in category_ids:
        errors.append(f"{path}: unknown category {category!r}")

    billing = data.get("billing")
    if billing and billing not in billing_enum:
        errors.append(f"{path}: billing must be one of {sorted(billing_enum)}")

    price_checked = data.get("priceCheckedAt")
    if price_checked and not DATE_RE.match(str(price_checked)):
        errors.append(f"{path}: priceCheckedAt must be YYYY-MM-DD")

    logo = data.get("logo")
    if logo:
        if any(logo.startswith(p) for p in URL_PREFIXES):
            errors.append(f"{path}: logo must be a relative path, not a URL")
        elif not LOGO_RE.match(logo):
            errors.append(f"{path}: logo must match logos/<file>.(svg|png|webp)")

    billing_month = data.get("billingMonth")
    if billing_month is not None:
        if billing != "year":
            errors.append(f"{path}: billingMonth is only valid when billing is year")
        elif not isinstance(billing_month, int) or billing_month < 1 or billing_month > 12:
            errors.append(f"{path}: billingMonth must be integer 1-12")

    price_usd = data.get("priceUsd")
    monthly_usd = data.get("monthlyUsd")
    if isinstance(price_usd, (int, float)) and isinstance(monthly_usd, (int, float)) and billing:
        expected = monthly_expected(float(price_usd), str(billing))
        if abs(float(monthly_usd) - expected) > 0.02:
            errors.append(
                f"{path}: monthlyUsd {monthly_usd} != expected {expected:.4f} "
                f"for priceUsd={price_usd} billing={billing}"
            )


def main() -> int:
    errors: list[str] = []

    catalog = load((ROOT / "catalog.yaml").read_text())
    validate_catalog(catalog, errors)

    categories = load((ROOT / "categories.yaml").read_text())
    category_ids = validate_categories(categories, errors)

    schema = load_json_schema()
    seen_ids: set[str] = set()

    service_files = sorted((ROOT / "services").glob("*.yaml"))
    if not service_files:
        errors.append("services/: no service files found")

    for path in service_files:
        data = load(path.read_text())
        validate_service(path.relative_to(ROOT), data, schema, category_ids, seen_ids, errors)

    if errors:
        print("Validation failed:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print(f"OK: {len(service_files)} services, {len(category_ids)} categories")
    return 0


if __name__ == "__main__":
    sys.exit(main())
