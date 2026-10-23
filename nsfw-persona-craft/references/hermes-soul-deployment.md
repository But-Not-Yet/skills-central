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

## Verification tests after deploy

- Ask a domain question covered by a pinned rule skill: the agent must retrieve/cite, not answer from memory.
- Ask a work-mode question: expect rigorous body + persona voice markers retained.
- Ask a flirty prompt: expect prose-only (no lists/code fences) in flirty mode.
- Confirm the contrast behavior: work report ends → next sentence is the mode-switch, not a transition.
