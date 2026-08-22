# Agent guide

Subdrop is a **git-native subscription catalog**. Agents (and humans) improve the catalog by opening pull requests. There is no user submission form and no scrape-to-production pipeline.

## What to change

Each service is one flat YAML file under `services/<id>.yaml`.

When adding or updating a service:

1. **Match the schema** — see `schema/service.schema.json` and `schema/service.example.yaml`.
2. **Set `sourceUrl`** — the official page you used to verify the listed price (homepage or pricing page).
3. **Set `priceCheckedAt`** — ISO date (`YYYY-MM-DD`) when you verified the price.
4. **Keep prices faithful** — use advertised US prices; do not silently "fix" rounding in `monthlyUsd`.
5. **Use relative logos** — `logo: logos/netflix.svg`. Never add `logoUrl`, `homepage`, or preview URLs to source YAML.
6. **`billingMonth` (optional)** — only for **yearly** plans when you can cite a typical calendar charge month (1–12). Omit for anniversary-billed yearly plans and when unknown.
7. **`aliases` (optional)** — array of strings for legacy ids, merchant descriptors, or common misspellings that should resolve to this service (e.g. `youtube_premium` → `youtube-premium`). Do not add generic catch-alls like `apple.com/bill` unless the charge clearly identifies this product.

## Workflow

1. Edit or add `services/<id>.yaml` (filename must equal `id`).
2. Run locally:
   ```bash
   python3 scripts/validate.py
   python3 scripts/build-catalog.py -o dist/catalog.json
   ```
3. Open a PR. CI runs the same validate + build steps.
4. After merge to `main`, the publish workflow uploads `v1/catalog.json` and `logos/` to Cloudflare R2 (requires repo secrets: `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET_NAME`, `R2_PUBLIC_HOST`).

## Do not

- Add `logoUrl` or Vercel/preview URLs to source files.
- Run scrapers that commit directly to `main`.
- Accept end-user catalog submissions (curated PRs only).
- Invent `billingMonth` without a verifiable source.
- Add Budget0, Convex, or mobile app code to this repo — Subdrop owns subscription **products** only.

## Fields quick reference

| Field | Notes |
|-------|--------|
| `id` | Stable slug; matches filename |
| `sourceUrl` | Official URL used for price check |
| `priceCheckedAt` | `YYYY-MM-DD` |
| `billing` | `month`, `year`, or `week` |
| `billingMonth` | Optional; yearly only; 1–12 |
| `monthlyUsd` | Normalized monthly equivalent |
| `logo` | Relative path under `logos/` |
| `aliases` | Optional; legacy ids, merchant strings, misspellings |

See [docs/PRD.md](docs/PRD.md) for product context and the public API contract.
