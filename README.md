# Subdrop

Public subscription catalog for US consumer services. **Git is the CMS** — one YAML file per service, validated in CI, published as static JSON.

- [Product requirements](docs/PRD.md)
- [Agent / contributor guide](AGENTS.md)

## Public API

Stable CDN host: `https://subdrop.repruv.com`

| URL | Purpose |
|-----|---------|
| [`/v1/catalog.json`](https://subdrop.repruv.com/v1/catalog.json) | Full catalog dump (wrapper + services) |
| [`/v1/schema.json`](https://subdrop.repruv.com/v1/schema.json) | JSON Schema for the published catalog wrapper and service object |
| [`/v1/meta.json`](https://subdrop.repruv.com/v1/meta.json) | Freshness: `generatedAt`, `count`, `schemaVersion`, git `commit` |

`schemaVersion` is **1**. Additive endpoints (`schema.json`, `meta.json`) do not bump it. Published services keep both `url` (homepage) and `sourceUrl` (price-check page); they often differ.

### CORS

`GET` and `HEAD` are allowed from any origin (`Access-Control-Allow-Origin: *`). Send an `Origin` header on the request. `ETag` is exposed (`Access-Control-Expose-Headers`).

### Caching and conditional GET

| Asset | `Cache-Control` (object metadata) | Edge cache |
|-------|-----------------------------------|------------|
| `/v1/catalog.json`, `/v1/meta.json` | `public, max-age=300, stale-while-revalidate=86400` | Needs Cache Rule (below) |
| `/v1/schema.json` | `public, max-age=86400, stale-while-revalidate=604800` | Needs Cache Rule (below) |
| `/logos/*` | `public, max-age=31536000, immutable` | Cached by default (svg/png/webp) |

R2 already returns `ETag` and `Last-Modified`. Clients should send `If-None-Match` and handle **304**. Origin conditional GET works today even while the JSON path is `cf-cache-status: DYNAMIC`.

Cloudflare **does not cache JSON by default** ([R2 + Cache](https://developers.cloudflare.com/cache/interaction-cloudflare-products/r2/)). Logos HIT because those extensions are in the default list. Catalog JSON stays `DYNAMIC` until a Cache Rule makes `/v1/*.json` eligible — `Cache-Control` on the object is not enough.

#### Cloudflare dashboard step (required once)

Code cannot create this rule. On the zone that owns `subdrop.repruv.com`:

1. **Caching → Cache Rules → Create rule**
2. Name: `Cache Subdrop v1 JSON`
3. When incoming requests match (Edit expression):

   ```
   (http.host eq "subdrop.repruv.com" and starts_with(http.request.uri.path, "/v1/") and http.request.uri.path.extension eq "json")
   ```

4. Then:
   - **Cache eligibility:** Eligible for cache
   - **Edge TTL:** Use cache-control header if present, use default Cloudflare caching behavior if not
5. Deploy the rule. Confirm with `GET` (not only `HEAD`): first request `MISS` or `EXPIRED`, then `HIT`. `DYNAMIC` means the rule is missing or not matching.

After that, warm catalog fetches should be edge HITs (~TTL 5 minutes, then revalidate). Cold R2 spikes should stop for cached PoPs.

### Published service fields (vs source YAML)

Build-time only — source files under `services/` are unchanged.

- `priceUsd` and `monthlyUsd` are always JSON **numbers with a decimal** (`17.99`, `69.0`), never ints.
- Absolute `logoUrl` is included; relative `logo` is omitted (YAML still has `logo:`).
- `url` and `sourceUrl` are both published (`url` is not dropped; ~half the rows differ).
- Empty `plans` is omitted. Use singular `plan`.
- `aliases` is always an array (possibly empty).

### Consumer example

```bash
# Freshness without the full dump
curl -sS https://subdrop.repruv.com/v1/meta.json

# Conditional GET
etag=$(curl -sS -D - -o /dev/null https://subdrop.repruv.com/v1/catalog.json \
  | awk -F': ' 'tolower($1)=="etag"{print $2}' | tr -d '\r')
curl -sS -D - -o catalog.json \
  -H "If-None-Match: $etag" \
  https://subdrop.repruv.com/v1/catalog.json
```

## Quick start

```bash
python3 scripts/validate.py
python3 scripts/build-catalog.py -o dist/v1/catalog.json
python3 scripts/check-published.py dist/v1/catalog.json
```

## Layout

```
catalog.yaml          # catalog metadata
categories.yaml       # category id + label
services/*.yaml       # one file per service
schema/               # source + published JSON Schema
scripts/              # validate + build (no deps)
logos/                # brand marks (relative paths in YAML)
dist/v1/              # catalog.json, schema.json, meta.json (generated)
```

Catalog data is [CC0 1.0](LICENSE). Trademarks remain with their owners.
