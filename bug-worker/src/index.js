/**
 * birdquiz-bug-worker — receives "Flag photo" reports from the Bird Quiz and commits
 * one Markdown file per report to bugs/ in the GitHub repo.
 *
 * Route:  POST https://birds-api.sethhopper.com/report
 * Body:   flag: { photo: "img/northern-cardinal-2.jpg", reason }  |  bug: { text, context }  (+ pageUrl, userAgent, website)
 * Env:    GITHUB_TOKEN (secret, Contents read/write on REPO only), REPO, BRANCH, ALLOWED_ORIGINS
 */
const PHOTO_RE = /^(img|topics\/[a-z-]+\/img)\/[a-z0-9-]+\.jpg$/;   // only real photo paths are accepted
const MAX_REASON = 1000;

export default {
  async fetch(request, env) {
    const origin = request.headers.get("Origin") || "";
    const allowed = allowOrigin(origin, env);
    const h = {
      "Access-Control-Allow-Origin": allowed || "null",
      "Access-Control-Allow-Methods": "POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
      "Access-Control-Max-Age": "86400",
      "Vary": "Origin",
    };
    if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: h });
    if (request.method !== "POST") return reply({ error: "method_not_allowed" }, 405, h);
    if (new URL(request.url).pathname !== "/report") return reply({ error: "not_found" }, 404, h);
    if (!allowed) return reply({ error: "origin_not_allowed" }, 403, h);

    let body;
    try { body = await request.json(); } catch { return reply({ error: "bad_json" }, 400, h); }
    if (body.website) return reply({ ok: true }, 200, h);           // honeypot

    // Two kinds of report: a photo flag ({photo, reason}) or a general bug ({text, context}).
    const photo = String(body.photo || "");
    const isFlag = photo !== "";
    if (isFlag && !PHOTO_RE.test(photo)) return reply({ error: "bad_photo" }, 400, h);
    const reason = String((isFlag ? body.reason : body.text) || "").trim().slice(0, MAX_REASON);
    if (!isFlag && reason.length < 3) return reply({ error: "empty_report" }, 400, h);
    const text = reason || "(no reason given)";

    const now = new Date();
    const stamp = now.toISOString().replace(/:/g, "-").replace(/\.\d+Z$/, "Z");
    const path = `bugs/${stamp}_${Math.random().toString(36).slice(2, 8)}.md`;
    const front = {
      kind: isFlag ? "flag" : "bug",
      ...(isFlag ? { photo } : { context: clip(body.context, 600) }),
      submitted: now.toISOString(), status: "open",
      page_url: clip(body.pageUrl, 300), user_agent: clip(body.userAgent, 300),
    };
    const md = "---\n" + Object.entries(front).map(([k, v]) => `${k}: ${JSON.stringify(v)}`).join("\n")
      + "\n---\n\n" + text + "\n";

    const gh = await fetch(`https://api.github.com/repos/${env.REPO}/contents/${path}`, {
      method: "PUT",
      headers: {
        "Authorization": `Bearer ${env.GITHUB_TOKEN}`,
        "Accept": "application/vnd.github+json",
        "User-Agent": "birdquiz-bug-worker",
        "X-GitHub-Api-Version": "2022-11-28",
      },
      body: JSON.stringify({ message: `${isFlag ? "flag: " + photo : "bug"} — ${text.replace(/\s+/g, " ").slice(0, 50)}`,
                             content: b64(md), branch: env.BRANCH || "main" }),
    });
    if (!gh.ok) return reply({ error: "commit_failed", status: gh.status,
                               detail: (await gh.text()).slice(0, 300) }, 502, h);
    return reply({ ok: true, path }, 200, h);
  },
};

function allowOrigin(origin, env) {
  const list = String(env.ALLOWED_ORIGINS || "").split(",").map(s => s.trim()).filter(Boolean);
  return list.includes(origin) ? origin : "";
}
function clip(v, n) { return String(v == null ? "" : v).slice(0, n); }
function b64(s) {
  let bin = ""; for (const b of new TextEncoder().encode(s)) bin += String.fromCharCode(b);
  return btoa(bin);
}
function reply(obj, status, headers) {
  return new Response(JSON.stringify(obj), { status, headers: { ...headers, "Content-Type": "application/json" } });
}
