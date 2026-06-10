// nim-bridge — CORS bridge to NVIDIA's free NIM API for browser apps.
//
// integrate.api.nvidia.com only allows CORS from build.nvidia.com, so static webapps
// (e.g. GitHub Pages) can't call it directly. This function forwards ONE endpoint —
// POST /v1/chat/completions — adding permissive CORS. It holds NO key and stores
// NOTHING: every caller must send their own free key (build.nvidia.com/models) in the
// Authorization header, so the bridge has nothing to abuse and nothing to leak.

const UPSTREAM = "https://integrate.api.nvidia.com/v1/chat/completions";

export default async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Authorization, Content-Type");
  res.setHeader("Access-Control-Max-Age", "86400");
  if (req.method === "OPTIONS") return res.status(204).end();
  if (req.method !== "POST") return res.status(405).json({ error: "POST only" });

  const auth = req.headers.authorization || "";
  if (!auth.startsWith("Bearer nvapi-")) {
    return res.status(401).json({
      error:
        "Send your own free NVIDIA key: 'Authorization: Bearer nvapi-…' — get one at build.nvidia.com/models",
    });
  }

  try {
    const upstream = await fetch(UPSTREAM, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: auth },
      body: JSON.stringify(req.body || {}),
    });
    const text = await upstream.text();
    res
      .status(upstream.status)
      .setHeader("Content-Type", upstream.headers.get("content-type") || "application/json")
      .send(text);
  } catch (e) {
    res.status(502).json({ error: `upstream unreachable: ${String(e).slice(0, 200)}` });
  }
}
