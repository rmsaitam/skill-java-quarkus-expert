# Report template

Use this scaffold for `JAVA-QUARKUS-IMPL.md`. Keep every marker and section; write `No changes.` where a section has no content.

````markdown
<!-- java-quarkus:artifact type=implementation version=1 -->
# Java Quarkus Implementation: order creation endpoint

- Status: Final
- Date: 2026-11-18
- Reviewer: Java Quarkus Agent
- Artifact: JAVA-QUARKUS-IMPL.md
- Java Version: 21
- Quarkus Version: 3.33.0
- Build Tool: maven
- Namespace: jakarta
- Execution Model: imperative
- Changes Applied: 1
- Tests Run: ./mvnw test
- Coverage: 88%
- Coverage Tool: jacoco
- Review Language: English

<!-- java-quarkus:section id=analysis -->
## Análise Breve

The repository already uses constructor injection, Panache repositories and service-layer transactions. This change follows those patterns and keeps the REST resource responsible only for mapping.

<!-- java-quarkus:section id=stack -->
## Stack detectado

<!-- java-quarkus:stack java=21 quarkus=3.33.0 build=maven namespace=jakarta -->

The detector read `pom.xml`: Java release 21, Quarkus platform 3.33.0, `quarkus-rest-jackson`, `quarkus-hibernate-orm-panache`, `quarkus-junit5-mockito` and `jacoco-maven-plugin`.

<!-- java-quarkus:section id=design -->
## Design

- Scope: `OrderService` remains `@ApplicationScoped` with constructor injection.
- Execution: imperative endpoints run on worker threads; no event-loop blocking.
- Persistence: writes move behind `@Transactional` in `OrderService`.
- Configuration: no new property is required.

<!-- java-quarkus:section id=implementation -->
## Código Limpo e Completo

<!-- java-quarkus:change id=CHG-001 status=implemented -->
### CHG-001: Move order persistence into the service

- File: src/main/java/com/example/order/OrderService.java:12
- Change: Added constructor injection of OrderRepository and a transactional create method.
- Design: The resource maps the request; the service owns persistence and mapping to the response.

```java
@ApplicationScoped
public class OrderService {

    private final OrderRepository repository;

    OrderService(OrderRepository repository) {
        this.repository = repository;
    }

    @Transactional
    public OrderResponse create(OrderRequest request) {
        Order order = Order.from(request);
        repository.persist(order);
        return OrderResponse.from(order);
    }
}
```

<!-- java-quarkus:section id=tests -->
## Testes unitários

<!-- java-quarkus:test id=T-001 framework=junit mockito=true context=unit -->
### T-001: OrderServiceTest covers creation paths

- File: src/test/java/com/example/order/OrderServiceTest.java
- Cases: success, invalid reference and repository failure.
- Coverage: constructor injection, validation and exception propagation.

The tests use JUnit 5 with `@ExtendWith(MockitoExtension.class)` and do not start the Quarkus context.

<!-- java-quarkus:section id=validation -->
## Validação

<!-- java-quarkus:coverage value=88 gate=80 tool=jacoco -->

- [x] `./mvnw test` passed with 24 tests.
- [x] `./mvnw verify` produced the JaCoCo report.
- [x] JaCoCo reported 88% coverage, above the 80% gate.
- [x] No blocking work was added to an event-loop method.

<!-- java-quarkus:section id=configurations -->
## Configurações

No changes.

<!-- java-quarkus:section id=evidence -->
## Evidências

<!-- java-quarkus:evidence id=EV-001 command=./mvnw test status=passed -->
### EV-001: Unit test run

- Result: 24 tests passed, 0 failures.
- Coverage: 88% reported by JaCoCo.

<!-- java-quarkus:section id=assumptions -->
## Premissas

- The detected `pom.xml` is the authoritative source for Java and Quarkus versions.
- No new dependency was introduced.

<!-- java-quarkus:section id=traceability -->
## Rastreabilidade

| Change | Test | Evidence |
| --- | --- | --- |
| CHG-001 | T-001 | EV-001 |
````
