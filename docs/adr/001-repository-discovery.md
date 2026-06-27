# ADR-001 Repository Discovery

## Decision

Repository exploration should be incremental instead of exhaustive.

## Reason

The agent should gather only enough information to make the next decision, rather than loading the entire repository into the LLM.

## Trade-off

### Pros

* Lower token usage
* Faster
* Scalable

### Cons

* Requires multiple iterations
* More agent loop complexity

## Alternatives Considered

### Option 1: Exhaustive Repository Scan

Rejected because it increases token usage and does not scale.

### Option 2: Incremental Repository Discovery

Accepted because the agent only needs enough context to make the next decision.

## Future Considerations

If repository summarization or caching is introduced in the future,
this decision may be revisited.
