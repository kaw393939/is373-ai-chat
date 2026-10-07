import { useLayoutEffect, useRef, useId } from "react";
import type { ReactNode } from "react";

/** showModal supplies native focus containment and inert background controls. */
export function Dialog({
  title,
  children,
  onClose,
  busy = false,
  error = "",
  initialFocus,
}: {
  title: string;
  children: ReactNode;
  onClose: () => void;
  busy?: boolean;
  error?: string;
  initialFocus?: string;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  useLayoutEffect(() => {
    const trigger =
      document.activeElement instanceof HTMLElement
        ? document.activeElement
        : null;
    const dialog = ref.current!;
    dialog.showModal();
    if (initialFocus) dialog.querySelector<HTMLElement>(initialFocus)?.focus();
    return () => {
      dialog.close();
      const target = trigger?.isConnected
        ? trigger
        : document.querySelector<HTMLElement>(".new-chat, main input");
      target?.focus();
    };
  }, []);
  return (
    <dialog
      ref={ref}
      className="modal"
      aria-labelledby={titleId}
      onKeyDown={(event) => {
        if (
          event.key !== "Tab" ||
          event.altKey ||
          event.ctrlKey ||
          event.metaKey
        )
          return;
        const targets = [
          ...event.currentTarget.querySelectorAll<HTMLElement>(
            "button, input, select, textarea, a[href], [tabindex]",
          ),
        ].filter(
          (target) =>
            target.tabIndex >= 0 &&
            !target.matches(":disabled") &&
            target.getClientRects().length > 0,
        );
        const first = targets[0];
        const last = targets.at(-1);
        if (!first) {
          event.preventDefault();
          event.currentTarget.focus();
        } else if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last?.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first.focus();
        }
      }}
      onCancel={(event) => {
        event.preventDefault();
        if (!busy) onClose();
      }}
    >
      <div className="panel">
        <h3 id={titleId}>{title}</h3>
        {error && (
          <p role="alert" className="notice">
            {error}
          </p>
        )}
        {children}
      </div>
    </dialog>
  );
}
