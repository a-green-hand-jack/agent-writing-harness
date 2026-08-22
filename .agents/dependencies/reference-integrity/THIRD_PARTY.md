# Reference-integrity third-party dependencies

This lock is used by the non-mutating BibTeX format gate, correction-candidate
audit, and online metadata audit. No dependency is vendored into the repository
or required to compile `paper/`.

Direct dependencies:

- `bibtex-updater==1.6.1` — MIT; upstream is marked Beta. Only its core
  dependency set is installed. The metadata audit uses `--non-generative`; the
  correction audit writes only a candidate under ignored `dist/`. Optional
  Scholar, Zotero, organizer, embedding, and LLM extras are excluded.
- `pybtex==0.26.1` — MIT; used only to parse classic BibTeX for syntax, entry
  type, and required-field validation. The gate does not rewrite the input.

The resolved core currently contains:

- MIT: `anyio`, `bibtex-updater`, `charset-normalizer`, `crossref-commons`
  (classifier), `h11`, `latexcodec`, `pybtex`, `pyparsing`, `PyYAML`,
  `rapidfuzz`, `ratelimit`, and `urllib3`;
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
