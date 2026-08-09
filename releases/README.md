# Release Instances

Generated publication artifacts are built under ignored `dist/<release-id>/`. They are uploaded by CI or attached to an external delivery system; they are not committed as a second paper source.

A release instance binds:

- an immutable release ID;
- one publication variant;
- a Draft-validation or strict Release profile;
- a canonical source fingerprint and Git audit commit;
- delivery targets and artifact checksums;
- build and isolated-compilation results;
- a separate durable Human-reviewed record when appropriate.

## Build

Strict release-ready build:

```bash
RELEASE_ID=iclr2027-submission-r1 VARIANT=anonymous \
  bash .agents/tools/release.sh
```

Direct tool usage:

```bash
python3 .agents/tools/release.py build \
  --id iclr2027-submission-r1 \
  --variant anonymous \
  --profile release \
  --targets pdf,source-zip,arxiv-flat,overleaf-zip \
  --verify-tex
```

The factory template contains unresolved placeholders, so a strict build is expected to fail until a real paper is ready. CI uses `--profile draft` only to verify the packaging mechanism and records `release_ready: false`.

## Storage boundary

- `dist/`: generated, ignored, replaceable only by deleting the whole candidate before rebuilding.
- `releases/records/`: tracked Markdown decisions and provenance; no PDF, ZIP, TeX copy, or binary artifact.
- GitHub Actions artifacts / GitHub Releases / Overleaf / arXiv: delivery systems, not authored sources.

## Immutability

A build refuses an existing release ID. A record refuses an existing filename. Published revisions use new IDs such as `submission-r2` or `arxiv-v2`; do not edit an old published record to represent a new artifact set.

## External truth

A successful local or CI package build does not prove a real Overleaf import, official venue upload, or arXiv platform build. Record those environments as unverified until actually exercised.
