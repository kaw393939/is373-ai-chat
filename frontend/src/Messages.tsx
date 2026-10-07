import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Message } from "./contracts";

/** Render provider text as untrusted content; remote images never fetch trackers. */
export function Messages({
  messages,
  busy,
  notify,
  fail,
}: {
  messages: Message[];
  busy: boolean;
  notify: (text: string) => void;
  fail: (error: unknown) => void;
}) {
  return messages.map((message) => (
    <article key={message.id} className={"message " + message.role}>
      <div className="message-label">
        {message.role === "user" ? "YOU" : "WORKSHOP"}
      </div>
      <div>
        {message.content ? (
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
              img: ({ alt }) => <span>[External image omitted: {alt}]</span>,
            }}
          >
            {message.content}
          </Markdown>
        ) : (
          <span className="typing">
            {busy && message.id === "live"
              ? "Thinking…"
              : "No response was saved. Retry your prompt."}
          </span>
        )}
      </div>
      {message.content && (
        <button
          aria-label={`Copy ${message.role} message`}
          onClick={() =>
            navigator.clipboard
              .writeText(message.content)
              .then(() => notify("Message copied."))
              .catch(fail)
          }
        >
          Copy
        </button>
      )}
    </article>
  ));
}
