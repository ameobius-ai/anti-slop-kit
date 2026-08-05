# Purpose

anti-slop-kit is a fidelity channel between agents, not a style guide for humans.

## The problem

When agents transmit instructions, specs, and legacy knowledge to each other, each hop adds slop: hedging, nominalization, filler, vague quantifiers. By the third hop the original precision is gone. This is the broken-telephone effect applied to machine-to-machine handoff.

## What slop actually is

Slop is not ugly prose. It is information loss.

- Hedging ("might", "could", "typically") encodes a probability or a vibe instead of a value. A downstream agent cannot act on it deterministically.
- Nominalization ("the realization of the configuration") strips the actor and the verb, so the receiver cannot reconstruct who does what.
- Banned and filler words carry zero bits. They dilute the signal without adding meaning.
- Vague quantifiers ("most", "many", "around") drop the count or the exact value.

Every rule in the linters is an information-preservation rule, re-justified under this lens. Style is the side effect; fidelity is the point.

## The hardest case: legacy

Offsets, magic numbers, function signatures, hardware timings, and architectural decisions are bits that, once lost, cannot be re-derived. Provenance must survive transmission verbatim.

This is why environment-specific values live behind named constants with a one-line comment naming what they depend on. That is lossless encoding of origin, not style. A constant whose source is unnamed is a future bug that no agent can trace.

## The consumer is another robot

Deliverables are read by agents, not eyeballed by humans. Therefore structured output (`--json`, `--format sarif`) is the core product, not an enterprise checkbox. Findings must be machine-consumable: line numbers, rule ids, suggested fixes. An unstructured warning is as good as no warning for a receiving agent.

## The metric

Today's score is violations per 100 words. That is a proxy. The true metric is semantic drift across a hop:

1. Encode a precise spec.
2. Transmit it through an agent (rewrite, summarize, re-express).
3. Decode the result.
4. Diff against the original.

The eval harness should grow round-trip transmission tasks that measure this drift directly, not just count surface violations.

## Determinism

Robot A to robot B must be reproducible. The linters are stdlib-only and deterministic. Skills must produce stable output under re-run. Any nondeterminism in the channel is indistinguishable from noise.

## The engineering directives

The two engineering directives shipped as eval tasks (en-08, en-09) are not examples to copy. They are the upstream encoding format that this kit is designed to preserve across hops. A re-expression of those directives that loses any of their rules has failed the fidelity test, regardless of how clean the prose reads.
