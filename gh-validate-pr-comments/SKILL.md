---
name: gh-validate-pr-comments
description: This skill should be used when the user asks to "check PR comments", "which unresolved comments have been resolved", "validate PR comments", "verify if review comments have been addressed", "review unresolved comments", "resolve addressed comments", "mark resolved comments as resolved", "audit resolved comments", "check comments not resolved by the original commenter", "verify self-resolved PR comments", or needs a reviewer workflow to validate whether PR feedback (unresolved or resolved by someone other than the original commenter) has been sufficiently addressed in code and resolve/unresolve threads upon user consent.
version: 1.1.0
---

# PR Review Comment Validator & Resolver

A reviewer workflow to pull unresolved PR comments and comments resolved by someone other than the original commenter, inspect the current codebase to verify whether feedback has been sufficiently addressed, present an assessed report to the user, and mark verified threads as resolved (or prematurely resolved threads as unresolved) on GitHub upon explicit user consent. Works with both `github.com` and GitHub Enterprise Server.

> **Note on Roles**:
> - Use `gh-address-comments` when acting as an **implementer** to write code fixes for review comments.
> - Use `gh-validate-pr-comments` when acting as a **reviewer** or **auditor** to:
>   1. Validate whether **unresolved** comments have been addressed in the code and resolve them.
>   2. Audit whether comments **not resolved by the original commenter** (e.g., self-resolved by the PR author or resolved by a third party) have actually been sufficiently addressed, and re-open (`--unresolve`) any that were prematurely resolved.

---

## Core Reviewer Principles

1. **Never Guess or Speculate — Read the Actual Files**: The auto-surfaced snippet (±5 lines) is only a fast pointer. If the snippet does not reveal the full context of the function, class, types, imports, or behavior needed to confirm whether the feedback was addressed, the agent **MUST** call the `read` tool on the source file (and any related callers, configs, or tests) to examine the full context. For resolved or outdated threads (`isOutdated: true`), line numbers may have shifted since the review — read a wider window or search for the symbol in the file. Never extrapolate or assume from a limited window.
2. **No Heuristic Auto-Resolution or Auto-Audit**: Determining whether a code review comment has been sufficiently addressed is an analytical task for the agent, not a keyword or timestamp script. A reply saying "Done" or a thread marked "Resolved" by the PR author is a claim, not evidence — the agent must read and reason over the actual code, commit history, and thread replies.
3. **Verify Resolution Authority (Original Commenter vs. Others)**: In strict review workflows, only the reviewer who raised a concern should resolve the thread, or an auditor must verify that non-commenter resolutions (`resolvedBy.login != comments[0].author.login`) are backed by a complete code fix, explicit concurrence from the original commenter in thread replies, or a formally tracked deferral ticket.
4. **Mandatory User Consent for Resolution / Unresolution**: The agent must **NEVER** mark comments as resolved or unresolved on GitHub without explicit user review and confirmation. Present the assessed list to the user first, and only call `resolve_thread.py` after the user approves.

---

## 5-Step Reviewer Workflow

```
┌────────────────────────────────────────────┐
│ 1. Pull Unresolved / Non-Author-Resolved   │ Run fetch_unresolved_comments.py (--audit, default, or --non-author-resolved)
└─────────────────────┬──────────────────────┘
                      ▼
┌────────────────────────────────────────────┐
│ 2. Inspect Proximal & Full Code + Replies  │ Read source files, git history & thread replies; verify sufficiency without guessing
└─────────────────────┬──────────────────────┘
                      ▼
┌────────────────────────────────────────────┐
│ 3. Present Assessment Report to User       │ Categorize: Addressed / Pending (unresolved) & Sufficient / Insufficient (audited)
└─────────────────────┬──────────────────────┘
                      ▼
┌────────────────────────────────────────────┐
│ 4. Mandatory User Consent Gate             │ Wait for user to confirm which threads to resolve or unresolve
└─────────────────────┬──────────────────────┘
                      ▼
┌────────────────────────────────────────────┐
│ 5. Execute Resolution / Unresolution       │ Run resolve_thread.py (or --unresolve) for approved thread IDs only
└────────────────────────────────────────────┘
```

---

### Step 1: Pull Unresolved & Non-Original-Commenter Resolved Comments

Run `fetch_unresolved_comments.py` to extract review threads with their resolution metadata, diff context, and proximal code:

```bash
# Pull both unresolved threads AND threads resolved by someone other than the original commenter (recommended for full review & audit)
python scripts/fetch_unresolved_comments.py --audit

# Pull only unresolved review threads (default)
python scripts/fetch_unresolved_comments.py

# Pull ONLY resolved threads that were NOT resolved by the original commenter
python scripts/fetch_unresolved_comments.py --non-author-resolved

# Fetch raw JSON with full resolution metadata (originalCommenter, resolvedByLogin, isResolvedByOriginalCommenter, isResolvedByOther, isResolvedByPrAuthor)
python scripts/fetch_unresolved_comments.py --audit --format json > /tmp/unresolved_comments.json

# Inspect all threads (including those resolved by the original commenter):
python scripts/fetch_unresolved_comments.py --all
```

The script automatically detects the repository host (`github.com` or GitHub Enterprise Server), PR number, and repository name from the git remote of the current branch. Override any value with flags if necessary (`--pr <num>`, `--repo <owner/name>`, `--hostname <host>`).

---

### Step 2: Inspect Proximal Code & Read Full File Context

For each surfaced review comment (whether unresolved or resolved by someone other than the original commenter):

1. **Examine the Thread & Resolution Metadata**: Note the file path, target line (`line` vs `originalLine`), original commenter (`@<originalCommenter>`), who resolved it (`@<resolvedByLogin>` if resolved, and whether `isResolvedByPrAuthor` is true), reviewer comment, replies, and diff hunk from Step 1.
2. **Mandatory File Reading**: If the auto-surfaced snippet is in any way insufficient to see the complete change, call `read` on the actual file with an appropriate window (e.g. 50–100 lines around the target). For outdated diffs (`line` is null, only `originalLine` is present), lines may have shifted—search for the relevant function or symbol in the file. Do not guess or infer what the rest of the file contains.
3. **Trace Git History**: When needed to verify what changed and why after the comment was left, run `git log -p -S <symbol> -- <path>` or `git diff origin/<base_ref>...HEAD -- <path>` to see the exact commit that modified the lines.
4. **Inspect Related Files**: If the feedback affected configurations, imports, tests, or callers across files, read those files too.
5. **Evaluate Sufficiency Criteria**:
   A review comment is **sufficiently addressed** only when verified by at least one of:
   - **Complete Code Resolution**: The current code (and tests, if requested) directly and completely resolves the concern raised by the original commenter.
   - **Explicit Original Commenter Concurrence**: The original commenter replied in the thread explicitly agreeing with the author's explanation or rationale for keeping the current design, even if someone else clicked "Resolve".
   - **Formal Tracked Deferral**: The feedback was formally deferred to a linked issue/ticket in accordance with project engineering standards (e.g., a `TODO: <TICKET>` in code or linked ticket in the thread).
   *(Note: A bare "Done" / "Fixed" reply without corresponding code changes, a partial fix that misses part of the reviewer's request, or an unanswered question resolved unilaterally by the PR author is **NOT** sufficiently addressed.)*
6. **Classify**:
   - **For Unresolved Threads (`isResolved: false`)**:
     - **Addressed (Ready to resolve)**: The code changes or thread discussion directly satisfy the reviewer's concern. Note the concrete evidence (file, lines, syntax, commit).
     - **Pending (Action required)**: The issue is still present in the file, or requires discussion / clarification.
   - **For Threads Resolved by Non-Original Commenter (`isResolvedByOther: true`)**:
     - **Sufficiently Addressed (Audit passed)**: Resolved by `@<resolver>` (original commenter `@<commenter>`), and verified with concrete evidence in the codebase or thread replies. Remains resolved.
     - **Insufficiently Addressed / Prematurely Resolved (Audit failed — recommend unresolving)**: Resolved by `@<resolver>` (original commenter `@<commenter>`), but the underlying issue remains unaddressed, only partially fixed, or unilaterally dismissed without the original commenter's concurrence.

---

### Step 3: Present Findings to the User

Present a clear, structured report to the user covering both unresolved threads and audited non-commenter-resolved threads (as applicable):
- **Addressed Comments (Unresolved — Ready to resolve)**: Specify the file, line, original commenter, comment summary, Thread ID, and how the current code resolves it.
- **Pending Comments (Unresolved — Action required)**: Summarize what is still requested and what edits or replies are required.
- **Audited Non-Commenter-Resolved Comments (Sufficiently Addressed)**: Specify the file, line, original commenter (`@<commenter>`), resolver (`@<resolver>`), Thread ID, and concrete evidence confirming the feedback was properly addressed.
- **Audited Non-Commenter-Resolved Comments (Insufficiently Addressed — Recommend unresolving)**: Specify the file, line, original commenter (`@<commenter>`), resolver (`@<resolver>`), Thread ID, why the resolution is insufficient, and what remains to be fixed or discussed.

Example format:

```markdown
### Addressed Comments (Unresolved — Ready to resolve)
1. `tools/generate-coverage-index.ts:247` (Thread `MDIz...` | Commenter: `@alice`)
   - **Feedback**: Sanitize baseRef and switch to execFileSync.
   - **Resolution**: `execFileSync('git', ['diff', '--name-only', baseRef])` is now used.

### Pending Comments (Unresolved — Action required)
2. `package.json:15` (Thread `MDIz...` | Commenter: `@alice`)
   - **Feedback**: Add timeout flag to test runner.
   - **Required Action**: Needs `--timeout 5000` added to test script.

### Audited Non-Commenter-Resolved Comments — Sufficiently Addressed
3. `src/parser.ts:88` (Thread `PRRT_1...` | Commenter: `@bob`, Resolved by PR author `@charlie`)
   - **Feedback**: Guard against empty input array before indexing.
   - **Audit Verification**: Verified in `src/parser.ts:86-90` (`if (items.length === 0) return null;` added) and unit test added in `src/parser.test.ts:42`.

### Audited Non-Commenter-Resolved Comments — Insufficiently Addressed (Recommend unresolving)
4. `src/client.ts:112` (Thread `PRRT_2...` | Commenter: `@bob`, Resolved by PR author `@charlie`)
   - **Feedback**: Handle 429 rate-limit responses with exponential backoff and add a test.
   - **Audit Finding**: `src/client.ts:112` now catches 429 and retries once immediately, without exponential backoff, and no unit test was added in `src/client.test.ts`.
```

---

### Step 4: Obtain Explicit User Consent

**MANDATORY GATE**: Ask the user which unresolved comments to mark as resolved and/or which insufficiently addressed threads to unresolve (re-open). Never proceed to Step 5 without explicit user authorization.

Example prompt to user:
> "Would you like me to mark comment #1 as resolved and unresolve comment #4 on GitHub so it can be properly addressed?"

---

### Step 5: Execute Resolution / Unresolution (Only with Approval)

After the user approves:
```bash
# Resolve approved threads by passing their Thread IDs
python scripts/resolve_thread.py <thread_id_1> <thread_id_2> ...

# Unresolve (re-open) prematurely resolved threads or threads resolved by mistake:
python scripts/resolve_thread.py <thread_id_4> --unresolve
```

---

## Bundled Resources

### Scripts (`scripts/`)
- **`fetch_unresolved_comments.py`**: Fetches PR review threads with resolution authority metadata (`originalCommenter`, `resolvedByLogin`, `isResolvedByOriginalCommenter`, `isResolvedByOther`, `isResolvedByPrAuthor`), diff context, and proximal code snippets. Supports filtering by unresolved (default), `--audit` (unresolved + resolved by non-original commenter), `--non-author-resolved` (only resolved by non-original commenter), `--resolved-only`, and `--all`. Supports GitHub.com and GitHub Enterprise Server.
- **`resolve_thread.py`**: Executes the `resolveReviewThread` (or `unresolveReviewThread` via `--unresolve`) GraphQL mutation on GitHub. Only run after explicit user approval.

### References (`references/`)
- **`references/graphql_queries.md`**: GraphQL schema definitions for queries, mutations, resolution authority fields, and multi-host authentication instructions.
