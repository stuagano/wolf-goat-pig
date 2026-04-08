/**
 * Vercel Serverless Function — proxies Gemini API calls.
 *
 * Render's Oregon datacenter IPs are geo-blocked by Google's Gemini API.
 * This proxy runs on Vercel (whose IPs Google accepts) and forwards the
 * request unchanged. The Render backend calls this instead of Google directly.
 *
 * Protected by an optional shared secret in the x-proxy-secret header.
 */

const GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models";

export default async function handler(req, res) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  const secret = process.env.GEMINI_PROXY_SECRET;
  if (secret && req.headers["x-proxy-secret"] !== secret) {
    return res.status(403).json({ error: "Forbidden" });
  }

  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) {
    return res.status(500).json({ error: "GEMINI_API_KEY not configured" });
  }

  const { model, ...body } = req.body || {};
  if (!model) {
    return res.status(400).json({ error: "model field is required" });
  }

  const url = `${GEMINI_BASE}/${model}:generateContent?key=${apiKey}`;

  try {
    const resp = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    const data = await resp.json();
    return res.status(resp.status).json(data);
  } catch (err) {
    return res.status(502).json({ error: "Failed to reach Gemini API" });
  }
}
