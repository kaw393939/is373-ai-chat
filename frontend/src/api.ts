let token = "";
let rotation: Promise<boolean> | null = null;
export function setToken(value: string) {
  token = value;
}
export async function refresh(): Promise<boolean> {
  if (rotation) return rotation;
  rotation = (async () => {
    const response = await fetch("/api/auth/refresh", { method: "POST" });
    if (!response.ok) {
      token = "";
      return false;
    }
    token = (await response.json()).access_token;
    return true;
  })().finally(() => {
    rotation = null;
  });
  return rotation;
}
export async function request(
  path: string,
  options: RequestInit = {},
  retry = true,
): Promise<Response> {
  const headers = new Headers(options.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (options.body) headers.set("Content-Type", "application/json");
  const response = await fetch("/api" + path, { ...options, headers });
  if (response.status === 401 && retry && token && (await refresh()))
    return request(path, options, false);
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(
      typeof body.detail === "string"
        ? body.detail
        : "Check your inputs and try again.",
    );
  }
  return response;
}
export async function api(path: string, method = "GET", body?: unknown) {
  const response = await request(path, {
    method,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  return response.status === 204 ? null : response.json();
}
export async function consume(
  response: Response,
  onEvent: (kind: string, data: any) => void,
) {
  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
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
        if (kind && data) onEvent(kind, JSON.parse(data));
      }
      if (done) break;
    }
  } finally {
    reader.releaseLock();
  }
}
