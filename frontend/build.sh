#!/usr/bin/env bash
set -euo pipefail

# Render injects AI_TUTOR_BACKEND_HOST (e.g. ai-tutor-backend.onrender.com)
HOST="${AI_TUTOR_BACKEND_HOST:-127.0.0.1:8000}"

if [[ "$HOST" == http://* ]] || [[ "$HOST" == https://* ]]; then
  API_BASE="$HOST"
elif [[ "$HOST" == *:* ]]; then
  API_BASE="http://${HOST}"
else
  API_BASE="https://${HOST}"
fi

printf 'window.API_BASE = "%s";\n' "$API_BASE" > config.js
echo "Wrote config.js with API_BASE=${API_BASE}"
