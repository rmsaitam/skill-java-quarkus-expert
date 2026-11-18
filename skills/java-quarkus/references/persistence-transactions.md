# Persistence and transactions

Follow the Panache style already present in the project. Do not introduce a second persistence abstraction for a single change.

## Active record

```java
@Entity
public class Order extends PanacheEntity {
    public String reference;
    public BigDecimal total;

    public static Order findByReference(String reference) {
        return find("reference", reference).firstResult();
    }
}
```

## Repository

```java
@ApplicationScoped
public class OrderRepository implements PanacheRepository<Order> {

    public Order findByReference(String reference) {
        return find("reference", reference).firstResult();
    }
}
```

## Transaction boundary

Writes belong in a service or use-case method:

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

The REST resource maps input and output only. Do not annotate the controller with `@Transactional`.

## Avoiding N+1 queries

- Use `select distinct o from Order o left join fetch o.items` when iterating over `order.items`.
- Use `@EntityGraph(attributePaths = "items")` on repository finders when the mapping is reused.
- Do not initialize lazy associations one entity at a time inside a loop or DTO mapper.
- For Hibernate Reactive, use the reactive Panache query API and keep the caller non-blocking.

## Test impact

Transaction boundaries and query shapes are integration concerns. Cover DTO mapping and service decisions with isolated Mockito unit tests; use `@QuarkusTest` and Dev Services for the actual database behavior.
