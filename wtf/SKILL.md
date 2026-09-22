---
name: wtf
description: Analyze mistakes, frustration points, or failed turns, distill an actionable prevention rule, and persist it into AGENTS.md and memory. Trigger with /wtf, "wtf", "that was wrong", "why did you do that", or when an agent mistake needs to be codified into a permanent rule.
---

# /wtf - Rules From Mistakes

When the user invokes `/wtf [complaint]` or expresses frustration about a mistake, your goal is to:
1. **Diagnose the breakdown** without excuses or defensiveness.
2. **Derive an actionable prevention rule**.
3. **Persist the rule permanently** to prevent the mistake from recurring in future sessions.

---

## Workflow

### Step 1: Analyze What Went Wrong
Review the immediate conversation history, tool calls, or user complaint:
- What assumption did the agent make that proved false?
- Did the agent violate a project convention, drop a critical comment, or hallucinate syntax?
- Did the agent ignore user instructions, over-complicate a simple task, or produce a broken patch?

### Step 2: Formulate the Prevention Rule
A good rule is **concrete, actionable, and directive**:
- **Format**: `[WHEN / CONTEXT] ALWAYS [REQUIRED ACTION] and NEVER [PROHIBITED ACTION] because [REASON].`
- **Example Bad Rule**: `Be more careful with TypeScript types.` (Too vague)
- **Example Good Rule**: `When editing database models, NEVER modify existing column names without adding a migration; ALWAYS check schema definitions in src/db/schema.ts.`

### Step 3: Persist the Rule
1. **Project Rules (`AGENTS.md`)**:
   - Check if `AGENTS.md` (or `.opencode/rules/` / `CLAUDE.md`) exists in the workspace root.
   - Append the rule to the appropriate guidelines or conventions section.
2. **Persistent Memory (Hindsight / Mem0)**:
   - If Hindsight or an MCP memory server is available, retain the distilled rule and context so it is automatically recalled in future sessions.

### Step 4: Confirm to the User
Present a concise 3-part summary:
- **Mistake Diagnosed**: 1 sentence summary of what went wrong.
- **Rule Created**: The exact directive formulated.
- **Where Stored**: Files (`AGENTS.md`) and memory banks updated.
