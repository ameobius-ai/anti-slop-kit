# Purpose

anti-slop-kit defines a register for technical prose that survives
transmission between any two participants — human or robot — without
fidelity loss.

## The channel is bilingual by agent type

Two populations read and write in this register:

- Humans compose specs (ADRs, incident reports, API contracts), edit
  skills (SKILL.md), and read reports (README, --explain output, SARIF
  rendered in a viewer).
- Robots parse linter output (JSON, SARIF), apply skills to generate
  text, and re-express specs across agent hops.

A single register serves both. That is the design choice, not an
accident. Every artifact the kit ships must be legible to at least one
population and parseable by at least one; the strongest artifacts are
both.

## What slop actually is

Slop is information loss in the channel. It degrades the signal for
both populations identically — a human reading hedged prose and a
robot parsing it both fail to act deterministically, for the same
reason:

- Hedging ("might", "could", "typically") encodes a probability or a
  vibe instead of a value. Neither reader can act on it.
- Nominalization strips the actor and the verb. Neither reader can
  reconstruct who does what.
- Filler words carry zero bits for either reader.
- Vague quantifiers ("most", "many", "around") drop the count for
  either reader.

Every rule in the linters is an information-preservation rule. Style
is the side effect for human readers; fidelity is the shared point.

## The hardest case: legacy

Offsets, magic numbers, function signatures, hardware timings, and
architectural decisions are bits that, once lost, cannot be re-derived
by either population. Provenance must survive transmission verbatim.

This is why environment-specific values live behind named constants
with a one-line comment naming what they depend on. That is lossless
encoding of origin — readable to a human tracing the code, parseable
to a robot re-expressing it.

## Both directions, same register

A human writes a spec → a robot rewrites it → a human reviews the
rewrite → a robot transmits it to another robot → a human reads the
final document. At every hop the register is the same. The linter
scores every hop with the same rules. Fidelity is measured against the
original spec, not against stylistic preference.

## The metric

Today's score is violations per 100 words. That is a proxy. The true
metric is semantic drift across a hop: encode a precise spec, transmit
through any participant (human rewrite, robot rewrite, summarizer),
decode, diff. The eval harness should grow round-trip transmission
tasks that measure this drift directly.

## Determinism for the robot half, legibility for the human half

The linter is stdlib-only and deterministic — a robot calling it twice
on the same input gets the same output. The output formats are chosen
so both populations can read them:

- `--explain` renders for human eyes with line numbers and suggestions.
- `--json` renders for robot parsing with the same findings.
- `--format sarif` renders for enterprise toolchains.

No format is privileged. The same findings, three renderings.

## The engineering directives

The two engineering directives shipped as eval tasks (en-08, en-09)
are both the upstream encoding format the kit preserves and an
artifact that humans and robots both read. A re-expression that loses
any of their rules has failed the fidelity test, regardless of whether
a human or a robot produced the rewrite.
