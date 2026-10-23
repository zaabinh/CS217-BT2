"""Check repository Markdown links to local files and Markdown heading anchors."""
from pathlib import Path
import re
import sys
import unicodedata
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {".git", ".venv", "node_modules", "dist", ".pytest_cache", "test-results", "playwright-report"}
LINK = re.compile(r'!?\[[^\]\n]*\]\((<[^>]+>|[^)\s]+)(?:\s+"[^"]*")?\)')


def anchors(text: str) -> set[str]:
    result: set[str] = set()
    counts: dict[str, int] = {}
    for title in re.findall(r"^#{1,6}\s+(.+?)\s*#*\s*$", text, re.MULTILINE):
        title = re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", title)
        slug = "".join(c for c in title.lower() if c in "-_ " or unicodedata.category(c)[0] in "LNM")
        slug = slug.replace(" ", "-")
        count = counts.get(slug, 0)
        counts[slug] = count+1
        result.add(slug if count == 0 else f"{slug}-{count}")
    return result


def main() -> int:
    errors = []
    checked = 0
    documents = [p for p in ROOT.rglob("*.md") if not EXCLUDED.intersection(p.relative_to(ROOT).parts)]
    for document in documents:
        raw = document.read_text(encoding="utf-8-sig")
        text = re.sub(r"```.*?```", "", raw, flags=re.DOTALL)
        for match in LINK.finditer(text):
            href = match[1].strip("<>")
            url = urlsplit(href)
            if url.scheme or url.netloc:
                continue
            checked += 1
            target = (document.parent / unquote(url.path)).resolve() if url.path else document
            if not target.exists():
                errors.append(f"{document.relative_to(ROOT)}: missing {href}")
            elif url.fragment and target.suffix.lower() == ".md":
                if unquote(url.fragment) not in anchors(target.read_text(encoding="utf-8-sig")):
                    errors.append(f"{document.relative_to(ROOT)}: missing heading {href}")
    for error in errors:
        print(error)
    print(f"Checked {checked} local links in {len(documents)} Markdown files; {len(errors)} errors")
    return int(bool(errors))


if __name__ == "__main__":
    sys.exit(main())
