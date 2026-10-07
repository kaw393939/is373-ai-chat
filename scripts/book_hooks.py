"""Keep repository links correct when the Markdown is rendered as a book."""

import os
import re
from pathlib import Path
from urllib.parse import quote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


def on_page_markdown(markdown, page, config, files):
    source = Path(page.file.abs_src_path)
    revision = os.environ.get("BOOK_SOURCE_REF", "main")

    def link(match):
        target = match.group(2)
        parsed = urlsplit(target)
        if parsed.scheme or target.startswith("#"):
            return match.group(0)
        path = (source.parent / parsed.path).resolve()
        if not path.is_relative_to(ROOT) or not path.exists():
            raise ValueError(
                f"Broken or escaping book link in {source.relative_to(ROOT)}: {target}"
            )
        if path.is_relative_to(ROOT / "book"):
            return match.group(0)
        relative = path.relative_to(ROOT).as_posix()
        fragment = "#" + parsed.fragment if parsed.fragment else ""
        url = f"https://github.com/kaw393939/is373-ai-chat/blob/{revision}/{quote(relative)}{fragment}"
        return f"{match.group(1)}{url}{match.group(3)}"

    return re.sub(r"(\]\()([^\s)]+)(\))", link, markdown)
