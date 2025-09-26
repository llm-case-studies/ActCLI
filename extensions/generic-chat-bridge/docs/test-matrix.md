Test Matrix (A6/A7)

Playground
- textarea.html: learn, validate, re-validate after reload
- contenteditable.html: learn, validate
- virtualized.html: observe appends with MutationObserver
- iframe.html: same-origin picking and validate inside iframe

OSS Servers (Docker)
- Rocket.Chat: DM/channel roundtrip (manual for now)
- Zulip: stream/topic roundtrip (manual for now)

Triad Scenario (A7)
- 2 humans (Rocket.Chat/Zulip) + Llama-3-8B (Ollama)
- Uniform participant interface; confirm consistent events in audit.json

Notes
- CI: Cache images or run Playground-only to stay lightweight
- Selector breaks: re-learn prompt should trigger (manual edge case)

