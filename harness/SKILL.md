---
name: harness-engineering
description: Diagnose and design the scaffolding around an agent - loop, tools, context, control. Use when an agent fails on real tasks, before adding a tool or an MCP server, and when reviewing an agent setup before production.
---

# Harness engineering

An agent is a model plus a harness. The harness is the runtime layer around the
model: the loop, the tool interface, context management, and the control
mechanisms. When an agent fails on a real task, the harness is the first place to
look, not the model.

Use this skill when someone asks to "make the agent better", wants to add a tool
or an MCP server, or is about to ship an agent setup.

Do not use this skill for prompt wording, for model selection alone, or for
ordinary application code.

## 1. Name the failure before you change anything

Classify the failure first. Each class has one right repair site. Guessing the
site is how teams add tools that do not help.

| Failure | Symptom | Repair site |
| --- | --- | --- |
| Context | The agent does not know a fact that exists in the repo | Context delivery |
| Constraint | The agent knew the rule and broke it | Control mechanism |
| Verification | The agent believes wrong work is done | Verification loop |
| Planning | The agent solves the wrong problem or loops | Planning artifact |
| Interface | The tool call is malformed or the result is unreadable | Tool design |

Ask for one failing trace before you propose a change. Without a trace you are
decorating, not engineering.

## 2. The four parts that must exist

A harness needs all four. If one is missing, name it as a gap.

1. Agent loop. Observe, plan, act, verify. Define the stop condition and the
   step budget. An open loop with no stop condition is a bug.
2. Tool interface. What the agent can call, and what comes back.
3. Context management. What enters the window, and what happens when it is full.
4. Control mechanisms. Permissions, approval gates, hooks, budgets.

## 3. Rules per part

### Loop

- Set a step limit and a wall-clock limit. Report which one stopped the run.
- Put the reasoning budget where it pays: planning and verification.
- Detect repetition. Three identical failing actions is a stop condition.
- Never let a subagent inherit permissions it does not need.

### Tools

- One tool does one thing. Split a tool that has a mode flag.
- The error message must say what to do next, not only what broke.
- Return the same shape on success and on failure.
- Cut optional fields the agent never fills.
- Prefer few good tools over many. Skill and tool sprawl costs accuracy, not
  only tokens.
- Before adding a tool, ask whether the agent can already do it with the shell,
  a script, or a file. A tool that wraps one command is usually not worth its
  schema.

### Context

- Durable state goes in files. Plans, decisions and progress do not belong in
  the prompt.
- Critical rules must live in the always-loaded instruction file. Compaction
  drops the middle of a session, and a rule that was compacted away is gone.
- Deliver pointers, not payloads. Let the agent pull a file, a symbol or a
  chunk when it needs it.
- Define what happens at the context limit before you hit it.
- Guidance that is not in the loaded context did not happen.

### Control

- Default to deny. Grant the minimum for this task.
- Destructive, irreversible, paid and credential-using actions need a gate.
- Enforce a rule with code, not with a sentence in the prompt. A linter, a
  schema or a hook holds. A polite instruction does not.
- Never give the agent a raw long-lived secret when a scoped one will do.
- Treat tool combinations as the risk unit: private data, untrusted input and an
  outbound channel together are dangerous even when each tool is safe alone.

### Verification

- The agent must be able to run the check itself.
- The check runs on task completion, not only in review.
- Write the pass criteria before the task starts.
- Keep two eval sets apart: capability evals, which should fail sometimes, and
  regression evals, which must stay near 100 percent.
- Emit a few summary lines to the loop and log the detail to a file. Verbose
  test output poisons the context.

## 4. Deliverable

Answer in this order.

1. Diagnosis. The failure class and the evidence for it.
2. Repair. The smallest change at the correct site.
3. Proof. The command, test or eval that shows the repair worked.
4. Expiry. What model improvement would make this component unnecessary.

Step 4 is not decoration. Every harness component exists because the model could
not do something. Record the assumption, or the harness will outlive it and slow
the agent down.

## 5. Review gate

Block the ship if any answer is no.

- [ ] The loop has a stop condition and a budget.
- [ ] Every tool has one job, a stable return shape, and actionable errors.
- [ ] Durable state is in files.
- [ ] Behaviour at the context limit is defined.
- [ ] Permissions are least-privilege and destructive actions are gated.
- [ ] The agent can run its own verification.
- [ ] Regression evals exist and pass.
- [ ] Traces are recorded and can be replayed.
- [ ] Each component has a written expiry condition.

## 6. Anti-patterns

- Adding a tool to fix a context problem.
- Adding a subagent to fix a verification problem.
- Writing a rule in the prompt to fix a constraint problem.
- Measuring a harness change without a fixed model and a fixed task set.
- Comparing two agents while the sandbox resources differ. Container limits
  alone move benchmark scores by several points.
- Keeping a component after the capability gap it covered has closed.

## Sources

- Harness definition and the four elements: arXiv 2606.10106.
- Failure classes and repair sites: deepset, agent harness engineering.
- Tool design and permissions: Anthropic, Writing Effective Tools for Agents;
  Beyond Permission Prompts.
- Component expiry: Anthropic, Harness Design for Long-Running Applications.
- Infrastructure noise in measurement: Anthropic, Quantifying Infrastructure
  Noise.
- Checklist cross-checked against templates/HARNESS_CHECKLIST.md in
  ai-boost/awesome-harness-engineering (CC0).
