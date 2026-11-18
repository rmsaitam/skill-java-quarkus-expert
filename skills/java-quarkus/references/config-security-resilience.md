# Configuration, security and resilience

## Configuration

Use `@ConfigProperty` for a single value and `@ConfigMapping` for a grouped set of properties.

```java
@ConfigMapping(prefix = "payment.gateway")
public interface PaymentGatewayConfig {

    @WithDefault("2S")
    Duration timeout();

    String baseUrl();
}
```

For a single key:

```java
@ConfigProperty(name = "orders.page-size", defaultValue = "50")
int pageSize;
```

When Quarkus 2.x is detected, import `org.eclipse.microprofile.config.inject.ConfigProperty`. In Quarkus 3+, prefer `io.quarkus.runtime.annotations.ConfigMapping` and `jakarta.*` APIs.

## Secrets

- Never put passwords, tokens, API keys or fixed environment URLs in Java source, tests or the report.
- Reference secrets through environment variables, for example `PAYMENT_GATEWAY_TOKEN=${PAYMENT_GATEWAY_TOKEN}` in `application.properties`.
- Redact any accidental secret in the artifact as `[REDACTED]` and report it as a risk.
- The stack detector reads configuration keys only; do not paste raw configuration values into the artifact.

## Resilience

Use SmallRye Fault Tolerance only when `quarkus-smallrye-fault-tolerance` is present or the user approves adding it.

```java
@Retry(maxRetries = 2, delay = 200)
@Timeout(2)
@Fallback(fallbackMethod = "fallbackStatus")
public PaymentStatus status(String id) {
    return client.status(id);
}
```

Apply these annotations to external calls, not to local business logic. Ensure a fallback method has the same signature.

## Observability

Reuse the project's SmallRye Health checks, Micrometer metrics or OpenTelemetry spans. Do not add a new observability stack for a single change.
