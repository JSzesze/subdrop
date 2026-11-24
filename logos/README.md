# Logos

Brand mark files live in this directory (for example `logos/netflix.svg` and `logos/netflix.png`).

- Paths in service YAML use **relative** paths: `logos/<file>.png` or `logos/<file>.webp` (no leading slash).
- **`logo:` must be a raster.** Budget0 on iOS loads `logoUrl` with `expo-image`, which cannot decode SVG. Official SVG marks may be committed alongside the PNG as the source, but the YAML field must point at the PNG/WebP.
- The referenced file must exist, and the bytes must match the extension (a JPEG or ICO named `.png` fails CI).
- Do **not** commit preview or deployment URLs (Vercel, temporary hosts, etc.).
- Only add logos you have the right to redistribute for identification purposes, or use marks supplied by the service owner under their brand guidelines. Use the real brand mark (icon, not wordmark). No placeholders.

Published `catalog.json` exposes absolute `logoUrl` and omits the relative `logo` field. Source YAML must keep `logo:` and must never contain `logoUrl`. Logo objects on the CDN are cached for one year as `immutable`; change the filename if you replace a mark.
