#!/usr/bin/env bash
set -euo pipefail

# inspect_runtime_artifacts.sh - Tier 3 fallback inspection utility for compiled binaries/runtimes.
#
# Only used when source code is completely unobtainable (closed-source, proprietary binaries).
# Inspects symbol tables, stripped status, DWARF sections, and embedded strings.

TARGET="${1:-}"

if [[ -z "$TARGET" ]]; then
  echo "Usage: $0 <binary_path_or_command_name> [--query <keyword>] [--json]" >&2
  exit 1
fi

QUERY=""
AS_JSON=false
shift || true
while [[ $# -gt 0 ]]; do
  case "$1" in
    --query)
      QUERY="$2"
      shift 2
      ;;
    --debug-file)
      EXPLICIT_DEBUG="$2"
      shift 2
      ;;
    --json)
      AS_JSON=true
      shift
      ;;
    *)
      QUERY="$1"
      shift
      ;;
  esac
done

# Resolve binary path
BIN_PATH=""
if [[ -f "$TARGET" ]]; then
  BIN_PATH="$(realpath "$TARGET" 2>/dev/null || readlink -f "$TARGET" 2>/dev/null || echo "$TARGET")"
elif command -v "$TARGET" &>/dev/null; then
  BIN_PATH="$(command -v "$TARGET")"
  BIN_PATH="$(realpath "$BIN_PATH" 2>/dev/null || readlink -f "$BIN_PATH" 2>/dev/null || echo "$BIN_PATH")"
elif [[ -f "$HOME/.local/bin/$TARGET" ]]; then
  BIN_PATH="$HOME/.local/bin/$TARGET"
fi

if [[ -z "$BIN_PATH" || ! -f "$BIN_PATH" ]]; then
  echo "ERROR: Target binary '$TARGET' not found." >&2
  exit 1
fi

FILE_TYPE="$(file -b "$BIN_PATH")"
FILE_SIZE="$(du -sh "$BIN_PATH" | cut -f1)"
IS_STRIPPED=false
if echo "$FILE_TYPE" | grep -qi "stripped"; then
  IS_STRIPPED=true
fi

# Check for debug symbols
HAS_DEBUG_INFO=false
if echo "$FILE_TYPE" | grep -qi "with debug_info"; then
  HAS_DEBUG_INFO=true
fi

# Look for companion .debug binary or DWARF
DEBUG_COMPANION=""
BASE_DIR="$(dirname "$BIN_PATH")"
BIN_NAME="$(basename "$BIN_PATH")"
DEBUG_COMPANIONS=()
if [[ -n "${EXPLICIT_DEBUG:-}" && -f "$EXPLICIT_DEBUG" ]]; then
  DEBUG_COMPANIONS+=("$EXPLICIT_DEBUG")
fi
DEBUG_COMPANIONS+=(
  "$BIN_PATH.debug"
  "$BASE_DIR/${BIN_NAME%.*}.debug"
  "$BASE_DIR/$BIN_NAME.debug"
  "/usr/lib/debug$BIN_PATH"
  "/usr/lib/debug/$BIN_NAME.debug"
  "$HOME/.local/share/debug/$BIN_NAME.debug"
)
for cand in "${DEBUG_COMPANIONS[@]}"; do
  if [[ -f "$cand" && "$cand" != "$BIN_PATH" ]]; then
    DEBUG_COMPANION="$cand"
    break
  fi
done

# Count symbols
SYMBOL_COUNT=0
SYMBOL_PROVIDER="$BIN_PATH"
if [[ "$IS_STRIPPED" == "true" && -n "$DEBUG_COMPANION" ]]; then
  SYMBOL_PROVIDER="$DEBUG_COMPANION"
fi

if command -v nm &>/dev/null; then
  SYMBOL_COUNT="$(nm "$SYMBOL_PROVIDER" 2>/dev/null | wc -l || echo 0)"
fi

# Search strings if query provided
MATCHED_STRINGS=()
if [[ -n "$QUERY" ]] && command -v strings &>/dev/null; then
  while IFS= read -r line; do
    MATCHED_STRINGS+=("$line")
  done < <(strings "$BIN_PATH" 2>/dev/null | grep -i "$QUERY" | head -n 10 || true)
fi

if [[ "$AS_JSON" == "true" ]]; then
  python3 -c "
import json
print(json.dumps({
  'binary_path': '$BIN_PATH',
  'file_type': '$FILE_TYPE',
  'size': '$FILE_SIZE',
  'is_stripped': ('$IS_STRIPPED'.lower() == 'true'),
  'has_debug_info': ('$HAS_DEBUG_INFO'.lower() == 'true'),
  'debug_companion': '$DEBUG_COMPANION' if '$DEBUG_COMPANION' else None,
  'symbol_provider': '$SYMBOL_PROVIDER',
  'symbol_count': int('$SYMBOL_COUNT'),
  'query': '$QUERY' if '$QUERY' else None,
  'sample_matched_strings': [s for s in '''$(printf '%s\n' "${MATCHED_STRINGS[@]:-}")'''.splitlines() if s]
}, indent=2))
"
else
  echo "================================================================================"
  echo " [TIER 3 RUNTIME ARTIFACT INSPECTION]"
  echo "================================================================================"
  echo "Binary Path:       $BIN_PATH"
  echo "File Type:         $FILE_TYPE"
  echo "Size:              $FILE_SIZE"
  echo "Stripped:          $IS_STRIPPED"
  echo "Has Debug Info:    $HAS_DEBUG_INFO"
  if [[ -n "$DEBUG_COMPANION" ]]; then
    echo "Debug Companion:   $DEBUG_COMPANION (unstripped symbol provider)"
  fi
  echo "Available Symbols: $SYMBOL_COUNT (from $SYMBOL_PROVIDER)"
  if [[ -n "$QUERY" ]]; then
    echo ""
    echo "Strings matching '$QUERY' (top 10):"
    for str in "${MATCHED_STRINGS[@]:-}"; do
      echo "  $str"
    done
  fi
fi
