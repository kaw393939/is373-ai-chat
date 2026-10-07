import React, { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  api,
  isAbort,
  onSessionInvalidated,
  ownsSession,
  refresh,
  sessionStamp,
  signIn,
  signOut,
  verifyMfa,
} from "./api";
import type {
  AuthOptions,
  MfaChallenge,
  MfaEnrollment,
  User,
} from "./contracts";
import { useConversations } from "./useConversations";
import { FormField } from "./FormField";
import { Dialog } from "./Dialog";
import { Admin } from "./Admin";
import { Account } from "./Account";
import { Messages } from "./Messages";
import { ProjectFooter } from "./ProjectFooter";
import "./style.css";

function App() {
  const [user, setUser] = useState<User | null>(null);
  const [ready, setReady] = useState(false);
  const [tab, setTab] = useState("chat");
  const [notice, setNotice] = useState("");
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [authBusy, setAuthBusy] = useState(false);
  const [authOptions, setAuthOptions] = useState<AuthOptions>({
    email_enabled: false,
    approval_required: true,
  });
  const [mfa, setMfa] = useState<MfaChallenge | null>(null);
  const [enrollment, setEnrollment] = useState<MfaEnrollment | null>(null);
  const [code, setCode] = useState("");
  const [recoveryCodes, setRecoveryCodes] = useState<string[]>([]);
  const resetToken = new URLSearchParams(location.hash.slice(1)).get("reset");
  const [editTitle, setEditTitle] = useState<string | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState(false);
  const [dialogBusy, setDialogBusy] = useState(false);
  const [dialogError, setDialogError] = useState("");
  const conversations = useConversations(user, setNotice);
  const {
    chats,
    selected,
    title,
    messages,
    prompt,
    setPrompt,
    models,
    model,
    setModel,
    filter,
    setFilter,
    openChat,
    newChat,
    send,
    stop,
    rename,
    remove,
    messagesCursor,
    historyBusy,
    listBusy,
    olderMessages,
    nextCursor,
    moreChats,
  } = conversations;
  const busy = user ? conversations.busy : authBusy;
  const bottom = useRef<HTMLDivElement>(null);
  const authVersion = useRef(0);
  const fail = (e: unknown) => {
    if (!isAbort(e))
      setNotice(e instanceof Error ? e.message : "Something went wrong.");
  };
  useEffect(() => {
    let active = true;
    const initial = sessionStamp();
    const unsubscribe = onSessionInvalidated(() => {
      setUser(null);
      setNotice("");
      setTab("chat");
      authVersion.current++;
      setAuthBusy(false);
      setEditTitle(null);
      setDeleteConfirm(false);
      setDialogError("");
      setDialogBusy(false);
      setMfa(null);
      setEnrollment(null);
      setCode("");
      setRecoveryCodes([]);
    });
    (async () => {
      try {
        const options = await api<AuthOptions>("/auth/options");
        if (active && ownsSession(initial)) setAuthOptions(options);
        const verifyToken = new URLSearchParams(location.hash.slice(1)).get(
          "verify",
        );
        if (verifyToken) {
          const result = await api<{ message: string }>(
            "/auth/verify",
            "POST",
            { token: verifyToken },
          );
          if (active && ownsSession(initial)) {
            history.replaceState(null, "", location.pathname);
            setNotice(result.message);
          }
        } else if (!resetToken && (await refresh())) {
          const current = await api<User>("/auth/me");
          if (active) setUser(current);
        }
      } catch (e) {
        if (active) fail(e);
      } finally {
        if (active) setReady(true);
      }
    })();
    return () => {
      active = false;
      unsubscribe();
    };
  }, []);
  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);
  async function authenticate(e: React.FormEvent) {
    e.preventDefault();
    setNotice("");
    setAuthBusy(true);
    let attempt = sessionStamp();
    let operation = ++authVersion.current;
    const current = () =>
      operation === authVersion.current && ownsSession(attempt);
    try {
      if (mfa) {
        const result = await verifyMfa(mfa.challenge, code);
        if (!current()) return;
        setUser(result.user);
        setMfa(null);
        setEnrollment(null);
        setCode("");
        setRecoveryCodes(result.recovery_codes ?? []);
      } else if (resetToken) {
        await api<void>("/auth/reset", "POST", { token: resetToken, password });
        if (!current()) return;
        location.hash = "";
        setNotice("Password changed. Sign in.");
        setPassword("");
      } else if (mode === "register") {
        const result = await api<{ message: string }>(
          "/auth/register",
          "POST",
          { email, password },
        );
        if (!current()) return;
        setNotice(result.message);
        setMode("login");
        setPassword("");
      } else if (mode === "recover" || mode === "resend") {
        const result = await api<{ message: string }>(
          "/auth/email?purpose=" + (mode === "resend" ? "verify" : "reset"),
          "POST",
          { email },
        );
        if (!current()) return;
        setNotice(result.message);
      } else {
        const pending = signIn(email, password);
        attempt = sessionStamp();
        operation = ++authVersion.current;
        setAuthBusy(true);
        const result = await pending;
        if (!current()) return;
        setPassword("");
        if ("mfa_required" in result) {
          setMfa(result);
          if (result.enrollment_required) {
            const setup = await api<MfaEnrollment>("/auth/mfa/enroll", "POST", {
              challenge: result.challenge,
            });
            if (current()) setEnrollment(setup);
          }
        } else setUser(result.user);
      }
    } catch (e) {
      if (current() || (operation === authVersion.current && attempt === null))
        fail(e);
    } finally {
      if (operation === authVersion.current) setAuthBusy(false);
    }
  }
  async function logout() {
    await signOut();
  }
  const recoveryDialog = recoveryCodes.length > 0 && (
    <Dialog
      title="Save your recovery codes"
      onClose={() => setRecoveryCodes([])}
      initialFocus="button"
    >
      <p>
        Store these one-use codes privately. They will not be shown again. Each
        code can sign in if your authenticator is unavailable.
      </p>
      <ul className="recovery-codes">
        {recoveryCodes.map((value) => (
          <li key={value}>
            <code>{value}</code>
          </li>
        ))}
      </ul>
      <button onClick={() => setRecoveryCodes([])}>I saved my codes</button>
    </Dialog>
  );
  if (!ready) return <main className="loading">Opening the workshop…</main>;
  if (!user)
    return (
      <>
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
              {mfa
                ? "Verify your second factor"
                : resetToken
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
              {mfa
                ? "Enter a six-digit code from your authenticator, or a recovery code. Challenges expire after five minutes."
                : mode === "register"
                  ? `${authOptions.email_enabled ? "Check your email to verify your address. " : ""}${authOptions.approval_required ? "Registration requests are reviewed by an administrator." : "Create your private account."}`
                  : mode === "recover" || mode === "resend"
                    ? "Enter your account email. Links expire after 30 minutes."
                    : "Sign in to continue your conversations."}
            </p>
            <form onSubmit={authenticate}>
              {!resetToken && !mfa && (
                <FormField
                  label="Email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              )}
              {!mfa && mode !== "recover" && mode !== "resend" && (
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
              {mfa && (
                <>
                  {enrollment && (
                    <div className="mfa-setup">
                      <p>
                        Add this setup key in your authenticator. Keep it
                        private.
                      </p>
                      <FormField
                        label="Authenticator setup key"
                        readOnly
                        value={enrollment.secret}
                      />
                      <p className="fine">
                        Use a TOTP account named Firehose360. Your authenticator
                        generates a new code every 30 seconds.
                      </p>
                    </div>
                  )}
                  <FormField
                    label="Authenticator or recovery code"
                    autoComplete="one-time-code"
                    maxLength={64}
                    required
                    value={code}
                    onChange={(e) => setCode(e.target.value)}
                  />
                </>
              )}
              <button className="primary" disabled={busy}>
                {busy
                  ? "Please wait…"
                  : mfa
                    ? "Verify code"
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
            {!resetToken && !mfa && (
              <button
                className="link"
                disabled={authBusy}
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
            {mfa ? (
              <button
                className="link"
                disabled={authBusy}
                onClick={() => {
                  setMfa(null);
                  setEnrollment(null);
                  setCode("");
                  setNotice("");
                }}
              >
                Back to sign in
              </button>
            ) : !resetToken && authOptions.email_enabled ? (
              <div className="fine">
                <button
                  className="link"
                  disabled={authBusy}
                  onClick={() => {
                    setMode("recover");
                    setNotice("");
                  }}
                >
                  Forgot password?
                </button>
                <button
                  className="link"
                  disabled={authBusy}
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
        {recoveryDialog}
      </>
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
            maxLength={100}
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          />
        </label>
        <nav aria-label="Conversations">
          {chats.map((c) => (
            <button
              key={c.id}
              className={selected === c.id && tab === "chat" ? "selected" : ""}
              disabled={busy}
              onClick={() => {
                setTab("chat");
                openChat(c.id).catch(fail);
              }}
            >
              {c.title}
            </button>
          ))}
          {nextCursor && (
            <button
              disabled={busy || listBusy}
              onClick={() => moreChats().catch(fail)}
            >
              Load more conversations
            </button>
          )}
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
                ? title || "Start something thoughtful"
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
          <Account
            user={user}
            done={logout}
            completeMfa={setRecoveryCodes}
            fail={fail}
          />
        ) : (
          <>
            <div className="messages">
              {messagesCursor && (
                <button
                  disabled={busy || historyBusy}
                  onClick={() => olderMessages().catch(fail)}
                >
                  Load older messages
                </button>
              )}
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
              <Messages
                messages={messages}
                busy={busy}
                notify={setNotice}
                fail={fail}
              />
              <div ref={bottom} />
            </div>
            <div className="composer-wrap">
              <div className="chat-tools">
                <label>
                  Model{" "}
                  <select
                    disabled={busy}
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
                      onClick={() => {
                        setDialogError("");
                        setEditTitle(title);
                      }}
                    >
                      Rename
                    </button>
                    <button
                      onClick={() => {
                        setDialogError("");
                        setDeleteConfirm(true);
                      }}
                    >
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
        <Dialog
          title="Rename conversation"
          onClose={() => setEditTitle(null)}
          busy={dialogBusy}
          error={dialogError}
          initialFocus="input"
        >
          <form
            onSubmit={async (e) => {
              e.preventDefault();
              const attempt = sessionStamp();
              setDialogBusy(true);
              setDialogError("");
              try {
                await rename(editTitle);
                if (ownsSession(attempt)) setEditTitle(null);
              } catch (e) {
                if (ownsSession(attempt) && !isAbort(e))
                  setDialogError(
                    e instanceof Error ? e.message : "Unable to rename.",
                  );
              } finally {
                if (ownsSession(attempt)) setDialogBusy(false);
              }
            }}
          >
            <FormField
              label="Conversation title"
              value={editTitle}
              required
              maxLength={100}
              onChange={(e) => setEditTitle(e.target.value)}
            />
            <button className="primary" disabled={dialogBusy}>
              Save title
            </button>{" "}
            <button
              type="button"
              disabled={dialogBusy}
              onClick={() => setEditTitle(null)}
            >
              Cancel
            </button>
          </form>
        </Dialog>
      )}
      {deleteConfirm && (
        <Dialog
          title="Delete conversation?"
          onClose={() => setDeleteConfirm(false)}
          busy={dialogBusy}
          error={dialogError}
          initialFocus=".cancel"
        >
          <p>This permanently deletes the conversation and its messages.</p>
          <button
            className="danger"
            disabled={dialogBusy}
            onClick={async () => {
              const attempt = sessionStamp();
              setDialogBusy(true);
              setDialogError("");
              try {
                await remove();
                if (ownsSession(attempt)) setDeleteConfirm(false);
              } catch (e) {
                if (ownsSession(attempt) && !isAbort(e))
                  setDialogError(
                    e instanceof Error ? e.message : "Unable to delete.",
                  );
              } finally {
                if (ownsSession(attempt)) setDialogBusy(false);
              }
            }}
          >
            Delete conversation
          </button>{" "}
          <button
            className="cancel"
            disabled={dialogBusy}
            onClick={() => setDeleteConfirm(false)}
          >
            Cancel
          </button>
        </Dialog>
      )}
      {recoveryDialog}
    </div>
  );
}
createRoot(document.getElementById("root")!).render(
  <>
    <App />
    <ProjectFooter />
  </>,
);
