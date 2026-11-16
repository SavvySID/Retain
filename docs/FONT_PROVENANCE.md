# Geist font provenance

Retrieved and checked on 16 November 2026. This is the genuine Geist Sans variable font from [Vercel's official Geist repository](https://github.com/vercel/geist-font), which is also linked from [Vercel's font page](https://vercel.com/font). It replaces no model or dataset artifact.

## Saved files

| Local file | Original pinned source | Verified bytes | SHA-256 |
|---|---|---:|---|
| `static/fonts/Geist-Variable.woff2` | `packages/next/dist/fonts/geist-sans/Geist-Variable.woff2` | 69,760 | `2ffebe993e969069a9789d15164b7715d42491b5835516c5e3b935d5f81b05f1` |
| `static/fonts/OFL.txt` | Repository-root `OFL.txt` | 4,384 | `021caa749f89fecd7c2e40a50499de29e84d2bc19251659b47d499c2fbfffc17` |

Both were fetched from immutable repository commit **`ef2597cfc42f4797676df105517ccc0a1cfa6569`**, using GitHub's Contents API and decoding its base64 content. Source bytes are preserved without editing; this includes the license's original whitespace.

The upstream license has a trailing space on line 21. Its exact-byte preservation is intentional; `.gitattributes` scopes a whitespace-check exception to that original license file rather than editing its recorded bytes.

- [Pinned font source](https://github.com/vercel/geist-font/blob/ef2597cfc42f4797676df105517ccc0a1cfa6569/packages/next/dist/fonts/geist-sans/Geist-Variable.woff2)
- [Exact font retrieval URL](https://api.github.com/repos/vercel/geist-font/contents/packages/next/dist/fonts/geist-sans/Geist-Variable.woff2?ref=ef2597cfc42f4797676df105517ccc0a1cfa6569)
- [Pinned original OFL](https://github.com/vercel/geist-font/blob/ef2597cfc42f4797676df105517ccc0a1cfa6569/OFL.txt)
- [Exact license retrieval URL](https://api.github.com/repos/vercel/geist-font/contents/OFL.txt?ref=ef2597cfc42f4797676df105517ccc0a1cfa6569)
- Git blob IDs: font `71dab8bedba3bfef5dccd7875ed05cac44c7345d`; license `999fa2373263f4ce66077075c9ede594c6a49510`.

## Verification actually performed

The saved font begins with the correct WOFF2 signature, `wOF2`, and its byte count and Git blob ID agree with the official tree entry. Chromium's native `FontFace` loader successfully decoded the actual saved bytes: status `loaded`, requested variable weight range `100 900`, and `document.fonts.check('600 16px "Geist verification"')` returned true. This was a local intercepted-resource check; no font CDN or external runtime request is required to serve the saved file.

The installed `fontTools.ttLib.TTFont` could not decode WOFF2 directly because the optional Python Brotli extension is absent. No package was installed to work around that limitation. FontTools did decode the official companion variable TTF from the **same pinned commit**, in memory, without saving or shipping that additional font:

| Companion metadata | Observed value |
|---|---|
| Family | Geist |
| Full name | Geist Regular |
| Version string | Version 1.800 |
| PostScript name | Geist-Regular |
| Variable axis | `wght`: minimum 100, default 400, maximum 900 |
| Glyph count | 975 |
| Embedded license | SIL Open Font License, Version 1.1 |

The companion TTF source is [fonts/Geist/variable/Geist[wght].ttf](https://github.com/vercel/geist-font/blob/ef2597cfc42f4797676df105517ccc0a1cfa6569/fonts/Geist/variable/Geist%5Bwght%5D.ttf), SHA-256 `73894e0448cae90a92b6c2f8732b7bb9acb7b94c418bff559dad4a18e1de9659`. These metadata values are explicitly from the companion TTF, not a claim that Python decoded the WOFF2 name table. The actual shipped WOFF2 was independently accepted by Chromium.

## License and use

The original [local license](../static/fonts/OFL.txt) is **SIL Open Font License, Version 1.1**, with the upstream copyright notice naming the Geist Project Authors. Retain that file with redistribution and follow its terms. The file is unmodified; no font subsetting, renaming of its internal family or glyph editing was performed.

The primary UI reference was measured as using the Geist family. This asset supports that typography choice without an external font service. The exact font binary used by the live shadcn preview was not identified or hash-compared, so this is a verified family match rather than a claim that both websites use byte-identical font releases. CSS wiring and final rendered font loading are the owning implementer's checks.
