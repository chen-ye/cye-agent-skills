#!/usr/bin/env bash
set -euo pipefail

# Candidates to search for OpenCode source checkout
CANDIDATES=(
  "${OPENCODE_SRC_DIR:-}"
  "$HOME/Projects/public/opencode"
  "$HOME/Extern/opencode"
  "$HOME/opencode"
  "/workspace/opencode"
)

FOUND_ROOT=""
for dir in "${CANDIDATES[@]}"; do
  if [[ -n "$dir" && -d "$dir" && -f "$dir/package.json" ]]; then
    if grep -q '"name": "@opencode-ai/' "$dir/package.json" 2>/dev/null || grep -q '"name": "opencode"' "$dir/package.json" 2>/dev/null || [[ -d "$dir/packages/core" ]]; then
      FOUND_ROOT="$(cd "$dir" && pwd -P)"
      break
    fi
  fi
done

if [[ -z "$FOUND_ROOT" ]]; then
  echo "ERROR: OpenCode source checkout not found in candidate paths:" >&2
  for dir in "${CANDIDATES[@]}"; do
    [[ -n "$dir" ]] && echo "  - $dir" >&2
  done
  exit 1
fi

# Locate documentation directory
DOCS_DIR=""
if [[ -d "$FOUND_ROOT/packages/web/src/content/docs" ]]; then
  DOCS_DIR="$FOUND_ROOT/packages/web/src/content/docs"
elif [[ -d "$FOUND_ROOT/dev/packages/web/src/content/docs" ]]; then
  DOCS_DIR="$FOUND_ROOT/dev/packages/web/src/content/docs"
elif [[ -d "$FOUND_ROOT/packages/docs" ]]; then
  DOCS_DIR="$FOUND_ROOT/packages/docs"
fi

# Gather git info if available
GIT_INFO="not a git repo"
if [[ -d "$FOUND_ROOT/.git" ]] && command -v git &>/dev/null; then
  BRANCH="$(git -C "$FOUND_ROOT" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")"
  COMMIT="$(git -C "$FOUND_ROOT" rev-parse --short HEAD 2>/dev/null || echo "unknown")"
  GIT_INFO="$BRANCH ($COMMIT)"
fi

if [[ "${1:-}" == "--json" ]]; then
  python3 -c "
import json
print(json.dumps({
  'root': '$FOUND_ROOT',
  'docs': '$DOCS_DIR',
  'git': '$GIT_INFO',
  'packages': '$FOUND_ROOT/packages',
  'core': '$FOUND_ROOT/packages/core',
  'opencode': '$FOUND_ROOT/packages/opencode',
  'specs': '$FOUND_ROOT/specs'
}, indent=2))
"
else
  echo "OpenCode Checkout Root: $FOUND_ROOT"
  echo "Git Branch/Commit:     $GIT_INFO"
  echo "Documentation Path:    $DOCS_DIR"
  echo "Core Package Path:     $FOUND_ROOT/packages/core"
  echo "CLI Package Path:      $FOUND_ROOT/packages/opencode"
  echo "Specs Path:            $FOUND_ROOT/specs"
fi
