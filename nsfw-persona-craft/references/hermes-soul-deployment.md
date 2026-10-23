# Hermes Deployment Notes for SOUL.md Personas

How a persona file actually lands in Hermes, and where the non-persona pieces go. Verified against the hermes-agent source (agent/prompt_builder.py, agent/skill_commands.py, agent/system_prompt.py).

## SOUL.md loading facts

- Loaded from `HERMES_HOME/SOUL.md` (`load_soul_md`), injected as **identity slot #1** and replaces the built-in default identity wholesale — no wrapper language.
- **Truncation**: content over the context-file limit is cut head/tail (70/20 ratio) with a `[...truncated...]` marker in the middle. Limit has a ~20,000-char floor and scales with model context; override with `context_file_max_chars`. Keep the persona under the limit so the middle (mode engine) is never lost.
- **Injection scan**: SOUL.md hitting prompt-injection patterns warns (⚠ in `/context`) but still loads. Skill/context files with the same patterns are BLOCKED — avoid "ignore previous instructions"-style phrasing when moving persona text into skills.
- Changes require a fresh session (`/reset`); the stable system-prompt prefix is cached.

## Where the non-persona pieces go

| Content type | Location | Mechanism |
|---|---|---|
| Persona (identity, modes, tone, examples) | `~/.hermes/SOUL.md` | identity slot, every session |
| Always-on rules (e.g. "must search research KB before answering math") | skill + `skills.auto_load` | `hermes config set skills.auto_load '["skill-name"]'` — full skill text injected into every new session with an `[IMPORTANT: auto-loaded...]` marker, no skill_view call needed |
| On-demand procedures (pentest workflow, LaTeX writing flow) | ordinary skill, lazy | agent loads via skill_view when relevant; zero cost when unused |
| User tuning preferences | MEMORY.md / USER.md | volatile layer |

`skills.auto_load` resolution: `resolve_auto_load_skills()` reads the list from user config; `build_auto_load_prompt()` renders the full skill blocks once per agent lifecycle (byte-stable across model switches/compression). Pinned skills are deliberately excluded from delegate children and internal forks — they are session-level operator guidance.

## Drafting & replacement workflow

1. Write review drafts to a project folder (e.g. `soul_v2_draft/`) with versioned names — `SOUL.md` (exact name) writes are refused by the protected-instruction hook without explicit user consent; use `SOUL.v2.draft.md` style names.
2. Keep a DEPLOY.md in the draft folder: cp commands for skills, the exact `hermes config set` line, and a post-deploy checklist (`/reset`, then `/context` to verify SOUL loaded with no ⚠, auto_load skill listed, persona behavior tested per mode).
3. Before replacing `~/.hermes/SOUL.md`, archive the current version (existing convention in this home: `SOUL_Archived_<date>.md`).

## Parallel writer profile (separate persona for one job)

When a dedicated fiction/NSFW writer voice is wanted alongside (not instead of) the companion persona, create a separate profile rather than editing the main SOUL:

1. `hermes profile create <name> --clone` — copies config.yaml, .env, SOUL.md, and skills from the active profile. `--no-skills` is mutually exclusive with `--clone`, so skill pruning (if wanted) happens afterwards.
2. Archive the cloned SOUL before overwriting: `cp ~/.hermes/profiles/<name>/SOUL.md ~/.hermes/profiles/<name>/backups/SOUL.clone-<date>.md`.
3. Deploy the writer SOUL onto the profile's SOUL.md; keep the draft copy in the project folder for diffing.
4. Test one-shot: `hermes -p <name> -z "<prompt>" > out.txt 2>err.txt`. The prompt must sit immediately after `-z` — flags wedged between them (`-z --ignore-rules -q "..."`) fail with `expected one argument`; drop `--ignore-rules` unless you specifically need to skip SOUL injection. For long multi-line prompts (rewrite instructions + quoted source text), prefer `--query-file <path>` with `--oneshot` — no shell quoting hazard. The reply comes back wrapped: reasoning box, then answer body inside the `╭─ ☤ Hermes ╮` frame, then a session-resume footer. Extract the answer by splitting on the frame characters, not by taking the whole stdout.
5. Verify the reply's self-claims by reading: the model reports word counts and "saved to <path>" — re-read the file and recount the Chinese chars before reporting success. A local model can fabricate the save.

## Clean-room profile (style-neutral rewriter for persona files)

Rewriting a persona/rules file that the main agent reads every turn cannot be done by the main agent itself — its own prose is contaminated by the file it is fixing (echo). Delegate the rewrite to a separate profile fed ONLY clean community-sourced text:

1. Create the profile (`--clone`), then strip everything cloned that carries the old style: move `memories/MEMORY.md`, `memories/USER.md`, the whole `skills/` dir, and `.skills_prompt_snapshot.json` into `backups/` (the snapshot feeds the skill list into the system prompt, so it must go too). Move, don't delete — rollback is a `mv` back.
2. The profile's SOUL.md becomes byte-exact concatenation of the owner-supplied source cards (`cat a b > SOUL.md`, then `cmp` against a re-concatenation to prove zero drift). No self-written rules may enter — a self-written rule re-imports the very voice being cured.
3. Keep the model identical to the main profile (same base at the same endpoint) so the rewritten prose can migrate back without changing voice provenance.
4. Rewrite prompt carries protected-facts constraints: meanings one-for-one, quoted spans / bracketed IDs / numbers / English tokens verbatim, no emoji, output only the rewritten section with no preamble. Verify the output with `scripts/style_fingerprint.py` (source vs rewrite) AND a manual fact-census that every protected token survived — density dropping to zero while facts leak is a failed rewrite.
5. Work section-by-section; long sections with tables need an extra constraint line ("表格结构与数字逐格保留"). Small-section success does not generalize to table-heavy sections.

## Verification tests after deploy

- Ask a domain question covered by a pinned rule skill: the agent must retrieve/cite, not answer from memory.
- Ask a work-mode question: expect rigorous body + persona voice markers retained.
- Ask a flirty prompt: expect prose-only (no lists/code fences) in flirty mode.
- Confirm the contrast behavior: work report ends → next sentence is the mode-switch, not a transition.
