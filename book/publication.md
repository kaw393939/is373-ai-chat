# Authorship, access and reuse

Keith Williams is the project owner and responsible editor. The source history
identifies contributions and review changes. AI assisted implementation,
explanations, research, editorial checks and test preparation. Executed automated
checks verify the stated examples; they do not establish independent human peer
review, classroom effectiveness or publisher acceptance. The instructor pilot
record must be completed by a reader who did not author the exercise.

The owner selected public repository access, MIT for original code and CC BY 4.0
for original educational content on October 6, 2026. Repository visibility is
verified in the revision evidence rather than inferred from that decision. Code
excerpts retain MIT; original prose in `book/` and `docs/` is CC BY 4.0. See
[LICENSE](../LICENSE), [LICENSE-CONTENT](../LICENSE-CONTENT) and [NOTICE](../NOTICE).
Third-party works retain their own rights. Cite this book's title, Keith Williams
and contributors, the repository, the edition and the license; identify changes.
The [CC BY 4.0 license](https://creativecommons.org/licenses/by/4.0/) permits
sharing and adaptation subject to its terms.

## Third-party material register

| Material | Treatment in this edition | Distribution boundary |
|---|---|---|
| Primary historical papers, personal accounts, official manuals | Linked references and original paraphrases, recorded in [bibliography](references.md) | No copied papers or screenshots; external works retain their rights |
| Agile Manifesto | Original discussion of its values and linked original declaration | No partial facsimile or full declaration republished; retain the original site's copying notice when reproducing it elsewhere |
| Application source listings | Generated from this repository's canonical software | MIT notice accompanies a redistributed listing |
| Original book diagrams | Original diagram descriptions and project-authored SVG | CC BY 4.0 with textual explanations |
| MkDocs and its Python dependencies | Build tools recorded in `uv.lock` | Upstream package notices apply; no upstream logo or theme is presented as our authorship |
| React, Vite, PostgreSQL, Python and container base packages | Companion dependencies, not original book content | Their package licenses apply; image SBOM belongs to the release evidence |
| User screenshots and private host/account data | Excluded from the distributed book build | Do not add real account screens, inbox messages or credentials to learner submissions |

The register is an inventory, not a legal clearance opinion. An added quote,
image, imported exercise or substantial excerpt requires a new entry and a
review of its redistribution terms. No portraits, commercial cover art or
publisher marks are included.

## Production and errata

`make book` builds an offline-readable HTML edition with local styles, explicit
navigation, code listings and accessible diagrams. `make book-check` checks
source links, generated listings, the edition identity and browser rendering.
See [edition policy](edition.md). HTML is the supported publication output for
this development edition. A print/PDF edition requires a separate layout proof;
browser printing is a convenience, not a publication-ready typesetting claim.

To read the downloaded edition without internet access, start a local static
server in the bundle directory: `python -m http.server 8765 --bind 127.0.0.1
--directory book-html`, then open `http://127.0.0.1:8765/`. All reading assets are
local. Directory-style chapter URLs need this server; double-clicking an HTML
file is not the supported navigation path. External references need internet
when followed. Stop the static server with Ctrl+C.

Report an erratum as a GitHub issue with edition, chapter/heading, expected and
observed behavior and a sanitized reproduction. Link a correction to that issue
in an atomic commit; publish a new edition rather than silently rewriting an
archived evidence bundle. Security reports should omit exploit credentials and
personal data; use the repository's private vulnerability reporting when enabled.
