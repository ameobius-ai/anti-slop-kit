# Round-Trip Transmission Evals

These tasks measure semantic drift across an agent hop (the true metric per `PURPOSE.md`).

## Structure
Each task folder contains:
- `source.md`: The precise, 0-slop original spec.
- `prompt.md`: The instruction given to the transmitting agent.
- `checklist.json`: The exact facts that must survive the hop.

## Execution
The harness passes `source.md` and `prompt.md` to an LLM, captures the `rewritten.md` output, and then runs `tools/transmit_check.py source.md rewritten.md`. The resulting fidelity score is aggregated across all tasks.
