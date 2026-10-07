import { useEffect, useRef, useState } from "react";
import { api, confirmMfa, isAbort, ownsSession, sessionStamp } from "./api";
import type { MfaEnrollment, OwnedExportPage, User } from "./contracts";
import { FormField } from "./FormField";

export function Account({
  user,
  done,
  completeMfa,
  fail,
}: {
  user: User;
  done: () => Promise<void>;
  completeMfa: (codes: string[]) => void;
  fail: (error: unknown) => void;
}) {
  const [password, setPassword] = useState("");
  const [currentPassword, setCurrentPassword] = useState("");
  const [factorPassword, setFactorPassword] = useState("");
  const [factorCode, setFactorCode] = useState("");
  const [factor, setFactor] = useState<{ enrolled: boolean } | null>(null);
  const [replacement, setReplacement] = useState<MfaEnrollment | null>(null);
  const [busy, setBusy] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [exportProgress, setExportProgress] = useState("");
  const exporter = useRef<AbortController | null>(null);
  const active = useRef(true);
  const stamp = useRef(sessionStamp());
  const owns = () => active.current && ownsSession(stamp.current);
  const report = (error: unknown) => {
    if (owns() && !isAbort(error)) fail(error);
  };
  useEffect(() => {
    active.current = true;
    const controller = new AbortController();
    api<{ enrolled: boolean }>("/auth/mfa", "GET", undefined, controller.signal)
      .then((value) => {
        if (owns()) setFactor(value);
      })
      .catch(report);
    return () => {
      active.current = false;
      controller.abort();
      exporter.current?.abort();
    };
  }, []);
  async function exportAccount() {
    if (exporter.current) return;
    const controller = new AbortController();
    exporter.current = controller;
    setExporting(true);
    const items: Record<OwnedExportPage["section"], Record<string, unknown>[]> =
      { conversations: [], messages: [], runs: [] };
    let lastRequest = 0;
    try {
      for (const section of ["conversations", "messages", "runs"] as const) {
        let cursor: string | null = null;
        do {
          // Respect the server's ten-page/minute export budget even for large accounts.
          const delay = Math.max(0, lastRequest + 6100 - Date.now());
          if (delay)
            await new Promise<void>((resolve, reject) => {
              const abort = () => {
                clearTimeout(timer);
                reject(new DOMException("Export cancelled", "AbortError"));
              };
              const timer = setTimeout(() => {
                controller.signal.removeEventListener("abort", abort);
                resolve();
              }, delay);
              controller.signal.addEventListener("abort", abort, {
                once: true,
              });
            });
          if (!owns() || controller.signal.aborted)
            throw new DOMException("Export cancelled", "AbortError");
          const params = new URLSearchParams({ section, limit: "100" });
          if (cursor) params.set("cursor", cursor);
          lastRequest = Date.now();
          const page = await api<OwnedExportPage>(
            "/account/export?" + params,
            "GET",
            undefined,
            controller.signal,
          );
          if (!owns() || controller.signal.aborted) return;
          items[section].push(...page.items);
          cursor = page.next_cursor;
          setExportProgress(`Collected ${items[section].length} ${section}…`);
        } while (cursor);
      }
      if (!owns()) return;
      const blob = new Blob(
        [
          JSON.stringify(
            {
              format: "firehose360-owned-v1",
              exported_at: new Date().toISOString(),
              account: user,
              ...items,
            },
            null,
            2,
          ),
        ],
        { type: "application/json" },
      );
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "firehose360-account.json";
      link.click();
      setTimeout(() => URL.revokeObjectURL(url), 0);
      setExportProgress(
        "Your account JSON download is ready. It contains private conversation text; store it securely.",
      );
    } catch (error) {
      report(error);
      if (owns() && isAbort(error)) setExportProgress("Export cancelled.");
    } finally {
      if (exporter.current === controller) exporter.current = null;
      if (owns()) setExporting(false);
    }
  }
  return (
    <section className="account-content">
      <div className="panel">
        <h3>Your account data</h3>
        <p>
          Download your account, conversations, messages, and generation records
          as JSON. Large exports collect all pages and take longer. Changes made
          during collection can appear in later pages.
        </p>
        <button disabled={exporting} onClick={exportAccount}>
          Download my account data
        </button>
        {exporting && (
          <button onClick={() => exporter.current?.abort()}>
            Cancel export
          </button>
        )}
        <p role="status" className="fine">
          {exportProgress}
        </p>
      </div>
      <div className="panel">
        <h3>Change your password</h3>
        <p>Changing your password signs out all your sessions.</p>
        <p>{user.email}</p>
        <form
          onSubmit={async (event) => {
            event.preventDefault();
            setBusy(true);
            try {
              await api<void>("/auth/password", "POST", {
                current_password: currentPassword,
                password,
              });
              if (owns()) await done();
            } catch (error) {
              report(error);
            } finally {
              if (owns()) setBusy(false);
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
            onChange={(event) => setCurrentPassword(event.target.value)}
          />
          <FormField
            label="New password"
            type="password"
            autoComplete="new-password"
            minLength={12}
            maxLength={128}
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
          <button className="primary" disabled={busy}>
            Change password & sign out
          </button>
        </form>
      </div>
      {factor && (
        <div className="panel">
          <h3>
            {factor.enrolled
              ? "Authenticator security"
              : "Enable an authenticator"}
          </h3>
          <p>
            {factor.enrolled
              ? "Your account requires an authenticator or a one-use recovery code at sign-in. Replacing the authenticator signs out every session."
              : "Add a second factor to protect your account. Confirming setup signs out every session; save the recovery codes before signing in again."}
          </p>
          {replacement ? (
            <form
              onSubmit={async (event) => {
                event.preventDefault();
                setBusy(true);
                try {
                  const result = await confirmMfa(factorCode);
                  completeMfa(result.recovery_codes);
                } catch (error) {
                  report(error);
                } finally {
                  if (owns()) setBusy(false);
                }
              }}
            >
              <p>Add the new key to your authenticator, then enter its code.</p>
              <FormField
                label="New authenticator setup key"
                readOnly
                value={replacement.secret}
              />
              <FormField
                label="New authenticator code"
                autoComplete="one-time-code"
                required
                maxLength={64}
                value={factorCode}
                onChange={(event) => setFactorCode(event.target.value)}
              />
              <button className="primary" disabled={busy}>
                Confirm replacement
              </button>
            </form>
          ) : (
            <form
              onSubmit={async (event) => {
                event.preventDefault();
                setBusy(true);
                try {
                  const result = await api<MfaEnrollment>(
                    "/auth/mfa/replace",
                    "POST",
                    { current_password: factorPassword, code: factorCode },
                  );
                  if (owns()) {
                    setReplacement(result);
                    setFactorPassword("");
                    setFactorCode("");
                  }
                } catch (error) {
                  report(error);
                } finally {
                  if (owns()) setBusy(false);
                }
              }}
            >
              <FormField
                label={
                  factor.enrolled
                    ? "Password to replace authenticator"
                    : "Password to enable authenticator"
                }
                type="password"
                autoComplete="current-password"
                required
                maxLength={128}
                value={factorPassword}
                onChange={(event) => setFactorPassword(event.target.value)}
              />
              {factor.enrolled && (
                <FormField
                  label="Current authenticator or recovery code"
                  autoComplete="one-time-code"
                  required
                  maxLength={64}
                  value={factorCode}
                  onChange={(event) => setFactorCode(event.target.value)}
                />
              )}
              <button disabled={busy}>
                {factor.enrolled
                  ? "Replace authenticator"
                  : "Set up authenticator"}
              </button>
            </form>
          )}
        </div>
      )}
    </section>
  );
}
