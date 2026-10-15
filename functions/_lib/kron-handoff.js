// Kron 跨站登录：kronenglish 是唯一的登录入口。Aha / Quiz / Class / Word 没登录或没开通，就跳到 kronenglish 登录。
//
// 同一份文件放在每个产品里，内容必须一致（和 kron-account.js 放在同一个目录）：
//   kronenglish  worker/kron-handoff.js            （源头，改动先改这里）
//   其他产品      functions/_lib/kron-handoff.js
//
// 各产品是不同的 *.pages.dev 网址，cookie 不能互通。所以：
//   1. 产品门禁跳到 kronenglish 的 /api/auth/handoff?site=aha&next=/原页面
//   2. kronenglish 没登录 → /login/；登录了但激活码不含这个产品 → /login/?need=aha（换一个含它的激活码登录）
//   3. 登录且已开通 → 在共用的 sessions 表里开一个 2 分钟的一次性通行证，带着它跳回产品的 /api/auth/handoff
//   4. 产品用掉通行证（只能用一次），换成本站 30 天的会话 cookie，回到原页面

import { access, authenticate, createSession, sessionCookie, sha256 } from "./kron-account.js";

export const KRON_LOGIN_ORIGIN = "https://kronenglish.pages.dev";
export const KRON_SITES = {
  aha: "https://kronaha.pages.dev",
  quiz: "https://kronquiz.pages.dev",
  class: "https://kronclass.pages.dev",
  word: "https://kronword.pages.dev"
};
export const HANDOFF_PATH = "/api/auth/handoff";
const PASS_SECONDS = 120;
const SITE_SESSION_SECONDS = 30 * 86400;
const IDLE_SECONDS = 14 * 86400;

// 只接受本站路径，挡住 //evil.com 这类跳转
const safePath = value => (typeof value === "string" && /^\/(?![\/\\])/.test(value) && value.length <= 2000 ? value : "/");
function redirect(location, headers = {}) {
  return new Response(null, { status: 302, headers: { Location: location, "Cache-Control": "no-store", "Referrer-Policy": "no-referrer", ...headers } });
}

/** 产品门禁要跳去的地址 */
export function kronLoginUrl(site, next) {
  const to = new URL(HANDOFF_PATH, KRON_LOGIN_ORIGIN);
  to.searchParams.set("site", site);
  to.searchParams.set("next", safePath(next));
  return to.toString();
}

/** kronenglish：GET /api/auth/handoff?site=aha&next=/path。auth 是 kronenglish 当前登录的账号（没登录为 null）。 */
export async function issueHandoff(request, env, auth, now = Date.now()) {
  const url = new URL(request.url);
  const site = url.searchParams.get("site");
  const origin = Object.hasOwn(KRON_SITES, site) ? KRON_SITES[site] : null;
  if (!origin) return new Response("Unknown site", { status: 400, headers: { "Cache-Control": "no-store" } });
  const next = safePath(url.searchParams.get("next"));
  const back = `${HANDOFF_PATH}?site=${encodeURIComponent(site)}&next=${encodeURIComponent(next)}`;
  if (!auth) return redirect(`/login/?redirect=${encodeURIComponent(back)}`);
  if (!(await access(env.DB, auth, site, now)).ok) return redirect(`/login/?need=${encodeURIComponent(site)}&redirect=${encodeURIComponent(back)}`);
  const pass = await createSession(env.DB, auth.userId, { maxAgeSeconds: PASS_SECONDS, now });
  const to = new URL(HANDOFF_PATH, origin);
  to.searchParams.set("pass", pass.rawToken);
  to.searchParams.set("next", next);
  return redirect(to.toString());
}

/** 产品：GET /api/auth/handoff?pass=…&next=/path。db 是共用账号库（kronenglish-production）。 */
export async function acceptHandoff(request, env, { site, db = env.DB, now = Date.now() }) {
  const url = new URL(request.url);
  const pass = url.searchParams.get("pass") || "";
  const next = safePath(url.searchParams.get("next"));
  if (!pass || pass.length > 256) return redirect(kronLoginUrl(site, next));
  const t = new Date(now).toISOString();
  // 只有第一次能用：撤销成功（之前没撤销、没过期）才算数
  const used = await db.prepare("UPDATE sessions SET revoked_at = ?1 WHERE token_hash = ?2 AND revoked_at IS NULL AND expires_at > ?1 RETURNING user_id")
    .bind(t, await sha256(pass)).first();
  if (!used) return redirect(kronLoginUrl(site, next));
  const s = await createSession(db, used.user_id, { userAgent: request.headers.get("User-Agent"), auditSecret: env.AUDIT_HASH_KEY, maxAgeSeconds: SITE_SESSION_SECONDS, now });
  return redirect(next, { "Set-Cookie": sessionCookie(s.rawToken, SITE_SESSION_SECONDS) });
}

/**
 * 产品门禁。返回 null 表示放行。
 * 页面：没登录或激活码不含本产品 → 跳 kronenglish 登录。其他资源（音频、图片、数据）：401 / 403。
 */
export async function siteGate(request, env, { site, db = env.DB, ctx, now = Date.now() }) {
  const auth = await authenticate(db, request, { idleSeconds: IDLE_SECONDS, ctx, now });
  if (auth && (await access(db, auth, site, now)).ok) return null;
  const url = new URL(request.url);
  const isPage = request.method === "GET" && (request.headers.get("Accept") || "").includes("text/html");
  if (isPage) return redirect(kronLoginUrl(site, url.pathname + url.search));
  return new Response(auth ? "还没有开通这个产品" : "请先登录", { status: auth ? 403 : 401, headers: { "Content-Type": "text/plain; charset=utf-8", "Cache-Control": "no-store" } });
}

/** 放行后的响应：页面不进共享缓存（门禁才能每次生效），其他资源允许本机缓存一天 */
export function privateCache(request, response) {
  const out = new Response(response.body, response);
  const isPage = (request.headers.get("Accept") || "").includes("text/html");
  out.headers.set("Cache-Control", isPage ? "private, no-store" : "private, max-age=86400");
  return out;
}
