# Release Records

This directory stores durable Markdown records for reviewed release instances. It does not store generated TeX trees, PDFs, ZIP files, or build logs.

Create a candidate record from a verified instance:

```bash
python3 .agents/tools/release.py record \
  --instance dist/iclr2027-submission-r1 \
  --output releases/records/iclr2027-submission-r1.md \
  --status candidate
```

For `approved` or `published`, the command requires explicit `--human-approval`. Records are immutable: create a new release ID for a new artifact set or revision. A superseded record remains readable and may point to the newer ID in its notes.

Each record includes status, variant, profile, source fingerprint, manifest checksum, Human approval, artifact checksums, and notes. `.agents/tools/check-release-records.py` validates the tracked record surface.
