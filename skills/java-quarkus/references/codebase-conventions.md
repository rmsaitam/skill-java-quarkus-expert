# Codebase conventions

The detected stack defines what is legal; the codebase defines what is idiomatic. Read the following before designing a change:

- `CONTRIBUTING.md`, `CODING_STANDARDS.md`, `SECURITY.md`, `ARCHITECTURE.md`.
- ADRs under `docs/adr/`.
- Test, lint, format and coverage configuration.
- `application.properties` or `application.yaml` key prefixes.
- The closest existing controller, service, entity, repository, DTO and test for the area being changed.
- Recent approved commits touching the same packages.

## Capture these facts

| Topic | Question to answer |
| --- | --- |
| Packages | Where do REST resources, services, entities, repositories and DTOs live? |
| Naming | Suffixes such as `Resource`, `Service`, `Repository`, `Mapper`, `Dto`, `Request`, `Response`. |
| DTO mapping | MapStruct, Java `record`, manual mapper, or direct entity exposure? |
| Errors | `ExceptionMapper`, problem details, `WebApplicationException`, or a custom error record? |
| Validation | `jakarta.validation` in Quarkus 3, `javax.validation` in Quarkus 2, or manual checks? |
| Panache | Active record via `PanacheEntity`, or repository via `PanacheRepository`? |
| Transactions | Existing service annotations and boundaries. |
| Tests | JUnit assertions vs. AssertJ, Mockito extension vs. plain mocks, naming and fixture style. |
| Configuration | Property prefixes and config mapping interfaces already in use. |

## Rules

- Copy the local style before introducing anything new.
- Do not reformat unrelated code or reorder imports in untouched files.
- Do not introduce MapStruct, AssertJ, Lombok, ArchUnit or a new test library unless the project already uses it or the user explicitly requests it.
- If the project exposes entities directly, do not silently add a DTO layer; mention it as a design option instead.
- If no local example exists, prefer the smallest official Quarkus pattern compatible with the detected version and record the assumption in the artifact.
