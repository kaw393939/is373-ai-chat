import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import ts from "typescript";

const source = ts.transpileModule(
  await readFile(new URL("../src/api.ts", import.meta.url), "utf8"),
  {
    compilerOptions: {
      target: ts.ScriptTarget.ES2022,
      module: ts.ModuleKind.ESNext,
    },
  },
).outputText;

function environment(fetcher = async () => Response.json({})) {
  const storage = new Map();
  const broadcasts = [];
  const channels = [];
  class Channel extends EventTarget {
    constructor() {
      super();
      channels.push(this);
    }
    postMessage(message) {
      broadcasts.push(message);
      for (const peer of channels)
        if (peer !== this)
          queueMicrotask(() =>
            peer.dispatchEvent(new MessageEvent("message", { data: message })),
          );
    }
  }
  let queue = Promise.resolve();
  Object.assign(globalThis, {
    window: new EventTarget(),
    BroadcastChannel: Channel,
    fetch: fetcher,
    localStorage: {
      getItem: (key) => storage.get(key) ?? null,
      setItem: (key, value) => storage.set(key, value),
    },
  });
  Object.defineProperty(globalThis, "navigator", {
    configurable: true,
    value: {
      locks: {
        request: (_name, callback) => {
          const operation = queue.then(callback);
          queue = operation.catch(() => {});
          return operation;
        },
      },
    },
  });
  return { storage, broadcasts };
}
async function client() {
  return import(
    `data:text/javascript;base64,${Buffer.from(source).toString("base64")}#${crypto.randomUUID()}`
  );
}
function streamed(text, width = 1) {
  const bytes = new TextEncoder().encode(text);
  return new Response(
    new ReadableStream({
      start(controller) {
        for (let offset = 0; offset < bytes.length; offset += width)
          controller.enqueue(bytes.slice(offset, offset + width));
        controller.close();
      },
    }),
  );
}
const frame = (kind, payload) =>
  `event: ${kind}\r\ndata: ${JSON.stringify(payload)}\r\n\r\n`;
const started = frame("started", { run_id: "run-1" });
const completed = frame("completed", { status: "complete", tokens: null });

await test("SSE preserves split UTF-8 characters, frames and unknown usage", async () => {
  environment();
  const api = await client();
  const events = [];
  await api.consume(
    streamed(started + frame("delta", { text: "naïve 🐍" }) + completed),
    (event) => events.push(event),
  );
  assert.deepEqual(events, [
    { kind: "started", run_id: "run-1" },
    { kind: "delta", text: "naïve 🐍" },
    { kind: "completed", status: "complete", tokens: null },
  ]);
});
await test("SSE rejects malformed payloads and out-of-order/incomplete replies", async () => {
  environment();
  const api = await client();
  for (const [kind, payload] of [
    ["delta", { text: 7 }],
    ["started", {}],
    ["started", { run_id: "../admin" }],
    ["completed", { status: "unknown", tokens: 0 }],
    ["completed", { status: "complete", tokens: -1 }],
    ["completed", { status: "complete", tokens: 1.5 }],
    ["error", { message: [] }],
  ])
    assert.throws(() => api.parseEvent(kind, payload), /Invalid stream event/);
  for (const content of [
    frame("delta", { text: "early" }) + completed,
    started + started + completed,
    started + completed + frame("delta", { text: "late" }),
    started,
    started + "event: delta\ndata: {}",
    started + "event: delta\ndata: not-json\n\n",
    started + "event: delta\n\n" + completed,
    started + 'data: {"text":"missing kind"}\n\n' + completed,
  ])
    await assert.rejects(api.consume(streamed(content, 7), () => {}));
  for (const status of [
    "incomplete",
    "refused",
    "failed",
    "cancelled",
    "interrupted",
  ])
    assert.equal(
      api.parseEvent("completed", { status, tokens: null }).status,
      status,
    );
});
await test("two clients serialize cookie refresh without publishing bearer secrets", async () => {
  let active = 0;
  let maximum = 0;
  let cookie = 0;
  const { storage, broadcasts } = environment(async () => {
    maximum = Math.max(maximum, ++active);
    await new Promise((resolve) => setTimeout(resolve, 5));
    const result = Response.json({
      access_token: `private-bearer-${++cookie}`,
    });
    active--;
    return result;
  });
  const a = await client();
  const b = await client();
  assert.deepEqual(await Promise.all([a.refresh(), b.refresh()]), [true, true]);
  assert.equal(maximum, 1);
  assert.equal(cookie, 2);
  assert.ok(
    [...storage.values(), ...broadcasts].every(
      (value) => !String(value).includes("private-bearer"),
    ),
  );
});
await test("logout waits for refresh's cookie but immediately invalidates its token", async () => {
  let finish;
  let startedRefresh;
  const startedPromise = new Promise((resolve) => {
    startedRefresh = resolve;
  });
  const calls = [];
  environment(async (path, options) => {
    calls.push([path, new Headers(options?.headers).get("Authorization")]);
    if (path.endsWith("/refresh")) {
      startedRefresh();
      return new Promise((resolve) => {
        finish = resolve;
      });
    }
    if (path.endsWith("/login"))
      return Response.json({
        access_token: "private-initial",
        user: { id: "owner" },
      });
    if (path.endsWith("/logout")) return new Response(null, { status: 204 });
    return Response.json({});
  });
  const api = await client();
  await api.signIn("synthetic@example.org", "synthetic-password");
  const pending = api.refresh();
  await startedPromise;
  const logout = api.signOut();
  await api.api("/data");
  finish(Response.json({ access_token: "private-obsolete" }));
  assert.equal(await pending, false);
  await logout;
  await api.api("/data");
  assert.deepEqual(
    calls.filter(([path]) => path === "/api/data").map(([, token]) => token),
    [null, null],
  );
  assert.deepEqual(
    calls.filter(([path]) => path.includes("/auth/")).map(([path]) => path),
    ["/api/auth/login", "/api/auth/refresh", "/api/auth/logout"],
  );
});
await test("a JSON body that finishes after logout cannot repopulate private state", async () => {
  let complete;
  environment(async (path) =>
    path.endsWith("/logout")
      ? new Response(null, { status: 204 })
      : new Response(
          new ReadableStream({
            start(controller) {
              complete = () => {
                controller.enqueue(
                  new TextEncoder().encode('{"private":"old-user"}'),
                );
                controller.close();
              };
            },
          }),
        ),
  );
  const api = await client();
  const pending = api.api("/slow");
  // Headers are already available; body decoding remains pending.
  await Promise.resolve();
  await api.signOut();
  complete();
  await assert.rejects(pending, (error) => error.name === "AbortError");
});

await test("a fresh page after explicit logout never redeems the remaining old cookie", async () => {
  const calls = [];
  environment(async (path) => {
    calls.push(path);
    return path.endsWith("/logout")
      ? new Response(null, { status: 204 })
      : Response.json({ access_token: "private-cookie" });
  });
  const first = await client();
  await first.signOut();
  const reloaded = await client();
  assert.equal(await reloaded.refresh(), false);
  assert.deepEqual(calls, ["/api/auth/logout"]);
});

await test("MFA replacement preserves its recovery receipt while queued refresh is invalidated", async () => {
  let complete;
  let entered;
  const startedConfirmation = new Promise((resolve) => {
    entered = resolve;
  });
  const { storage } = environment(async (path, options) => {
    if (path.endsWith("/login"))
      return Response.json({
        access_token: "private-mfa",
        user: { id: "owner" },
      });
    if (path.endsWith("/mfa/confirm")) {
      assert.equal(
        new Headers(options.headers).get("Authorization"),
        "Bearer private-mfa",
      );
      entered();
      return new Promise((resolve) => {
        complete = resolve;
      });
    }
    if (path.endsWith("/logout")) return new Response(null, { status: 204 });
    if (path.endsWith("/refresh"))
      throw new Error("An obsolete queued refresh must not be sent");
    return Response.json({ detail: "Session revoked" }, { status: 401 });
  });
  const api = await client();
  await api.signIn("synthetic@example.org", "synthetic-password");
  const confirmation = api.confirmMfa("123456");
  await startedConfirmation;
  const obsoleteRequest = api.api("/private");
  // Let its 401 reach the lock queue while confirmation owns the cookie lock.
  await new Promise((resolve) => setTimeout(resolve, 0));
  complete(Response.json({ recovery_codes: ["one-use-synthetic"] }));
  assert.deepEqual(await confirmation, {
    recovery_codes: ["one-use-synthetic"],
  });
  await assert.rejects(obsoleteRequest, (error) => error.name === "AbortError");
  assert.ok(
    [...storage.values()].every(
      (value) => !value.includes("one-use-synthetic"),
    ),
  );
});
