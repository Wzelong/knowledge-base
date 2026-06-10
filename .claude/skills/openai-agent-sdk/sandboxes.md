# Sandbox agents

Contents:
- When to use
- Pieces
- Quick start (Unix-local)
- Switch providers
- Capabilities
- Manifest inputs
- Secrets
- Resume and seed state
- Memory across runs
- Compose with handoffs and tools
- Providers

A sandbox gives an agent an isolated Unix-like environment: filesystem, shell, packages, mounts, ports, and snapshots. `SandboxAgent` keeps the full `Agent` surface (instructions, tools, handoffs, MCP, model settings, output, guardrails); what changes is that the runner prepares it against a live sandbox session. Beta — APIs may change. Available in the Python and TypeScript SDKs.

Key boundary: the **harness** (control plane) owns the agent loop, model calls, tool routing, approvals, tracing, and run state; **compute** (the sandbox) runs files, commands, and ports. Keep auth, billing, and audit in the harness; keep narrow credentials and mounts in the sandbox. A turn is still a model step, not a single shell command.

## When to use

Use a sandbox when the answer depends on workspace work, not just prompt reasoning: a directory of documents, files your app inspects later, commands/packages/scripts, generated artifacts (Markdown, CSV, screenshots, sites), a service on an exposed port, or work that pauses for review and resumes. If you only need a short response, use the basic Agents SDK runtime; if shell is one occasional tool, use the hosted shell tool instead.

## Pieces

| Piece | Owns |
|-------|------|
| `SandboxAgent` | Agent definition plus sandbox defaults |
| `Manifest` | Fresh-session workspace contract (files, repos, mounts, env, users) |
| Capabilities | Sandbox-native behavior attached to the agent |
| Sandbox client | Provider integration (Unix-local, Docker, hosted) |
| Sandbox session | Live execution environment |
| Sandbox run config | Per-run session source and provider options |
| Saved state | `RunState`, serialized session state, snapshots |

Sandbox-specific defaults go on `SandboxAgent`; per-run session choices go in the run's sandbox config.

## Quick start (Unix-local)

Start with Unix-local on macOS/Linux. The runner creates a temp workspace from the agent's default manifest and cleans up after.

```python
from agents import Runner
from agents.run import RunConfig
from agents.sandbox import Manifest, SandboxAgent, SandboxRunConfig
from agents.sandbox.capabilities import Shell
from agents.sandbox.entries import File
from agents.sandbox.sandboxes.unix_local import UnixLocalSandboxClient

manifest = Manifest(entries={
    "brief.md": File(content=b"# Account brief\n- Renewal: 2026-04-15\n"),
})

agent = SandboxAgent(
    name="Renewal analyst",
    model="gpt-5.5",
    instructions="Review the workspace before answering; cite file names.",
    default_manifest=manifest,
    capabilities=[Shell()],
)

result = await Runner.run(
    agent,
    "Summarize the renewal blockers and recommend next actions.",
    run_config=RunConfig(
        sandbox=SandboxRunConfig(client=UnixLocalSandboxClient()),
        workflow_name="Unix-local review",
    ),
)
print(result.final_output)
```

## Switch providers

The provider is part of run config, not the agent. Keep the `SandboxAgent`, manifest, and capabilities stable; swap the client. Docker gives local container isolation; hosted providers follow the same pattern.

```python
from docker import from_env as docker_from_env
from agents.run import RunConfig
from agents.sandbox import SandboxRunConfig
from agents.sandbox.config import DEFAULT_PYTHON_SANDBOX_IMAGE
from agents.sandbox.sandboxes.docker import DockerSandboxClient, DockerSandboxClientOptions

run_config = RunConfig(sandbox=SandboxRunConfig(
    client=DockerSandboxClient(docker_from_env()),
    options=DockerSandboxClientOptions(image=DEFAULT_PYTHON_SANDBOX_IMAGE),
))
```

## Capabilities

Default `SandboxAgent` includes filesystem, shell, and compaction. Passing a `capabilities` list **replaces** the defaults, so re-include any you still need (`Capabilities.default() + [...]`).

| Capability | Add when |
|-----------|----------|
| `Shell` | Agent needs command execution |
| `Filesystem` | Agent edits files or inspects images (`apply_patch`, `view_image`) |
| `Skills` | Skill discovery/materialization in the sandbox |
| `Memory` | Follow-on runs read/generate memory (requires `Shell`; live updates need `Filesystem`) |
| `Compaction` | Long flows need context trimming |

Skill sources: lazy local dir (large, discover-then-load), local dir (small, staged up front), or Git repo (own release cadence / many sandboxes).

## Manifest inputs

Workspace-relative paths only (no absolute or `..`). Put repos, inputs, and output dirs in the manifest; put long task specs in workspace files (`repo/task.md`, `AGENTS.md`).

| Input | Use for |
|-------|---------|
| `File`, `Dir` | Small synthetic inputs, helpers, output dirs |
| Local file/dir | Host files materialized into the sandbox |
| Git repo | Repository fetched into the workspace |
| `S3Mount`, `GCSMount`, `R2Mount`, `AzureBlobMount`, `BoxMount`, `S3FilesMount` | External storage |
| `environment` | Env vars at startup |
| `users`, `groups` | Sandbox-local OS accounts (providers that support it) |

Mounts are ephemeral: snapshot/persistence flows skip mounted remote storage.

## Secrets

Treat credentials as runtime config, not prompt content. Never put them in prompts, instructions, task files, committed manifests, or artifacts. Prefer provider-native secret systems; scope storage credentials to the mount that needs them; use `Manifest.environment` for startup values and mark sensitive/generated entries ephemeral. Review artifacts before moving them out.

## Resume and seed state

| Surface | Restores | Use when |
|---------|----------|----------|
| `RunState` | Harness state: model items, tool state, approvals, active agent | Runner carries the workflow across pauses |
| Session state | Serialized sandbox session to reconnect to | Your app/job system stores provider session state |
| `snapshot` | Saved workspace contents to seed a fresh session | A new run starts from saved files, not empty |

Session resolution order: injected live `session` → resume from `RunState` → explicit serialized state → fresh session (using per-run manifest, else the agent default). Fresh-session inputs (`manifest`, `snapshot`) apply only when the runner creates a new session.

## Memory across runs

Sandbox memory distills lessons from prior workspace runs into files the agent reads later (separate from `Session` message history). Enable with `Memory()` (+ `Shell`, `Filesystem`). Reads use progressive disclosure: `memory_summary.md` injected at run start, agent searches `MEMORY.md`, opens rollout summaries on demand. To reuse memory later, preserve memory dirs via the same live session, resumed state, a snapshot, or persistent storage (e.g. S3).

## Compose with handoffs and tools

- **Handoff**: a non-sandbox intake agent delegates the workspace-heavy part to a sandbox agent, which becomes the active agent.
- **Agents as tools**: an outer orchestrator calls sandbox agents as nested tools, each with its own sandbox run config and provider.

## Providers

| Provider | Client |
|----------|--------|
| Unix-local | `UnixLocalSandboxClient` |
| Docker | `DockerSandboxClient` |
| Blaxel | `BlaxelSandboxClient` |
| Cloudflare | `CloudflareSandboxClient` |
| Daytona | `DaytonaSandboxClient` |
| E2B | `E2BSandboxClient` |
| Modal | `ModalSandboxClient` |
| Runloop | `RunloopSandboxClient` |
| Vercel | `VercelSandboxClient` |

Start with Unix-local or Docker; move to a hosted provider for managed execution, scaling, previews, storage mounts, snapshots, or credentials kept outside your app server.
