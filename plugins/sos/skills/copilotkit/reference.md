# CopilotKit integration — gotchas (learned the hard way)

Every one of these cost real debugging time. Check them up front.

## 1. Missing PostCSS config silently kills ALL styling (Tailwind v3 + Next)
Symptom: page renders but **completely unstyled** (raw inputs, default fonts) even though
`tailwind.config.*` exists and `@tailwind` directives are in `globals.css`. Cause: no
`postcss.config.*` and/or no `postcss`/`autoprefixer` installed → Next never runs Tailwind →
**zero utility classes generated**. (Plain CSS like `:root` vars still works, which is why the
dark background survives and masks the problem.)
Fix: `pnpm add -D postcss autoprefixer` + create `postcss.config.mjs`:
```js
export default { plugins: { tailwindcss: {}, autoprefixer: {} } };
```
This is unrelated to CopilotKit but surfaces while wiring it; check it first or you'll chase ghosts.

## 2. The runtime 500s until you install `openai` (even when using Claude)
Symptom: `POST /api/copilotkit` returns **500 instantly** (~30ms); log shows
`service-adapters/openai/openai-adapter.mjs ... could not be resolved`. Cause:
`@copilotkit/runtime`'s index **eagerly imports the OpenAI adapter**, which needs the `openai`
package — absent if you only installed the Anthropic SDK. Fix: `pnpm add openai`. (You don't use
it; it just has to resolve.)

## 3. `shiki` monorepo-hoist break (pnpm workspaces)
Symptom: dev log warns `Package shiki can't be external ... could not be resolved`. Cause:
`@copilotkit/react-ui` → `streamdown` → `shiki` gets hoisted to the workspace root and Next
can't externalize it from the app dir. Fix: `pnpm add shiki` directly in the app package.

## 4. v1 vs v2 API — they are different; match the installed version
Docs/blogs mix them. v2 uses `@copilotkit/react-core/v2`, `BuiltInAgent`, model strings like
`"anthropic:claude-sonnet-4-5"`. v1.59.x uses `@copilotkit/react-core` (no `/v2`),
`AnthropicAdapter`/`OpenAIAdapter`, hooks from `@copilotkit/react-core`, `CopilotSidebar` from
`@copilotkit/react-ui`. **Check `node_modules/@copilotkit/react-core/package.json` version and
match.** When unsure, grep the real `.d.ts` exports rather than trusting a tutorial.

## 5. Pick a model the account actually has, and don't assume Sonnet is faster
`AnthropicAdapter({ anthropic, model })` passes the model straight to the Anthropic SDK. A model
the key can't access → slow 500 (~2-3s, reaches the API then fails). Use a model you've confirmed
works. Surprise from real profiling: **Sonnet was ~1.4–1.9× SLOWER than Opus on one account** —
don't swap models for "speed" without measuring; latency varies by account/capacity.

## 6. CSS isolation / import order
Import `@copilotkit/react-ui/styles.css` **before** your app's `globals.css` so your utilities
win on conflict. Scope CopilotKit overrides under a wrapper class; never edit `node_modules`.

## 7. Theme via CSS variables or it's default-blue
Set these on the chat wrapper to match your design tokens:
`--copilot-kit-primary-color`, `--copilot-kit-contrast-color`, `--copilot-kit-background-color`,
`--copilot-kit-secondary-color`, `--copilot-kit-secondary-contrast-color`,
`--copilot-kit-separator-color`, `--copilot-kit-muted-color`.

## 8. The `api` self-reference TS trap (pattern, not CopilotKit-specific)
If your API client object references its own type (`Parameters<typeof api.foo>`), TS infers the
whole object as `any` (TS7022) and downstream `.map`/spread break. Extract a named payload type.

## 9. Verifying without a browser
Headless/automation browsers often crash on the post-fetch re-render of CopilotKit chats — don't
rely on them. Verify structurally instead: typecheck clean; empty `POST /api/copilotkit` → **400
not 500**; `curl / | grep copilotKitButton` shows the sidebar mounted; then a single real chat
message through a normal browser. A direct SDK call (`anthropic.messages.create`) confirms the
model+key path independent of CopilotKit.

## What each piece is (mental model)
- **Provider** (`<CopilotKit runtimeUrl>`) — connects the UI to the runtime.
- **Runtime route** (`/api/copilotkit`) — server endpoint that talks to the LLM (the adapter).
- **`useCopilotAction`** — a tool the copilot's LLM can call; its `handler` runs *your* code
  (wire it to your backend API client). `render` lets you draw custom tool-activity cards.
- **`useCopilotReadable`** — exposes app state to the copilot as context.
- **`CopilotSidebar`/`CopilotPopup`/`CopilotChat`** — the chat UI; `CopilotChat` can be the main
  column for an agent-first layout instead of a floating sidebar.
