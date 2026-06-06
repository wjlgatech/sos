#!/usr/bin/env bash
# Scaffold a CopilotKit integration into a Next.js (App Router) app.
# Usage: scaffold.sh <app-dir>   (defaults to current dir). Idempotent-ish; review the diff.
# Installs the deps that avoid the known 500/bundling traps; writes the runtime route.
set -euo pipefail
APP="${1:-.}"
cd "$APP"

PM="pnpm"; command -v pnpm >/dev/null 2>&1 || PM="npm"
echo "Using package manager: $PM (in $(pwd))"

# CopilotKit + the non-obvious extras (openai: runtime eagerly imports its adapter;
# shiki: pnpm-hoist break; postcss/autoprefixer: Tailwind won't compile without them).
$PM add @copilotkit/react-core @copilotkit/react-ui @copilotkit/runtime openai shiki
$PM add @anthropic-ai/sdk@^0.57.0 || true
$PM add -D postcss autoprefixer

# PostCSS config (only if missing) — without this, Tailwind generates zero utilities.
if ! ls postcss.config.* >/dev/null 2>&1; then
  printf 'export default { plugins: { tailwindcss: {}, autoprefixer: {} } };\n' > postcss.config.mjs
  echo "wrote postcss.config.mjs"
fi

# Runtime route (only if missing).
ROUTE="src/app/api/copilotkit/route.ts"
[ -d src/app ] || ROUTE="app/api/copilotkit/route.ts"
mkdir -p "$(dirname "$ROUTE")"
if [ ! -f "$ROUTE" ]; then
  cat > "$ROUTE" <<'TS'
import { CopilotRuntime, AnthropicAdapter, copilotRuntimeNextJSAppRouterEndpoint } from "@copilotkit/runtime";
import Anthropic from "@anthropic-ai/sdk";
import { NextRequest } from "next/server";

const anthropic = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });
const serviceAdapter = new AnthropicAdapter({ anthropic, model: "claude-sonnet-4-6" });
const runtime = new CopilotRuntime();

export const POST = async (req: NextRequest) => {
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({ runtime, serviceAdapter, endpoint: "/api/copilotkit" });
  return handleRequest(req);
};
TS
  echo "wrote $ROUTE"
fi

echo
echo "Next (manual — see examples.md):"
echo "  1. Add ANTHROPIC_API_KEY to .env.local (and confirm the model is one your key has)."
echo "  2. Wrap layout in <CopilotKit runtimeUrl=\"/api/copilotkit\"> and import react-ui/styles.css BEFORE globals.css."
echo "  3. Add a 'use client' component with useCopilotAction (wired to your backend) + <CopilotSidebar/>."
echo "  4. Verify: empty POST /api/copilotkit returns 400 (not 500)."
