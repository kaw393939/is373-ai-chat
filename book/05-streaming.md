# 5 · Streaming is a protocol

A learner sees half a reply and a stopped spinner. Did the model finish, did the network end, or did the user cancel? Those outcomes can look similar in a browser while having different persistence and billing consequences. This chapter follows that distinction from bytes to business state.

**Learning outcomes:** explain network chunks versus protocol frames; trace admission, streaming and cleanup; evaluate when retry is safe; define evidence that would establish a provider's completion contract. Prerequisites: [transactions](03-data.md), [identity](04-auth.md), and the [glossary](glossary.md).

## How the problem developed

The early Web connected documents; W3C's historical account traces Berners-Lee's 1989 proposal and subsequent clients and servers. An interactive application adds a different question: how does a page learn that something changed without navigating to another document? Repeated polling, a streamed HTTP response and a WebSocket connection are alternative answers, with different connection and state costs. This is an evolution in requirements, not evidence that older pages became useless. [Web history](references.md#ref-web).

The HTML standard defines server-sent event (SSE) framing and the native `EventSource` subscription interface. `EventSource` also has reconnection behavior; our authenticated POST uses Fetch and our own reader instead. We therefore own parsing and failure handling rather than automatically inheriting the entire native interface's behavior. [SSE specification](references.md#ref-sse).

## Worked case: bytes are not events

Suppose a synthetic response contains `event: delta`, followed by a JSON data line and a blank line. A network read can end halfway through that JSON, or halfway through the bytes encoding a character such as `é`. Parsing every read as JSON would reject valid traffic. `consume` first decodes bytes incrementally with `TextDecoder`, then retains text until the blank-line frame delimiter appears. Only a complete frame becomes an application event.

Our UI sends a POST with an Authorization header. The API returns `text/event-stream` events named `started`, `delta`, `error` and `completed`. The server first reserves capacity and commits the prompt/run; it does not hold that admission transaction throughout the external model call. Later short transactions save partial output and terminal state. A terminal state means the run has ended; it does not alone prove that the provider supplied a complete answer.

The mock adapter yields deterministic text. The OpenAI adapter uses Responses with `store=false`; the compatible adapter uses Chat Completions. Vendor HTTP objects remain behind the adapter. Provider independence means a shared text-chat boundary, not equal model capabilities, output quality or prices. Tools, images, retrieval and reasoning controls require additional contracts.

## Read the implementation

| Symbol | Decision to investigate |
|---|---|
| [`consume`](../frontend/src/api.ts) | Why buffer both decoded text and frames? What does EOF establish? |
| [`prepare_run`, `generate`](../app/services.py) | Which state is committed before output, and which failures persist partial text? |
| [`Provider`, `HTTPProvider.stream`, `make_provider`](../app/providers.py) | Where are vendor payloads translated into the shared boundary? |
| [`send`, `stop`, Markdown rendering](../frontend/src/main.tsx) | How do browser aborts, server cancellation and safe display cooperate? |
| [Provider tests](../tests/unit/test_providers.py), [chat tests](../tests/integration/test_chat.py) | Which success, failure and cancellation cases are actually asserted? |

Request keys reject duplicate generations within an account; explicit retry creates another prompt/run and another reservation. Paid streams are not silently restarted after text has appeared. Stop requests database cancellation and aborts the browser stream. Timeout/output bounds and expiring leases limit unfinished work. Cleanup preserves partial text. The normalized contract uses immutable `TextDelta`, `TokenUsage` and `StreamEnd` values: usage is optional; EOF without terminal completion fails. Compatible `stop` means complete, `length` means incomplete, and filtering/refusal means refused. Unsupported tool finishes fail under this text-chat contract. Sources: [Responses streaming events](https://developers.openai.com/api/reference/resources/responses/streaming-events), [Chat Completions streaming events](https://developers.openai.com/api/reference/resources/chat/subresources/completions/streaming-events).

## Alternatives and limits

Polling can simplify short jobs at the cost of repeated requests and delay. Native EventSource suits GET subscriptions when its authentication/reconnection model fits. WebSockets support bidirectional interaction, but introduce their own lifecycle responsibilities. Choose using message direction, latency, authentication and recovery requirements.

Model output is untrusted input. React's constrained Markdown renderer disables raw HTML, omits remote images and restricts link protocols. That is a deliberate feature boundary, not a universal guarantee for future renderer changes. Browser state races and cross-tab sessions also remain separate concerns.

**Laboratory:** [Lab 05 — stream contracts](labs/05-stream-contract.md); use mock transport and a disposable local environment. **Evaluate:** specify the observation that distinguishes provider success from transport EOF, and reject one unsafe retry policy. For user-interface evidence, continue with [Lab 06 — browser accessibility](labs/06-browser-accessibility.md).


## Keep transport at its boundary

`generate` now emits typed application notifications (`Started`, `Delta`, `Error`, `Completed`) from [events.py](../app/events.py); [transport.py](../app/transport.py) translates them into the existing SSE event names and JSON data. The provider outcome mapping admits only complete, incomplete and refused terminals. An unsupported terminal cannot become a persisted success. Use-case failures carry domain kinds, and the HTTP adapter selects status codes. Provider normalization, durable generation state and browser frame encoding can change independently without copying HTTP concerns into every service.
