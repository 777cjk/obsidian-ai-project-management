#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
TARGET=""
REPLACE=0

usage() {
    cat <<'EOF'
Usage: scripts/install.sh --target PATH [--replace]

Validate this portable skill and install it into an explicit skills directory.
The target is the final skill folder (for example,
~/.codex/skills/obsidian-ai-project-management). Existing targets require
--replace and are moved to a timestamped sibling backup before installation.

No credentials, vault files, or host configuration are copied.
EOF
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --target)
            [ "$#" -ge 2 ] || { echo "--target requires a path" >&2; exit 2; }
            TARGET=$2
            shift 2
            ;;
        --replace)
            REPLACE=1
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "unknown option: $1" >&2
            usage >&2
            exit 2
            ;;
    esac
done

[ -n "$TARGET" ] || { usage >&2; exit 2; }
case "$TARGET" in
    /*) : ;;
    *) TARGET=$(CDPATH= cd -- "$TARGET" 2>/dev/null && pwd || printf '%s/%s' "$PWD" "$TARGET") ;;
esac

case "$TARGET" in
    "$ROOT_DIR"|"$ROOT_DIR"/*)
        echo "target must be outside the source checkout: $TARGET" >&2
        exit 2
        ;;
esac

PYTHON_BIN="${PYTHON_BIN:-python3}" "$ROOT_DIR/scripts/verify.sh"

PARENT_DIR=$(dirname -- "$TARGET")
TARGET_NAME=$(basename -- "$TARGET")
mkdir -p "$PARENT_DIR"
if [ -e "$TARGET" ] && [ "$REPLACE" -ne 1 ]; then
    echo "target exists; rerun with --replace: $TARGET" >&2
    exit 3
fi

STAGING="$PARENT_DIR/.${TARGET_NAME}.install.$$"
BACKUP_ROOT="$PARENT_DIR/.${TARGET_NAME}.backups"
cleanup() {
    if [ -d "$STAGING" ]; then
        rm -rf "$STAGING"
    fi
}
trap cleanup EXIT INT TERM

mkdir "$STAGING"
if command -v rsync >/dev/null 2>&1; then
    rsync -a --exclude '.git' --exclude '.DS_Store' "$ROOT_DIR/" "$STAGING/"
else
    cp -R "$ROOT_DIR/." "$STAGING/"
    rm -rf "$STAGING/.git" "$STAGING/.DS_Store"
fi

if [ -e "$TARGET" ]; then
    mkdir -p "$BACKUP_ROOT"
    BACKUP="$BACKUP_ROOT/$(date +%Y%m%d%H%M%S)-$$"
    mv "$TARGET" "$BACKUP"
    echo "previous installation moved to: $BACKUP"
fi
mv "$STAGING" "$TARGET"
trap - EXIT INT TERM
echo "installed skill: $TARGET"
