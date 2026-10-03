# Agent instructions

## Repository

This repository contains Python and shell utilities for reading data from a HAN interface, controlling GPIO, managing services, and working with sensor data. Keep changes focused and preserve existing behavior and deployment assumptions unless the task calls for changing them.

## Working rules

- Never create commits or push changes automatically. Commit or push only when the user explicitly asks you to do so.
- Before editing, inspect the relevant script and its callers or service setup so changes fit the existing flow.
- Avoid exposing credentials or overwriting user configuration. Treat configuration and data files as potentially machine-specific.
- Keep shell scripts compatible with the target system and Python code compatible with the version used by the project; check nearby documentation and deployment files before changing runtime assumptions.
- Report the files changed and any checks performed. Run checks appropriate to the task when requested or useful, and state clearly when hardware-dependent behavior could not be exercised.
