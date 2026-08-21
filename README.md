# Subdrop

Public subscription catalog for US consumer services. **Git is the CMS** — one YAML file per service, validated in CI, published as static JSON.

- [Product requirements](docs/PRD.md)
- [Agent / contributor guide](AGENTS.md)

## Quick start

```bash
python3 scripts/validate.py
python3 scripts/build-catalog.py -o dist/catalog.json
```

## Layout

```
catalog.yaml          # catalog metadata
categories.yaml       # category id + label
services/*.yaml       # one file per service
schema/               # JSON Schema + example
scripts/              # validate + build (no deps)
logos/                # brand marks (relative paths in YAML)
dist/catalog.json     # build output (generated)
```

Catalog data is [CC0 1.0](LICENSE). Trademarks remain with their owners.
