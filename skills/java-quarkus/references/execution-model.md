# Execution model: imperative vs. reactive

Quarkus REST uses event-loop threads for non-blocking I/O and worker threads for blocking work. A method is considered non-blocking by default when it returns `Uni`, `Multi`, `CompletionStage` or a reactive streams `Publisher`. Imperative methods that return the value directly run on a worker thread.

## Rules

1. Never perform JDBC, Hibernate, filesystem or synchronous HTTP calls on an event-loop thread.
2. If a blocking operation is unavoidable in a method with a reactive signature, annotate it with `@Blocking` so Quarkus moves it to a worker thread.
3. Prefer a genuinely non-blocking chain with Mutiny (`Uni`/`Multi`), Hibernate Reactive or reactive REST clients when the stack already supports it.
4. A `@Transactional` method is treated as blocking. An explicit `@Blocking` or `@NonBlocking` on the class overrides that default.
5. Do not mix `Uni<T>` and direct blocking calls in the same method without an explicit thread decision.

```java
@Path("/orders")
public class OrderResource {

    private final OrderService service;

    OrderResource(OrderService service) {
        this.service = service;
    }

    @GET
    @Path("/{id}")
    public Uni<OrderResponse> get(String id) {
        return service.findById(id);
    }

    @POST
    @Blocking
    public OrderResponse createBlocking(OrderRequest request) {
        return service.create(request);
    }
}
```

## With reactive messaging

Keep processors non-blocking when they consume `Multi` or return `Uni`. If a processor writes with Hibernate ORM, mark it `@Blocking` or use Hibernate Reactive. Record the chosen thread model in the artifact's design section.
