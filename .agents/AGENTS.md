# Codex Adapter Entry

Read the root `AGENTS.md`, then load the focused skill selected by the active
task. Load one primary owner skill plus any explicitly permitted sidecars;
never load the whole family. Bundled third-party skills are thin wrappers in
`.agents/skills/` that route to immutable snapshots in `.agents/vendor/`; never
edit the vendor tree.
