import React, { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { api, consume, refresh, request, setToken } from "./api";
import { ProjectFooter } from "./ProjectFooter";
import "./style.css";

type User = {
  id: string;
  email: string;
  role: string;
  active: boolean;
  approved: boolean;
  email_verified: boolean;
  daily_requests: number | null;
  daily_units: number | null;
  max_concurrent: number | null;
};
type Chat = { id: string; title: string };
type Message = { id: string; role: string; content: string };
function FormField({
  label,
  ...props
}: React.InputHTMLAttributes<HTMLInputElement> & { label: string }) {
  const id = React.useId();
  return (
    <label htmlFor={id}>
      {label}
      <input id={id} {...props} />
    </label>
  );
}
function App() {
  const [user, setUser] = useState<User | null>(null);
  const [ready, setReady] = useState(false);
  const [tab, setTab] = useState("chat");
  const [notice, setNotice] = useState("");
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [authOptions, setAuthOptions] = useState({
    email_enabled: false,
    approval_required: true,
  });
  const resetToken = new URLSearchParams(location.hash.slice(1)).get("reset");
  const [chats, setChats] = useState<Chat[]>([]);
  const [selected, setSelected] = useState("");
  const [editTitle, setEditTitle] = useState<string | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [prompt, setPrompt] = useState("");
  const [busy, setBusy] = useState(false);
  const controller = useRef<AbortController | null>(null);
  const run = useRef("");
  const [models, setModels] = useState<any[]>([]);
  const [model, setModel] = useState("default");
  const [filter, setFilter] = useState("");
  const bottom = useRef<HTMLDivElement>(null);
  const fail = (e: unknown) =>
    setNotice(e instanceof Error ? e.message : "Something went wrong.");
  useEffect(() => {
    (async () => {
      try {
        setAuthOptions(await api("/auth/options"));
        const verifyToken = new URLSearchParams(location.hash.slice(1)).get(
          "verify",
        );
        if (verifyToken) {
          const result = await api("/auth/verify", "POST", {
            token: verifyToken,
          });
          history.replaceState(null, "", location.pathname);
          setNotice(result.message);
        } else if (!resetToken && (await refresh()))
          setUser(await api("/auth/me"));
      } catch (e) {
        fail(e);
      } finally {
        setReady(true);
      }
    })();
  }, []);
  async function listChats() {
    setChats(await api("/conversations"));
  }
  async function openChat(id: string) {
    const c = await api(`/conversations/${id}`);
    setSelected(id);
    setMessages(c.messages);
  }
  useEffect(() => {
    if (user) {
      listChats().catch(fail);
      api("/models").then(setModels).catch(fail);
    }
  }, [user]);
  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);
  async function authenticate(e: React.FormEvent) {
    e.preventDefault();
    setNotice("");
    setBusy(true);
    try {
      if (resetToken) {
        await api("/auth/reset", "POST", { token: resetToken, password });
        location.hash = "";
        setNotice("Password changed. Sign in.");
        setPassword("");
      } else if (mode === "register") {
        const r = await api("/auth/register", "POST", { email, password });
        setNotice(r.message);
        setMode("login");
        setPassword("");
      } else if (mode === "recover" || mode === "resend") {
        const result = await api(
          `/auth/email?purpose=${mode === "resend" ? "verify" : "reset"}`,
          "POST",
          { email },
        );
        setNotice(result.message);
      } else {
        const r = await api("/auth/login", "POST", { email, password });
        setToken(r.access_token);
        setUser(r.user);
        setPassword("");
      }
    } catch (e) {
      fail(e);
    } finally {
      setBusy(false);
    }
  }
  async function logout() {
    controller.current?.abort();
    try {
      await api("/auth/logout", "POST");
    } finally {
      setToken("");
      setUser(null);
      setMessages([]);
      setSelected("");
    }
  }
  async function newChat() {
    const c = await api("/conversations", "POST");
    setSelected(c.id);
    setMessages([]);
    await listChats();
    return c.id;
  }
  async function send(e?: React.FormEvent, retryText?: string) {
    e?.preventDefault();
    const content = retryText ?? prompt;
    if (!content.trim() || busy) return;
    setBusy(true);
    setNotice("");
    setPrompt("");
    run.current = "";
    controller.current = new AbortController();
    let cid = selected;
    try {
      if (!cid) cid = await newChat();
      setMessages((m) => [
        ...m,
        { id: crypto.randomUUID(), role: "user", content },
        { id: "live", role: "assistant", content: "" },
      ]);
      const response = await request(`/conversations/${cid}/stream`, {
        method: "POST",
        body: JSON.stringify({
          content,
          request_key: crypto.randomUUID(),
          model,
        }),
        signal: controller.current.signal,
      });
      await consume(response, (kind, data) => {
        if (kind === "started") run.current = data.run_id;
        if (kind === "delta")
          setMessages((m) =>
            m.map((item) =>
              item.id === "live"
                ? { ...item, content: item.content + data.text }
                : item,
            ),
          );
        if (kind === "error") setNotice(data.message);
      });
    } catch (e) {
      if (!(e instanceof DOMException && e.name === "AbortError")) {
        fail(e);
        if (!run.current) setPrompt(content);
      }
    } finally {
      setBusy(false);
      controller.current = null;
      if (cid) await openChat(cid).catch(fail);
      await listChats().catch(fail);
    }
  }
  async function stop() {
    if (run.current)
      await api(`/generations/${run.current}/cancel`, "POST").catch(fail);
    controller.current?.abort();
  }
  if (!ready) return <main className="loading">Opening the workshop…</main>;
  if (!user)
    return (
      <main className="entry">
        <section className="entry-story">
          <div className="brand">
            373 <span>CHAT WORKSHOP</span>
          </div>
          <p className="eyebrow">A SMALL SYSTEM. THE WHOLE PICTURE.</p>
          <h1>
            Conversation,
            <br />
            with a foundation.
          </h1>
          <p>
            A private workspace for thoughtful conversations. Built with clear
            boundaries, useful limits, and tools you can understand.
          </p>
          <div className="entry-footer">
            FASTAPI · POSTGRESQL · REACT
            <br />
            Learn by following a request from browser to release.
          </div>
        </section>
        <section className="entry-form">
          <p className="eyebrow">YOUR WORKSPACE</p>
          <h2>
            {resetToken
              ? "Set a new password"
              : mode === "login"
                ? "Welcome back"
                : mode === "recover"
                  ? "Recover your account"
                  : mode === "resend"
                    ? "Verify your email"
                    : "Join the workshop"}
          </h2>
          <p>
            {mode === "register"
              ? `${authOptions.email_enabled ? "Check your email to verify your address. " : ""}${authOptions.approval_required ? "Registration requests are reviewed by an administrator." : "Create your private account."}`
              : mode === "recover" || mode === "resend"
                ? "Enter your account email. Links expire after 30 minutes."
                : "Sign in to continue your conversations."}
          </p>
          <form onSubmit={authenticate}>
            {!resetToken && (
              <FormField
                label="Email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            )}
            {mode !== "recover" && mode !== "resend" && (
              <FormField
                label="Password"
                type="password"
                autoComplete={
                  mode === "login" ? "current-password" : "new-password"
                }
                minLength={resetToken || mode === "register" ? 12 : 1}
                maxLength={128}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            )}
            <button className="primary" disabled={busy}>
              {busy
                ? "Please wait…"
                : resetToken
                  ? "Save password"
                  : mode === "login"
                    ? "Sign in"
                    : mode === "recover" || mode === "resend"
                      ? "Send email"
                      : "Request account"}
            </button>
          </form>
          <p role="status" className="notice">
            {notice}
          </p>
          {!resetToken && (
            <button
              className="link"
              onClick={() => {
                setMode(mode === "login" ? "register" : "login");
                setNotice("");
              }}
            >
              {mode === "login"
                ? "Need an account? Register"
                : "Already registered? Sign in"}
            </button>
          )}
          {!resetToken && authOptions.email_enabled ? (
            <div className="fine">
              <button
                className="link"
                onClick={() => {
                  setMode("recover");
                  setNotice("");
                }}
              >
                Forgot password?
              </button>
              <button
                className="link"
                onClick={() => {
                  setMode("resend");
                  setNotice("");
                }}
              >
                Resend verification email
              </button>
            </div>
          ) : (
            <p className="fine">
              For password recovery, contact your administrator for a
              short-lived recovery link.
            </p>
          )}
        </section>
      </main>
    );
  return (
    <div className="workspace">
      <aside>
        <div className="brand">
          373 <span>CHAT WORKSHOP</span>
        </div>
        <button
          className="primary new-chat"
          disabled={busy}
          onClick={() => {
            setTab("chat");
            newChat().catch(fail);
          }}
        >
          ＋ New conversation
        </button>
        <label className="search">
          <span className="sr-only">Search conversations</span>
          <input
            placeholder="Find a conversation…"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          />
        </label>
        <nav aria-label="Conversations">
          {chats
            .filter((c) => c.title.toLowerCase().includes(filter.toLowerCase()))
            .map((c) => (
              <button
                key={c.id}
                className={
                  selected === c.id && tab === "chat" ? "selected" : ""
                }
                disabled={busy}
                onClick={() => {
                  setTab("chat");
                  openChat(c.id).catch(fail);
                }}
              >
                {c.title}
              </button>
            ))}
        </nav>
        <div className="sidebar-footer">
          {user.role === "admin" && (
            <button
              onClick={() => {
                setTab("admin");
                setNotice("");
              }}
            >
              ▦ Administration
            </button>
          )}
          <button onClick={() => setTab("account")}>◎ Account</button>
          <div className="user-line">
            <span>
              {user.email}
              <small>{user.role}</small>
            </span>
            <button onClick={() => logout().catch(fail)}>Sign out</button>
          </div>
        </div>
      </aside>
      <main className="main">
        <header>
          <div>
            <p className="eyebrow">
              {tab === "chat"
                ? "YOUR CONVERSATIONS"
                : tab === "admin"
                  ? "OPERATIONS"
                  : "YOUR ACCOUNT"}
            </p>
            <h2>
              {tab === "chat"
                ? (chats.find((c) => c.id === selected)?.title ??
                  "Start something thoughtful")
                : tab === "admin"
                  ? "Workshop administration"
                  : "Account & security"}
            </h2>
          </div>
          <span className="status">
            <i /> Signed in
          </span>
        </header>
        <div role="status" className="notice">
          {notice}
        </div>
        {tab === "admin" ? (
          <Admin actor={user} fail={fail} />
        ) : tab === "account" ? (
          <Account user={user} done={logout} fail={fail} />
        ) : (
          <>
            <div className="messages">
              {!messages.length && (
                <div className="welcome">
                  <div className="motif">✳</div>
                  <p className="eyebrow">ROOM TO THINK</p>
                  <h1>
                    What would you like
                    <br />
                    to work through?
                  </h1>
                  <p>
                    Choose a model, ask a question, and watch the response
                    arrive.
                    <br />
                    Your conversations stay in your account.
                  </p>
                  <div className="suggestions">
                    {[
                      "Explain how JWT sessions work",
                      "Help me plan a small project",
                      "What makes a good deployment?",
                    ].map((s) => (
                      <button key={s} onClick={() => setPrompt(s)}>
                        {s} ↗
                      </button>
                    ))}
                  </div>
                </div>
              )}
              {messages.map((m) => (
                <article key={m.id} className={"message " + m.role}>
                  <div className="message-label">
                    {m.role === "user" ? "YOU" : "WORKSHOP"}
                  </div>
                  <div>
                    {m.content ? (
                      <Markdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                          a: ({ children, href }) => (
                            <a
                              href={href}
                              target="_blank"
                              rel="noopener noreferrer"
                              referrerPolicy="no-referrer"
                            >
                              {children}
                            </a>
                          ),
                          img: ({ alt }) => (
                            <span>[External image omitted: {alt}]</span>
                          ),
                        }}
                      >
                        {m.content}
                      </Markdown>
                    ) : (
                      <span className="typing">
                        {busy && m.id === "live"
                          ? "Thinking…"
                          : "No response was saved. Retry your prompt."}
                      </span>
                    )}
                  </div>
                  {m.content && (
                    <button
                      aria-label={`Copy ${m.role} message`}
                      onClick={() =>
                        navigator.clipboard
                          .writeText(m.content)
                          .then(() => setNotice("Message copied."))
                          .catch(fail)
                      }
                    >
                      Copy
                    </button>
                  )}
                </article>
              ))}
              <div ref={bottom} />
            </div>
            <div className="composer-wrap">
              <div className="chat-tools">
                <label>
                  Model{" "}
                  <select
                    aria-label="Model"
                    value={model}
                    onChange={(e) => setModel(e.target.value)}
                  >
                    {models.map((m) => (
                      <option key={m.id} value={m.id} disabled={!m.enabled}>
                        {m.name}
                      </option>
                    ))}
                  </select>
                </label>
                {selected && !busy && (
                  <>
                    <button
                      onClick={() =>
                        setEditTitle(
                          chats.find((c) => c.id === selected)?.title ?? "",
                        )
                      }
                    >
                      Rename
                    </button>
                    <button onClick={() => setDeleteConfirm(true)}>
                      Delete
                    </button>
                  </>
                )}
                {messages.length > 0 && !busy && (
                  <button
                    onClick={() =>
                      send(
                        undefined,
                        [...messages].reverse().find((m) => m.role === "user")
                          ?.content,
                      )
                    }
                  >
                    Retry last prompt
                  </button>
                )}
              </div>
              <form onSubmit={send} className="composer">
                <label className="sr-only" htmlFor="prompt">
                  Message
                </label>
                <textarea
                  id="prompt"
                  placeholder="Ask a question…"
                  maxLength={12000}
                  required
                  value={prompt}
                  disabled={busy}
                  onChange={(e) => setPrompt(e.target.value)}
                  onKeyDown={(e) => {
                    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
                      e.preventDefault();
                      send().catch(fail);
                    }
                  }}
                />
                {busy ? (
                  <button type="button" onClick={() => stop().catch(fail)}>
                    Stop
                  </button>
                ) : (
                  <button className="primary" disabled={!prompt.trim()}>
                    Send ↑
                  </button>
                )}
              </form>
              <p className="fine">
                AI can make mistakes. Check important answers. Usage is subject
                to your account limits. Ctrl/⌘+Enter sends; Enter adds a line.
              </p>
            </div>
          </>
        )}
      </main>
      {editTitle !== null && (
        <div
          className="modal"
          role="dialog"
          aria-modal="true"
          aria-label="Rename conversation"
        >
          <form
            className="panel"
            onSubmit={async (e) => {
              e.preventDefault();
              try {
                await api(`/conversations/${selected}`, "PATCH", {
                  title: editTitle,
                });
                setEditTitle(null);
                await listChats();
              } catch (e) {
                fail(e);
              }
            }}
          >
            <h3>Rename conversation</h3>
            <FormField
              label="Conversation title"
              value={editTitle}
              required
              maxLength={100}
              autoFocus
              onChange={(e) => setEditTitle(e.target.value)}
            />
            <button className="primary">Save title</button>{" "}
            <button type="button" onClick={() => setEditTitle(null)}>
              Cancel
            </button>
          </form>
        </div>
      )}
      {deleteConfirm && (
        <div
          className="modal"
          role="dialog"
          aria-modal="true"
          aria-label="Delete conversation"
        >
          <div className="panel">
            <h3>Delete conversation?</h3>
            <p>This permanently deletes the conversation and its messages.</p>
            <button
              className="danger"
              onClick={async () => {
                try {
                  await api(`/conversations/${selected}`, "DELETE");
                  setDeleteConfirm(false);
                  setSelected("");
                  setMessages([]);
                  await listChats();
                } catch (e) {
                  fail(e);
                }
              }}
            >
              Delete conversation
            </button>{" "}
            <button onClick={() => setDeleteConfirm(false)}>Cancel</button>
          </div>
        </div>
      )}
    </div>
  );
}
function Account({
  user,
  done,
  fail,
}: {
  user: User;
  done: () => Promise<void>;
  fail: (e: unknown) => void;
}) {
  const [password, setPassword] = useState("");
  const [currentPassword, setCurrentPassword] = useState("");
  return (
    <section className="panel">
      <h3>Change your password</h3>
      <p>Changing your password signs out all your sessions.</p>
      <p>{user.email}</p>
      <form
        onSubmit={async (e) => {
          e.preventDefault();
          try {
            await api("/auth/password", "POST", {
              current_password: currentPassword,
              password,
            });
            await done();
          } catch (e) {
            fail(e);
          }
        }}
      >
        <FormField
          label="Current password"
          type="password"
          autoComplete="current-password"
          maxLength={128}
          required
          value={currentPassword}
          onChange={(e) => setCurrentPassword(e.target.value)}
        />
        <FormField
          label="New password"
          type="password"
          minLength={12}
          maxLength={128}
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <button className="primary">Change password & sign out</button>
      </form>
    </section>
  );
}
function Admin({ actor, fail }: { actor: User; fail: (e: unknown) => void }) {
  const [overview, setOverview] = useState<any>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [budgets, setBudgets] = useState<any[]>([]);
  const [editing, setEditing] = useState<User | null>(null);
  const [recovery, setRecovery] = useState("");
  async function load() {
    const [o, u, b] = await Promise.all([
      api("/admin/overview"),
      api("/admin/users"),
      api("/admin/budgets"),
    ]);
    setOverview(o);
    setUsers(u);
    setBudgets(b);
  }
  useEffect(() => {
    load().catch(fail);
    const timer = setInterval(
      () => api("/admin/overview").then(setOverview).catch(fail),
      30000,
    );
    return () => clearInterval(timer);
  }, []);
  const sample = overview?.host?.samples?.at(-1);
  const stale = sample && Date.now() / 1000 - sample.at > 90;
  return (
    <section className="admin-content">
      <div className="section-title">
        <h3>System overview</h3>
        <button onClick={() => load().catch(fail)}>Refresh metrics</button>
      </div>
      <div className="stats">
        {Object.entries(overview?.totals ?? {}).map(([key, value]) => (
          <div className="stat" key={key}>
            <span>{key.replace(/_/g, " ")}</span>
            <strong>{String(value)}</strong>
          </div>
        ))}
      </div>
      <div className="panel">
        <h3>
          Host resources{" "}
          <span className="badge">
            {sample
              ? stale
                ? "Stale"
                : "Live · 30 sec"
              : overview
                ? "Collector unavailable"
                : "Loading metrics…"}
          </span>
        </h3>
        <div className="stats">
          {sample &&
            [
              ["CPU", sample.cpu_percent.toFixed(1) + "%"],
              [
                "Memory",
                ((sample.memory_used / sample.memory_total) * 100).toFixed(1) +
                  "%",
              ],
              [
                "Disk",
                ((sample.disk_used / sample.disk_total) * 100).toFixed(1) + "%",
              ],
            ].map(([name, value]) => (
              <div className="stat" key={name}>
                <span>{name}</span>
                <strong>{value}</strong>
              </div>
            ))}
        </div>
        <p className="fine">
          Host limits are versioned in Compose. No Docker socket is exposed to
          this application.
        </p>
        {sample && (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Container</th>
                  <th>CPU</th>
                  <th>Memory / limit</th>
                  <th>State</th>
                </tr>
              </thead>
              <tbody>
                {sample.containers.map((c: any) => (
                  <tr key={c.name}>
                    <td>{c.name}</td>
                    <td>{c.cpu}</td>
                    <td>{c.memory}</td>
                    <td>{c.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
      <div className="panel">
        <h3>Role defaults</h3>
        <p>
          Reservation units conservatively budget UTF-8 input bytes plus maximum
          output tokens. They are not dollar costs.
        </p>
        {budgets.map((b) => (
          <form
            className="budget-form"
            key={b.role}
            onSubmit={async (e) => {
              e.preventDefault();
              try {
                const { role, ...body } = b;
                await api(`/admin/budgets/${role}`, "PUT", body);
                await load();
              } catch (e) {
                fail(e);
              }
            }}
          >
            <strong>{b.role}</strong>
            {[
              ["daily_requests", "Requests / day"],
              ["daily_units", "Units / day"],
              ["max_concurrent", "Concurrent"],
              ["max_output", "Output tokens"],
            ].map(([key, label]) => (
              <FormField
                key={key}
                label={label}
                type="number"
                min={
                  key === "max_output" ? 64 : key === "daily_units" ? 100 : 1
                }
                max={
                  key === "max_concurrent"
                    ? 4
                    : key === "max_output"
                      ? 4096
                      : key === "daily_requests"
                        ? 10000
                        : 10000000
                }
                required
                value={b[key]}
                onChange={(e) =>
                  setBudgets((bs) =>
                    bs.map((x) =>
                      x.role === b.role
                        ? { ...x, [key]: Number(e.target.value) }
                        : x,
                    ),
                  )
                }
              />
            ))}
            <label>
              <input
                type="checkbox"
                checked={b.model_enabled}
                onChange={(e) =>
                  setBudgets((bs) =>
                    bs.map((x) =>
                      x.role === b.role
                        ? { ...x, model_enabled: e.target.checked }
                        : x,
                    ),
                  )
                }
              />{" "}
              Model enabled
            </label>
            <button>Save {b.role} budget</button>
          </form>
        ))}
      </div>
      <div className="panel">
        <h3>Accounts</h3>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Email</th>
                <th>Role</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id}>
                  <td>{u.email}</td>
                  <td>{u.role}</td>
                  <td>
                    {!u.active
                      ? "Disabled"
                      : !u.email_verified
                        ? "Email unverified"
                        : u.approved
                          ? "Approved"
                          : "Pending approval"}
                  </td>
                  <td>
                    {u.id !== actor.id && (
                      <button onClick={() => setEditing({ ...u })}>
                        Edit {u.email}
                      </button>
                    )}{" "}
                    <button
                      onClick={() =>
                        api(`/admin/users/${u.id}/revoke`, "POST")
                          .then(load)
                          .catch(fail)
                      }
                    >
                      Revoke sessions
                    </button>{" "}
                    <button
                      onClick={() =>
                        api(`/admin/users/${u.id}/recovery`, "POST")
                          .then((r) => setRecovery(r.url))
                          .catch(fail)
                      }
                    >
                      Recovery link
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      {editing && (
        <div
          className="modal"
          role="dialog"
          aria-modal="true"
          aria-label="Edit account"
        >
          <form
            className="panel"
            onSubmit={async (e) => {
              e.preventDefault();
              try {
                const { id, email, ...body } = editing;
                await api(`/admin/users/${id}`, "PATCH", body);
                setEditing(null);
                await load();
              } catch (e) {
                fail(e);
              }
            }}
          >
            <h3>{editing.email}</h3>
            <label>
              Role
              <select
                value={editing.role}
                onChange={(e) =>
                  setEditing({ ...editing, role: e.target.value })
                }
              >
                <option>user</option>
                <option>admin</option>
              </select>
            </label>
            {["active", "approved"].map((key) => (
              <label key={key}>
                <input
                  type="checkbox"
                  checked={editing[key as "active" | "approved"]}
                  onChange={(e) =>
                    setEditing({ ...editing, [key]: e.target.checked })
                  }
                />
                {key}
              </label>
            ))}
            {[
              ["daily_requests", "Request override"],
              ["daily_units", "Unit override"],
              ["max_concurrent", "Concurrency override"],
            ].map(([key, label]) => (
              <FormField
                label={label + " (blank uses role default)"}
                key={key}
                type="number"
                min={key === "daily_units" ? 100 : 1}
                max={
                  key === "max_concurrent"
                    ? 4
                    : key === "daily_units"
                      ? 10000000
                      : 10000
                }
                value={editing[key as "daily_requests"] ?? ""}
                onChange={(e) =>
                  setEditing({
                    ...editing,
                    [key]:
                      e.target.value === "" ? null : Number(e.target.value),
                  })
                }
              />
            ))}
            <button className="primary">Save account</button>
            <button type="button" onClick={() => setEditing(null)}>
              Cancel
            </button>
          </form>
        </div>
      )}
      {recovery && (
        <div className="panel">
          <h3>Private recovery link · 30 minutes</h3>
          <label>
            Recovery URL
            <input readOnly value={recovery} />
          </label>
          <p>
            Share securely with the account owner. Anyone holding it can reset
            that account.
          </p>
          <button onClick={() => setRecovery("")}>Dismiss</button>
        </div>
      )}
      <div className="panel">
        <h3>Recent administrative changes</h3>
        <ul>
          {overview?.audit?.map((a: any, i: number) => (
            <li key={i}>
              {a.action} · {new Date(a.at * 1000).toLocaleString()}
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
createRoot(document.getElementById("root")!).render(
  <>
    <App />
    <ProjectFooter />
  </>,
);
