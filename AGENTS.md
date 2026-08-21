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

## Workflow

1. Edit or add `services/<id>.yaml` (filename must equal `id`).
2. Run locally:
   ```bash
   python3 scripts/validate.py
   python3 scripts/build-catalog.py -o dist/catalog.json
   ```
3. Open a PR. CI runs the same validate + build steps.
4. After merge to `main`, a publish workflow (stub today) will eventually upload `catalog.json` and `logos/` to Cloudflare R2.

## Do not

- Add `logoUrl` or Vercel/preview URLs to source files.
- Run scrapers that commit directly to `main`.
- Accept end-user catalog submissions (curated PRs only).
- Invent `billingMonth` without a verifiable source.

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

See [docs/PRD.md](docs/PRD.md) for product context and the public API contract.
