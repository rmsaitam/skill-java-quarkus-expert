---
description: Validate a JAVA-QUARKUS-IMPL.md artifact against the implementation report contract.
argument-hint: "[path/to/JAVA-QUARKUS-IMPL.md]"
---

# Validate Java Quarkus Report

Validate an existing `JAVA-QUARKUS-IMPL.md` produced by the `java-quarkus` skill.

## Instructions

- Default to `JAVA-QUARKUS-IMPL.md` at the repository root when no path is provided.
- Run:

  ```bash
  python3 scripts/validate_report.py JAVA-QUARKUS-IMPL.md
  ```

  From the plugin repository root, prefix the script path with `skills/java-quarkus/`.

- Use `--strict` to treat warnings as failures, `--json` for machine-readable output and `--min-coverage N` to change the default 80% gate.
- Do not modify the report unless the user explicitly asks for fixes. If fixes are requested, preserve the artifact markers and re-run the validator.
