<!--
SYNC IMPACT REPORT
==================
Version change: 1.0.0 → 1.1.0
Added sections:
  - Principle VI: Cost-Conscious AI Usage (no AI SDK / programmatic API calls)
Modified principles: none
Removed sections: none
Templates updated:
  - .specify/templates/plan-template.md ✅ (no AI SDK references; existing gates unchanged)
  - .specify/templates/spec-template.md ✅ (no AI SDK references present)
  - .specify/templates/tasks-template.md ✅ (no AI SDK references present)
Deferred TODOs: none
-->

# Jobforce Constitution

## Core Principles

### I. Test-First Development (NON-NEGOTIABLE)

Tests MUST be written and confirmed to fail before any implementation begins.
The Red-Green-Refactor cycle is strictly enforced on every feature and bugfix.

- Every user story MUST have at least one independently runnable acceptance test.
- Unit tests MUST cover all non-trivial logic; integration tests MUST cover all
  cross-module contracts.
- No code is considered complete until its tests pass and coverage has not
  regressed.
- Tests MUST be co-located or clearly structured under `tests/` with mirroring
  paths that map 1:1 to source modules.

**Rationale**: Untested code is unfinished code. Test-first forces design clarity
and prevents the habit of skipping tests under time pressure.

### II. Code Quality Standards

All code MUST meet quality gates before merging:

- Linting MUST pass (ruff or project-configured linter) with zero warnings.
- Type annotations MUST be present on all public functions and methods.
- No function or method MAY exceed 40 lines; complex logic MUST be decomposed.
- Cyclomatic complexity MUST stay ≤ 10 per function.
- Dead code, commented-out blocks, and TODO markers older than one sprint MUST
  be removed before merge.

**Rationale**: Consistent quality prevents the accumulation of debt that makes
self-improvement loops expensive.

### III. Self-Improvement Loop

The project MUST maintain mechanisms that allow it to measure and improve itself:

- A structured feedback artifact (e.g., `docs/retrospective.md` or equivalent)
  MUST be updated after each significant feature or milestone.
- Linting, type-check, and test steps MUST be runnable locally with a single
  command (e.g., `make check` or equivalent).
- Any recurring failure pattern (test flake, lint class, runtime error category)
  MUST be captured as a tracked issue and addressed within two iterations.
- Tooling improvements (new linter rules, test helpers, code generators) are
  first-class deliverables and MUST be planned and tracked like feature work.

**Rationale**: Self-improvement requires instrumentation. Without explicit
feedback loops, quality improvements stagnate.

### IV. Simplicity & Clarity

Complexity MUST be justified. The default choice is always the simpler one.

- YAGNI (You Aren't Gonna Need It): no abstractions are introduced for
  hypothetical future requirements.
- Three similar concrete implementations are preferred over one premature
  abstraction.
- Every module, class, and public function MUST have a single, clearly stated
  responsibility.
- Comments MUST explain WHY, not WHAT. Code that needs a comment explaining
  what it does MUST be renamed or restructured instead.

**Rationale**: Simple code is easier to test, review, and improve. Complexity
is the primary enemy of self-improvement.

### V. Observability & Feedback

The system MUST produce useful signals for understanding its own behavior:

- Structured logging MUST be used for all non-trivial operations (stdlib
  `logging` or equivalent).
- Errors MUST include enough context to reproduce the failure without a
  debugger.
- Test output MUST be deterministic and human-readable in CI.
- Performance-sensitive paths MUST include timing instrumentation before
  optimization work begins.

**Rationale**: You cannot improve what you cannot measure. Observability
is the runtime equivalent of test coverage.

### VI. Cost-Conscious AI Usage (NON-NEGOTIABLE)

AI capabilities MUST be delivered through Claude Code (subscription) only.
Programmatic AI SDK / API calls that incur per-token billing are PROHIBITED.

- The Anthropic AI SDK (`anthropic` Python package, `@anthropic-ai/sdk` npm
  package, or any other language SDK) MUST NOT be imported or invoked in
  application or test code.
- No feature MAY make direct HTTP calls to `api.anthropic.com` or any other
  LLM provider API from application code.
- AI-assisted workflows (summarisation, extraction, generation) MUST be
  implemented via Claude Code's interactive or headless CLI interfaces, not
  programmatic API calls.
- If a future need arises that genuinely cannot be met without the SDK, it MUST
  be raised as a governance amendment with a written cost/benefit analysis before
  any code is written.

**Rationale**: Per-token billing accumulates quickly and unpredictably. The
Claude Code subscription provides equivalent capability at a fixed cost. Keeping
AI usage within the subscription boundary makes costs deterministic and avoids
surprise invoices.

## Quality Gates

*All gates MUST pass before any code is merged or a feature is declared complete.*

| Gate | Tool | Threshold |
| ---- | ---- | --------- |
| Tests pass | pytest | 100% pass rate |
| Coverage | pytest-cov | No regression from previous run |
| Linting | ruff | Zero warnings |
| Type check | mypy or pyright | Zero errors on public API |
| Complexity | ruff/mccabe | Cyclomatic complexity ≤ 10 |
| AI SDK usage | grep / CI lint | Zero imports of `anthropic` or `@anthropic-ai/sdk` |

A single command MUST run all gates: `make check` or equivalent.

## Development Workflow

1. **Write tests first** — confirm they fail.
2. **Implement** to make tests pass — minimum viable code only.
3. **Refactor** — simplify, remove duplication, enforce naming clarity.
4. **Run all quality gates** — fix any failures before proceeding.
5. **Update feedback artifact** — note what was learned, what could be better.
6. **Commit** — atomic commits that map to a single logical change.

Pull requests MUST reference the user story they implement and MUST NOT
introduce quality gate regressions. Complexity violations MUST be documented
in the plan's Complexity Tracking table with explicit justification.

## Governance

This constitution supersedes all other coding practices and conventions in this
project. Amendments require:

1. A written rationale explaining why the current principle is insufficient.
2. An updated version number following semantic versioning:
   - MAJOR: principle removed or redefined incompatibly.
   - MINOR: new principle or section added.
   - PATCH: clarification, wording, or non-semantic refinement.
3. All dependent templates MUST be reviewed and updated in the same commit.

All code reviews MUST verify compliance with this constitution. Violations that
are not justified in the Complexity Tracking table are grounds for rejection.

**Version**: 1.1.0 | **Ratified**: 2026-05-27 | **Last Amended**: 2026-05-27
