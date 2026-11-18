# Official documentation map

Consult these official Quarkus guides when a rule needs version-specific confirmation. They are the authority over memory or generic Java EE knowledge.

| Topic | Official guide |
| --- | --- |
| CDI basics and constructor injection | https://quarkus.io/guides/cdi/ |
| ArC reference, scopes and injection details | https://quarkus.io/guides/cdi-reference/ |
| Quarkus REST execution model, `@Blocking` and `@NonBlocking` | https://quarkus.io/guides/rest/ |
| REST JSON and `Uni`/`Multi` endpoints | https://quarkus.io/guides/rest-json/ |
| Hibernate ORM with Panache | https://quarkus.io/guides/hibernate-orm-panache/ |
| Hibernate Reactive Panache and `join fetch` | https://quarkus.io/guides/hibernate-reactive-panache/ |
| SmallRye Fault Tolerance | https://quarkus.io/guides/smallrye-fault-tolerance/ |
| Getting started with testing, `@QuarkusTest` and `@InjectMock` | https://quarkus.io/guides/getting-started-testing/ |
| Component testing with Mockito | https://quarkus.io/guides/testing-components/ |

For MCP-enabled agents, the Context7 library ID `/websites/quarkus_io_guides` exposes the same documentation. Use it before recommending an annotation or API whose name changed between Quarkus 2 and 3, such as `quarkus-resteasy-reactive` versus `quarkus-rest`, or `javax.*` versus `jakarta.*`.
