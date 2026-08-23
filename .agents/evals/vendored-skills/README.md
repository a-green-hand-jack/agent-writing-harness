# Vendored Skill Task Evaluations

`scenarios.json` defines one narrow task-level probe for each bundled wrapper.
The deterministic checker validates coverage and scenario shape:

```bash
python3 .agents/tools/check-vendored-skill-evals.py
```

The checker does not invoke a model and does not claim output quality. A live
evaluation uses an isolated, read-only worker sub-agent for each scenario and a
different sub-agent to judge the response against `must` and `must_not`.
Generated prompts, responses, and reviewer packets belong under ignored
`.agents/runtime/vendored-skills/evals/<run-id>/`.

Classify each response as `PASS`, `PARTIAL`, or `FAIL`. A forbidden behavior is
always a failure. A pass is evidence only for that scenario and model/runtime;
it is not scientific approval, general model benchmarking, or permission to
activate Writing DNA. Stochastic live evaluations are explicit and non-blocking
until a provider-neutral runner and stable receipts exist.

Live result summaries are deliberately not tracked because ignored runtime is
not durable project truth. A local run must retain a manifest that binds its
prompts, raw responses, reviewer packets, scenario bundle, fixture bundle, and
vendored provenance by SHA-256. A clean checkout must rerun the live evaluation
instead of relying on a historical count. If the runtime cannot record model
metadata, the receipt must disclose that limitation.
