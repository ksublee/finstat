"""Keep chapter-4 labels stable after splitting its HTML pages."""
from pathlib import Path
from urllib.parse import unquote, urlsplit
import os
import re

ROOT = Path(__file__).resolve().parents[1]
PAGES = ("01-var", "02-es", "03-portfolio-var", "04-portfolio-es")
LABEL = re.compile(r"\{#((eq|fig|tbl)-[^ }]+)")
XREF = re.compile(r'(<a\b[^>]*class="[^"]*quarto-xref[^"]*"[^>]*>)(.*?)(</a>)', re.S)

def labels():
    counters = dict(eq=0, fig=0, tbl=0)
    result = {}
    for page in PAGES:
        source = ROOT / "chapters/04-var-es" / (page + ".qmd")
        for match in LABEL.finditer(source.read_text(encoding="utf-8")):
            key, kind = match.groups()
            if key in result:
                raise ValueError("Duplicate label: " + key)
            counters[kind] += 1
            result[key] = (page, kind, "4." + str(counters[kind]))
    return result

def rewrite_xref(match, numbering):
    opening, body, closing = match.groups()
    href = re.search(r'href="([^"]+)"', opening)
    if not href:
        return match.group(0)
    key = unquote(urlsplit(href.group(1)).fragment)
    if key not in numbering:
        return match.group(0)
    number = numbering[key][2]
    body, count = re.subn(r"<span>[^<]+</span>", lambda m: "<span>" + number + "</span>", body, count=1)
    if not count:
        raise ValueError("Unexpected xref markup: " + key)
    return opening + body + closing

def main():
    output = Path(os.environ.get("QUARTO_PROJECT_OUTPUT_DIR", "docs"))
    if not output.is_absolute():
        output = ROOT / output
    output = output.resolve()
    if ROOT not in output.parents:
        raise ValueError("Output must stay inside this project")
    numbering = labels()
    found = set()
    for path in output.rglob("*.html"):
        text = path.read_text(encoding="utf-8")
        updated = text
        if path.parent == output / "chapters/04-var-es" and path.stem in PAGES:
            for key, (page, kind, number) in numbering.items():
                if path.stem != page:
                    continue
                if kind == "eq":
                    pattern = re.compile(r'(<span id="' + re.escape(key) + r'">.*?\\tag\{)[^}]+(\})', re.S)
                else:
                    pattern = re.compile(r'(<figcaption[^>]*id="' + re.escape(key) + r'-caption-[^"]+"[^>]*>\s*(?:그림|표|Figure|Table)(?:&nbsp;|\s)+)[\d.]+(:)', re.S)
                updated, count = pattern.subn(lambda m: m.group(1) + number + m.group(2), updated, count=1)
                if count != 1:
                    raise ValueError("Missing tag/caption: " + key)
                found.add(key)
        updated = XREF.sub(lambda m: rewrite_xref(m, numbering), updated)
        if updated != text:
            path.write_text(updated, encoding="utf-8")
    expected = {key for key, (page, _, _) in numbering.items()
                if (output / "chapters/04-var-es" / (page + ".html")).is_file()}
    if found != expected:
        raise ValueError("Chapter-4 numbering validation failed")
    print("Chapter 4: preserved " + str(len(found)) + " equation/figure/table labels")

if __name__ == "__main__":
    main()
