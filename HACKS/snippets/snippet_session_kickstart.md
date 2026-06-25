This is [Session N] of our development workflow. Please review the latest handover document and the current [Fix Plan] in the attachments.

Before drafting any code or performing deep calculations, execute the generalized Zero-Assumption Protocol (ZAP):
1. **Physical Inventory**: Inspect the active workspace directory on your disk directly and list the exact files you have access to.
2. **Dependency Mapping**: Cross-reference the targeted tasks in the current phase against your inventory. Identify if any active tasks imply modifications to files that are currently missing from your workspace.
3. **Blocker Evaluation**: If a missing file is required to complete the task safely without regressions, flag it immediately. Do not attempt code workarounds.

Provide your workspace inventory and state whether the active phase tasks are **blocked** (due to missing files) or **ready** to proceed.