**After the script finishes, add a graceful auto-disconnect block.**
Context: this script runs in a Google Colab terminal (not a notebook cell),
which means it runs in a containerized Linux environment.
The block should wait a grace period, then programmatically terminate the runtime.
Handle both clean exits and crashes.
Hints: think about how containerized environments handle PID 1,
or how Python can send OS-level signals,
or how a bash wrapper could handle this outside the script entirely.
