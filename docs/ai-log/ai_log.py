# AI-assisted: Claude (Anthropic). See docs/ai-log/2026-11-14_1430_nicholas_documentacao.md
"""Utilities for the team's AI log (docs/ai-log/*.md).

Usage:
    python docs/ai-log/ai_log.py pendencias [nome]   # open "- [ ] @nome" items
    python docs/ai-log/ai_log.py ai-use              # AI Use declaration (Markdown)

Only the standard library is used.
"""
import re
import sys
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent
SECTION_AI_CODE = "código gerado ou alterado com ia"
SECTION_TODO = "pendências"


def iter_logs():
    """Yield (path, meta: dict, sections: dict[str, list[str]]) for each log file."""
    for path in sorted(LOG_DIR.glob("*.md")):
        if path.name.startswith("_") or path.name.lower() == "readme.md":
            continue
        text = path.read_text(encoding="utf-8")
        meta, body = {}, text
        m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.S)
        if m:
            for line in m.group(1).splitlines():
                if ":" in line:
                    key, value = line.split(":", 1)
                    meta[key.strip()] = re.split(r"\s+#", value, maxsplit=1)[0].strip()
            body = m.group(2)
        sections, current = {}, None
        for line in body.splitlines():
            if line.startswith("## "):
                current = line[3:].strip().lower()
                sections[current] = []
            elif current and line.strip():
                sections[current].append(line.rstrip())
        yield path, meta, sections


def find_section(sections, prefix):
    for name, lines in sections.items():
        if name.startswith(prefix):
            return lines
    return []


def pendencias(nome=None):
    found = 0
    for path, meta, sections in iter_logs():
        for line in find_section(sections, SECTION_TODO):
            item = line.strip()
            if not item.startswith("- [ ]"):
                continue
            if nome and f"@{nome.lower()}" not in item.lower():
                continue
            print(f"{item}   ({meta.get('autor', '?')}, {path.name})")
            found += 1
    if not found:
        print("Nenhuma pendência aberta.")


def ai_use():
    tools, rows = set(), []
    for path, meta, sections in iter_logs():
        if meta.get("ferramenta"):
            tools.add(meta["ferramenta"])
        for line in find_section(sections, SECTION_AI_CODE):
            item = line.strip().lstrip("-").strip()
            if item and item != "—":
                rows.append((item, meta.get("autor", "?"), meta.get("data", "?"), path.name))
    print("## AI Use\n")
    print(f"Tools used: {', '.join(sorted(tools)) or '—'}.\n")
    print("Each AI session is summarized in `docs/ai-log/`; AI-assisted files carry a header comment.\n")
    print("| File / function | Author | Date | Session log |")
    print("|---|---|---|---|")
    for item, autor, data, log in rows:
        print(f"| {item.replace('|', '/')} | {autor} | {data} | [{log}](ai-log/{log}) |")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "pendencias":
        pendencias(args[1] if len(args) > 1 else None)
    elif args and args[0] == "ai-use":
        ai_use()
    else:
        print(__doc__)
