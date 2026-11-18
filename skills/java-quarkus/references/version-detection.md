# Stack detection

This gate is mandatory and blocking. Run it before reading source code for the purpose of proposing or applying a change.

```bash
python3 scripts/detect_stack.py <project-root> --output stack.json
```

## What the detector reads

| Source | Extracted values |
| --- | --- |
| `pom.xml` | `maven.compiler.release`, `maven.compiler.source`, `java.version`, `quarkus.platform.version`, BOM versions, `quarkus-maven-plugin`, dependency artifact IDs |
| `build.gradle`, `build.gradle.kts` | `sourceCompatibility`, `JavaLanguageVersion`, `quarkusPlatformVersion`, Quarkus plugin version, dependency notations |
| `gradle.properties` | version properties used by Gradle builds |
| `application.properties`, `application.yaml` | property keys only; values are never copied to the report |

## Output fields

- `buildTool`: `maven`, `gradle` or `gradle-kts`.
- `java.version`: detected release, source or toolchain version.
- `quarkus.version` and `quarkus.major`: detected platform version and major line.
- `namespace`: `jakarta` for major 3+, `javax` for major 2.
- `extensions`: sorted list of Quarkus artifact IDs.
- `testDependencies`: JUnit, Mockito, REST Assured and JaCoCo indicators.
- `warnings` and `blockers`: actionable messages with the source file.

## Stop conditions

1. No `pom.xml`, `build.gradle` or `build.gradle.kts`: ask the user for the descriptor or the exact Java and Quarkus versions. Do not continue in the same turn.
2. Unparseable descriptor: report the file and the missing property. Do not guess.
3. Mixed Quarkus 2.x and 3+ indicators: ask which source is authoritative.
4. Quarkus version present but Java version absent: ask for the Java release before using records or newer syntax.

## Extension aliases

| Detected artifact | Interpretation |
| --- | --- |
| `quarkus-rest`, `quarkus-rest-jackson` | Quarkus 3 reactive REST stack |
| `quarkus-resteasy-reactive`, `quarkus-resteasy-reactive-jackson` | Reactive REST stack, legacy name in Quarkus 3 and normal name in Quarkus 2 |
| `quarkus-resteasy`, `quarkus-resteasy-jackson` | Imperative REST stack, typically Quarkus 2 |
| `quarkus-hibernate-orm-panache`, `quarkus-hibernate-orm-panache-kotlin` | Active record or repository persistence with Hibernate ORM |
| `quarkus-hibernate-reactive-panache` | Reactive Panache; keep flows non-blocking |
| `quarkus-smallrye-reactive-messaging` | Reactive messaging channels |
| `quarkus-smallrye-fault-tolerance` | `@Retry`, `@Timeout`, `@Fallback`, `@CircuitBreaker` available |
| `quarkus-junit5`, `quarkus-junit5-mockito`, `mockito-core`, `mockito-junit-jupiter`, `quarkus-jacoco` | Test and coverage capabilities |

## Security boundary

The detector reads only property keys from configuration files. It never emits values that look like passwords, tokens, API keys or URLs with embedded credentials. Feed its JSON into the report; never paste raw configuration files into the artifact.
