# The Anatomy of a Robust Phased Implementation Plan

**Purpose:** To serve as a deterministic blueprint for multi-session, multi-agent LLM development.

Because LLMs lose context between sessions, suffer from scope creep, and often attempt to silently refactor adjacent code, a standard task list is insufficient. A robust Phased Plan acts as a strict state machine, an emergency brake, and a memory bridge. It ensures that any LLM, dropping into any phase of the project, knows exactly what is locked, what to do, how to prove it works, and when to stop.

Based on successful multi-session architectures, every good Phased Plan must contain the following core elements:

### 1. Executive Summary & Locked Decisions

The plan must immediately ground the LLM in the current reality of the project.

- **Current State vs. Goal:** A binary statement of what exists right now versus what this specific plan will achieve.
- **Locked Decisions:** A table of architectural choices, previous findings, or parameters that are **closed for debate**. This prevents a new LLM from re-litigating past decisions, hallucinating new architectures, or reverting to default behaviors.

### 2. Pre-Coding Checklists & Baseline Assumptions

LLMs often assume the environment is ready and write code blindly. A good plan forces validation first.

- **Environment Baselines:** Explicit commands to run before touching code (e.g., "Ensure test suite is green," "Verify server is healthy").
- **Assumption Checks:** Verifying that expected variables, functions, or files actually exist in the current codebase before attempting to modify them.
- **Hard Gates:** A strict rule: _Do not proceed to Phase 1 if the pre-coding checklist fails._

### 3. Risk-First, Strictly Ordered Phasing

Phases must not be arbitrary groupings of tasks; they must be ordered by architectural risk.

- **Isolate the Unknowns:** The highest-risk technical assumption (the "core contract") must be proven in Phase 1, Task 1, in isolation, before any surrounding UI or scaffolding is built.
- **Sequential Execution:** Tasks must explicitly state if they are dependent on the previous task.
- **Shippable Increments:** Every phase boundary must result in a working, verifiable state.

### 4. Hyper-Specific Task Definitions

LLMs are prone to "helpful" over-engineering. Tasks must be defined with extreme precision to constrain the LLM's output.

- **Exact Locations:** State the exact file, and often the exact function or line block, where the change will occur.
- **Minimum Change Rule:** Explicitly forbid adjacent refactoring. If a task requires adding one line, the plan must state: "Add exactly one line. Do not touch surrounding logic."
- **Dangerous Zones:** Identify highly sensitive files or functions and explicitly warn the LLM to maintain specific invariants (e.g., "Function X must still fire before Function Y").

### 5. Verifiable Success Criteria

An LLM cannot "feel" if a feature works; it needs binary, observable tests.

- **Observable Proof:** Define exactly what the user or developer should see, hear, or log to prove the task succeeded (e.g., "Console logs X," "Network tab shows Y," "File size remains identical").
- **Negative Checks:** Explicitly list what should _not_ happen (e.g., "Action X does not trigger a network request").

### 6. Stop Conditions & Rollback Plans (The Emergency Brakes)

This is the most critical component for autonomous or semi-autonomous LLM coding. It prevents the LLM from spiraling into endless debugging loops.

- **Explicit Stop Conditions:** A clear list of triggers that require the LLM to halt all coding and ask the human for help (e.g., "STOP if tests turn red," "STOP if the API returns a 500 error after two attempts").
- **Rollback Plans:** For every high-risk task, define exactly how to revert the codebase to a safe state if the implementation fails.

### 7. Strict Scope Boundaries

To prevent hallucination and scope creep, the plan must define what is _not_ happening.

- **In Scope:** What is being built today.
- **Out of Scope:** Explicitly list related features, UI polish, or future architecture that the LLM might be tempted to build or "scaffold toward." Instruct the LLM: _Do not implement, do not scaffold._

### 8. The Session Handover Protocol

Because the LLM will eventually hit a context limit or the user will end the session, the plan must define how to save state.

- **Standardized Output:** Require the LLM to generate a `Session_Handover.md` document at the end of every session.
1. **What we did** — tasks completed, files changed, key decisions made
2. **Artefacts produced** — table of new/modified files and their role
3. **Key numbers** — inference call counts, OOM events, track counts processed, scored, failed
4. **Current project state** — which phase is active, what is the last confirmed working state of each script
5. **Next session work items** — ordered list, first command to run
6. **Known issues / watch points** — anything fragile, deferred, or asymmetric

**Rules:**

- One page. If it runs longer, cut prose, not coverage.
- Produce the handover even if the session ended early or a phase was abandoned mid-way — document what was attempted and what state the codebase is in.
- The handover replaces memory. Write it as if handing off to someone who has never seen the project — but who has access to the `CLIENT_BRIEF.md` and the phased plan.
- File naming: `Session_N_Handover.md` where N increments per session, not per phase. Multiple sessions may cover the same phase.
- Keep all handover files in the project root alongside the source files.
- The incoming LLM for the next session must read the latest `Session_N_Handover.md` and the phased plan before doing anything else. If neither is attached, invoke ZAP: ask for them explicitly before proceeding.

---

### Summary for the LLM:

When executing a project based on a Phased Plan, your job is **compliance, not creativity**. Follow the task order strictly, validate your assumptions before writing code, respect the out-of-scope boundaries, and halt immediately if a Stop Condition is met.
