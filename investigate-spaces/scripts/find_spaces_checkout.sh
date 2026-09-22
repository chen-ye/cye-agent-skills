#!/usr/bin/env bash
set -euo pipefail

# 1. Locate spaces executable
SPACES_BIN=""
if command -v spaces &>/dev/null; then
  SPACES_BIN="$(command -v spaces)"
elif [[ -x "$HOME/.local/bin/spaces" ]]; then
  SPACES_BIN="$HOME/.local/bin/spaces"
elif [[ -x "/usr/local/bin/spaces" ]]; then
  SPACES_BIN="/usr/local/bin/spaces"
fi

if [[ -z "$SPACES_BIN" ]]; then
  echo "ERROR: spaces binary not found in PATH or standard installation locations." >&2
  exit 1
fi

RESOLVED_BIN="$(realpath "$SPACES_BIN" 2>/dev/null || readlink -f "$SPACES_BIN" 2>/dev/null || echo "$SPACES_BIN")"

# 2. Extract version
SPACES_VERSION="$("$SPACES_BIN" --version 2>/dev/null || echo "unknown")"

# 3. Locate source checkout if available
CANDIDATE_SRC=(
  "${SPACES_SRC_DIR:-}"
  "$HOME/Projects/public/work-spaces"
  "$HOME/Projects/public/spaces"
  "$HOME/Extern/work-spaces"
  "$HOME/Extern/spaces"
  "$HOME/Projects/work-spaces"
  "$HOME/work-spaces"
  "$HOME/spaces"
  "/workspace/work-spaces"
  "/workspace/spaces"
)

SRC_CHECKOUT=""
SRC_GIT="none"
for dir in "${CANDIDATE_SRC[@]}"; do
  if [[ -n "$dir" && -d "$dir" && -f "$dir/Cargo.toml" ]]; then
    if [[ -d "$dir/crates/spaces" && -d "$dir/crates/starstd" ]]; then
      SRC_CHECKOUT="$(cd "$dir" && pwd -P)"
      if [[ -d "$SRC_CHECKOUT/.git" ]] && command -v git &>/dev/null; then
        BRANCH="$(git -C "$SRC_CHECKOUT" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")"
        COMMIT="$(git -C "$SRC_CHECKOUT" rev-parse --short HEAD 2>/dev/null || echo "unknown")"
        SRC_GIT="$BRANCH ($COMMIT)"
      fi
      break
    fi
  fi
done

# 4. Global cache / store directory
GLOBAL_STORE="$HOME/.spaces"
STORE_EXISTS=false
STORE_SIZE="0B"
if [[ -d "$GLOBAL_STORE" ]]; then
  STORE_EXISTS=true
  STORE_SIZE="$(du -sh "$GLOBAL_STORE" 2>/dev/null | cut -f1 || echo "unknown")"
fi

# 5. Check if current working directory is inside a Spaces workspace
CURRENT_WS=""
IS_IN_WS=false
SEARCH_DIR="$(pwd -P)"
while [[ "$SEARCH_DIR" != "/" ]]; do
  if [[ -f "$SEARCH_DIR/co.spaces.toml" || -f "$SEARCH_DIR/spaces.star" || -f "$SEARCH_DIR/0.checkout.spaces.star" ]]; then
    CURRENT_WS="$SEARCH_DIR"
    IS_IN_WS=true
    break
  elif [[ -d "$SEARCH_DIR/.spaces" && "$SEARCH_DIR" != "$HOME" ]]; then
    CURRENT_WS="$SEARCH_DIR"
    IS_IN_WS=true
    break
  fi
  SEARCH_DIR="$(dirname "$SEARCH_DIR")"
done

# 6. Output results
if [[ "${1:-}" == "--json" ]]; then
  python3 -c "
import json
print(json.dumps({
  'spaces_bin': '$SPACES_BIN',
  'resolved_bin': '$RESOLVED_BIN',
  'version': '$SPACES_VERSION',
  'source_checkout': '$SRC_CHECKOUT' if '$SRC_CHECKOUT' else None,
  'source_git': '$SRC_GIT' if '$SRC_CHECKOUT' else None,
  'global_store': '$GLOBAL_STORE',
  'store_exists': ('$STORE_EXISTS'.lower() == 'true'),
  'store_size': '$STORE_SIZE',
  'is_in_workspace': ('$IS_IN_WS'.lower() == 'true'),
  'workspace_root': '$CURRENT_WS' if '$CURRENT_WS' else None,
  'crates': {
    'spaces': '$SRC_CHECKOUT/crates/spaces' if '$SRC_CHECKOUT' else None,
    'starstd': '$SRC_CHECKOUT/crates/starstd' if '$SRC_CHECKOUT' else None,
    'spaces_utils': '$SRC_CHECKOUT/crates/spaces-utils' if '$SRC_CHECKOUT' else None,
    'spaces_console': '$SRC_CHECKOUT/crates/spaces-console' if '$SRC_CHECKOUT' else None,
    'spaces_archiver': '$SRC_CHECKOUT/crates/spaces-archiver' if '$SRC_CHECKOUT' else None
  }
}, indent=2))
"
else
  echo "Spaces Binary:        $SPACES_BIN"
  echo "Resolved Path:        $RESOLVED_BIN"
  echo "Version:              $SPACES_VERSION"
  if [[ -n "$SRC_CHECKOUT" ]]; then
    echo "Source Checkout:      $SRC_CHECKOUT"
    echo "Git Branch/Commit:    $SRC_GIT"
  else
    echo "Source Checkout:      Not found in candidate locations"
  fi
  echo "Global Store (~/.spaces): $GLOBAL_STORE (exists: $STORE_EXISTS, size: $STORE_SIZE)"
  if [[ "$IS_IN_WS" == "true" ]]; then
    echo "Active Workspace:     $CURRENT_WS"
  else
    echo "Active Workspace:     None (not inside a spaces workspace)"
  fi
fi
