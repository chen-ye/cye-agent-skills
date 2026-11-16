# Diagnostic lenses for post-review reflection

Use these five lenses when comparing human review feedback against automated review passes and assistant recommendations.

## 1. Platform and spec alignment vs. local workarounds

Look for cases where automated passes or the assistant accepted, preserved, or invented a local workaround instead of asking why the underlying platform caused friction.

Signals:
- Patching around disabled validation (`novalidate`, imperative `reportValidity()`, double-clearing error state) instead of handling native events properly.
- Accepting non-standard interaction state machines when standard browser or upstream library semantics exist.
- Guessing browser or framework internals instead of inspecting upstream source code.
- Treating surprising platform spec quirks in shared primitives as "Low" or "Safe to ignore" solely because current callers do not hit them.

## 2. Boundary integrity vs. premature "Code Judo"

Automated quality passes frequently push structural collapses or speculative caches while overlooking genuine local API smells.

Signals:
- Proposing structural collapses that mutate semantic element identity (for example, swapping unrelated forms under a single form element) or break 1:1 parity of wrapper components with native primitives.
- Proposing redundant lifecycle hooks, state caches, or memoization layers before tracing native framework update order (such as FIFO microtasks).
- Missing real API ergonomics smells in new code: configuration passed per render with custom equality helpers instead of constructor options, leaked public internal methods, redundant `requestUpdate()` calls, or inconsistent naming between internal fields and external states.

## 3. Domain and operator UX invariants

Static checks and headless layout scripts confirm bounding boxes and types, not human ergonomics or operational workflows.

Signals:
- Technically non-overflowing sizes that are unusable in real input workflows (for example, `min-width: 4ch` vs `8ch`).
- Reset or cleanup suggestions that silently erase partial user drafts on light-dismiss when preserving unsubmitted values is intentional.
- Visual or state modes (`loud` vs `quiet`) broken by missing interaction gating rather than refined cleanly.

## 4. Maintainability, documentation, and test resilience

Automated review passes optimize for finding runtime bugs and often go silent on developer ergonomics after blocking issues are resolved.

Signals:
- New shared utilities, controllers, or directives shipped without JSDoc docstrings or concrete `@example` usage.
- Test assertions coupled to fragile CSS properties (such as `getComputedStyle(...).display === 'flex'`) when semantic platform APIs (such as `checkVisibility()`) exist.
- Missed cross-consumer or sibling-app blast radius checks until explicitly requested.

## 5. Review output coherence and triage calibration

Inspect the review workflow itself, not only the code under review:
- Did posted review comments contradict each other, omit referenced preconditions, or anchor on stale lines?
- Did triage cards default real spec or primitive fixes to `Ignore` while elevating speculative refactors?
- Were later review rounds satisfied with "0 blockers" while obvious surface polish remained untouched?
