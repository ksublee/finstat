"""Keep labels and sidebar hierarchy stable for split book chapters."""
from pathlib import Path
from urllib.parse import unquote, urlsplit
import os
import re
import argparse

ROOT = Path(__file__).resolve().parents[1]
PAGES = ("01-var", "02-es", "03-portfolio-var", "04-portfolio-es")
CHAPTER = 4
FOLDER = "04-var-es"
TITLE = "VaR와 ES"
LABEL = re.compile(r"\{#((eq|fig|tbl)-[^ }]+)")
XREF = re.compile(r'(<a\b[^>]*class="[^"]*quarto-xref[^"]*"[^>]*>)(.*?)(</a>)', re.S)

def labels():
    counters = dict(eq=0, fig=0, tbl=0)
    result = {}
    for page in PAGES:
        source = ROOT / "chapters" / FOLDER / (page + ".qmd")
        for match in LABEL.finditer(source.read_text(encoding="utf-8")):
            key, kind = match.groups()
            if key in result:
                raise ValueError("Duplicate label: " + key)
            counters[kind] += 1
            result[key] = (page, kind, str(CHAPTER) + "." + str(counters[kind]))
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

def nest_chapter_sidebar(text):
    """Use the numbered chapter link as the parent of its split pages."""
    folder = re.escape(FOLDER)
    heading = str(CHAPTER) + "장 세부 내용"
    parent = "chapter-" + str(CHAPTER).zfill(2) + "-parent"
    pattern = re.compile(
        r'<li class="sidebar-item">\s*<div class="sidebar-item-container">\s*'
        r'(?P<link><a href="[^"]*chapters/' + folder + r'/index\.html"[^>]*>.*?</a>)'
        r'\s*</div>\s*</li>\s*<li class="sidebar-item sidebar-item-section">'
        r'\s*<div class="sidebar-item-container">\s*'
        r'<a\b[^>]*>\s*<span class="menu-text">' + re.escape(heading) + r'</span></a>\s*'
        r'(?P<toggle><a class="sidebar-item-toggle[^>]*>.*?</a>)\s*</div>', re.S)
    def replace(match):
        return ('<li class="sidebar-item sidebar-item-section ' + parent + '">'
                '\n<div class="sidebar-item-container">' + match['link']
                + match['toggle'] + '</div>')
    text, count = pattern.subn(replace, text)
    if count != 1 and parent not in text:
        raise ValueError(f"Chapter-{CHAPTER} sidebar structure changed")
    # The part breadcrumb originally points to its first child, not the overview.
    text = re.sub(
        r'(<a href=")([^"<>]*chapters/' + folder + r'/)' + re.escape(PAGES[0]) + r'\.html(">)' + re.escape(heading) + r'</a>',
        r'\g<1>\g<2>index.html\g<3>' + str(CHAPTER) + ' ' + TITLE + '</a>', text)
    if heading in text:
        raise ValueError(f"Obsolete chapter-{CHAPTER} heading remains")
    return text

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
        updated = nest_chapter_sidebar(text) if 'id="quarto-sidebar"' in text else text
        if path.parent == output / "chapters" / FOLDER and path.stem in PAGES:
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
                if (output / "chapters" / FOLDER / (page + ".html")).is_file()}
    if found != expected:
        raise ValueError(f"Chapter-{CHAPTER} numbering validation failed")
    print(f"Chapter {CHAPTER}: preserved " + str(len(found)) + " equation/figure/table labels")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chapter", type=int, choices=(4, 12), default=4)
    args = parser.parse_args()
    if args.chapter == 12:
        CHAPTER = 12
        FOLDER = "12-continuous-time-model"
        TITLE = "연속시간 모형"
        PAGES = ("01-stochastic-models", "02-black-scholes", "03-dynamic-trading")
    main()
