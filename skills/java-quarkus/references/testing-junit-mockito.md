# JUnit 5 plus Mockito unit tests

Unit tests must be fast, isolated and free of the Quarkus bootstrap. Constructor injection makes this straightforward: instantiate the class under test directly and pass Mockito mocks.

```java
package com.example.order;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.math.BigDecimal;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

@ExtendWith(MockitoExtension.class)
class OrderServiceTest {

    @Mock
    OrderRepository repository;

    OrderService service;

    @BeforeEach
    void setUp() {
        service = new OrderService(repository);
    }

    @Test
    void createPersistsValidOrderAndReturnsResponse() {
        OrderRequest request = new OrderRequest("ORD-1", new BigDecimal("19.90"));

        OrderResponse response = service.create(request);

        assertEquals("ORD-1", response.reference());
        assertEquals(new BigDecimal("19.90"), response.total());
        verify(repository).persist(any(Order.class));
    }

    @Test
    void createRejectsBlankReferenceWithoutPersisting() {
        OrderRequest request = new OrderRequest("", new BigDecimal("19.90"));

        assertThrows(IllegalArgumentException.class, () -> service.create(request));
        verify(repository, never()).persist(any(Order.class));
    }

    @Test
    void createPropagatesRepositoryFailure() {
        OrderRequest request = new OrderRequest("ORD-1", new BigDecimal("19.90"));
        when(repository.persist(any(Order.class))).thenThrow(new IllegalStateException("database down"));

        assertThrows(IllegalStateException.class, () -> service.create(request));
    }
}
```

## Rules

- Unit tests use JUnit 5 and Mockito only; no `@QuarkusTest` and no REST Assured here.
- Use `@ExtendWith(MockitoExtension.class)` when `mockito-junit-jupiter` is available; otherwise create mocks with `Mockito.mock(...)`.
- Prefer direct construction over `@InjectMocks`. The latter is optional when constructor injection exists.
- Assert observable outcomes. Verify interactions only at boundaries such as repository, REST client or message emitter.
- Cover success, invalid input and failure paths for each changed behavior.
- Use JUnit assertions by default; use AssertJ only when already present.
- If Mockito is missing from the detected test dependencies, ask before adding `quarkus-junit5-mockito` and show the exact snippet:

```xml
<dependency>
  <groupId>io.quarkus</groupId>
  <artifactId>quarkus-junit5-mockito</artifactId>
  <scope>test</scope>
</dependency>
```

```groovy
testImplementation 'io.quarkus:quarkus-junit5-mockito'
```

If JaCoCo is missing, propose the exact coverage setup before adding it:

```xml
<plugin>
  <groupId>org.jacoco</groupId>
  <artifactId>jacoco-maven-plugin</artifactId>
  <version>0.8.12</version>
  <executions>
    <execution>
      <goals><goal>prepare-agent</goal><goal>report</goal></goals>
    </execution>
  </executions>
</plugin>
```

```groovy
plugins {
  id 'jacoco'
}
tasks.named('test') {
  finalizedBy 'jacocoTestReport'
}
```

## Reactive code

For a service returning `Uni<T>`, keep the unit test synchronous by subscribing with Mutiny's `await().indefinitely()` on the returned `Uni`, then assert the item or failure. Do not sleep or block a Quarkus event loop.

## Integration tests

Use `@QuarkusTest` and REST Assured for HTTP contracts and Dev Services for databases or brokers:

```java
@QuarkusTest
class OrderResourceTest {

    @Test
    void createsOrder() {
        given()
            .contentType(ContentType.JSON)
            .body("{\"reference\":\"ORD-1\",\"total\":19.90}")
        .when().post("/orders")
        .then().statusCode(201);
    }
}
```

## Coverage

Enable JaCoCo with the project's existing setup. If absent, propose the plugin and dependency snippets explicitly. The gate is at least 80%; record the measured value in the artifact and never lower the gate to pass.
