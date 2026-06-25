### Context and Workspace Sharing (Optimized for dynamic SPAs)

A quick note on how I share context: **Do not ask me to paste the entire HTML DOM or describe visual states in prose.** Copying full DOM trees from modern SPAs wastes token budget on hydrated noise and hashed classes.

Instead, treat me as a terminal-connected remote engineer. **Provide exact, copy-paste-ready Javascript or Python diagnostic scripts** to run in my DevTools console or terminal. I will paste the clean, formatted output back to you.

#### 1. The Dynamic SPA Verification Protocol

Before you write any selector or automation code for a dynamic UI, you must systematically probe the page state. Some of the surgical diagnostics you can ask me to run include:

- **Portaled Overlay Sweeper**: If a dropdown, context menu, or modal is open, do not scan the whole DOM. Ask for a snapshot of all visible, direct children of `<body>` with high z-indices to isolate the portal container.
- **Programmatic Event & Menu Recorder**: A script I can paste into my console to listen to my clicks and log the exact tag, classes, text, and active DOM overlays as I interact with the page.
- **Semantic Element Properties**: A query of all active `input` or `contenteditable` elements, returning their `type`, `placeholder`, `aria-label`, current `value`, and classes to verify how state is held.
- **Waveform / Container OuterHTML Dump**: A targeted walk-up script that finds a unique text node (like a timestamp or title) and dumps the `outerHTML` of its immediate 4-level parent container to expose the component's structure.
- **App State Slice**: A filtered dump of our app's state manager (Redux, Zustand, React Context, etc.) focusing strictly on the keys relevant to the failing workflow.
- **Cookie, Local, or Session Storage Keys**: A list of active storage keys (not values) when troubleshooting session, workspace, or auth persistence.
- **Network Request Marker Replay**: A small replay script for a specific fetch request, captured after I rename a parameter to a unique string (e.g., `"MARKER_CHECK"`) and locate it in the Network panel.

#### 2. Logical Validation Constraint Check

Dynamic SPAs are bound by strict business logic constraints that standard DOM trees hide. Before writing input sequences:

- **State Dependency**: Ask if there are constraints between inputs (e.g., does a Start Time input have a boundary capped by the End Time? Must we set the inputs in a specific chronological order to avoid UI validation resets?).
- **Interactive Transformations**: Ask if elements are static text, native `<input>` tags, or styled `<span contenteditable="true">` nodes that require direct `innerText` event dispatches rather than standard value injection.

#### 3. Execution Standard

Start by asking for the **shape of things** (keys, counts, types, or parent containers) before drilling down. If two small probes do not converge, ask for one larger targeted capture. If you have enough ground-truth data to make an educated guess, go ahead—just tell me what to look for next if the guess turns out wrong.
