#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
NODE_VERSION=22.16.0
if [ ! -d node ]; then
  curl -fsSL https://nodejs.org/dist/v$NODE_VERSION/node-v$NODE_VERSION-linux-x64.tar.xz | tar -xJf -
  mv node-v$NODE_VERSION-linux-x64 node
fi
export PATH="$PWD/node/bin:$PATH"
corepack enable
corepack prepare pnpm@10.12.1 --activate
if [ ! -d node_modules ]; then
  pnpm install --prod
  pnpm build
fi
if [ ! -f .env ]; then
  echo "N8N_ENCRYPTION_KEY=$(openssl rand -hex 32)" > .env
  echo "N8N_HOST=0.0.0.0" >> .env
  echo "N8N_PORT=5678" >> .env
fi
packages/cli/bin/n8n start
