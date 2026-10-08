#!/usr/bin/env bash
# Instala Node 24, Paperclip, Cubicle e as CLIs dos agentes num Debian (LXC).
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  echo "Rode como root." >&2
  exit 1
fi

apt-get update
apt-get install -y curl ca-certificates git

# Paperclip pede Node.js 24.11+
if ! node -v 2>/dev/null | grep -qE '^v(2[4-9]|[3-9][0-9])\.'; then
  curl -fsSL https://deb.nodesource.com/setup_24.x | bash -
  apt-get install -y nodejs
fi
echo "Node $(node -v)"

# CLIs dos agentes
npm install -g @anthropic-ai/claude-code @google/gemini-cli opencode-ai

# Cubicle (escritório visual)
if [ ! -d /opt/cubicle ]; then
  git clone https://github.com/caglarutkuguler/cubicle.git /opt/cubicle
fi

cat <<'MSG'

Pronto. Próximos passos:
  1. Paperclip:  npx paperclipai@latest onboard --yes   (UI em http://localhost:3100)
  2. Cubicle:    node /opt/cubicle/bin/cubicle.js --host 0.0.0.0
                 depois abra http://IP-DO-CONTAINER:3200
  3. Logins:     claude   |   gemini   |   opencode auth login
  Veja setup/configurar-agentes.md
MSG
