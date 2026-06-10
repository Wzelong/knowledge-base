# Evaluating agent workflows

Two stages: trace grading while debugging, then datasets and eval runs for repeatability.

## Trace grading (start here)

A trace is the end-to-end record of one run — model calls, tool calls, guardrails, handoffs. Graders score traces with structured criteria to catch regressions at scale. Use it to answer: did the agent pick the right tool, did a handoff happen when it should, did the run violate an instruction or policy, did a prompt/routing change improve behavior.

Workflow:
1. Open Logs > Traces in the dashboard.
2. Inspect a representative workflow trace (from an SDK app with tracing on, or Agent Builder).
3. Create a grader and run it against selected traces.
4. Refine prompts, tool surfaces, routing, or guardrails from the results.

Get high-signal traces first (see Tracing in SKILL.md), then formalize graders.

## Datasets and eval runs

Once you know what "good" looks like, move from individual traces to repeatable datasets and eval runs to benchmark changes, compare prompts, and run larger-scale evaluation over time. For evaluation against external models, eval APIs, or large-scale batch evaluation, use the platform Evals surface alongside datasets.

## Related surfaces

- Evaluation getting-started: continuous-improvement flywheel.
- Evals: external-model evaluation and the evals API.
- Prompt optimizer: use a dataset to automatically improve prompts.
