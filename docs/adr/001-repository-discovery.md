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
