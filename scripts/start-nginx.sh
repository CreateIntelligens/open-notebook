#!/usr/bin/env bash
set -euo pipefail

TEMPLATE_PATH="/app/nginx.conf"
TARGET_PATH="/etc/nginx/sites-enabled/default"
SSL_CERT="/app/ssl/ssl-cert.pem"
PORT_VALUE="${PORT:-8899}"

if [ ! -f "${TEMPLATE_PATH}" ]; then
  echo "nginx template not found at ${TEMPLATE_PATH}" >&2
  exit 1
fi

if [ ! -f "${SSL_CERT}" ]; then
  echo "Waiting for SSL certificate at ${SSL_CERT}..."
  while [ ! -f "${SSL_CERT}" ]; do
    sleep 1
  done
fi

python - "$TEMPLATE_PATH" "$TARGET_PATH" "$PORT_VALUE" <<'PY'
import sys
from pathlib import Path

template_path = Path(sys.argv[1])
target_path = Path(sys.argv[2])
port = sys.argv[3]

content = template_path.read_text()
updated = content.replace("__PORT__", port)
target_path.write_text(updated)
PY

exec /usr/sbin/nginx -g 'daemon off;'
