# Tracking an actively-developed fork & verifying a build swap

## What "latest" means on this fork
The fork publishes releases (`v16-<base>-rN`) built from an upstream base commit, and **regenerates `release.json` (release/base/tip/tree + artifact hashes) at the repo tip per release — treat it as the delivery's single source of truth for what "latest" is.** The newest pushed TAG can LAG the recorded release (seen: `release.json` declared rN+1 while the newest tag was rN), and commits after the release commit are docs/wip only. Never chase the branch tip for code, and never infer the current release from tags alone.

A fork point change (new base commit upstream) means the entire patch series rebases — full recompile, no incremental path (this box has no ccache; `GGML_CCACHE=ON` resolves to NOTFOUND). "Wait for the next release" and "rebuild now" cost the same night.

When the user says "the newest build", disambiguate three axes before answering: (a) newest commit/round, (b) newest built binary (mtime of `build/bin`), (c) newest actually wired into launch scripts (`grep` the launcher scripts for binary paths). These can be three different trees — name which axis each claim is on.

## Reproducing an official release tree
1. Refresh the delivery repo (local clone of the fork): `git fetch --all && git pull --ff-only origin main` (local-only standing order). Read `release.json`: `release`, `base` (fork point), `tree`, `n_blocks`; optionally `sha256sum rdna-boosts-all.patch` vs its recorded `all_patch.sha256`.
2. `git -C <parent-repo> worktree add ../<newdir> <base> --detach` — fresh disposable worktree at the declared base (never at the tag object).
3. Apply with the official script: `RDNA_BRANCH=<name> bash <delivery>/scripts/apply-all.sh .` — per-block `git am` (strict; auto `git am -3` fallback on drifted bases), then it asserts the applied tree equals release.json's `tree` (needs jq). The combined `rdna-boosts-all.patch` is a `git diff` blob for archival — do NOT apply it via plain `git apply` (silently drops hunks) or `git am` (refuses "Patch format detection failed"); the per-block script is the application path. Branches are shared across worktrees of the same .git — name clash: override with `RDNA_BRANCH=`.
4. Re-verify independently: `git rev-parse HEAD^{tree}` vs release.json `tree`, character for character. Mismatch = stop; do not build.
5. Configure: replicate ALL explicit cache flags from the last known-good build's CMakeCache, and pin HIP discovery to the system ROCm — a pip-installed ROCm SDK on PATH (`~/.local/bin/hipconfig|hipcc` shims, `_rocm_sdk_core` package) otherwise hijacks detection and configure dies on missing `hip-lang-config.cmake`. Fix: `cmake --fresh` + `-DCMAKE_HIP_COMPILER=/opt/rocm/<core>/lib/llvm/bin/clang++ -Dhip_DIR=/opt/rocm/lib/cmake/hip` + `PATH=/opt/rocm/bin:$PATH` (exact core version from the previous cache's CMAKE_HIP_COMPILER). Ninja + `-j$(nproc)`, tee the build log (~800 units ≈ minutes at 24 cores).
6. Post-build identity: `llama-server --version` (build number + commit must equal the new tree tip) and `strings libllama.so.0` for capability symbols (arch / nextn / spec flags).

For a master-approved **modified** build (unblocking a source-gated feature, e.g. mixed K/V): same base and same CMakeCache flags as the official build, add ONLY the feature's own flags (extra `GGML_CUDA_FA_QUANTS` entries); gate the behavior change behind an env switch so default semantics stay identical — the binary must remain a drop-in swap for the official tree, or the swap-verification below loses its baseline. Label the worktree/branch as a local variant; production stays on the official tree until the master says otherwise.

## Verifying a build swap from logs (before/after comparison)
- Compare the startup accounting blocks line by line between old-build and new-build boot sections: model buffer sizes, KV buffer sizes, compute buffer, graph nodes/splits, and which warnings appear or disappear. A warning that existed on the old build and vanishes on the new one (e.g. a staging-disabled warning) is positive evidence the new code path is live — report it as such.
- Cumulative t/s in `print_timing` progress lines is contaminated by cache hits — compute the MARGINAL rate between consecutive equal-size progress lines and compare like chunk sizes against like.
- Same-instance cold vs cached comparisons need identical prompt sizes; cross-build comparisons need identical regimes (don't compare a cold full-prefill run against a cache-hit-diluted one and call it regression).
- Server log timestamps are mm.ss.mmm (see main skill) — two boot sections must be delimited by their `initializing ...` lines before comparison, and process age verified with `ps -o lstart`.
- Match crash asserts across rebuilt trees by assert TEXT, never line number — code shifts between rebases, same text = same unfixed bug. A known-dead combo on this fork: `--no-kv-offload` + host-resident MoE hits the host-copy `GGML_ASSERT(id >= 0 && id < n_expert)` path (reproduced across two independently rebuilt trees); treat as dead until an upstream rebase lands a fix, then retest once.
- When a user-run experiment crashed on the first request after a clean load, the crash segment may live in a ROTATED log (`server.err.log.1` or older `.gz`) — grep the assert text across all rotations (zcat the .gz) before concluding there is no crash evidence.

## Verifying an external-advice audit against local state

When reviewing an external AI conversation's analysis of this stack, cross-check every factual claim against local ground truth (server logs across rotations, `git log` of the build tree, the harness's own config source for default values) — the external side does not know what was already tested or already fixed in-tree; claims already resolved locally get marked closed, not re-recommended. Deliver as per-claim verdicts plus the few genuinely actionable items; neither blindly accept nor defend.

## Inventorying a pile of build trees (which is clean upstream, which is an overlay, which can sync)

- A `.git` **FILE** (not directory) = git worktree of another repo (`cat .git` → `gitdir: <parent>/.git/worktrees/<name>`). Directory-style tests (`[ -d .git ]`) misclassify a worktree as "not a git repo" and produce wrong conclusions about the whole inventory. Enumerate with `git -C <dir> rev-parse --abbrev-ref HEAD` (works in worktrees; non-zero exit = truly not a repo) and run `git worktree list` from the parent repo to recover the parent↔worktree map.
- Classify each tree's HEAD against upstream, never by branch name: `curl -s .../repos/<org>/<repo>/commits/<sha>` — 200 = HEAD is an upstream commit (clean checkout or fork-point-based line); 404/422 = local/overlay commit. Cross-check with `git rev-list --count origin/master..HEAD` and a non-untracked dirty count.
- "Can this tree pull/merge the fork's latest?" is an **ancestor test**, not a date or name test: `git merge-base --is-ancestor <local-tip> <fork-tip>`; when sweeping the whole inventory, loop it over EVERY local branch — one ✓ changes the answer from "replay" to "fast-forward".

## Regenerated rounds: no ancestry between rounds

The fork re-creates each round's commit series (fresh hashes, re-stamped timestamps, sometimes disconnected roots). Consequences:

- An older local snapshot is NOT an ancestor of the newer round: `merge` refuses ("unrelated histories"), fast-forward is impossible, and a full-set patch replay onto a newer upstream conflicts heavily (probe with `git apply --3way --reject` and count `.rej` before committing to a manual resolution session).
- Do NOT "sync to latest" by merging or replaying between old and new rounds. The update path is: refresh the delivery/patch repo (local clone of the fork — `git pull --ff-only origin main`), then re-apply the refreshed `rdna-boosts-all.patch` per the reproduction recipe onto the declared fork point (a local squashed re-apply onto a newer upstream commit is the disposable-worktree variant).
- Match a local tree to a round via the fork's release tags only — two snapshots of "the same" round can differ by thousands of files with no common ancestor; commit dates and branch names cannot identify a round.
- Local folder names and local "rN" apply-rounds are NOT the fork's round numbers: two generations of the same round number under different bases coexisted, and a local `r7`/`r8` directory can be a re-apply of the *current* official tree. When listing tags, filter to the base recorded in `release.json` — other-base tags are dead generations. Identify any tree by (base, tree hash, release), never by folder name.

## History-op safety on these repos (standing order)

- **Local-only, no push**: these build/patch repos are under a no-push standing instruction — never push or publish from them. Do history experiments (rebase/replay/merge) on NEW branches; leave the original branches untouched.
- Create `backup/<name>-<date>` branch + tag at the current tips before any history operation, and keep them afterwards — they are the only undo.
- `git apply` (including `--3way`) is **all-or-nothing**: per-file "Applied ... with conflicts" lines in a streamed log can end in a FULL rollback when a later file fails. Read the post-state from `git status` / `git ls-files -u` AFTER the command — never from the log alone. After a probe run, restore tracked files with `git checkout -- .`; avoid recursive `find -delete` style cleanup idioms (hard-blocked in this environment; use explicit restores instead).
