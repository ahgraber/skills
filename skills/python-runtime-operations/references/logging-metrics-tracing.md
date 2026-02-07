# Logging, Metrics, and Tracing

## Outcome

Production behavior is observable and diagnosable under load and failure.

## Logging

- Configure logging once at process entrypoint; use module loggers (`logging.getLogger(__name__)`) in code.
- Use structured logs with stable keys and consistent timestamps.
- Include operation/request IDs, phase, attempt, and relevant context on every boundary log.
- Log phase transitions and critical checkpoints for long-running operations.
- Follow the repository's logging interpolation convention (`%` style for stdlib `logging` by default) and use `extra={...}` for machine-parseable fields.
- Log exceptions with context at meaningful boundaries, once per failure path.
- Keep logging at imperative-shell boundaries; avoid logging inside pure core functions.
- Keep secrets and sensitive payloads out of logs.

## Metrics

- Track latency, throughput, errors, retries, and saturation/queue depth.
- Split retryable failures from permanent failures in counters.
- Export phase-specific timeout and cancellation signals.
- Define alert thresholds for critical paths and retry exhaustion.

## Tracing

- Propagate trace/request IDs across async boundaries.
- Propagate context across queue/job boundaries and outbound calls.
- Annotate spans around external dependencies, retries, and timeout phases.
- Ensure logs, metrics, and traces share correlation IDs.
