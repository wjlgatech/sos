# nim-bridge

A single Vercel serverless function that gives **browser apps** CORS access to NVIDIA's
free NIM API (`integrate.api.nvidia.com` only allows CORS from `build.nvidia.com`).

- Forwards exactly one endpoint: `POST /api/chat` → NIM `/v1/chat/completions`.
- **Holds no key, stores nothing** — every caller sends their own free `nvapi-…` key
  (build.nvidia.com/models) in the `Authorization` header. Rate limits are per caller key.
- Used by the living-repo skill's "Ask" panel (e.g. the
  [awesome-auto-ai-research](https://wjlgatech.github.io/awesome-auto-ai-research/) map).

Deploy your own:

```bash
cd nim-bridge && vercel deploy --prod --yes
```

`.vercel/` (project linkage metadata) is intentionally not committed.
