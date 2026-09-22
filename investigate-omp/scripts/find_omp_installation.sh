#!/usr/bin/env bash
set -euo pipefail

# 1. Locate omp executable
OMP_BIN=""
if command -v omp &>/dev/null; then
  OMP_BIN="$(command -v omp)"
elif [[ -x "/home/linuxbrew/.linuxbrew/bin/omp" ]]; then
  OMP_BIN="/home/linuxbrew/.linuxbrew/bin/omp"
elif [[ -x "$HOME/.local/bin/omp" ]]; then
  OMP_BIN="$HOME/.local/bin/omp"
elif [[ -x "/usr/local/bin/omp" ]]; then
  OMP_BIN="/usr/local/bin/omp"
fi

if [[ -z "$OMP_BIN" ]]; then
  echo "ERROR: omp binary not found in PATH or standard installation locations." >&2
  exit 1
fi

RESOLVED_BIN="$(realpath "$OMP_BIN" 2>/dev/null || readlink -f "$OMP_BIN" 2>/dev/null || echo "$OMP_BIN")"

# 2. Extract version
OMP_VERSION="$("$OMP_BIN" --version 2>/dev/null || echo "unknown")"

# 3. Locate source checkout if available
CANDIDATE_SRC=(
  "${OMP_SRC_DIR:-}"
  "$HOME/Projects/public/oh-my-pi"
  "$HOME/Extern/oh-my-pi"
  "$HOME/Projects/oh-my-pi"
  "$HOME/oh-my-pi"
  "/workspace/oh-my-pi"
)

SRC_CHECKOUT=""
SRC_GIT="none"
for dir in "${CANDIDATE_SRC[@]}"; do
  if [[ -n "$dir" && -d "$dir" && -f "$dir/package.json" ]]; then
    if grep -q '"name": "@oh-my-pi/' "$dir/package.json" 2>/dev/null || grep -q 'oh-my-pi' "$dir/package.json" 2>/dev/null || [[ -d "$dir/crates/pi-natives" ]]; then
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

# 4. Locate base directories
AGENT_DIR="${PI_CODING_AGENT_DIR:-$HOME/.omp/agent}"
OMP_ROOT="$HOME/.omp"
PROJECT_OMP=""
if [[ -d "./.omp" ]]; then
  PROJECT_OMP="$(pwd -P)/.omp"
fi

# 5. Key configuration files
GLOBAL_CONFIG="$AGENT_DIR/config.yml"
GLOBAL_MODELS="$AGENT_DIR/models.yml"
AUTH_DB="$AGENT_DIR/agent.db"
HISTORY_DB="$AGENT_DIR/history.db"

# 6. Natives addon inspection
NATIVES_DIR="$OMP_ROOT/natives"
ACTIVE_NATIVE=""
if [[ -d "$NATIVES_DIR" ]]; then
  ACTIVE_NATIVE="$(find "$NATIVES_DIR" -maxdepth 2 -name "*.node" 2>/dev/null | head -n 1 || true)"
fi

# 7. Extensions and plugins
EXTENSIONS_DIR="$AGENT_DIR/extensions"
PLUGINS_DIR="$OMP_ROOT/plugins"

# 8. Recent log files
LOGS_DIR="$OMP_ROOT/logs"
LATEST_LOG=""
TOTAL_LOGS=0
if [[ -d "$LOGS_DIR" ]]; then
  LATEST_LOG="$(ls -t "$LOGS_DIR"/omp.*.log 2>/dev/null | head -n 1 || true)"
  TOTAL_LOGS="$(ls -1 "$LOGS_DIR"/omp.*.log 2>/dev/null | wc -l || echo 0)"
fi

# 9. Output results
if [[ "${1:-}" == "--json" ]]; then
  python3 -c "
import json
print(json.dumps({
  'omp_bin': '$OMP_BIN',
  'resolved_bin': '$RESOLVED_BIN',
  'version': '$OMP_VERSION',
  'source_checkout': '$SRC_CHECKOUT' if '$SRC_CHECKOUT' else None,
  'source_git': '$SRC_GIT' if '$SRC_CHECKOUT' else None,
  'omp_root': '$OMP_ROOT',
  'agent_dir': '$AGENT_DIR',
  'project_omp': '$PROJECT_OMP',
  'config_yml': '$GLOBAL_CONFIG' if '$GLOBAL_CONFIG' else None,
  'models_yml': '$GLOBAL_MODELS' if '$GLOBAL_MODELS' else None,
  'auth_db': '$AUTH_DB',
  'natives_dir': '$NATIVES_DIR',
  'active_native_addon': '$ACTIVE_NATIVE',
  'extensions_dir': '$EXTENSIONS_DIR',
  'plugins_dir': '$PLUGINS_DIR',
  'logs_dir': '$LOGS_DIR',
  'latest_log': '$LATEST_LOG',
  'total_logs': int('$TOTAL_LOGS')
}, indent=2))
"
else
  echo "OMP Executable:         $OMP_BIN -> $RESOLVED_BIN"
  echo "OMP Version:            $OMP_VERSION"
  echo "Source Checkout:        ${SRC_CHECKOUT:-not checked out locally (installed via Homebrew binary)}"
  if [[ -n "$SRC_CHECKOUT" ]]; then
    echo "Source Git Info:        $SRC_GIT"
  fi
  echo "Global Root:            $OMP_ROOT"
  echo "Agent Directory:        $AGENT_DIR"
  [[ -n "$PROJECT_OMP" ]] && echo "Project .omp Directory: $PROJECT_OMP"
  echo "Global Config:          $GLOBAL_CONFIG ($(if [[ -f "$GLOBAL_CONFIG" ]]; then echo "exists"; else echo "missing"; fi))"
  echo "Global Models:          $GLOBAL_MODELS ($(if [[ -f "$GLOBAL_MODELS" ]]; then echo "exists"; else echo "missing"; fi))"
  echo "Active Native Addon:    ${ACTIVE_NATIVE:-none detected}"
  echo "Extensions Directory:   $EXTENSIONS_DIR"
  echo "Plugins Directory:      $PLUGINS_DIR"
  echo "Logs Directory:         $LOGS_DIR ($TOTAL_LOGS log files, latest: $(basename "${LATEST_LOG:-none}"))"
fi
