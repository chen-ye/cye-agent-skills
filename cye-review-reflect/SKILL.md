---
name: cye-review-reflect
description: This skill should be used when the user asks for a "post-review reflection", "review retrospective", "extract issues you missed", "compare my review comments with yours", "what did I catch that you missed", or invokes `cye-review-reflect` after a PR review, code review, or Crit session to audit blind spots and codify review guidance.
---

# Post-Review Reflection (`cye-review-reflect`)

Analyze a completed code or PR review session to uncover bugs, smells, design errors, and review blind spots that the human reviewer caught while automated passes and assistant syntheses missed, minimized, or got wrong. Produce an evidence-backed retrospective report first, then route approved takeaways into persistent memory, project docs, or skills.

## Core principles

1. **Recover full raw history before analyzing.** Context compaction and `session.messages` omit OpenChamber UI-block answers, card notes, and inline quote comments (`type = "synthetic"`). Always extract the raw session export, child subagent reports, and external PR or Crit comments before writing findings.
2. **Attribute accurately.** Separate complete blind spots (user-only catches), overruled or rejected assistant recommendations, reshaped fixes, and issues that automated passes actually caught. Never rewrite history or claim credit for user-discovered insights.
3. **Infer failure modes, not just file edits.** Group individual diffs into recurring reasoning, boundary, UX, and triage blind spots.
4. **Report first; gate every persistent write.** Present the retrospective report before saving memories or editing skills, `AGENTS.md`, or prompts. Propose concrete candidate edits for user approval and generalize principles away from single-PR identifiers unless scoped explicitly to a repository.

## Workflow

### Step 1: Collect ground-truth artifacts

Run `scripts/extract_review_trace.py` (bundled with this skill) to gather all review threads, session turns, and subagent passes into `/tmp/opencode/review-reflect`:

```bash
python3 scripts/extract_review_trace.py \
  --session <SESSION_ID> \
  --pr <PR_NUMBER> \
  --repo-dir <REPO_PATH>
```

Adjust flags as needed:
- Omit `--pr` for local-only or Crit-only reviews; inspect `.crit/` or local git commits (`git log`, `git show`) directly.
- Omit `--session` when reflecting solely on an external PR or multi-reviewer thread.
- Inspect `session_user_feedback.md`, `session_subagent_reports.md`, `session_assistant_turns.md`, `pr_comments.md`, `pr_reviews.md`, and `pr_commits.txt` in full before classifying findings. Read the final landed commit (`git show <merge_or_head_sha>`) to verify exact landed behavior.

### Step 2: Map the chronological delta

Walk through each review round chronologically and compare four streams:
1. Automated subagent findings (for example, `thermos`, `rev_review`, or specialist passes).
2. Assistant syntheses, proposed fixes, and triage card defaults (`Draft` vs `Ignore`).
3. Human questions, card notes, inline diff comments, pushbacks, and direct PR comments.
4. Author commits and replies through merge.

Classify every user intervention into one of four buckets:
- **Complete blind spot:** Flagged or questioned by the user while every automated pass and assistant synthesis missed it.
- **Actively wrong or rejected:** Proposed by automated passes or the assistant and corrected, overruled, or blocked by the user (including valid fixes defaulted to `Ignore` or speculative "Code Judo" that broke invariants).
- **Reshaped fix:** Symptom noted by automated passes where the user identified the cleaner root cause, upstream platform semantics, or minimal scope.
- **Baseline automated catch:** Briefly note legitimate bugs caught by automated passes so the signal-to-noise assessment stays objective.

### Step 3: Infer patterns and smells

Consult `references/diagnostic-lenses.md` and synthesize the round-by-round deltas into recurring patterns across five areas:
- Platform and spec alignment vs. local workarounds.
- Semantic boundary integrity vs. premature abstraction or missed API ergonomics smells.
- Domain and operator UX invariants.
- Documentation, test resilience, and cross-consumer blast radius.
- Review comment coherence and triage severity calibration.

### Step 4: Present the retrospective report

Deliver a structured report containing:
1. **Summary scorecard and comparison table:** Pair concise counts (comments, user-driven deltas, late-round blind spots, rejected proposals) with a comparison table linking automated takes, user catches, and outcomes.
2. **Complete blind spots:** Detail each issue the user caught independently, citing exact `comment_id`, commit SHAs, and clickable `path:line` references.
3. **Rejected or corrected recommendations:** List cases where automated passes or the assistant pushed flawed designs, missed UX constraints, or mis-triaged real issues as `Ignore`.
4. **Systemic patterns:** Explain the underlying habits that caused the misses and the heuristics the user applied instead.
5. **Follow-up offer:** Ask whether to distill approved lessons into persistent memory, project `AGENTS.md` or skills, reviewer subagent prompts, or follow-up tickets. Wait for user confirmation before mutating any persistent store.

### Step 5: Codify approved takeaways

When the user chooses to persist lessons:
1. **Check existing stores first.** Read existing memories (`openchamber_memory` `memory.list` / `memory.read`) and relevant skills or `AGENTS.md` files to avoid duplicating existing rules.
2. **Route to the right scope:**
   - Cross-session review habits and general engineering heuristics go to global memory (`preference`).
   - Repository-specific conventions and settled architectural invariants belong in `AGENTS.md` or project skills when shared files exist, or project memory when the repository keeps no agent docs.
   - Reviewer workflow gaps belong in explicit diffs to reviewer prompts or skills.
3. **Generalize before proposing.** Strip single-PR symbol names and one-off filenames from global rules so each rule remains valid across codebases.
4. **Present interactive approval cards.** Show each proposed entry (concise `<= 60`-char title, scope, type, rationale, and exact body) for user approval or refinement, then write only approved items.

## Supporting resources

- **`scripts/extract_review_trace.py`** - Exports OpenCode session user/synthetic turns, subagent outputs, assistant responses, and paginated PR comments/reviews/commits (with GHES `GH_HOST` detection).
- **`references/diagnostic-lenses.md`** - Five diagnostic lenses for inferring blind spots, API smells, and triage miscalibrations.
