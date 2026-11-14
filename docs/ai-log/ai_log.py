# AI-assisted: Claude (Anthropic). See docs/ai-log/2026-11-14_1454_nicholas_merge-ideias.md
"""Utilities for the team's AI log (docs/ai-log/*.md + docs/decisions.md).

Usage:
    python docs/ai-log/ai_log.py pendencias [nome]   # open "- [ ] @nome" items
    python docs/ai-log/ai_log.py sintese             # merged view of both people (Markdown)
    python docs/ai-log/ai_log.py ai-use              # AI Use declaration (Markdown)

`sintese` is regenerated automatically into docs/SINTESE.md by the GitHub Action
.github/workflows/sintese.yml on every push. Only the standard library is used.
"""
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent
DECISIONS = LOG_DIR.parent / "decisions.md"
SECTION_AI_CODE = "código gerado ou alterado com ia"
SECTION_TODO = "pendências"
SECTION_IDEAS = "ideias"
IDEA_RE = re.compile(r"^-\s+#([\w-]+)\s+(.+)$")
REF_RE = re.compile(r"(confirma|descarta|substitui)\s*#(\d+)", re.I)
STOPWORDS = {
    "para", "como", "com", "sem", "pelo", "pela", "entre", "sobre", "cada", "mais",
    "menos", "quando", "onde", "isso", "esse", "essa", "este", "esta", "usar", "fazer",
    "todos", "todas", "apenas", "também", "depois", "antes", "porque", "mesmo",
}


# ---------------------------------------------------------------- parsing
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


def read_decisions():
    """Parse docs/decisions.md into a list of dicts, in table order."""
    rows = []
    if not DECISIONS.exists():
        return rows
    for line in DECISIONS.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 6 or not cells[0].isdigit():
            continue
        cells += [""] * (7 - len(cells))
        rows.append(dict(zip(["n", "data", "quem", "decisao", "motivo", "status", "log"], cells)))
        rows[-1]["n"] = int(rows[-1]["n"])
    return rows


def resolve_decisions(rows):
    """Apply 'Confirma #N', 'Descarta #N' and 'substitui #N' to get each decision's state.

    Returns (decisions, actions): decisions keyed by number with an 'estado' field
    (confirmada | proposta | descartada | substituida), and the action rows.
    """
    decisions, actions = {}, []
    for r in rows:
        ref = REF_RE.match(r["decisao"])
        if ref and ref.group(1).lower() in ("confirma", "descarta"):
            actions.append(r)
            continue
        r = dict(r, estado="confirmada" if r["status"].startswith("confirmada") else
                 "descartada" if r["status"].startswith("descartada") else "proposta",
                 confirmado_por=None, substituida_por=None, substituicao_proposta=None)
        decisions[r["n"]] = r
    for a in actions:  # confirmations / discards
        ref = REF_RE.match(a["decisao"])
        target = decisions.get(int(ref.group(2)))
        if not target:
            continue
        if ref.group(1).lower() == "confirma":
            target["estado"], target["confirmado_por"] = "confirmada", a["quem"]
        else:
            target["estado"] = "descartada"
    for r in decisions.values():  # substitutions only take effect once confirmed
        ref = REF_RE.search(r["status"])
        if not (ref and ref.group(1).lower() == "substitui" and int(ref.group(2)) in decisions):
            continue
        old = decisions[int(ref.group(2))]
        if r["estado"] == "confirmada":
            old["estado"], old["substituida_por"] = "substituida", r["n"]
        elif r["estado"] == "proposta":
            old["substituicao_proposta"] = r["n"]
    return decisions, actions


def note(d):
    n = d.get("substituicao_proposta")
    return f" *(substituição proposta em #{n})*" if n else ""


def tokens(text):
    text = unicodedata.normalize("NFKD", text.lower()).encode("ascii", "ignore").decode()
    return {w for w in re.findall(r"[a-z0-9]{4,}", text) if w not in STOPWORDS}


def similar(a, b, threshold=0.25):
    ta, tb = tokens(a), tokens(b)
    return bool(ta and tb) and len(ta & tb) / len(ta | tb) >= threshold


# ---------------------------------------------------------------- commands
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


def sintese():
    decisions, _ = resolve_decisions(read_decisions())
    logs = list(iter_logs())
    authors = sorted({d["quem"] for d in decisions.values()} | {m.get("autor", "?") for _, m, _ in logs})
    out = ["# Síntese da dupla", "",
           "> Gerado automaticamente a cada push por `.github/workflows/sintese.yml`. **Não edite à mão.**",
           "> Fonte: `docs/decisions.md` + `docs/ai-log/`.", ""]

    # 1. current state
    confirmed = [d for d in decisions.values() if d["estado"] == "confirmada"]
    out += ["## ✅ Estado atual (confirmado pelos dois)", ""]
    out += [f"- **#{d['n']}** {d['decisao']} — *{d['quem']}*{note(d)}" for d in confirmed] or ["- —"]
    out.append("")

    # 2. waiting for review, per author
    pending = [d for d in decisions.values() if d["estado"] == "proposta"]
    out += ["## ⏳ Esperando revisão da outra pessoa", ""]
    if not pending:
        out += ["- —", ""]
    for who in authors:
        mine = [d for d in pending if d["quem"] == who]
        if mine:
            out += [f"**Propostas de {who}:**", ""]
            out += [f"- **#{d['n']}** {d['decisao']} — {d['motivo']}{note(d)}" for d in mine]
            out.append("")

    # 3. ideas grouped by theme
    ideas = defaultdict(list)
    for path, meta, sections in logs:
        for line in find_section(sections, SECTION_IDEAS):
            m = IDEA_RE.match(line.strip())
            if m:
                ideas[m.group(1).lower()].append((m.group(2).strip(), meta.get("autor", "?"), path.name))
    out += ["## 💡 Ideias por tema", ""]
    if not ideas:
        out += ["- —", ""]
    for tema in sorted(ideas):
        who = {a for _, a, _ in ideas[tema]}
        flag = " 🔀 *ideias dos dois — combinar*" if len(who) > 1 else ""
        out += [f"### #{tema}{flag}", ""]
        out += [f"- {text} — *{a}* ([log](ai-log/{log}))" for text, a, log in ideas[tema]]
        out.append("")

    # 4. possible conflicts between people
    active = [d for d in decisions.values() if d["estado"] in ("confirmada", "proposta")]
    conflicts = [(a, b) for i, a in enumerate(active) for b in active[i + 1:]
                 if a["quem"] != b["quem"] and similar(a["decisao"], b["decisao"])]
    out += ["## ⚠️ Possíveis conflitos ou sobreposições", "",
            "*Detectados por palavras em comum; confirme com o Claude no \"abrir sessão\".*", ""]
    out += [f"- #{a['n']} ({a['quem']}) × #{b['n']} ({b['quem']}): {a['decisao']} ↔ {b['decisao']}"
            for a, b in conflicts] or ["- —"]
    out.append("")

    # 5. open tasks per person
    todo = defaultdict(list)
    for path, meta, sections in logs:
        for line in find_section(sections, SECTION_TODO):
            item = line.strip()
            if item.startswith("- [ ]"):
                m = re.search(r"@([\w-]+)", item)
                todo[m.group(1).lower() if m else "sem-dono"].append((item[5:].strip(), path.name))
    out += ["## 📋 Pendências abertas", ""]
    if not todo:
        out += ["- —", ""]
    for who in sorted(todo):
        out += [f"**@{who}:**", ""]
        out += [f"- [ ] {t} ([log](ai-log/{log}))" for t, log in todo[who]]
        out.append("")

    # 6. history
    old = [d for d in decisions.values() if d["estado"] in ("substituida", "descartada")]
    if old:
        out += ["<details><summary>Histórico: substituídas e descartadas</summary>", ""]
        for d in old:
            extra = f" → substituída por #{d['substituida_por']}" if d["substituida_por"] else " → descartada"
            out.append(f"- ~~#{d['n']} {d['decisao']}~~{extra}")
        out += ["", "</details>", ""]
    print("\n".join(out))


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
    sys.stdout.reconfigure(encoding="utf-8")
    args = sys.argv[1:]
    commands = {"sintese": sintese, "ai-use": ai_use}
    if args and args[0] == "pendencias":
        pendencias(args[1] if len(args) > 1 else None)
    elif args and args[0] in commands:
        commands[args[0]]()
    else:
        print(__doc__)
