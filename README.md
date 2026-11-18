# Java Quarkus

[![skills.sh](https://skills.sh/b/rmsaitam/skill-java-quarkus)](https://skills.sh/rmsaitam/skill-java-quarkus)

A version-aware Java and Quarkus implementation skill for coding agents. Before suggesting any dependency, annotation or configuration, the skill inspects `pom.xml`, `build.gradle` or `build.gradle.kts` to identify the exact Java version, Quarkus version and installed extensions. If no build descriptor is available, it stops and asks for the descriptor or the versions instead of guessing.

The skill follows the conventions already present in the codebase and the official Quarkus guides. It uses `jakarta.*` for Quarkus 3+, keeps `javax.*` only for explicitly detected Quarkus 2.x, prefers constructor injection, respects the imperative and reactive execution models, places `@Transactional` in the service layer, and writes JUnit 5 plus Mockito unit tests with an 80% coverage gate.

## Supported agents

| Agent | Manifest |
| --- | --- |
| Claude Code | `.claude-plugin/plugin.json` |
| Codex | `.codex-plugin/plugin.json` |
| Cursor | `.cursor-plugin/plugin.json` |
| GitHub Copilot CLI | `.github/plugin/marketplace.json` |
| Antigravity | `plugin.json` |
| skills.sh / generic Agent Skills | `skills/java-quarkus/SKILL.md` |

## Install

```bash
npx skills add rmsaitam/skill-java-quarkus
npx skills add rmsaitam/skill-java-quarkus -g -y
npx skills add rmsaitam/skill-java-quarkus --list
```

Claude Code:

```text
/plugin marketplace add rmsaitam/skill-java-quarkus
/plugin install java-quarkus
```

Manual install for generic Agent Skills:

```bash
mkdir -p ~/.agents/skills
cp -R skills/java-quarkus ~/.agents/skills/java-quarkus
python3 scripts/validate_plugin.py .
```

## What it does

1. Runs `detect_stack.py` to produce a normalized stack report: Java version, Quarkus version, build tool, extensions, namespace and available test dependencies.
2. Loads repository standards and mirrors existing package, DTO, error handling and test patterns.
3. Implements the change with the correct CDI scope, constructor injection, execution model, transaction boundary, configuration mapping and resilience annotations.
4. Adds isolated JUnit 5 plus Mockito unit tests and checks coverage with JaCoCo against the 80% gate.
5. Writes and validates a traceable `JAVA-QUARKUS-IMPL.md` artifact with `validate_report.py`.

The final answer always follows this format: **Análise Breve**, **Código Limpo e Completo**, **Configurações**.

## Artifact markers

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

## Development

```bash
make test        # run the test suite
make coverage    # run tests with an 80% coverage gate
make validate    # validate the plugin structure
make check       # coverage plus plugin validation
```

The executable test suite of this plugin uses pytest and covers `detect_stack.py`, `validate_report.py` and `validate_plugin.py`. The generated Java code contract requires JUnit 5 plus Mockito and 80% coverage measured by JaCoCo in the target codebase.

## Official documentation

The `references/official-docs.md` file maps each rule to the official Quarkus guides for CDI, REST, Panache, fault tolerance and testing.

## License

MIT
