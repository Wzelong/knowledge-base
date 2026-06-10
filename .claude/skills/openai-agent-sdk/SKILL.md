---
name: openai-agent-sdk
description: Build agents with the OpenAI Agents SDK - define agents, tools, handoffs, sessions, guardrails, streaming, and MCP. Includes current OpenAI and Gemini model slugs with pricing. Use when writing or modifying agent code with @openai/agents or openai-agents, choosing a model, or estimating token cost.
---

# OpenAI Agents SDK

An agent packages a model, instructions, and optional tools, handoffs, guardrails, and structured output. One run is one application turn: the runner loops over model calls and tool/handoff execution until the model returns a final answer.

Examples below are Python (`pip install openai-agents`). The TypeScript SDK (`npm install @openai/agents zod`) mirrors the same concepts. Set `OPENAI_API_KEY`.

Deeper references (read only when the task needs them):
- [models.md](models.md) — OpenAI and Gemini model slugs with pricing
- [sandboxes.md](sandboxes.md) — sandbox agents: workspace, filesystem/shell, providers, resume, memory
- [voice.md](voice.md) — voice agents (chained and speech-to-speech) and transport options
- [evals.md](evals.md) — trace grading, datasets, and eval runs

## Define and run one agent

Start with the smallest agent that owns a clear task. Set `model` explicitly in production.

```python
from agents import Agent, Runner

agent = Agent(
    name="History tutor",
    instructions="Answer history questions clearly and concisely.",
    model="gpt-5.5",
)

result = await Runner.run(agent, "When did the Roman Empire fall?")
print(result.final_output)
```

## Tools

Use function tools for code the agent calls directly.

```python
from agents import Agent, function_tool

@function_tool
def get_weather(city: str) -> str:
    """Return the weather for a given city."""
    return f"The weather in {city} is sunny."

agent = Agent(name="Weather bot", instructions="Help with weather.", tools=[get_weather])
```

## Structured output

Use `output_type` when downstream code needs typed data instead of prose.

```python
from pydantic import BaseModel
from agents import Agent

class CalendarEvent(BaseModel):
    name: str
    date: str
    participants: list[str]

agent = Agent(name="Extractor", instructions="Extract calendar events.", output_type=CalendarEvent)
```

## Local context vs model context

Pass application state (auth, db clients, loggers) into a run without sending it to the model. Conversation history is what the model sees; run context is what your code sees.

```python
from dataclasses import dataclass
from agents import Agent, RunContextWrapper, Runner, function_tool

@dataclass
class UserInfo:
    name: str
    uid: int

@function_tool
async def fetch_user_age(wrapper: RunContextWrapper[UserInfo]) -> str:
    return f"{wrapper.context.name} is 47 years old."

agent = Agent[UserInfo](name="Assistant", tools=[fetch_user_age])
result = await Runner.run(agent, "How old is the user?", context=UserInfo(name="John", uid=123))
```

## Orchestration: handoffs vs agents-as-tools

| Pattern | Use when | Result |
|---------|----------|--------|
| Handoffs | A specialist should own the next response | Control moves to the specialist |
| Agents as tools | A manager should keep ownership and call specialists as bounded helpers | Manager synthesizes the final answer |

Add specialists only when instructions, tools, or policy genuinely differ. Keep each `handoff_description` short and concrete.

```python
from agents import Agent

history = Agent(name="History tutor", handoff_description="History questions.", instructions="...")
math = Agent(name="Math tutor", handoff_description="Math questions.", instructions="...")
triage = Agent(name="Triage", instructions="Route to the right specialist.", handoffs=[history, math])

# Agents as tools
summarizer = Agent(name="Summarizer", instructions="Summarize text concisely.")
manager = Agent(name="Assistant", tools=[summarizer.as_tool(
    tool_name="summarize_text", tool_description="Summarize the supplied text.")])
```

## Conversation state

Pick one strategy per conversation; don't mix local replay with server-managed state.

| Strategy | State lives | Best for |
|----------|-------------|----------|
| Local history (`result.to_input_list()`) | Your app | Small loops, maximum control |
| `session` | Your storage + SDK | Persistent, resumable runs |
| `conversation_id` | OpenAI Conversations API | Shared state across services |
| `previous_response_id` | OpenAI Responses API | Cheapest response-to-response chaining |

```python
from agents import Agent, Runner, SQLiteSession

agent = Agent(name="Tour guide", instructions="Compact travel facts.")
session = SQLiteSession("conversation_123")

await Runner.run(agent, "What city is the Golden Gate Bridge in?", session=session)
await Runner.run(agent, "What state is it in?", session=session)
```

## Streaming

Same loop and state strategies; consume events as the run happens. Wait for the stream to finish before treating the run as settled.

```python
from openai.types.responses import ResponseTextDeltaEvent
from agents import Agent, Runner

stream = Runner.run_streamed(agent, "Three short facts about Saturn.")
async for event in stream.stream_events():
    if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
        print(event.data.delta, end="", flush=True)
print(stream.final_output)
```

## Guardrails and approvals

| Use case | Control |
|----------|---------|
| Block disallowed input before the main model runs | Input guardrail |
| Validate or redact final output | Output guardrail |
| Pause before side effects (cancellations, edits, shell, sensitive MCP) | Human-in-the-loop approval |

A tripped input guardrail raises `InputGuardrailTripwireTriggered`. Input guardrails run only for the first agent; output guardrails only for the agent producing the final output. For per-tool checks in manager workflows, validate next to the tool.

```python
from agents import Agent, Runner, function_tool

@function_tool(needs_approval=True)
async def cancel_order(order_id: int) -> str:
    return f"Cancelled order {order_id}"

agent = Agent(name="Support", instructions="Ask for approval when needed.", tools=[cancel_order])

result = await Runner.run(agent, "Cancel order 123.")
if result.interruptions:
    state = result.to_state()
    for interruption in result.interruptions:
        state.approve(interruption)
    result = await Runner.run(agent, state)
```

Approvals are paused runs, not new turns: resume from `state` to keep turn counts and continuation IDs consistent. Serialize `state` to approve later.

## MCP

```python
from agents import Agent, Runner
from agents.mcp import MCPServerStdio

async with MCPServerStdio(
    name="Filesystem MCP",
    params={"command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", "./files"]},
) as server:
    agent = Agent(name="FS assistant", instructions="Read files before answering.", mcp_servers=[server])
    result = await Runner.run(agent, "List the files.")
```

Use hosted MCP (`HostedMCPTool`) for public remote servers; use local transports when your runtime owns connectivity and approvals.

## Tracing

Tracing is on by default on the server-side SDK path. Inspect runs in the [Traces dashboard](https://platform.openai.com/traces). Wrap multiple runs in one trace with `trace("Workflow name")` (Python) / `withTrace` (TS).

## Olva backend

This project wraps every agent call with workflow logging — never call `Runner.run` directly. Use the [ai-service](../ai-service/SKILL.md) skill (`logged_run` inside `ai_workflow`).
