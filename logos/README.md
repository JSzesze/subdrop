# Logos

Brand mark files live in this directory (for example `logos/netflix.svg`).

- Paths in service YAML use **relative** paths: `logos/<file>.svg` (no leading slash).
- Do **not** commit preview or deployment URLs (Vercel, temporary hosts, etc.).
- Missing logo files do not fail CI during early seeding; consumers may fall back to `simpleIconsSlug` or placeholders until marks are added.
- Only add logos you have the right to redistribute for identification purposes, or use marks supplied by the service owner under their brand guidelines.

Published `catalog.json` exposes absolute `logoUrl` and omits the relative `logo` field. Source YAML must keep `logo:` and must never contain `logoUrl`.
