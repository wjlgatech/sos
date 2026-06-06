---
name: copilotkit
description: Integrate CopilotKit (in-app AI copilot UI) into a React/Next.js app — provider + runtime API route + useCopilotAction/useCopilotReadable wiring, themed to the app, with the version/bundling gotchas pre-solved. Use when adding an in-app copilot, chat sidebar, or agentic UI to a web app.
allowed-tools: Read, Grep, Glob, Edit, Write, Bash(npm *), Bash(pnpm *), Bash(node *)
---

# Skill: Integrate CopilotKit into a web app

CopilotKit (https://github.com/CopilotKit/CopilotKit) embeds an AI copilot **inside** a
React/Next.js app: a **provider**, a **runtime API route** that talks to an LLM, and
**`useCopilotAction`** tools the copilot can call (which you wire to *your* backend). Done
right it makes the app agentic — users drive features by conversation.

This skill captures a *known-good* integration plus the gotchas that cost hours. Read
`reference.md` for the full gotcha list and `examples.md` for copy-paste snippets.

## When to use
Adding an in-app copilot / chat sidebar / agentic UI to a Next.js (App Router) app, or
wiring an existing backend's capabilities to a conversational surface.

## Procedure

1. **Confirm the stack.** Next.js App Router + React 18/19. Check Tailwind actually
   compiles first — see gotcha #1 (a missing `postcss.config` silently kills all styling).

2. **Install.** `pnpm add @copilotkit/react-core @copilotkit/react-ui @copilotkit/runtime`
   Then **also** `pnpm add openai shiki` and ensure `@anthropic-ai/sdk@^0.57` if using Claude
   (see gotchas #2, #3, #4 — these are non-obvious and cause 500s / broken markdown).

3. **Check the installed major version.** `cat node_modules/@copilotkit/react-core/package.json | grep version`.
   **v1.x and v2.x have different APIs** (import paths, adapter vs `BuiltInAgent`). Match the
   examples to the installed version — do NOT trust a blog/doc that targets the other major.
   Inspect real exports if unsure: `grep -rhoE "AnthropicAdapter|BuiltInAgent|CopilotKit" node_modules/@copilotkit/runtime/dist/*.d.*`.

4. **Runtime route** at `app/api/copilotkit/route.ts` (LLM lives here). For Claude use
   `AnthropicAdapter` (v1) — see `examples.md`. Put the API key in `.env.local` (server-side).

5. **Provider** in `app/layout.tsx`: wrap children in `<CopilotKit runtimeUrl="/api/copilotkit">`
   and import the UI stylesheet **before** your `globals.css` (gotcha #6 — CSS isolation).

6. **Tools + state.** In a `"use client"` component, register `useCopilotAction` for each
   capability (wire its `handler` to your backend API client) and `useCopilotReadable` to
   expose app state. Render `<CopilotSidebar>` (or `<CopilotChat>` as the main column for an
   agent-first UI). See `examples.md`.

7. **Theme it** to the app's design tokens via the `--copilot-kit-*` CSS variables, scoped to
   a wrapper class — otherwise it renders default-blue (gotcha #7).

8. **Verify** without the flaky path: typecheck; `curl -X POST /api/copilotkit -d '{}'` should
   return **400, not 500** (500 = a bundling/model error — see gotchas). Confirm the sidebar
   DOM renders (`copilotKitButton` classes in the HTML). Then have the model answer one message.

## Hard rule
Run `scripts/scaffold.sh <app-dir>` to do steps 2–5 mechanically, or follow them by hand.
Always verify the runtime route returns 400 (not 500) on an empty POST before claiming it works.
