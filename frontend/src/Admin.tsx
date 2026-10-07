import { useEffect, useId, useRef, useState } from "react";
import { api, isAbort, ownsSession, sessionStamp } from "./api";
import type { Budget, Overview, Page, Role, User } from "./contracts";
import { Dialog } from "./Dialog";
import { FormField } from "./FormField";

const budgetFields = [
  ["daily_requests", "Requests / day", 1, 10000],
  ["daily_units", "Units / day", 100, 10000000],
  ["max_concurrent", "Concurrent", 1, 4],
  ["max_output", "Output tokens", 64, 4096],
] as const;
const overrides = [
  ["daily_requests", "Request override", 1, 10000],
  ["daily_units", "Unit override", 100, 10000000],
  ["max_concurrent", "Concurrency override", 1, 4],
] as const;

/** Admin requests belong to this mounted screen and its session, never a later user. */
export function Admin({
  actor,
  fail,
}: {
  actor: User;
  fail: (error: unknown) => void;
}) {
  const roleId = useId();
  const [overview, setOverview] = useState<Overview | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [budgets, setBudgets] = useState<Budget[]>([]);
  const [editing, setEditing] = useState<User | null>(null);
  const [recovery, setRecovery] = useState("");
  const [query, setQuery] = useState("");
  const queryRef = useRef("");
  const [cursor, setCursor] = useState<string | null>(null);
  const [listBusy, setListBusy] = useState(false);
  const [saving, setSaving] = useState(false);
  const [dialogError, setDialogError] = useState("");
  const active = useRef(true);
  const stamp = useRef(sessionStamp());
  const userRequest = useRef<AbortController | null>(null);
  const metricRequest = useRef<AbortController | null>(null);
  const listVersion = useRef(0);
  const owns = () => active.current && ownsSession(stamp.current);
  const report = (error: unknown) => {
    if (owns() && !isAbort(error)) fail(error);
  };

  async function loadUsers(after?: string) {
    userRequest.current?.abort();
    const controller = new AbortController();
    userRequest.current = controller;
    const version = ++listVersion.current;
    setListBusy(true);
    const params = new URLSearchParams({
      page: "true",
      limit: "50",
      q: queryRef.current,
    });
    if (after) params.set("cursor", after);
    try {
      const page = await api<Page<User>>(
        "/admin/users?" + params,
        "GET",
        undefined,
        controller.signal,
      );
      if (!owns() || version !== listVersion.current) return;
      setUsers((current) =>
        after
          ? [
              ...current,
              ...page.items.filter(
                (item) => !current.some((old) => old.id === item.id),
              ),
            ]
          : page.items,
      );
      setCursor(page.next_cursor);
    } catch (error) {
      if (version === listVersion.current) report(error);
    } finally {
      if (owns() && version === listVersion.current) setListBusy(false);
    }
  }
  async function loadMetrics() {
    metricRequest.current?.abort();
    const controller = new AbortController();
    metricRequest.current = controller;
    try {
      const value = await api<Overview>(
        "/admin/overview",
        "GET",
        undefined,
        controller.signal,
      );
      if (owns() && !controller.signal.aborted) setOverview(value);
    } catch (error) {
      report(error);
    }
  }
  async function load() {
    await Promise.all([
      loadUsers(),
      loadMetrics(),
      api<Budget[]>("/admin/budgets")
        .then((value) => {
          if (owns()) setBudgets(value);
        })
        .catch(report),
    ]);
  }
  useEffect(() => {
    active.current = true;
    loadMetrics();
    api<Budget[]>("/admin/budgets")
      .then((value) => {
        if (owns()) setBudgets(value);
      })
      .catch(report);
    const timer = setInterval(loadMetrics, 30000);
    return () => {
      active.current = false;
      clearInterval(timer);
      userRequest.current?.abort();
      metricRequest.current?.abort();
    };
  }, []);
  useEffect(() => {
    userRequest.current?.abort();
    listVersion.current++;
    setCursor(null);
    const timer = setTimeout(() => loadUsers(), 200);
    return () => clearTimeout(timer);
  }, [query]);
  const sample = overview?.host?.samples?.at(-1);
  const stale = sample && Date.now() / 1000 - sample.at > 90;
  const backups = overview?.host?.backups;
  return (
    <section className="admin-content">
      <div className="section-title">
        <h3>System overview</h3>
        <button onClick={() => load().catch(report)}>Refresh metrics</button>
      </div>
      <div className="stats">
        {Object.entries(overview?.totals ?? {}).map(([key, value]) => (
          <div className="stat" key={key}>
            <span>{key.replace(/_/g, " ")}</span>
            <strong>{value}</strong>
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
                sample.memory_total
                  ? ((sample.memory_used / sample.memory_total) * 100).toFixed(
                      1,
                    ) + "%"
                  : "Unavailable",
              ],
              [
                "Disk",
                sample.disk_total
                  ? ((sample.disk_used / sample.disk_total) * 100).toFixed(1) +
                    "%"
                  : "Unavailable",
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
        {backups && (
          <div aria-label="Backup status">
            <h4>Backup freshness</h4>
            {(
              [
                ["Local", backups.local],
                ["Off-host", backups.off_host],
              ] as const
            ).map(([label, backup]) => (
              <p key={label}>
                {label}: {backup.status}
                {backup.created_at !== null && (
                  <>
                    {" "}
                    · created{" "}
                    {new Date(backup.created_at * 1000).toLocaleString()}
                    {" · "}
                    {Math.max(
                      0,
                      (Date.now() / 1000 - backup.created_at) / 3600,
                    ).toFixed(1)}
                    h ago
                  </>
                )}
              </p>
            ))}
            <p className="fine">
              Freshness records successful copies. Recovery readiness also
              requires a verified restore; an offline backup host can leave the
              off-host copy stale.
            </p>
          </div>
        )}
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
                {sample.containers.map((container) => (
                  <tr key={container.name}>
                    <td>{container.name}</td>
                    <td>{container.cpu}</td>
                    <td>{container.memory}</td>
                    <td>{container.status}</td>
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
        {budgets.map((budget) => (
          <form
            className="budget-form"
            key={budget.role}
            onSubmit={async (event) => {
              event.preventDefault();
              try {
                const { role, ...body } = budget;
                await api<void>(`/admin/budgets/${role}`, "PUT", body);
                if (owns()) await load();
              } catch (error) {
                report(error);
              }
            }}
          >
            <strong>{budget.role}</strong>
            {budgetFields.map(([key, label, min, max]) => (
              <FormField
                key={key}
                label={label}
                type="number"
                min={min}
                max={max}
                required
                value={budget[key]}
                onChange={(event) =>
                  setBudgets((current) =>
                    current.map((item) =>
                      item.role === budget.role
                        ? { ...item, [key]: Number(event.target.value) }
                        : item,
                    ),
                  )
                }
              />
            ))}
            <label>
              <input
                type="checkbox"
                checked={budget.model_enabled}
                onChange={(event) =>
                  setBudgets((current) =>
                    current.map((item) =>
                      item.role === budget.role
                        ? { ...item, model_enabled: event.target.checked }
                        : item,
                    ),
                  )
                }
              />{" "}
              Model enabled
            </label>
            <button>Save {budget.role} budget</button>
          </form>
        ))}
      </div>
      <div className="panel">
        <h3>Accounts</h3>
        <FormField
          label="Search account email"
          maxLength={100}
          value={query}
          onChange={(event) => {
            queryRef.current = event.target.value;
            userRequest.current?.abort();
            listVersion.current++;
            setCursor(null);
            setUsers([]);
            setQuery(event.target.value);
          }}
        />
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
              {users.map((person) => (
                <tr key={person.id}>
                  <td>{person.email}</td>
                  <td>{person.role}</td>
                  <td>
                    {!person.active
                      ? "Disabled"
                      : !person.email_verified
                        ? "Email unverified"
                        : person.approved
                          ? "Approved"
                          : "Pending approval"}
                  </td>
                  <td>
                    {person.id !== actor.id && (
                      <button
                        onClick={() => {
                          setDialogError("");
                          setEditing({ ...person });
                        }}
                      >
                        Edit {person.email}
                      </button>
                    )}{" "}
                    <button
                      onClick={async () => {
                        try {
                          await api<void>(
                            `/admin/users/${person.id}/revoke`,
                            "POST",
                          );
                          if (owns()) await load();
                        } catch (error) {
                          report(error);
                        }
                      }}
                    >
                      Revoke sessions
                    </button>{" "}
                    <button
                      onClick={async () => {
                        try {
                          const result = await api<{ url: string }>(
                            `/admin/users/${person.id}/recovery`,
                            "POST",
                          );
                          if (owns()) setRecovery(result.url);
                        } catch (error) {
                          report(error);
                        }
                      }}
                    >
                      Recovery link
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {cursor && (
          <button disabled={listBusy} onClick={() => loadUsers(cursor)}>
            Load more accounts
          </button>
        )}
        <p role="status" className="fine">
          {listBusy ? "Loading accounts…" : `${users.length} accounts shown`}
        </p>
      </div>
      {editing && (
        <Dialog
          title="Edit account"
          onClose={() => setEditing(null)}
          busy={saving}
          error={dialogError}
          initialFocus="select"
        >
          <p>{editing.email}</p>
          <form
            onSubmit={async (event) => {
              event.preventDefault();
              setSaving(true);
              setDialogError("");
              try {
                const {
                  role,
                  active,
                  approved,
                  daily_requests,
                  daily_units,
                  max_concurrent,
                } = editing;
                await api<User>(`/admin/users/${editing.id}`, "PATCH", {
                  role,
                  active,
                  approved,
                  daily_requests,
                  daily_units,
                  max_concurrent,
                });
                if (owns()) {
                  setEditing(null);
                  await load();
                }
              } catch (error) {
                if (owns() && !isAbort(error))
                  setDialogError(
                    error instanceof Error
                      ? error.message
                      : "Unable to save account.",
                  );
              } finally {
                if (owns()) setSaving(false);
              }
            }}
          >
            <label htmlFor={roleId}>Role</label>
            <select
              id={roleId}
              value={editing.role}
              onChange={(event) =>
                setEditing({ ...editing, role: event.target.value as Role })
              }
            >
              <option>user</option>
              <option>admin</option>
            </select>
            {(["active", "approved"] as const).map((key) => (
              <label key={key}>
                <input
                  type="checkbox"
                  checked={editing[key]}
                  onChange={(event) =>
                    setEditing({ ...editing, [key]: event.target.checked })
                  }
                />
                {key}
              </label>
            ))}
            {overrides.map(([key, label, min, max]) => (
              <FormField
                label={label + " (blank uses role default)"}
                key={key}
                type="number"
                min={min}
                max={max}
                value={editing[key] ?? ""}
                onChange={(event) =>
                  setEditing({
                    ...editing,
                    [key]:
                      event.target.value === ""
                        ? null
                        : Number(event.target.value),
                  })
                }
              />
            ))}
            <button className="primary" disabled={saving}>
              Save account
            </button>{" "}
            <button
              type="button"
              disabled={saving}
              onClick={() => setEditing(null)}
            >
              Cancel
            </button>
          </form>
        </Dialog>
      )}
      {recovery && (
        <div className="panel">
          <h3>Private recovery link · 30 minutes</h3>
          <FormField label="Recovery URL" readOnly value={recovery} />
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
          {overview?.audit?.map((entry, index) => (
            <li key={index}>
              {entry.action} · {new Date(entry.at * 1000).toLocaleString()}
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
