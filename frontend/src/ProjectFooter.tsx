const repository = "https://github.com/kaw393939/is373-ai-chat";

/** Public learning/project navigation stays available across account states. */
export function ProjectFooter() {
  const links = [
    ["Textbook", `${repository}/blob/main/book/README.md`],
    ["Download book", `${repository}/releases/tag/book-v0.3.0`],
    ["Source code", repository],
    ["Issues / roadmap", `${repository}/issues`],
    ["Security report", `${repository}/security/policy`],
    ["Licenses", `${repository}/blob/main/NOTICE`],
    [
      "Privacy",
      `${repository}/blob/main/docs/decisions/0002-data-retention-and-export.md`,
    ],
  ];
  return (
    <footer className="project-footer">
      <nav aria-label="Project resources">
        {links.map(([label, href]) => (
          <a key={label} href={href} target="_blank" rel="noopener noreferrer">
            {label}
          </a>
        ))}
      </nav>
      <small>From Request to Release · a working textbook laboratory</small>
    </footer>
  );
}
