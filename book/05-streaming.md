# 5 · Streaming is a protocol

The UI sends a POST using Fetch with an Authorization header. The API responds with `text/event-stream`: started, delta, error and completed events. Native EventSource does not offer this POST/header interface; [our reader](../frontend/src/api.ts) parses frames across arbitrary chunks and decodes UTF-8 incrementally.

[Provider adapters](../app/providers.py) normalize text and token-usage events. The mock adapter is deterministic. OpenAI uses Responses streaming with `store=false`; the compatible adapter uses Chat Completions. A provider name/base URL/model are operator configuration, not arbitrary user-supplied URLs.

The domain does not expose SDK types. Provider independence means a common core contract, not identical feature support. This release supports text chat; tools, images, document retrieval and provider-specific reasoning controls are separate work.

Request keys prevent duplicate paid generations within an account. A second active run in the same conversation is rejected. Requests are timed out, output is bounded, and interrupted leases stop consuming concurrency after expiry. Stop sets a database cancellation flag and aborts the browser stream; supported provider HTTP connections close as the generator is cancelled. Cleanup is shielded so partial replies retain a terminal state.

The app never silently retries a paid stream after delivering text. Explicit retry creates another prompt/run and consumes another reservation. Provider failures save partial text and show a generic message without credentials or vendor response bodies.

Responses use React with a deliberately constrained Markdown renderer: raw HTML is disabled, remote images are omitted and link protocols are restricted. Code blocks and Markdown formatting improve readability without treating model output as executable HTML. See the [renderer](../frontend/src/main.tsx) and [browser assertions](../tests/e2e/test_workshop.py); safe rendering still requires validation when the renderer changes.

**Exercise:** split an SSE event across bytes and frames. Explain why a network chunk is neither a complete event nor necessarily a complete Unicode character.
