# Release Records

This directory stores durable Markdown records for reviewed release instances. It does not store generated TeX trees, PDFs, ZIP files, or build logs.

Create a candidate record from a verified instance:

```bash
python3 .agents/tools/release.py record \
  --instance dist/aris-iclr2026-submission-r1 \
  --output releases/records/aris-iclr2026-submission-r1.md \
  --status candidate
```

For `approved` or `published`, the command requires `--human-approval` in the exact grammar `Approved by <optional display name> [id:@stable-handle] on YYYY-MM-DD`. Examples are `Approved by José García [id:@jgarcia] on 2026-08-09` and the direct-handle form `Approved by [id:@reviewer-42] on 2026-08-09`. The display name is optional and may contain broad Unicode text, including mononyms, lowercase particles, apostrophes, and hyphens, but not square brackets, backticks, or control characters. The required durable handle is `@` followed by 1-63 ASCII letters, digits, periods, underscores, or hyphens, beginning with a letter or digit. Spaces and delimiters are exact, and the date must be a real ISO calendar date. Bare prose such as `no reviewer available`, `human unavailable`, or `approval is awaited` cannot match this grammar. This syntax validates only the durable attribution format; actual Human approval remains a Human decision and a Git/provenance fact that tooling cannot establish. Candidate and other non-approved statuses may use `pending`. Records are immutable: create a new release ID for a new artifact set or revision. A superseded record remains readable and may point to the newer ID in its notes.

Each record includes a known status and variant, a `draft` or `release` profile, a Boolean release-ready value, lowercase SHA-256 source and manifest fingerprints, Human approval, artifact checksums, and notes. `.agents/tools/check-release-records.py` validates the tracked record surface.
