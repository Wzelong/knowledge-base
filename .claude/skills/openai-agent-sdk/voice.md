# Voice agents and transport

Voice is an SDK-first path — Agent Builder doesn't support voice workflows.

## Two voice paths

- **Chained pipeline**: speech-to-text → a normal text agent (the same agent loop, tools, handoffs, guardrails) → text-to-speech. Use when you want to reuse existing text agents and inspect intermediate transcripts.
- **Speech-to-speech (realtime)**: low-latency live audio over WebRTC or WebSocket. Use for natural, interruptible conversation where round-tripping through text adds too much latency.

Build on the Voice agents guide and the live audio (realtime) API guide for session setup, audio formats, and interruption handling.

## Transport (text runs)

Most runs use the default OpenAI provider path. Two distinctions:

| Need | Use |
|------|-----|
| Standard SDK runs on OpenAI | Default OpenAI provider path |
| Many repeated Responses round trips over a socket | Responses WebSocket transport (still the normal text-and-tools loop) |
| Non-OpenAI / mixed-provider stack | Provider or adapter surface in the language-specific SDK docs |

The Responses WebSocket transport is separate from the voice session path: it speeds up text-and-tools runs but is not a live audio session. Live audio over WebRTC/WebSocket is only for the voice/realtime path above.
