# ADR 022: fix(web-fetch): cap extracted webpage content before returning it

## Context

Webpage downloads are bounded at 50MB, but extracted text is returned in full to the model. A modest large HTML page can exceed the shared 50KB tool output budget and overwhelm the conversation.

## Decision

Bound long title previews, then apply the shared head truncation utility to the complete title and content output, reserving room for a visible notice within the same byte budget.

## Consequences

Small pages keep their exact output. Huge titles and body text share the byte and line limits, and the visible notice identifies omitted content. Independent review exposed the title bypass in the first candidate; the frozen revision includes adversarial title tests.

## Acceptance

The regression in `tests/test_cow32_webpage_output_budget.py` fails on `5f54fc5beb55e522091ebfbe3a11aece9bb7d502` and passes with this decision. Related existing tests must pass. Validation uses local fixtures without external services or model calls.
