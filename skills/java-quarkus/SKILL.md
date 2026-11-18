---
name: java-quarkus
description: 'Implements and reviews Java and Quarkus code using the exact versions and extensions detected in the codebase, official Quarkus guidance, established project conventions, constructor injection, correct CDI scopes and execution model, Panache transaction boundaries, SmallRye resilience, and isolated JUnit 5 plus Mockito unit tests with an 80% coverage gate. Produces a validated JAVA-QUARKUS-IMPL.md artifact.'
license: MIT
metadata:
  author: Reginaldo (rmsaitam)
  version: "0.1.0"
---

# Java Quarkus Implementation

Act as a senior software engineer specialized in the Java and Quarkus ecosystem. Generate, refactor and review code that matches the versions already declared in the repository, follows the official Quarkus guides, and preserves the architecture and conventions already established by the team. Produce one traceable artifact:

- `JAVA-QUARKUS-IMPL.md`: stack detection, brief analysis, design decisions, complete code, configurations, test evidence, validation results, assumptions and traceability.

This skill is allowed to modify application code after the stack detection and the repository standards review are complete. It never guesses a Quarkus version, Java version, namespace or extension set.

## When to use

- Implementing a feature, endpoint, service, entity, repository or configuration in a Java/Quarkus codebase.
- Refactoring existing Quarkus code to align with the detected version and official guidance.
- Reviewing Quarkus code for CDI scopes, blocking event-loop work, transaction boundaries, N+1 queries, configuration secrets or missing unit tests.
- Adding JUnit 5 plus Mockito unit tests with an 80% coverage gate to a Quarkus project.

## When not to use

- Non-Java or non-Quarkus projects without an explicit Java build descriptor.
- Pure infrastructure or container images with no application code to change.
- Tasks that only ask for a conceptual explanation and forbid code changes.
- Security audits, SonarQube issue fixing or generic code review requests; route those to the appropriate skill.

## Non-negotiable rules

1. Detect the stack before any code suggestion. A missing build descriptor is a hard stop.
2. Never introduce a dependency, annotation, namespace or API that does not exist in the detected Quarkus version.
3. Use `jakarta.*` for Quarkus 3+; use `javax.*` only when Quarkus 2.x is explicitly detected.
4. Prefer constructor injection over field `@Inject`; keep collaborators `final` where possible.
5. Choose `@ApplicationScoped`, `@RequestScoped` or `@Dependent` deliberately; avoid `@Singleton` unless eager initialization without a proxy is required.
6. Respect the predominant execution model and never block a Vert.x event-loop thread.
7. Use `@Blocking` for blocking work on a reactive signature; return `Uni<T>` or `Multi<T>` only for genuinely non-blocking flows.
8. Follow the existing Panache style: active record (`PanacheEntity`/`PanacheEntityBase`) or repository (`PanacheRepository`/`PanacheRepositoryBase`). Do not mix styles in one change.
9. Put write operations behind `@Transactional` in the service or use-case layer, never in the REST controller.
10. Avoid N+1 queries with `JOIN FETCH` or `@EntityGraph` when an association is read in a loop or serialized to a response.
11. Map configuration with `@ConfigProperty` or `@ConfigMapping`; never hardcode credentials, tokens or fixed environment URLs.
12. Apply SmallRye Fault Tolerance (`@Retry`, `@Timeout`, `@Fallback`, `@CircuitBreaker`) only to external calls and only when the project already uses it or the user approves adding it.
13. Reuse the project's DTO mapping approach (MapStruct, records or manual mappers) and error-handling pattern.
14. Do not add a library or architectural layer without explicit need.
15. Write isolated JUnit 5 plus Mockito unit tests for every behavioral change; do not start the Quarkus context in unit tests.
16. Enforce at least 80% coverage with JaCoCo in the target codebase and never claim a command ran when it did not.
17. Use Dev Services and `@QuarkusTest` with REST Assured for integration tests, following the project's existing test setup.
18. End with `JAVA-QUARKUS-IMPL.md` validated by `validate_report.py` and report the remaining risks without an approval verdict.

## Modes

- **Implement** (default): detect, design, change code, add tests, validate and write the artifact.
- **Review**: detect, compare against the standards and official guides, list findings with file and line references, and do not modify code unless authorized.
- **Validate**: run the detector and the artifact validator only; report the result.

## Workflow

### Gate 1: Detect the stack (mandatory and blocking)

Run the detector before reading source files for the purpose of making a change:

```bash
python3 scripts/detect_stack.py <project-root> --output stack.json
```

Then:

1. Read `stack.json` and confirm Java version, Quarkus version, build tool, namespace and installed extensions.
2. If no `pom.xml`, `build.gradle` or `build.gradle.kts` exists, stop and ask the user to provide the build descriptor or the exact Java and Quarkus versions. Do not propose any code in that turn.
3. If the version cannot be parsed, report the exact file and property that is missing instead of assuming a version.
4. If Quarkus 2.x and Quarkus 3+ indicators are mixed, list the conflict and ask which one is authoritative.
5. Record the stack marker in the artifact, for example `<!-- java-quarkus:stack java=21 quarkus=3.33.0 build=maven namespace=jakarta -->`.

### Gate 2: Load repository standards

Read `CONTRIBUTING.md`, `CODING_STANDARDS.md`, `ARCHITECTURE.md`, ADRs in `docs/adr/`, the test and lint configuration, `application.properties` or `application.yaml`, and the nearest existing examples of the code being changed.

Capture: package layout, naming, DTO mapping, exception mapping, logging, Panache style, test naming, assertion library and configuration key prefixes.

### Gate 3: Decide the execution model

Use `references/execution-model.md`. Identify whether the endpoint is imperative or reactive from the detected extensions and the method signatures it will touch. Returning `Uni`, `Multi`, `CompletionStage` or a reactive streams `Publisher` means the method runs on the event loop by default; blocking JDBC, Hibernate, filesystem or synchronous HTTP work must move to a worker thread with `@Blocking` or be expressed with a non-blocking API.

### Gate 4: Design the change

Before editing, state internally: target packages and files, bean scope, injection points, transaction boundary, DTO shape allowed by the Java version, configuration keys, resilience annotations and the unit tests to write. Consult `references/cdi-scopes.md`, `references/persistence-transactions.md` and `references/config-security-resilience.md`.

### Gate 5: Implement

Apply the smallest complete change:

- Use constructor injection and modern Java features only when the detected Java version supports them (`record` requires Java 16+; Quarkus 3 requires Java 17+).
- Keep DTOs as `record` when the project already uses records or the Java version allows it and no framework constraint exists.
- Keep writes in a service or use-case method annotated with `@Transactional`; the REST controller only maps input and output.
- Use the Panache pattern already present in the project and add `JOIN FETCH` or `@EntityGraph` for associations used in the response.
- Use `@ConfigProperty` or `@ConfigMapping` and reference secrets through environment variables, never literals.
- Reuse existing SmallRye Health, Micrometer or OpenTelemetry conventions.

### Gate 6: Write JUnit 5 plus Mockito unit tests

Follow `references/testing-junit-mockito.md`:

- Name test classes `*Test` and keep them out of the Quarkus context.
- Use `@ExtendWith(MockitoExtension.class)` when `mockito-junit-jupiter` is available; otherwise use plain `Mockito.mock()` calls.
- Because collaborators are injected through the constructor, instantiate the class under test directly in the test; `@InjectMocks` is optional and only for convenience.
- Cover success, validation failure and exception paths for the changed behavior.
- Assert outcomes with JUnit assertions by default; use AssertJ only when it is already a project dependency.
- If Mockito is not on the test classpath, ask before adding `quarkus-junit5-mockito` or `mockito-junit-jupiter` and show the exact dependency snippet.
- Use `@QuarkusTest`, REST Assured and Dev Services only for integration tests, never for isolated unit tests.

### Gate 7: Validate

Run the project's own commands and record each one with its result:

```bash
./mvnw test
./mvnw verify
```

or:

```bash
./gradlew test
./gradlew jacocoTestReport
```

Then open the JaCoCo report and verify at least 80% coverage for the changed code. If coverage is below 80%, add or adjust unit tests instead of lowering the gate.

### Gate 8: Write the artifact

Write `JAVA-QUARKUS-IMPL.md` using `references/report-template.md`. Keep IDs stable: `CHG-001`, `T-001`, `CFG-001` and `EV-001`. Use `No changes.` in a section with no content and never leave an empty section.

### Gate 9: Validate the artifact

```bash
python3 scripts/validate_report.py JAVA-QUARKUS-IMPL.md
```

Use `--strict` for a stricter gate and `--min-coverage N` only when the user explicitly changes the policy.

### Gate 10: Handoff

Answer in exactly this order:

1. **Análise Breve** — alignment with existing patterns, detected versions and key design decisions.
2. **Código Limpo e Completo** — only the necessary code, fully typed, with every modern Java feature gated by the detected version and no placeholders.
3. **Configurações** — exact `application.properties` or `application.yaml` additions, or `No changes.`

Finish with validation commands, measured coverage and remaining risks. Do not end with an approval verdict.

## Artifact contract

Required markers:

```markdown
<!-- java-quarkus:artifact type=implementation version=1 -->
<!-- java-quarkus:section id=analysis -->
<!-- java-quarkus:section id=stack -->
<!-- java-quarkus:section id=design -->
<!-- java-quarkus:section id=implementation -->
<!-- java-quarkus:section id=tests -->
<!-- java-quarkus:section id=validation -->
<!-- java-quarkus:section id=configurations -->
<!-- java-quarkus:section id=evidence -->
<!-- java-quarkus:section id=assumptions -->
<!-- java-quarkus:section id=traceability -->
<!-- java-quarkus:stack java=21 quarkus=3.33.0 build=maven namespace=jakarta -->
<!-- java-quarkus:coverage value=88 gate=80 tool=jacoco -->
<!-- java-quarkus:change id=CHG-001 status=implemented -->
<!-- java-quarkus:test id=T-001 framework=junit mockito=true context=unit -->
```

Stable ID families: `CHG-NNN` for changes, `T-NNN` for tests, `CFG-NNN` for configuration additions and `EV-NNN` for validation evidence.

## Version matrix

| Detected Quarkus | Namespace | Baseline Java | REST artifacts to recognize |
| --- | --- | --- | --- |
| 2.x | `javax.*` | 11+ | `quarkus-resteasy`, `quarkus-resteasy-reactive`, `quarkus-resteasy-jackson` |
| 3.x | `jakarta.*` | 17+ | `quarkus-rest`, `quarkus-rest-jackson`, legacy `quarkus-resteasy-reactive` alias |

The detector output is authoritative. When it reports `quarkus-rest`, treat the REST layer as reactive-capable but still decide each endpoint's thread from its signature and annotations.

## Evidence rules

- Record the exact command, exit status and measured value for tests and coverage.
- Reference changed files with `path:line` when explaining a decision.
- Keep IDs, markers, severities, framework names and status values in English.
- Redact tokens and personal data as `[REDACTED]`.
- Do not claim a Quality Gate, CI result or Dev Service startup that was not observed.

## Handling edge cases

### No build descriptor

Stop and ask for `pom.xml`, `build.gradle`, `build.gradle.kts` or the exact Java and Quarkus versions. Never default to Quarkus 3.

### Mixed or ambiguous versions

List every source of evidence and ask which is authoritative before proposing code.

### Mockito missing

Show the exact dependency to add and wait for approval; do not silently change the test stack.

### Coverage below 80%

Add unit tests for uncovered branches. Do not lower `--min-coverage` or exclude classes to make the gate pass.

### Blocking work in a reactive endpoint

Use `@Blocking` for JDBC, Hibernate or synchronous REST clients; otherwise convert the flow to `Uni`/`Multi` with non-blocking APIs.

### `@Transactional` in the controller

Move the boundary to the service or use-case layer and keep the controller responsible only for mapping.

### N+1 queries

Use `JOIN FETCH` or `@EntityGraph` and assert the resulting DTO shape in a unit test where possible.

### Secret or hardcoded environment URL

Replace the literal with `@ConfigProperty`/`@ConfigMapping` backed by an environment variable and record the property in the **Configurações** section.

### Suppression annotations

Do not add `NOSONAR` or `@SuppressWarnings` without a proven false positive and explicit user authorization recorded in the artifact.

## Definition of done

- [ ] `detect_stack.py` ran successfully and the stack marker is present.
- [ ] Repository standards were loaded and followed.
- [ ] Code uses the detected Java/Quarkus versions, namespace and extensions.
- [ ] Constructor injection and deliberate CDI scopes are used.
- [ ] Writes are `@Transactional` in the service layer.
- [ ] Execution model is safe for the event loop.
- [ ] JUnit 5 plus Mockito unit tests exist for the changed behavior.
- [ ] Coverage is at least 80% according to JaCoCo.
- [ ] Any new configuration is shown exactly in the **Configurações** section.
- [ ] `JAVA-QUARKUS-IMPL.md` passes `validate_report.py`.

## Output format

```markdown
## Análise Breve
...

## Código Limpo e Completo
...

## Configurações
...
```

## Resources

- [Stack detection](references/version-detection.md)
- [Codebase conventions](references/codebase-conventions.md)
- [CDI and scopes](references/cdi-scopes.md)
- [Execution model](references/execution-model.md)
- [Persistence and transactions](references/persistence-transactions.md)
- [Configuration, security and resilience](references/config-security-resilience.md)
- [JUnit and Mockito tests](references/testing-junit-mockito.md)
- [Official documentation map](references/official-docs.md)
- [Report template](references/report-template.md)
- [Validation checklist](references/validation-checklist.md)
- [Stack detector](scripts/detect_stack.py)
- [Report validator](scripts/validate_report.py)
