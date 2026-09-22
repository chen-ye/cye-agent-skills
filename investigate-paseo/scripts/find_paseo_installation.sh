#!/usr/bin/env bash
set -euo pipefail

# 1. Locate paseo executable
PASEO_BIN=""
if command -v paseo &>/dev/null; then
  PASEO_BIN="$(command -v paseo)"
elif [[ -x "$HOME/.local/share/mise/shims/paseo" ]]; then
  PASEO_BIN="$HOME/.local/share/mise/shims/paseo"
elif [[ -x "$HOME/.local/bin/paseo" ]]; then
  PASEO_BIN="$HOME/.local/bin/paseo"
elif [[ -x "/usr/local/bin/paseo" ]]; then
  PASEO_BIN="/usr/local/bin/paseo"
elif [[ -x "/home/linuxbrew/.linuxbrew/bin/paseo" ]]; then
  PASEO_BIN="/home/linuxbrew/.linuxbrew/bin/paseo"
elif [[ -x "/Applications/Paseo.app/Contents/Resources/bin/paseo" ]]; then
  PASEO_BIN="/Applications/Paseo.app/Contents/Resources/bin/paseo"
fi

RESOLVED_BIN=""
if [[ -n "$PASEO_BIN" ]]; then
  RESOLVED_BIN="$(realpath "$PASEO_BIN" 2>/dev/null || readlink -f "$PASEO_BIN" 2>/dev/null || echo "$PASEO_BIN")"
fi

# 2. Extract version
PASEO_VERSION="not-installed"
if [[ -n "$PASEO_BIN" ]]; then
  PASEO_VERSION="$("$PASEO_BIN" --version 2>/dev/null || echo "unknown")"
fi

# 3. Locate source checkout if available
CANDIDATE_SRC=(
  "${PASEO_SRC_DIR:-}"
  "$HOME/Projects/public/paseo"
  "$HOME/Projects/paseo"
  "$HOME/Extern/paseo"
  "$HOME/paseo"
  "/workspace/paseo"
)

SRC_CHECKOUT=""
SRC_GIT="none"
for dir in "${CANDIDATE_SRC[@]}"; do
  if [[ -n "$dir" && -d "$dir" && -f "$dir/package.json" ]]; then
    if grep -q '"name": "@getpaseo/' "$dir/package.json" 2>/dev/null || grep -q '"name": "paseo"' "$dir/package.json" 2>/dev/null; then
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

# 4. Locate daemon home & state directories
PASEO_HOME="${PASEO_HOME:-$HOME/.paseo}"
DAEMON_CONFIG="$PASEO_HOME/config.json"
DAEMON_LOG="$PASEO_HOME/daemon.log"
DAEMON_PID_FILE="$PASEO_HOME/daemon.pid"
AGENTS_DIR="$PASEO_HOME/agents"
WORKTREES_DIR="$PASEO_HOME/worktrees"
PLUGINS_DIR="$PASEO_HOME/plugins"

# 5. Check daemon running status
DAEMON_RUNNING=false
DAEMON_PID=""
if [[ -f "$DAEMON_PID_FILE" ]]; then
  PID_VAL="$(cat "$DAEMON_PID_FILE" 2>/dev/null || true)"
  if [[ -n "$PID_VAL" ]] && kill -0 "$PID_VAL" 2>/dev/null; then
    DAEMON_RUNNING=true
    DAEMON_PID="$PID_VAL"
  fi
fi

# Also probe local port 6767 health if curl is available
HTTP_PROBE="unreachable"
if command -v curl &>/dev/null; then
  if curl -s -f -m 1 http://127.0.0.1:6767/api/health &>/dev/null; then
    HTTP_PROBE="healthy (127.0.0.1:6767)"
    DAEMON_RUNNING=true
  fi
fi

# Count agent files
TOTAL_AGENTS=0
if [[ -d "$AGENTS_DIR" ]]; then
  TOTAL_AGENTS="$(find "$AGENTS_DIR" -maxdepth 1 -name "*.json" 2>/dev/null | wc -l || echo 0)"
fi

# Count worktrees
TOTAL_WORKTREES=0
if [[ -d "$WORKTREES_DIR" ]]; then
  TOTAL_WORKTREES="$(find "$WORKTREES_DIR" -maxdepth 1 -mindepth 1 -type d 2>/dev/null | wc -l || echo 0)"
fi

# 6. JSON output mode
if [[ "${1:-}" == "--json" ]]; then
  cat <<EOF
{
  "installed": $(if [[ -n "$PASEO_BIN" ]]; then echo true; else echo false; fi),
  "executable": "${PASEO_BIN:-null}",
  "resolvedBinary": "${RESOLVED_BIN:-null}",
  "version": "${PASEO_VERSION}",
  "daemonRunning": ${DAEMON_RUNNING},
  "daemonPid": "${DAEMON_PID:-null}",
  "daemonHttpProbe": "${HTTP_PROBE}",
  "paseoHome": "${PASEO_HOME}",
  "daemonConfig": "${DAEMON_CONFIG}",
  "daemonLog": "${DAEMON_LOG}",
  "agentsCount": ${TOTAL_AGENTS},
  "worktreesCount": ${TOTAL_WORKTREES},
  "sourceCheckout": "${SRC_CHECKOUT:-null}",
  "gitRevision": "${SRC_GIT}"
}
EOF
  exit 0
fi

# 7. Pretty text output
cat <<EOF
================================================================================
Paseo Runtime & Environment Inspection
================================================================================

[CLI & Executable]
  Active Command   : ${PASEO_BIN:-"NOT FOUND"}
  Resolved Binary  : ${RESOLVED_BIN:-"NOT FOUND"}
  Installed Version: ${PASEO_VERSION}

[Daemon Runtime & State]
  PASEO_HOME       : ${PASEO_HOME}
  Daemon Process   : $(if [[ "$DAEMON_RUNNING" == true ]]; then echo "RUNNING (PID: ${DAEMON_PID:-unknown})"; else echo "STOPPED"; fi)
  HTTP API Probe   : ${HTTP_PROBE}
  Daemon Config    : $(if [[ -f "$DAEMON_CONFIG" ]]; then echo "$DAEMON_CONFIG (present)"; else echo "$DAEMON_CONFIG (absent)"; fi)
  Daemon Log       : $(if [[ -f "$DAEMON_LOG" ]]; then echo "$DAEMON_LOG ($(stat -c%s "$DAEMON_LOG" 2>/dev/null || echo 0) bytes)"; else echo "$DAEMON_LOG (absent)"; fi)
  Active Agents    : ${TOTAL_AGENTS} persisted agent records
  Active Worktrees : ${TOTAL_WORKTREES} managed worktree directories

[Source Repository]
  Source Checkout  : ${SRC_CHECKOUT:-"Not detected in candidate paths"}
  Git Revision     : ${SRC_GIT}

================================================================================
EOF
