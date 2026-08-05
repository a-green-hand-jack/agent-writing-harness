# Reference-integrity third-party dependencies

This lock is used only by the optional online metadata audit. No dependency is
vendored into the repository or required to compile `paper/`.

Direct dependency:

- `bibtex-updater==1.6.1` — MIT; upstream is marked Beta. Only its core
  dependency set is installed, with `--non-generative`; optional Scholar,
  Zotero, organizer, embedding, and LLM extras are excluded.

The resolved core currently contains:

- MIT: `anyio`, `bibtex-updater`, `charset-normalizer`, `crossref-commons`
  (classifier), `h11`, `pyparsing`, `rapidfuzz`, `ratelimit`, and `urllib3`;
- BSD-3-Clause: `httpcore`, `httpx`, and `idna`;
- Apache-2.0: `requests`;
- MPL-2.0: `certifi`;
- PSF-2.0: `typing-extensions`; and
- `BSD-3-Clause OR LGPL-3.0-or-later`: `bibtexparser`.

Package versions and artifact SHA256 values are authoritative in `uv.lock`.
The lock must be regenerated and this inventory reviewed whenever any resolved
version changes.

These tools verify bibliographic identity and metadata. Their licenses and
outputs do not transfer authority to approve paper claims.
