---
description: Implement Java and Quarkus changes using the detected project versions, official guides, codebase conventions, and JUnit 5 plus Mockito unit tests.
argument-hint: "[--project-root PATH] [--scope DESCRIPTION] [--output PATH]"
---

# Java Quarkus

Invoke the `java-quarkus` skill. The skill must first detect the stack; it must not suggest dependencies, annotations or code before that gate is complete.

## Instructions

- Run `python3 scripts/detect_stack.py <project-root> --output stack.json` from the installed skill directory as the first action. From the plugin repository root, use `python3 skills/java-quarkus/scripts/detect_stack.py <project-root> --output stack.json`. If there is no `pom.xml`, `build.gradle` or `build.gradle.kts`, stop and ask for the build descriptor or the exact Java and Quarkus versions.
- Use `jakarta.*` for Quarkus 3+ and `javax.*` only when Quarkus 2.x is explicitly detected.
- Follow the existing package layout, naming, DTO mapping, error handling and test style. Do not introduce a new library or architecture without an explicit need.
- Prefer constructor injection and the correct CDI scope. Put `@Transactional` in the service or use-case layer, never in the REST controller.
- Respect the execution model: never block a Vert.x event loop; use `@Blocking` for blocking work or return `Uni<T>` / `Multi<T>` for non-blocking flows.
- Write isolated JUnit 5 plus Mockito unit tests without starting Quarkus. Use `@QuarkusTest`, REST Assured and Dev Services only for integration tests.
- Enforce at least 80% coverage with JaCoCo and record the exact commands and measured result.
- Write only `JAVA-QUARKUS-IMPL.md` at the repository root unless the user supplies another path.
- Before finishing, run:

  ```bash
  python3 scripts/validate_report.py JAVA-QUARKUS-IMPL.md
  ```

  From the plugin repository root, prefix the script path with `skills/java-quarkus/`.

- Report the artifact path, detected Java and Quarkus versions, main changes, test commands, measured coverage and remaining risks.
