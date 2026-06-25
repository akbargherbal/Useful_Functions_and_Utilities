## 8. Phased Planning Protocol

Every bug fix and feature — however small — must be preceded by a written
Phased Plan. This section defines what a valid plan looks like, when one is
required, and how it relates to the session handover cycle.

The protocol is intentionally project-agnostic. It can be applied verbatim to
any software project.

---

### 8.1 When a Plan Is Required

A Phased Plan is required before any session that will:

- Change a dangerous-zone file or function (as designated in the project's
  equivalent of §2)
- Add a new feature at any scale
- Fix a bug that touches more than one function
- Modify an invariant, a module boundary, or a data schema

A plan is **not** required for:

- Documentation-only sessions (comments, README, handover files)
- A single-line fix to a non-dangerous-zone file where the change and its
  complete verification are both trivially self-evident

When in doubt, write a plan. A short plan costs less than an unplanned
regression.

---

### 8.2 Plan Header

Every plan must open with a locked header:

```
Plan version:           N.M
Based on:               [source documents reviewed before writing this plan]
Current codebase state: [last known-good milestone]
Source files reviewed:  [every source file read before writing the plan]
```

`Source files reviewed` is not optional. A plan written without reading the
relevant source files is not a valid plan. If a required source file is missing,
apply the Zero-Assumption Protocol — ask for it before writing the plan.

---

### 8.3 Required Sections

Every plan must contain the following sections in order. Sections may be brief;
they may not be omitted.

**Executive Summary** — four bullets, maximum:

- _Current state_ — what the system does today in the area being changed
- _Goal_ — what the change accomplishes (one sentence)
- _Key architectural constraint_ — the most important invariant or rule that
  governs the approach
- _Estimated time_ — honest range including verification time, not just
  implementation time

**Locked Decisions** — a table of design choices that are closed before coding
begins. Format: `# | Decision | Resolution | Rationale (optional)`. Decisions
carried from a prior session appear here with a "Carried from Session N —
closed" note. A locked decision cannot be re-opened without a plan version bump.
The purpose of this section is to prevent the session from relitigating settled
questions. If a decision is not in this table, it is open and must be resolved
before coding begins.

**Assumptions to Validate Before Starting** — a numbered list of things that
must be true in the live environment before any file is touched. Each item must
include a concrete verification step: a console command, a test run, or a named
manual check. If any assumption cannot be verified, the session stops.

**Pre-Coding Checklist** — a checkbox list derived directly from the assumptions
above. This is the final gate before the first file is opened for editing. No
task begins until every box is ticked.

**Phases and Tasks** — see §8.4 and §8.5.

**Decision Tree and Stop Conditions** — see §8.6.

**Known Risks** — a table: `Risk | Likelihood | Impact | Mitigation`. Document
risks even when their likelihood is "None" — explaining why a risk does not
apply is as valuable as the mitigation itself.

**Scope Boundaries** — two explicit lists: **In Scope** (✅) and **Out of
Scope** (❌). Both lists must be populated. Naming out-of-scope items is as
important as naming in-scope ones: an item not in the ❌ list cannot be ruled
out by a later session.

**ZAP — Files Still Needed** — a table of files required to complete tasks in
this plan that have not yet been attached. Any phase whose tasks depend on a
missing file is blocked until the file is provided.

---

### 8.4 Phase and Task Structure

A plan is divided into numbered phases. Each phase has a single, sentence-length
goal. Phases are sequenced so that earlier phases prove the foundations that
later phases depend on.

**Phase structure:**

| Element            | Requirement                                                                     |
| ------------------ | ------------------------------------------------------------------------------- |
| Goal               | One sentence                                                                    |
| Task Ordering Note | Which tasks must be done in sequence and why (gate conditions within the phase) |
| Tasks              | Numbered as phase.task: 1.1, 1.2 … 2.1, 2.2 …                                   |
| Success Criteria   | The conditions under which the phase is complete                                |
| Deliverables       | A checkbox list of files changed or created                                     |
| Rollback Plan      | What to revert and how if the phase is abandoned                                |

**Ordering principle:** Prove isolated components first; wire them into
dangerous zones last. The highest-risk change in a phase is always the _last_
task, not the first. An additive task (adding a new function) must precede the
integrative task that calls it from a dangerous-zone function. Do not proceed
to task N+1 until task N is verified.

---

### 8.5 Task Entry Requirements

Every task entry must contain all six of the following. Omitting any one of them
is a planning defect.

1. **Ownership declaration** — the exact file and function being changed.
   Confirm it is the correct owner of the concern per the module ownership table.
   Do not split a concern across tasks or modules to make a change fit.

2. **Dangerous zone flag** — an explicit ⚠ warning if the file or function is
   designated as dangerous. Reference the specific rule by number.

3. **Time estimate** — an honest range that includes verification time, not
   just implementation time.

4. **Minimum change description** — what is added or changed, stated precisely
   enough that it could be implemented without the session transcript. For code
   changes: show the before-state and after-state of the target block, not just
   a narrative description. The word "minimal" is not ornamental: do not propose
   a change larger than the problem requires.

5. **Invariant checkpoint** — for each invariant in the project rules that the
   change could plausibly affect, state the invariant by name and confirm it is
   preserved (✓), or explain why it is not triggered. Do not skip this for
   "simple" changes — simple changes are where invariant violations go
   undetected.

6. **Verification steps** — a numbered list of manual checks or automated tests
   that confirm the task is complete and has not regressed anything. Each step
   states the action and the expected result. Cover both the happy path and at
   least the most relevant failure path. "pytest green" is always one of the
   steps if a test suite exists.

---

### 8.6 Stop Conditions and Revert Protocol

A stop condition is a trigger, not a guideline. When one fires, the session
reverts the relevant task immediately and documents the result in the handover.
Stop conditions are never argued away in the session — if the condition was
wrong, fix the plan in the next session.

**Universal stop conditions** (apply to every plan regardless of domain):

- The test suite, if green before the session, turns red at any point
- Any invariant named in the project rules is violated by a change, even
  transiently
- An unexpected side effect is observed and its cause cannot be immediately
  identified

**Plan-specific stop conditions** are listed in each plan's Decision Tree
section. They must cover, at minimum: cases where a write fires unexpectedly,
an ordering invariant is violated, or a sole-call-site constraint gains a second
call site.

**Decision Tree format** — every plan must include an ASCII flowchart:

```
START → PRE-CODING CHECKLIST
  ├─ [gate fails]   → STOP: [reason and action]
  └─ [all pass]     → PHASE 1
PHASE 1
  ├─ [check fails]  → REVERT task N; [action]
  └─ [all pass]     → PHASE 2
...
```

The flowchart is followed by a prose "STOP immediately if:" list. Each entry
is a single observable condition, not a category.

**Rollback plan** — every phase must describe exactly which lines to revert
and confirm what state the codebase returns to after the revert. "Revert the
file" is not a rollback plan. "Remove the added block (lines X–Y); no other
file is affected; the function returns to the state it was in before task N.M"
is a rollback plan.

---

### 8.7 Plan–Handover Relationship

The plan and the session handover are a closed loop. Neither replaces the other.

- The **plan** is written before coding begins. It is the source of truth for
  what the session intends to do.
- The **handover** is written after coding ends. It records what actually
  happened: which lines changed, which verification steps passed, which stop
  conditions fired, and what remains open.
- The **next session** reads both — the plan (intent) and the handover (current
  state) — before doing anything. If either is missing, apply the
  Zero-Assumption Protocol and ask for it explicitly.

A plan is not invalidated by the session that executes it. If the session
diverges from the plan — because a stop condition fired, a phase was abandoned,
or new information changed the approach — the divergence is recorded in the
handover and the plan is updated with a version bump before the next session
begins.

The plan version must appear in the handover's Artefacts table.

---

### 8.8 Scope Rules

- **One session, one plan domain.** A session executing a plan must not
  simultaneously make changes outside the plan's scope, however small (§7.4).
  If an adjacent issue is discovered, document it in the handover and address
  it in a separate session with its own plan.
- **No scaffolding toward out-of-scope items.** A task must not introduce code,
  interfaces, or data structures whose only purpose is to support a feature that
  is explicitly out of scope. Out-of-scope items belong in a future plan.
- **Version bump on scope change.** If the scope of a plan changes after it is
  written — even by a single task — the plan version increments (1.0 → 1.1)
  and the change is noted in the plan header.
