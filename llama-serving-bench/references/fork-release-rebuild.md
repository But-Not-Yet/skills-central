# Tracking an actively-developed fork & verifying a build swap

## What "latest" means on this fork
The fork publishes frozen release tags (`v16-<base>-rN`) built from an upstream base commit. The branch tip keeps moving with docs-only commits (README/reply drafts/patch archives) after the last tag. **The latest release TAG is the code-frozen point — never chase the branch tip for builds.** When the author pushes new commits, check `git diff --stat <last-tag> <tip>`: if it's only README/patch/reply files, the tag still IS the latest code.

A fork point change (new base commit upstream) means the entire patch series rebases — full recompile, no incremental path (this box has no ccache; `GGML_CCACHE=ON` resolves to NOTFOUND). "Wait for the next release" and "rebuild now" cost the same night.

## Reproducing an official release tree
1. `git fetch <fork> --tags`; list release tags, pick newest.
2. `git worktree add ../<newdir> <base-commit>` (checkout the release's declared base, not the tag object itself).
3. Extract the release's combined patch: `git show <tag>:rdna-boosts-all.patch > /tmp/all.patch`; **verify sha256 against the tag's `release.json`** before applying.
4. `git am` refuses the combined patch ("Patch format detection failed") — use `git apply` (after `git apply --check`), then a local commit.
5. Verify `git rev-parse HEAD^{tree}` equals the tree hash declared in the release's release.json, character for character. Mismatch = stop.
6. Reconfigure by replicating ALL explicit cache flags from the production build's CMakeCache (scripted dump, ~150 flags), changing only the intended experiment variable; confirm configure log clean before building.

## Verifying a build swap from logs (before/after comparison)
- Compare the startup accounting blocks line by line between old-build and new-build boot sections: model buffer sizes, KV buffer sizes, compute buffer, graph nodes/splits, and which warnings appear or disappear. A warning that existed on the old build and vanishes on the new one (e.g. a staging-disabled warning) is positive evidence the new code path is live — report it as such.
- Cumulative t/s in `print_timing` progress lines is contaminated by cache hits — compute the MARGINAL rate between consecutive equal-size progress lines and compare like chunk sizes against like.
- Same-instance cold vs cached comparisons need identical prompt sizes; cross-build comparisons need identical regimes (don't compare a cold full-prefill run against a cache-hit-diluted one and call it regression).
- Server log timestamps are mm.ss.mmm (see main skill) — two boot sections must be delimited by their `initializing ...` lines before comparison, and process age verified with `ps -o lstart`.
- Match crash asserts across rebuilt trees by assert TEXT, never line number — code shifts between rebases, same text = same unfixed bug. A known-dead combo on this fork: `--no-kv-offload` + host-resident MoE hits the host-copy `GGML_ASSERT(id >= 0 && id < n_expert)` path (reproduced across two independently rebuilt trees); treat as dead until an upstream rebase lands a fix, then retest once.
- When a user-run experiment crashed on the first request after a clean load, the crash segment may live in a ROTATED log (`server.err.log.1` or older `.gz`) — grep the assert text across all rotations (zcat the .gz) before concluding there is no crash evidence.

## Verifying an external-advice audit against local state

When reviewing an external AI conversation's analysis of this stack, cross-check every factual claim against local ground truth (server logs across rotations, `git log` of the build tree, the harness's own config source for default values) — the external side does not know what was already tested or already fixed in-tree; claims already resolved locally get marked closed, not re-recommended. Deliver as per-claim verdicts plus the few genuinely actionable items; neither blindly accept nor defend.
