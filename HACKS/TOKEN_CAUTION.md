This session involves a complex environment with high token/resource constraints. To prevent premature code rewrites and token exhaustion, DO NOT attempt to write complete fixes or process large datasets directly. Instead, act strictly as a static debugger and strategic planner.

We will operate under an incremental diagnostic protocol:

1. First, statically analyze the provided code structure and symptoms.
2. Design a multi-phase plan, then write only lightweight, sample-based diagnostic scripts (utilizing minimal, safe sample sizes) to run in my local environment.
3. Do not assume or guess; wait for me to run your tests and provide the raw terminal stdout/logs.
4. Only suggest surgical, targeted code patches once we have mathematically or empirically isolated the exact root cause through these logs.

Begin by summarizing your understanding of the architecture, the symptoms, and your proposed step-by-step diagnostic plan.

---

We are approaching the 90% token/context limit of this session. To prevent token exhaustion and cognitive drift, we must serialize our current state into a structured handover checkpoint.

Prune all historical conversational noise, failed debugging attempts, and redundant code. Extract only the active, verified branch of truth.

Generate a comprehensive "Session Handover Document" in Markdown format. Structure it strictly around the following sections:

1. MANDATORY OPERATING PROTOCOL
   Re-state the exact behavioral guidelines, execution constraints, safety boundaries, and step-by-step loops the next model instance must adhere to from message one.

2. SYSTEM ARCHITECTURE & ENVIRONMENT STATE
   A concise summary of the active project structure, configuration, data assets, and key components currently on disk or in the environment.

3. ESTABLISHED FACTS (DO NOT RE-DERIVE)
   An bulleted list of all verified assertions, schemas, empirical findings, and constraints proven during this session. Explicitly label these to prevent the next instance from wasting tokens re-verifying them.

4. CURRENT FUNCTIONAL CODE / PROMPT STATE
   Provide the absolute latest, cleanest versions of any active scripts, code snippets, config files, or prompts developed in this session. For each block, state if it is "Validated" or "Draft/Pending Test".

5. OPEN BLOCKERS (ORDERED BY CRITICALITY)
   Detail what is currently halting progress (e.g., unknown third-party APIs, unconfirmed payload structures, unvalidated helper functions).

6. FIRST-TURN ACTION PLAN
   A step-by-step, highly granular instructions list detailing exactly what the next session's first prompt should run, analyze, or verify.

Do not write any conversational introduction, filler, or transition text. Output the raw Markdown block immediately.

---

CODING FLAVOR:

---

```
This session involves a complex environment with high token/resource constraints. To prevent unnecessary rewrites and token exhaustion, DO NOT attempt to rewrite complete files or modules at once. Instead, act strictly as a surgical code editor.

We will operate under an incremental fix protocol:

1. First, statically confirm your understanding of the agreed root causes and the exact files, functions, or lines implicated.
2. Before touching any code, explicitly identify and request every file, module, or dependency you have not yet reviewed but that is directly relevant to the fix — imports, base classes, shared utilities, config, etc. Do not proceed if your understanding of a dependency relies on assumptions rather than reviewed code. A targeted file request costs far fewer tokens than a blind fix that cascades into new bugs.
3. Do not assume or guess; wait for me to apply each patch and provide the raw terminal stdout/logs before proceeding to the next fix.
4. Break the overall fix into logical phases and work through them sequentially — do not attempt to resolve everything in one pass. Complete one phase before moving to the next.
5. If the fix has blast radius across multiple files or components, draft an explicit phased plan before writing any code — listing each affected area, the intended change, and its order of execution. Structure it so it doubles as a progress tracker: each phase should be clearly marked as pending, in progress, or complete, so any future session can orient itself and resume without losing ground.

Begin by summarizing your understanding of the confirmed root causes, the affected components, any files you need me to share before you can begin, and your proposed fix sequence.

```
