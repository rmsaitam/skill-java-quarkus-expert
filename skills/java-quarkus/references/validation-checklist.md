# Validation checklist

Use this checklist when the validator cannot be executed. Every box must be checked before handoff.

## 1. Artifact contract

- [ ] The `<!-- java-quarkus:artifact type=implementation version=1 -->` marker appears once.
- [ ] All required section markers appear once: analysis, stack, design, implementation, tests, validation, configurations, evidence, assumptions, traceability.
- [ ] `CHG-NNN`, `T-NNN`, `CFG-NNN` and `EV-NNN` IDs are unique and stable.
- [ ] No `TODO`, `FIXME`, `TBD` or unfinished marker remains.

## 2. Summary and stack

- [ ] Status, date, reviewer and artifact fields are present.
- [ ] Java Version, Quarkus Version, Build Tool, Namespace and Execution Model match `stack.json`.
- [ ] Namespace is `jakarta` for Quarkus 3+ and `javax` only for detected Quarkus 2.x.
- [ ] Changes Applied equals the number of `CHG-NNN` entries.

## 3. Implementation

- [ ] Constructor injection is used for collaborators.
- [ ] Scopes are deliberate and `@Singleton` is justified when present.
- [ ] Writes are `@Transactional` in the service layer.
- [ ] No event-loop thread performs blocking work; `@Blocking` or `Uni`/`Multi` is used where required.
- [ ] Panache style matches the codebase and N+1 queries are addressed.
- [ ] No credentials, tokens or fixed environment URLs are hardcoded.

## 4. Tests and coverage

- [ ] JUnit 5 and Mockito are present in the test entry.
- [ ] Unit tests do not use `@QuarkusTest` or REST Assured.
- [ ] Success, validation failure and exception paths are covered.
- [ ] JaCoCo coverage is at least 80% and the measured value is recorded.
- [ ] Every test command in the report was actually executed.

## 5. Configurations and evidence

- [ ] New properties are shown exactly with file and key, or the section says `No changes.`
- [ ] Each evidence row has a command and an observed result.
- [ ] Traceability links every change to at least one test and one evidence row.

## 6. Manual commands

```bash
python3 scripts/detect_stack.py . --output stack.json
python3 scripts/validate_report.py JAVA-QUARKUS-IMPL.md --strict
```

Both commands must exit with status 0.
