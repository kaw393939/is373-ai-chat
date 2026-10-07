import type {
  TerminalStatus,
  LoginResult,
  SignedIn,
  StreamEvent,
} from "./contracts";

// No bearer secret enters localStorage/BroadcastChannel. The opaque marker only
// invalidates obsolete work; Web Locks serialize cookie-changing operations.
const markerKey = "373-session-generation";
const listeners = new Set<() => void>();
let token = "";
let rotation: Promise<boolean> | null = null;
function readMarker() {
  try {
    return localStorage.getItem(markerKey) ?? "";
  } catch {
    return null;
  }
}
let observedMarker = readMarker();
const channel =
  typeof BroadcastChannel === "undefined"
    ? null
    : new BroadcastChannel("373-session-events");

export function sessionStamp() {
  return readMarker();
}
export function ownsSession(stamp: string | null) {
  return stamp !== null && readMarker() === stamp;
}
export function isAbort(error: unknown) {
  return error instanceof DOMException && error.name === "AbortError";
}
function obsolete() {
  return new DOMException("Session or operation changed", "AbortError");
}
export function onSessionInvalidated(listener: () => void) {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}
function notify() {
  token = "";
  for (const listener of listeners) listener();
}
function observe() {
  const marker = readMarker();
  // Read the durable marker rather than trust event ordering between tabs.
  if (marker !== observedMarker) {
    observedMarker = marker;
    notify();
  }
}
channel?.addEventListener("message", observe);
window.addEventListener("storage", (event) => {
  if (event.key === markerKey) observe();
});
function invalidate(signedOut = true) {
  // The durable sign-out intent also survives an immediate reload before the
  // server's logout receipt arrives; startup must not redeem that old cookie.
  const marker = `${signedOut ? "out" : "in"}:${crypto.randomUUID()}`;
  localStorage.setItem(markerKey, marker);
  observedMarker = marker;
  notify();
  channel?.postMessage("session-changed");
  return marker;
}
function coordinator() {
  if (!navigator.locks || readMarker() === null)
    throw new Error(
      "Sign-in needs a current browser with Web Locks and local site storage. Use HTTPS or localhost.",
    );
  return navigator.locks;
}
export function setToken(value: string) {
  if (!value) invalidate();
  else token = value;
}
async function checked(response: Response) {
  if (!response.ok) {
    const body: unknown = await response.json().catch(() => null);
    throw new Error(
      body &&
        typeof body === "object" &&
        "detail" in body &&
        typeof body.detail === "string"
        ? body.detail
        : "Check your inputs and try again.",
    );
  }
  return response;
}
async function authFetch(
  path: string,
  body?: unknown,
  allowFailure = false,
  authenticated = false,
) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 15000);
  try {
    const headers = new Headers();
    if (body !== undefined) headers.set("Content-Type", "application/json");
    if (authenticated && token) headers.set("Authorization", `Bearer ${token}`);
    const response = await fetch("/api" + path, {
      method: "POST",
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: controller.signal,
      keepalive: path === "/auth/logout",
    });
    if (!allowFailure) await checked(response);
    const result: unknown =
      response.status === 204 ? null : await response.json();
    return { response, result };
  } finally {
    clearTimeout(timer);
  }
}
export async function signIn(
  email: string,
  password: string,
): Promise<LoginResult> {
  const locks = coordinator();
  const stamp = invalidate(false);
  return locks.request("373-auth-cookie", async () => {
    if (!ownsSession(stamp)) throw obsolete();
    const { result: value } = await authFetch("/auth/login", {
      email,
      password,
    });
    const result = value as LoginResult;
    if (!ownsSession(stamp)) throw obsolete();
    if ("access_token" in result) token = result.access_token;
    return result;
  });
}
export async function verifyMfa(
  challenge: string,
  code: string,
): Promise<SignedIn> {
  const stamp = sessionStamp();
  return coordinator().request("373-auth-cookie", async () => {
    if (!ownsSession(stamp)) throw obsolete();
    const { result: value } = await authFetch("/auth/mfa/verify", {
      challenge,
      code,
    });
    const result = value as SignedIn;
    if (!ownsSession(stamp)) throw obsolete();
    token = result.access_token;
    return result;
  });
}
export async function signOut() {
  const locks = coordinator();
  invalidate(); // Invalidate pending work before waiting for another tab's refresh.
  await locks.request("373-auth-cookie", async () => {
    await authFetch("/auth/logout");
  });
}
/** Factor replacement is a terminal session transition. Preserve its one-time
 * receipt at the auth boundary while invalidating all other private work. */
export async function confirmMfa(
  code: string,
): Promise<{ recovery_codes: string[] }> {
  const stamp = sessionStamp();
  return coordinator().request("373-auth-cookie", async () => {
    if (!ownsSession(stamp)) throw obsolete();
    const { result } = await authFetch(
      "/auth/mfa/confirm",
      { code },
      false,
      true,
    );
    if (!ownsSession(stamp)) throw obsolete();
    if (
      !result ||
      typeof result !== "object" ||
      !("recovery_codes" in result) ||
      !Array.isArray(result.recovery_codes) ||
      !result.recovery_codes.every((value) => typeof value === "string")
    )
      throw new Error("Invalid recovery-code receipt.");
    const signedOut = invalidate();
    // The backend has already revoked every session. Clearing the cookie is
    // best effort; a network error must not hide newly issued recovery codes.
    await authFetch("/auth/logout").catch(() => {});
    if (!ownsSession(signedOut)) throw obsolete();
    return { recovery_codes: result.recovery_codes };
  });
}
export async function refresh(): Promise<boolean> {
  if (rotation) return rotation;
  const stamp = sessionStamp();
  if (stamp?.startsWith("out:")) return false;
  const task = (async () =>
    await coordinator().request("373-auth-cookie", async () => {
      if (!ownsSession(stamp)) return false;
      const { response, result } = await authFetch(
        "/auth/refresh",
        undefined,
        true,
      );
      if (!ownsSession(stamp)) return false;
      if (
        !response.ok ||
        !result ||
        typeof result !== "object" ||
        !("access_token" in result) ||
        typeof result.access_token !== "string"
      ) {
        invalidate();
        return false;
      }
      token = result.access_token;
      return true;
    }))();
  rotation = task;
  try {
    return await task;
  } finally {
    if (rotation === task) rotation = null;
  }
}
export async function request(
  path: string,
  options: RequestInit = {},
  retry = true,
): Promise<Response> {
  const stamp = sessionStamp();
  const headers = new Headers(options.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (options.body) headers.set("Content-Type", "application/json");
  const response = await fetch("/api" + path, { ...options, headers });
  if (!ownsSession(stamp)) {
    await response.body?.cancel().catch(() => {});
    throw obsolete();
  }
  if (response.status === 401 && retry && token) {
    // Free this response before rotating; the retry obtains the new bearer token.
    const refreshed = await refresh();
    if (refreshed) {
      await response.body?.cancel().catch(() => {});
      return request(path, options, false);
    }
    if (!ownsSession(stamp)) throw obsolete();
  }
  return checked(response);
}
export async function api<T = unknown>(
  path: string,
  method = "GET",
  body?: unknown,
  signal?: AbortSignal,
): Promise<T> {
  const stamp = sessionStamp();
  const response = await request(path, {
    method,
    body: body === undefined ? undefined : JSON.stringify(body),
    signal,
  });
  const result = response.status === 204 ? undefined : await response.json();
  // A delayed body can finish after logout even when its headers arrived earlier.
  if (!ownsSession(stamp)) throw obsolete();
  return result as T;
}
export function parseEvent(kind: string, value: unknown): StreamEvent {
  if (!value || typeof value !== "object")
    throw new Error("Invalid stream event.");
  const data = value as Record<string, unknown>;
  if (
    kind === "started" &&
    typeof data.run_id === "string" &&
    /^[a-zA-Z0-9_-]{1,64}$/.test(data.run_id)
  )
    return { kind, run_id: data.run_id };
  if (kind === "delta" && typeof data.text === "string")
    return { kind, text: data.text };
  if (kind === "error" && typeof data.message === "string")
    return { kind, message: data.message };
  const statuses = [
    "complete",
    "failed",
    "cancelled",
    "interrupted",
    "incomplete",
    "refused",
  ];
  if (
    kind === "completed" &&
    typeof data.status === "string" &&
    statuses.includes(data.status) &&
    (data.tokens === null ||
      (typeof data.tokens === "number" &&
        Number.isSafeInteger(data.tokens) &&
        data.tokens >= 0))
  )
    return {
      kind,
      status: data.status as TerminalStatus,
      tokens: data.tokens as number | null,
    };
  throw new Error("Invalid stream event.");
}
export async function consume(
  response: Response,
  onEvent: (event: StreamEvent) => void,
) {
  if (!response.body) throw new Error("The response has no stream.");
  const reader = response.body.getReader();
  // A network chunk may split a UTF-8 character or an SSE frame. Decode incrementally,
  // then buffer until the protocol delimiter arrives; see book/05-streaming.md.
  const decoder = new TextDecoder();
  let buffer = "";
  let started = false;
  let completed = false;
  try {
    while (true) {
      const { value, done } = await reader.read();
      buffer += decoder.decode(value, { stream: !done }).replace(/\r/g, "");
      let boundary: number;
      while ((boundary = buffer.indexOf("\n\n")) >= 0) {
        const frame = buffer.slice(0, boundary);
        buffer = buffer.slice(boundary + 2);
        const lines = frame.split("\n");
        const kind = lines
          .find((line) => line.startsWith("event:"))
          ?.slice(6)
          .trim();
        const data = lines
          .filter((line) => line.startsWith("data:"))
          .map((line) => line.slice(5).trimStart())
          .join("\n");
        if (kind || data) {
          if (!kind || !data) throw new Error("Invalid stream frame.");
          const event = parseEvent(kind, JSON.parse(data));
          if (completed || (event.kind !== "started" && !started))
            throw new Error("Invalid stream sequence.");
          if (event.kind === "started") {
            if (started) throw new Error("Invalid stream sequence.");
            started = true;
          }
          if (event.kind === "completed") completed = true;
          onEvent(event);
        }
      }
      if (done) break;
    }
    if (buffer.trim() || !completed)
      throw new Error("The reply stream ended before completion.");
  } finally {
    await reader.cancel().catch(() => {});
    reader.releaseLock();
  }
}
