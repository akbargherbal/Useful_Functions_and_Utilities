# Phased Plan Template for LLM Development Projects
**Version:** 2.0

> **For the plan-writing LLM:** This document defines both the *philosophy* behind a robust Phased Plan and the *exact template* you must follow when generating one. Read Part A to understand the "why", then use Part B as your fill-in scaffold. Replace every `[PLACEHOLDER]` with project-specific content. Do not remove any section — write `N/A — [reason]` if a section genuinely does not apply.

---

## PART A: Principles

### Why a Phased Plan Is Not a Task List

Standard task lists fail in multi-session LLM development for three compounding reasons:

- **Context loss** — the next LLM has no memory of decisions already made; it will re-litigate, revert, or invent from scratch.
- **Scope creep** — LLMs default to "helpfully" refactoring adjacent code, renaming things, and scaffolding toward imagined future features.
- **Hallucination compounds** — an LLM that cannot verify its environment will invent answers and proceed confidently into broken states.

A Phased Plan is a **strict state machine**: it defines legal states, legal transitions, and what happens when something goes wrong. Every section exists to constrain one of the above failure modes.

---

### The Six Core Principles

**1. Compliance Over Creativity**
When *executing* a Phased Plan, the LLM follows the plan — it does not improve it. If the plan appears wrong, the LLM must STOP and flag it, not silently correct it.

**2. Risk-First Ordering**
Phase 1, Task 1 must address the highest-risk technical unknown (the "contract test"). No UI, no scaffolding, no boilerplate — until the core assumption is proven to work in isolation.

**3. Minimum Viable Change**
Every task defines the smallest change that proves the task complete. The LLM must not touch code outside the defined scope, even if adjacent code "looks broken."

**4. Observable Proof**
Every task must have a binary, observable success criterion. *"It works"* is not valid. *"Console prints `[AuthService] Token verified`"* or *"File size is unchanged"* is valid.

**5. Hard Gates**
If a pre-coding check fails, or a stop condition is triggered, the LLM halts and reports to the human. It does not retry indefinitely, invent workarounds, or proceed.

**6. Phase Sizing**
Each phase must fit within one focused session of work — a maximum of **6 tasks**. If a phase exceeds 6 tasks, split it into two phases. Overfull phases are the primary cause of context loss mid-phase.

---

### The ZAP Protocol

If an LLM begins a session and **neither a Phased Plan nor a Session Handover document is attached**, it must immediately invoke ZAP before doing anything else:

> **ZAP:** *"I don't have the Phased Plan or Session Handover for this project. Please attach both before I proceed. I will not make assumptions about project state, file structure, or prior decisions."*

ZAP is non-negotiable. An LLM that proceeds without these documents will diverge from project intent within one or two turns.

---

### Blast Radius

Every task must carry a **blast radius** tag — the scope of damage if the task goes wrong:

| Tag | Meaning |
|---|---|
| **LOW** | Change is isolated to one function or file; trivially reversible with a one-line revert. |
| **MEDIUM** | Change affects one module or integration point; rollback requires 2–3 steps. |
| **HIGH** | Change affects shared state, the database, core routing, or authentication. **Human must approve before execution.** |

A HIGH blast radius task must appear in the Human Checkpoints table (Section 7) and must have an explicit rollback command.

---

### What Good vs. Bad Task Definitions Look Like

**BAD — too vague:**
> "Add error handling to the API calls."

Fails because: which calls? what errors? where do errors surface? The LLM will invent answers and proceed.

**GOOD — hyper-specific:**
> "In `src/api/fetchUser.ts`, wrap the `axios.get()` call on line 42 in a `try/catch` block. The `catch` must log `[fetchUser ERROR] ${error.message}` to the console and `return null`. Do not modify the function signature, the return type, or any callers."

Works because: file, function, line, exact behaviour, and what not to touch are all explicit.

**The test for a good task:** could two different LLMs read this task and independently produce identical diffs? If not, it needs more specificity.

---

## PART B: The Template

> Everything below this line is the template. Copy it in full when generating a Phased Plan for a project. Populate every `[PLACEHOLDER]`.

---

# [PROJECT NAME] — Phased Implementation Plan

**Version:** [v1.0]
**Created:** [DATE]
**Author:** [LLM or human who wrote this plan]
**Status:** [Phase N of M — Active / Complete / Blocked]

---

## 0. How to Read This Plan

You are an LLM reading this document for the first time. Before touching anything:

1. Read this entire document.
2. Read the latest `Session_N_Handover.md` if one exists.
3. Run the Pre-Coding Checklist (Section 3). If any check fails, stop.
4. Execute tasks in the exact order written. No skipping, no reordering.
5. If you are unsure whether an action is in scope: it is out of scope.
6. If a STOP condition is met, halt immediately and output your reason.

---

## 1. Executive Summary

**Current State:**
[One sentence. What exists right now — e.g., "A working Express API with no authentication layer."]

**Goal of This Plan:**
[One sentence. What will exist when every phase is complete — e.g., "JWT-based authentication integrated into all protected routes."]

**What This Plan Does Not Do:**
[One sentence. The hardest boundary — e.g., "This plan does not implement role-based permissions or a refresh token flow."]

---

## 2. Locked Decisions

> These choices are **closed for debate**. Do not re-litigate, revert, suggest alternatives, or scaffold toward something different. If you believe a locked decision is incorrect, STOP and flag it — do not silently work around it.

| Decision | Choice Made | Rationale | Locked Since |
|---|---|---|---|
| [e.g., State management library] | [e.g., Zustand] | [e.g., Already in bundle; team familiar] | [Session 1 / Phase N] |
| [e.g., Database] | [e.g., PostgreSQL, not SQLite] | [e.g., Production parity required] | [Session 1] |
| [Add rows as needed] | | | |

---

## 3. Pre-Coding Checklist

> Run every check before writing any code. If any check fails, do **not** proceed. Output: `"PRE-CHECK FAILED: [check name] — [what you found]. Awaiting instructions."`

- [ ] **Environment healthy:** `[command — e.g., npm run dev]` starts without errors. Expected output: `[e.g., "Server running on port 3000"]`
- [ ] **Test suite green:** `[test command — e.g., npm test]` passes. If any test is red, STOP.
- [ ] **Key file exists:** `[file path]` exists and contains `[expected function / class / export]`.
- [ ] **Dependency available:** `[package or service name]` is installed at version `[version constraint]`.
- [ ] **[Project-specific check]:** `[command]` → Expected: `[result]`

**Hard Gate:** Do not begin Phase 1 if any pre-coding check fails.

---

## 4. Phases

---

### Phase 1: [Name — e.g., "Contract Test: Prove Core Integration"]

> **Purpose:** This phase must isolate and prove the highest-risk technical assumption before any surrounding code is built. If Phase 1 fails, the architecture may need to be reconsidered. This is intentional.

**Goal:** [One sentence — what does this phase prove? e.g., "Prove that the third-party payment API accepts our payload format and returns a parseable response."]
**Entry Condition:** Pre-coding checklist is fully green.
**Exit Condition:** [Observable state that proves this phase is complete — e.g., "Task 1.2 success criteria are met and test suite remains green."]

---

#### Task 1.1: [Task Name]

**Blast Radius:** LOW / MEDIUM / HIGH
**Depends On:** None (first task)
**File(s):** `[exact file path — e.g., src/services/paymentService.ts]`
**Location:** `[function name, class, or line range — e.g., "the makeCharge() function, lines 34–67"]`

**What to do:**
[Step-by-step, specific instructions. Name exact variables, function signatures, and line numbers where possible. Write at the level where two different LLMs would produce identical diffs.]

**Minimum Change Rule:**
[e.g., "Add exactly one `try/catch` block. Do not rename the function, modify its signature, or touch the caller in `index.ts`."]

**⚠ Dangerous Zone:**
[If applicable — e.g., "The `onSuccess` callback on line 58 must fire before the `logEvent` call on line 61. Do not reorder." / Delete this line if not applicable.]

**Success Criteria:**
- [ ] [Observable proof — e.g., "Running `node test-charge.js` logs: `[PaymentService] Charge accepted: txn_abc123`"]
- [ ] [Second proof if needed — e.g., "The `charges` table in the database contains one new row"]
- [ ] [Negative check — e.g., "`/api/payment` does not trigger a second network request in the Network tab"]

**Rollback:**
`[Exact revert command or instruction — e.g., "git checkout src/services/paymentService.ts"]`

---

#### Task 1.2: [Task Name]

> *Depends on Task 1.1 passing its success criteria.*

**Blast Radius:** LOW / MEDIUM / HIGH
**Depends On:** Task 1.1
**File(s):** `[file path]`
**Location:** `[function or line range]`

**What to do:**
[Instructions]

**Minimum Change Rule:**
[Constraint]

**⚠ Dangerous Zone:**
[Warning or delete]

**Success Criteria:**
- [ ] [Proof]
- [ ] [Negative check]

**Rollback:**
`[Revert command]`

---

### Phase 2: [Name]

> **Hard Gate:** Do not begin Phase 2 until Phase 1's exit condition is confirmed and the test suite is green.

**Goal:** [One sentence]
**Entry Condition:** Phase 1 exit condition met; test suite green.
**Exit Condition:** [Observable state]

---

#### Task 2.1: [Task Name]

**Blast Radius:** LOW / MEDIUM / HIGH
**Depends On:** Phase 1 complete
**File(s):** `[file path]`
**Location:** `[function or line range]`

**What to do:**
[Instructions]

**Minimum Change Rule:**
[Constraint]

**⚠ Dangerous Zone:**
[Warning or delete]

**Success Criteria:**
- [ ] [Proof]

**Rollback:**
`[Revert command]`

---

*[Repeat Phase and Task blocks as needed. Maximum 6 tasks per phase.]*

---

## 5. Scope Boundaries

### In Scope
[Bullet list of exactly what this plan builds — be specific]

- [Feature or change 1]
- [Feature or change 2]

### Out of Scope

> The following are **explicitly forbidden** in this plan. Do not implement. Do not scaffold toward. Do not leave `TODO` comments for. If you find yourself thinking "I'll just stub this out for later" — stop. That is out of scope.

- [Related feature that is tempting but deferred — e.g., "Refresh token rotation"]
- [UI polish deferred — e.g., "Error message styling and toast notifications"]
- [Future architecture — e.g., "Microservice extraction of the auth module"]
- [Add as many as needed to close obvious escape hatches]

---

## 6. Stop Conditions

> If any of the following occur, **halt all coding immediately**. Do not attempt fixes. Do not retry more than twice. Output:
> `"STOP — [condition name] — [what you observed] — Awaiting human input."`

| Trigger | Max Retries | Required Action |
|---|---|---|
| Test suite turns red | 0 | STOP. Report which tests failed and the last change made. |
| Any external API returns 5xx | 2 | STOP. Log full response body. |
| A required file or function is missing | 0 | STOP. Do not create it speculatively. |
| Any HIGH blast radius task fails | 0 | STOP. Execute its rollback. Report state. |
| Pre-coding check fails mid-session | 0 | STOP. Something changed unexpectedly. |
| [Project-specific trigger] | [N] | [Action] |

---

## 7. Human Checkpoints

> These are moments requiring **explicit human approval** before the LLM continues. The LLM must output: `"CHECKPOINT — [reason] — Please review and reply 'proceed' to continue."` and then wait.

| Moment | Reason | What the Human Must Do |
|---|---|---|
| After Phase 1 completes | [e.g., "Confirms core contract before building on it"] | Run smoke test; reply "proceed" |
| Before Task [N.M] (HIGH blast radius) | [e.g., "Modifies shared auth middleware"] | Review the proposed diff; reply "proceed" |
| [Any other moment requiring human eyes] | [Reason] | [Action] |

---

## 8. Session Handover Protocol

At the end of **every** session — including sessions that ended early or were abandoned mid-phase — the LLM must generate a `Session_N_Handover.md` file. N increments per session, not per phase. Multiple sessions may cover the same phase.

**Rules:**
- One page maximum. Cut prose, not coverage.
- Write as if handing off to someone who has never seen the project, but who has access to this Phased Plan.
- The incoming LLM for the next session must read the latest handover **and** this Phased Plan before doing anything else. If neither is attached, invoke ZAP.
- Keep all handover files in the project root.

### Handover File Template

> Save as `Session_[N]_Handover.md` in the project root.

```markdown
# Session [N] Handover

**Date:** [DATE]
**Phase Active:** Phase [N] — last completed task: [Task N.M name]
**Overall Status:** On Track / Blocked / Phase Complete / Plan Needs Revision

---

## What We Did
[Bullet list: tasks completed, key decisions made during the session, any deviations from the plan and why]

---

## Artefacts Produced / Modified

| File | Change Made | Role |
|---|---|---|
| `path/to/file.ts` | [e.g., Added `validateToken()` function] | [e.g., Validates JWT on protected routes] |

---

## Key Numbers

| Metric | Value |
|---|---|
| Tasks completed this session | [N of M planned] |
| Tests passing | [N / M total] |
| [Project-specific metric — e.g., API calls made] | [Value] |

---

## Current Project State
[One sentence per active script/service: what state it is in, last confirmed working behaviour]

---

## Next Session — First Actions
1. Run: `[first verification command]` → Expected: `[result]`
2. Begin: Task [N.M] — [Task Name]
3. [Any other prep steps before coding starts]

---

## Known Issues / Watch Points
- [Anything fragile, deferred, or only partially working]
- [Any decision that felt uncertain and may need revisiting]
- [Any asymmetry between environments — e.g., "works locally, untested on staging"]
```

---

## 9. Glossary

> Optional but recommended. Define project-specific terms, abbreviations, or system names that an incoming LLM must understand to read this plan correctly.

| Term | Definition |
|---|---|
| [e.g., "The Core Contract"] | [e.g., "The assumption that Service A can POST to Service B's `/ingest` endpoint and receive a 200 with a valid `job_id`"] |
| [Term] | [Definition] |

---

## Summary for the Executing LLM

Your role when executing this plan is **compliance, not creativity**:

- Follow the task order strictly. Validate assumptions before writing code.
- Respect the out-of-scope list — if it's not explicitly in scope, don't touch it.
- Halt immediately on any Stop Condition and report your state.
- Pause at every Human Checkpoint and wait for explicit approval.
- Produce a Session Handover at the end of every session, even if work is incomplete.

When in doubt: do less, report more.
