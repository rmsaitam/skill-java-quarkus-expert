# CDI and scopes with ArC

Quarkus uses ArC, a CDI-compatible container optimized for build time. Prefer constructor injection so the class is immutable and unit-testable without starting Quarkus.

```java
@ApplicationScoped
public class OrderService {

    private final OrderRepository repository;
    private final PaymentGateway gateway;

    OrderService(OrderRepository repository, PaymentGateway gateway) {
        this.repository = repository;
        this.gateway = gateway;
    }

    public OrderResponse create(OrderRequest request) {
        Order order = Order.from(request);
        repository.persist(order);
        return OrderResponse.from(order);
    }
}
```

With a single constructor, `@Inject` on the constructor is not required in Quarkus. A no-args constructor is not generated when the bean extends a class without one.

## Scope selection

| Scope | Use when |
| --- | --- |
| `@ApplicationScoped` | Stateless service shared across requests; the default choice for most services. |
| `@RequestScoped` | State that lives for exactly one HTTP request, such as a request context object. |
| `@Dependent` | Short-lived helper tied to the lifecycle of the injecting bean. |
| `@Singleton` | Only when eager initialization without a client proxy is required. It is not the default. |

## Rules

- Keep injected collaborators `final` and avoid field injection.
- Do not put mutable request state in `@ApplicationScoped` beans.
- Avoid `@Singleton` for ordinary services; it changes proxying and initialization behavior.
- Do not use `@InjectMock` as a universal replacement for Mockito unit tests. It configures unsatisfied CDI dependencies in tests that boot Quarkus.
- Annotate the transaction boundary on the service method, not on the REST resource.
