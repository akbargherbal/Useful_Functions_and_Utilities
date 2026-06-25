**IMPORTANT NOTES & WORKSPACE INVARIANTS:**

- **Zero-Assumption Protocol (ZAP) & Scope Gate**: 
  1. **Inventory**: Access the workspace environment directly to inventory all attached files. List your active files before starting.
  2. **Boundary Enforcement**: If any task in `<plan_document>` requires, references, or structurally implies changes to a module or file not currently in your active workspace (e.g., an unattached architectural orchestrator or config file), **STOP immediately**.
  3. **No Speculative Bypass**: Do not attempt to design workarounds, local overrides, or "graceful degradation" logic in active files to compensate for a missing dependency. 
  4. **Halt and Request**: Flag the missing file as a blocking dependency and request it from the user.
- **Diligence & Regression Control**: Cross-reference `<plan_document>` instructions against the actual code on disk to perform a sanity check before executing edits. Do not assume the plan's assumptions are correct if they mismatch the live codebase.
- **Phase-Gate Protocol**: Pause and present your changes at the end of the current phase. Await explicit user verification and instructions before proceeding to the next phase.