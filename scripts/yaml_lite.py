"""Minimal YAML loader/dumper for Subdrop catalog files.

Supports flat key-value documents, quoted strings, and simple lists of
objects with id/label pairs (categories.yaml). No external dependencies.
"""

from __future__ import annotations

import re
from typing import Any


def _parse_scalar(raw: str) -> Any:
    raw = raw.strip()
    if not raw or raw in ("null", "~"):
        return None
    if raw in ("true", "false"):
        return raw == "true"
    if (raw.startswith('"') and raw.endswith('"')) or (
        raw.startswith("'") and raw.endswith("'")
    ):
        return raw[1:-1]
    if re.fullmatch(r"-?\d+", raw):
        return int(raw)
    if re.fullmatch(r"-?\d+\.\d+", raw):
        return float(raw)
    return raw


def _first_content_line(lines: list[str]) -> str | None:
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            return stripped
    return None


def load(text: str) -> Any:
    lines = text.splitlines()
    if not lines:
        return {}

    first = _first_content_line(lines)

    # Detect list-of-objects (categories.yaml)
    if first and first.startswith("- "):
        items: list[dict[str, Any]] = []
        current: dict[str, Any] | None = None
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if stripped.startswith("- "):
                if current is not None:
                    items.append(current)
                current = {}
                rest = stripped[2:].strip()
                if rest:
                    key, _, value = rest.partition(":")
                    current[key.strip()] = _parse_scalar(value)
            elif current is not None and ":" in stripped:
                key, _, value = stripped.partition(":")
                current[key.strip()] = _parse_scalar(value)
        if current is not None:
            items.append(current)
        return items

    doc: dict[str, Any] = {}
    current_list_key: str | None = None
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- ") and current_list_key is not None:
            doc.setdefault(current_list_key, [])
            doc[current_list_key].append(_parse_scalar(stripped[2:]))
            continue
        if ":" not in stripped:
            raise ValueError(f"Invalid YAML line: {line!r}")
        key, _, value = stripped.partition(":")
        key = key.strip()
        value = value.strip()
        if not value:
            current_list_key = key
            doc[key] = []
            continue
        current_list_key = None
        doc[key] = _parse_scalar(value)
    return doc


def dump(data: dict[str, Any]) -> str:
    lines: list[str] = []
    for key, value in data.items():
        if value is None:
            lines.append(f"{key}: null")
        elif isinstance(value, bool):
            lines.append(f"{key}: {'true' if value else 'false'}")
        elif isinstance(value, (int, float)):
            lines.append(f"{key}: {value}")
        elif isinstance(value, str):
            if re.search(r'[:#{}\[\],&*!|>\'"@`]', value) or value.startswith(" "):
                escaped = value.replace("\\", "\\\\").replace('"', '\\"')
                lines.append(f'{key}: "{escaped}"')
            else:
                lines.append(f"{key}: {value}")
        elif isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                if isinstance(item, str):
                    if re.search(r'[:#{}\[\],&*!|>\'"@`]', item) or item.startswith(" "):
                        escaped = item.replace("\\", "\\\\").replace('"', '\\"')
                        lines.append(f'  - "{escaped}"')
                    else:
                        lines.append(f"  - {item}")
                else:
                    raise TypeError(f"Unsupported list item for key {key!r}: {type(item)}")
        else:
            raise TypeError(f"Unsupported type for key {key!r}: {type(value)}")
    return "\n".join(lines) + "\n"
