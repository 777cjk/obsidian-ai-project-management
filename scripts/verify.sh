#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
PYTHON_BIN=${PYTHON_BIN:-python3}
cd "$ROOT_DIR"

"$PYTHON_BIN" - "$ROOT_DIR" <<'PY'
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
skill = root / "SKILL.md"
if not skill.is_file():
    raise SystemExit("missing SKILL.md")
text = skill.read_text(encoding="utf-8")
lines = text.splitlines()
if not lines or lines[0] != "---" or "---" not in lines[1:]:
    raise SystemExit("SKILL.md must start with YAML frontmatter")
closing = lines[1:].index("---") + 1
frontmatter = "\n".join(lines[1:closing])
for key in ("name:", "description:"):
    if not re.search(rf"^ {{0,2}}{re.escape(key)}", frontmatter, re.MULTILINE):
        raise SystemExit(f"frontmatter is missing {key}")
if "name: obsidian-ai-project-management" not in frontmatter:
    raise SystemExit("unexpected skill name")

for path in root.rglob("*"):
    if not path.is_file() or ".git" in path.parts:
        continue
    if path.suffix.lower() not in {".md", ".yaml", ".yml"}:
        continue
    body = path.read_text(encoding="utf-8")
    if re.search(r"/(Users|home)/[A-Za-z0-9_.-]+", body):
        raise SystemExit(f"host-specific absolute path found: {path}")
    if re.search(r"(?i)(api[_-]?key|access[_-]?token|refresh[_-]?token|cookie)\s*[:=]\s*['\"]?[^ <>{}\n]+", body):
        raise SystemExit(f"credential-like value found: {path}")

link_pattern = re.compile(r"\[[^\]]+\]\(([^)#]+)(?:#[^)]+)?\)")
for path in root.rglob("*.md"):
    if ".git" in path.parts:
        continue
    for target in link_pattern.findall(path.read_text(encoding="utf-8")):
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        target_path = (path.parent / target).resolve()
        if not target_path.exists():
            raise SystemExit(f"broken relative link in {path}: {target}")
print("skill package verification passed")
PY

"$PYTHON_BIN" -m unittest discover -s tests -v

VALIDATOR=${SKILL_VALIDATOR:-}
if [ -n "$VALIDATOR" ]; then
    "$PYTHON_BIN" "$VALIDATOR" "$ROOT_DIR"
fi
