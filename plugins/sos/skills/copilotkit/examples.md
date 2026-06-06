# CopilotKit known-good snippets (v1.59.x, Next.js App Router, Claude)

These are battle-tested from a real integration. Adjust model/imports to your installed version.

## Runtime route — `app/api/copilotkit/route.ts`
```ts
import {
  CopilotRuntime,
  AnthropicAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import Anthropic from "@anthropic-ai/sdk";
import { NextRequest } from "next/server";

const anthropic = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });
const serviceAdapter = new AnthropicAdapter({
  anthropic,
  model: "claude-sonnet-4-6", // use a model your key has; verify with a direct SDK call
});
const runtime = new CopilotRuntime();

export const POST = async (req: NextRequest) => {
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter,
    endpoint: "/api/copilotkit",
  });
  return handleRequest(req);
};
```

## Provider — `app/layout.tsx`
```tsx
import { CopilotKit } from "@copilotkit/react-core";
import "@copilotkit/react-ui/styles.css";   // BEFORE globals.css (CSS isolation)
import "./globals.css";
import { AppCopilot } from "@/components/AppCopilot";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <CopilotKit runtimeUrl="/api/copilotkit">
          {children}
          <AppCopilot />
        </CopilotKit>
      </body>
    </html>
  );
}
```

## Tools wired to YOUR backend — `components/AppCopilot.tsx`
```tsx
"use client";
import { useCopilotAction, useCopilotReadable } from "@copilotkit/react-core";
import { CopilotSidebar } from "@copilotkit/react-ui";
import { api } from "@/lib/api"; // your backend client

export function AppCopilot() {
  useCopilotAction({
    name: "doThing",
    description: "Clear description of WHEN to use this and what it returns.",
    parameters: [{ name: "input", type: "string", description: "...", required: true }],
    handler: async ({ input }) => {
      const r = await api.doThing(input);     // <- your real backend call
      return { summary: r.summary, ...r };     // returned to the LLM
    },
    // optional: stream a custom tool-activity card
    // render: ({ status, result }) => <ToolCard status={status} result={result} />,
  });

  useCopilotReadable({ description: "current app state", value: /* your state */ {} });

  return (
    <CopilotSidebar
      defaultOpen={false}
      labels={{ title: "Copilot", initial: "How can I help?" }}
      instructions="Use the actions to ground every answer in real data; never invent facts."
    />
  );
}
```

## Theming to your tokens — in `globals.css`
```css
.app-copilot {
  --copilot-kit-primary-color:            var(--accent);
  --copilot-kit-contrast-color:           var(--bg);
  --copilot-kit-background-color:         var(--surface);
  --copilot-kit-secondary-color:          var(--surface2);
  --copilot-kit-secondary-contrast-color: var(--text);
  --copilot-kit-separator-color:          var(--border);
  --copilot-kit-muted-color:              var(--muted);
}
```

## Verify (no browser needed)
```bash
pnpm typecheck
curl -s -o /dev/null -w "%{http_code}\n" -X POST localhost:3000/api/copilotkit -d '{}'   # expect 400, not 500
curl -s localhost:3000/ | grep -o copilotKitButton | head -1                              # sidebar mounted
```
```

## MCP-backed tools (CopilotKit runtime can consume MCP)
`@copilotkit/runtime` exports `MCPClient` — the runtime can call MCP servers, so the copilot's
tools can be backed by an MCP spine rather than (or alongside) `useCopilotAction`. Useful if you
already expose your engine over MCP.
