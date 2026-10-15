"""Smoke-test a rendered book without third-party Python dependencies."""

from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


def check(output: Path) -> list[str]:
    errors = []
    # Entries in this book's chapter list, including part landing pages.
    sources = re.findall(r"^\s*(?:-\s+)?(?:part:\s*)?([\w./-]+\.qmd)\s*$",
                         (ROOT / "_quarto.yml").read_text(encoding="utf-8"), re.MULTILINE)
    if not sources:
        errors.append("No book chapters found in _quarto.yml")
    for source in sources:
        page = output / Path(source).with_suffix(".html")
        if not page.is_file() or page.stat().st_size == 0:
            errors.append(f"Missing or empty page: {page}")

    for source in (ROOT / "assets").rglob("*"):
        if source.is_file():
            target = output / source.relative_to(ROOT)
            if not target.is_file() or target.read_bytes() != source.read_bytes():
                errors.append(f"Missing or changed resource: {target}")

    for name in (".nojekyll", "search.json"):
        if not (output / name).is_file():
            errors.append(f"Missing {name}")

    for page in output.rglob("*.html"):
        html = page.read_text(encoding="utf-8")
        if 'id="quarto-sidebar"' in html:
            if 'chapter-04-parent' not in html or '4장 세부 내용' in html:
                errors.append(f"Chapter-4 sidebar hierarchy is incorrect: {page}")
            if 'chapter-12-parent' not in html or '12장 세부 내용' in html:
                errors.append(f"Chapter-12 sidebar hierarchy is incorrect: {page}")

    # Split chapter pages must link to rendered HTML, with existing targets.
    for page in (output / "chapters/12-continuous-time-model").glob("*.html"):
        html = page.read_text(encoding="utf-8")
        for value in re.findall(r'(?:href|src)="([^"]+)"', html):
            link = urlsplit(value)
            if link.scheme or link.netloc or value.startswith("/"):
                continue
            target = page.parent / unquote(link.path) if link.path else page
            if target.suffix == ".qmd":
                errors.append(f"Unrendered QMD link in {page}: {value}")
            elif target.suffix in (".html", ".svg", ".png"):
                if not target.is_file():
                    errors.append(f"Missing chapter-12 link target in {page}: {value}")
                elif link.fragment and target.suffix == ".html":
                    anchor = 'id="' + unquote(link.fragment) + '"'
                    if anchor not in target.read_text(encoding="utf-8"):
                        errors.append(f"Missing chapter-12 anchor in {page}: {value}")
        if re.search(r'\?(?:eq|fig|tbl)-', html):
            errors.append(f"Unresolved chapter-12 cross-reference in {page}")

    probes = {
        "chapters/04-var-es/index.html": ["chapter-04-redirects.js", "01-var.html"],
        "chapters/04-var-es/01-var.html": ["sec-five-day-var", r"\tag{4.6}"],
        "chapters/04-var-es/02-es.html": ["eq-es-general", r"\tag{4.8}"],
        "chapters/04-var-es/03-portfolio-var.html": ["eq-marginal-var", r"\tag{4.13}"],
        "chapters/04-var-es/04-portfolio-es.html": ["eq-portfolio-es", r"\tag{4.21}"],
        "chapters/12-continuous-time-model/index.html": [
            "01-stochastic-models.html", "02-black-scholes.html", "03-dynamic-trading.html"],
        "chapters/12-continuous-time-model/01-stochastic-models.html": [
            "12.1 확률 모형", r"\tag{12.1}", "eq-gbm-s"],
        "chapters/12-continuous-time-model/02-black-scholes.html": [
            "12.2 블랙-숄즈", "eq-delta", "fig-surface"],
        "chapters/12-continuous-time-model/03-dynamic-trading.html": [
            "12.3 동적 거래 전략", "eq-bs-pde", "fig-c-repl"],
        "chapters/13-option-market-price/index.html": [
            '<span class="chapter-number">13</span>'],
        "chapters/02-modern-portfolio-theory/index.html": [
            'class="math', "portfolio-mu-c", "market-portfolio"],
        "labs/09-backtesting-lab.html": [
            "qwebr", "webr.mjs", 'class="math'],
    }
    for name, markers in probes.items():
        path = output / name
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        for marker in markers:
            if marker not in text:
                errors.append(f"Missing {marker!r} in {name}")
    return errors


if __name__ == "__main__":
    errors = check(Path(sys.argv[1] if len(sys.argv) > 1 else "docs"))
    if errors:
        sys.exit("Render checks failed:\n" + "\n".join(errors))
    print("Render checks passed: book pages, resources, math and webR markup.")
