// Kron 账号：手机号 + 激活码登录，所有 Kron 产品共用一个账号库（kronenglish 的 D1）。
//
// 同一份文件放在每个接入的产品里，内容必须一致：
//   kronenglish        worker/kron-account.js        （源头，改动先改这里）
//   kron-english-aha   functions/_lib/kron-account.js
//   其他产品            照 docs/kron-account.md 接入
// 只用 Web 标准 API（crypto.subtle、TextEncoder）和 D1，Cloudflare Workers / Pages Functions / Node 18+ 都能跑。
//
// 数据表见 kronenglish/migrations/0007_activation_codes.sql：
//   users.phone               手机号（激活码登录自动建的账号，username 就是手机号）
//   activation_codes          激活码：解锁哪些产品（products）、有效天数、绑定的账号、到期时间
//   sessions                  和用户名密码登录共用的会话表
//   login_failure_windows     和用户名密码登录共用的失败计数表
//   entitlements              会员时段（邀请奖励等，见 0008_invites.sql），权限和激活码取并集

export const SESSION_COOKIE = "__Host-ke_session";
const DAY_MS = 86_400_000;
const enc = new TextEncoder();

// ---------- 小工具 ----------
const b64url = bytes => {
  let s = "";
  for (const b of bytes) s += String.fromCharCode(b);
  return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
};
export const randomToken = (n = 32) => b64url(crypto.getRandomValues(new Uint8Array(n)));
export async function sha256(value) {
  return b64url(new Uint8Array(await crypto.subtle.digest("SHA-256", enc.encode(value))));
}
export async function hmac(value, secret) {
  const key = await crypto.subtle.importKey("raw", enc.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  return b64url(new Uint8Array(await crypto.subtle.sign("HMAC", key, enc.encode(value))));
}
export function constantTimeEqual(a, b) {
  const x = enc.encode(String(a)), y = enc.encode(String(b));
  let diff = x.length ^ y.length;
  for (let i = 0; i < Math.max(x.length, y.length); i++) diff |= (x[i] || 0) ^ (y[i] || 0);
  return diff === 0;
}
const iso = ms => new Date(ms).toISOString();

export function json(data, status = 200, headers = {}) {
  return new Response(JSON.stringify(data), { status, headers: { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store", ...headers } });
}

// ---------- 格式 ----------
// 去掉容易看混的 0/O、1/I/L，学生抄写不出错
const ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ";

/** 新激活码：XXXX-XXXX-XXXX，约 59 bit 随机 */
export function newCode() {
  let s = "";
  while (s.length < 14) {
    for (const b of crypto.getRandomValues(new Uint8Array(16))) {
      if (b >= 248 || s.length >= 14) continue; // 248 = 31 × 8，丢掉尾数避免取模偏差
      s += ALPHABET[b % ALPHABET.length];
      if (s.length === 4 || s.length === 9) s += "-";
    }
  }
  return s;
}

/** 学生输入的激活码：忽略大小写、空格、横线 */
export function normalizeCode(input) {
  const raw = String(input || "").toUpperCase().replace(/[^0-9A-Z]/g, "");
  return raw.length === 12 ? `${raw.slice(0, 4)}-${raw.slice(4, 8)}-${raw.slice(8)}` : null;
}

/** 中国大陆手机号，可带 +86 / 0086 / 空格 / 横线 */
export function normalizePhone(input) {
  let s = String(input || "").replace(/[\s-]/g, "");
  if (s.startsWith("+86")) s = s.slice(3);
  else if (s.startsWith("0086")) s = s.slice(4);
  return /^1[3-9]\d{9}$/.test(s) ? s : null;
}
export const maskPhone = p => (p ? `${p.slice(0, 3)}****${p.slice(7)}` : "");

/**
 * 激活码解锁的产品，逗号分隔：
 *   aha / quiz / class / english …   整个产品
 *   english:think-l4                 产品里的一本书
 *   *                                全部
 */
const PRODUCT = /^(\*|[a-z][a-z0-9-]{0,23}(:[a-z0-9-]{1,40})?)$/;
export function parseProducts(input) {
  const list = (Array.isArray(input) ? input : String(input || "").split(","))
    .map(s => String(s).trim().toLowerCase()).filter(Boolean);
  if (!list.length || list.some(p => !PRODUCT.test(p))) return null;
  return [...new Set(list)];
}

/** 一组权限里有没有某个产品（或产品里的某本书） */
export function covers(products, want) {
  const [app] = want.split(":");
  return products.includes("*") || products.includes(want) || products.includes(app);
}

// ---------- 激活码登录 ----------
const userColumns = "u.id, u.username, u.display_name, u.role, u.phone, u.is_active";

export async function getUserByPhone(db, phone) {
  return db.prepare(`SELECT ${userColumns} FROM users u WHERE u.phone = ?1 LIMIT 1`).bind(phone).first();
}

export async function createPhoneUser(db, phone, now) {
  const id = crypto.randomUUID();
  const t = iso(now);
  // 激活码账号没有密码：password_* 留空，credential_digest 为 NULL，用户名密码登录永远对不上
  await db.prepare(
    "INSERT INTO users (id, username, display_name, role, password_hash, password_salt, password_iterations, must_change_password, is_active, created_at, updated_at, phone) VALUES (?1, ?2, ?3, 'student', '', '', 0, 0, 1, ?4, ?4, ?2)"
  ).bind(id, phone, maskPhone(phone), t).run();
  return getUserByPhone(db, phone);
}

/**
 * 手机号 + 激活码登录。
 * 激活码第一次使用：这个手机号没有账号就自动建一个，激活码绑定到这个账号，有效期从这一刻算。
 * 之后：同一个手机号 + 同一个激活码在任何设备、任何 Kron 产品都能登录；别的手机号用不了。
 * 一个账号可以绑定多个激活码（续费、加购别的产品），权限取所有有效激活码的并集。
 */
export async function codeLogin(db, phoneInput, codeInput, now = Date.now()) {
  const phone = normalizePhone(phoneInput);
  if (!phone) return { ok: false, status: 400, error: "请输入 11 位手机号" };
  const code = normalizeCode(codeInput);
  if (!code) return { ok: false, status: 400, error: "激活码是 12 位字母和数字" };

  let row = await db.prepare("SELECT * FROM activation_codes WHERE code = ?1 LIMIT 1").bind(code).first();
  if (!row) return { ok: false, status: 401, error: "激活码不对，请检查是否输错", fail: true };
  if (row.disabled_at) return { ok: false, status: 403, error: "这个激活码已停用，请联系老师" };

  let user;
  if (!row.user_id) {
    user = (await getUserByPhone(db, phone)) || (await createPhoneUser(db, phone, now));
    if (!user?.is_active) return { ok: false, status: 403, error: "这个账号已停用，请联系老师" };
    const expires = row.days > 0 ? iso(now + row.days * DAY_MS) : null;
    // 只在还没绑定时绑定，两个人同时抢一个码只有一个成功
    await db.prepare("UPDATE activation_codes SET user_id = ?1, activated_at = ?2, expires_at = ?3 WHERE code = ?4 AND user_id IS NULL")
      .bind(user.id, iso(now), expires, code).run();
    row = await db.prepare("SELECT * FROM activation_codes WHERE code = ?1 LIMIT 1").bind(code).first();
  }
  if (!user || row.user_id !== user.id) {
    user = await db.prepare(`SELECT ${userColumns} FROM users u WHERE u.id = ?1 LIMIT 1`).bind(row.user_id).first();
    if (!user || user.phone !== phone) return { ok: false, status: 403, error: "这个激活码已绑定其他手机号", fail: true };
  }
  if (!user.is_active) return { ok: false, status: 403, error: "这个账号已停用，请联系老师" };
  if (row.expires_at && Date.parse(row.expires_at) <= now) return { ok: false, status: 403, error: "激活码已过期，请联系老师续期" };
  return { ok: true, user, code: row };
}

/** 账号当前有效的激活码（没停用、没过期） */
export async function activeCodes(db, userId, now = Date.now()) {
  const { results } = await db.prepare(
    "SELECT code, products, expires_at FROM activation_codes WHERE user_id = ?1 AND disabled_at IS NULL AND (expires_at IS NULL OR expires_at > ?2)"
  ).bind(userId, iso(now)).all();
  return (results || []).map(r => ({ code: r.code, products: r.products.split(","), expiresAt: r.expires_at }));
}

/** 账号还没结束的会员时段（entitlements：邀请奖励、活动赠送……），按开始时间排；顺延的时段可能还没开始 */
export async function activeEntitlements(db, userId, now = Date.now()) {
  const { results } = await db.prepare(
    "SELECT products, starts_at, ends_at FROM entitlements WHERE user_id = ?1 AND revoked_at IS NULL AND ends_at > ?2 ORDER BY starts_at"
  ).bind(userId, iso(now)).all();
  return (results || []).map(r => ({ products: r.products.split(","), startsAt: r.starts_at, endsAt: r.ends_at }));
}

/** 账号此刻能用的全部产品：有效激活码 + 正在生效的会员时段 */
export async function activeProducts(db, userId, now = Date.now()) {
  const codes = (await activeCodes(db, userId, now)).flatMap(c => c.products);
  const ents = (await activeEntitlements(db, userId, now)).filter(e => Date.parse(e.startsAt) <= now).flatMap(e => e.products);
  return [...new Set([...codes, ...ents])];
}

/**
 * 账号对某个产品的权限：{ ok, expiresAt }。
 * owner（老师）和 kron 账号永远有权限；其余看有效激活码和会员时段。
 * expiresAt：激活码最晚到期日，再接上首尾相连的会员时段（顺延的邀请奖励）之后的结束时间；null = 永久。
 */
export async function access(db, auth, product, now = Date.now()) {
  if (!auth) return { ok: false };
  if (auth.role === "owner" || auth.username === "kron") return { ok: true, expiresAt: null, owner: true };
  const hits = (await activeCodes(db, auth.userId, now)).filter(c => covers(c.products, product));
  if (hits.some(c => !c.expiresAt)) return { ok: true, expiresAt: null };
  let until = hits.length ? Math.max(...hits.map(c => Date.parse(c.expiresAt))) : now;
  for (const e of await activeEntitlements(db, auth.userId, now)) {
    if (covers(e.products, product) && Date.parse(e.startsAt) <= until && Date.parse(e.endsAt) > until) until = Date.parse(e.endsAt);
  }
  return until > now ? { ok: true, expiresAt: iso(until) } : { ok: false };
}

// ---------- 会话（和 kronenglish 用户名密码登录同一张 sessions 表） ----------
export function readCookie(request, name = SESSION_COOKIE) {
  for (const part of (request.headers.get("Cookie") || "").split(";")) {
    const [k, ...v] = part.trim().split("=");
    if (k === name) return v.join("=");
  }
  return null;
}
export const sessionCookie = (token, maxAgeSeconds) => `${SESSION_COOKIE}=${token}; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=${maxAgeSeconds}`;
export const clearSessionCookie = () => `${SESSION_COOKIE}=; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=0`;

export async function createSession(db, userId, { userAgent, auditSecret, maxAgeSeconds, now = Date.now() }) {
  const rawToken = randomToken(32), csrfToken = randomToken(32);
  const uaHash = userAgent && auditSecret ? await hmac(userAgent, auditSecret) : null;
  await db.prepare("INSERT INTO sessions (token_hash, user_id, csrf_token, created_at, last_seen_at, expires_at, user_agent_hash) VALUES (?1, ?2, ?3, ?4, ?4, ?5, ?6)")
    .bind(await sha256(rawToken), userId, csrfToken, iso(now), iso(now + maxAgeSeconds * 1000), uaHash).run();
  return { rawToken, csrfToken };
}

/** 读会话：{ userId, username, displayName, role, phone, csrfToken, tokenHash } 或 null */
export async function authenticate(db, request, { idleSeconds, ctx, now = Date.now() } = {}) {
  const raw = readCookie(request);
  if (!raw || raw.length > 256) return null;
  const tokenHash = await sha256(raw);
  const row = await db.prepare("SELECT s.*, u.username, u.display_name, u.role, u.phone, u.is_active FROM sessions s JOIN users u ON u.id = s.user_id WHERE s.token_hash = ?1 LIMIT 1").bind(tokenHash).first();
  if (!row || row.revoked_at || !row.is_active || Date.parse(row.expires_at) <= now) return null;
  const idle = now - Date.parse(row.last_seen_at);
  if (idleSeconds && idle > idleSeconds * 1000) return null;
  if (idle > 5 * 60 * 1000) {
    const touch = db.prepare("UPDATE sessions SET last_seen_at = ?1 WHERE token_hash = ?2").bind(iso(now), tokenHash).run();
    if (ctx?.waitUntil) ctx.waitUntil(touch); else await touch;
  }
  return { tokenHash, userId: row.user_id, csrfToken: row.csrf_token, username: row.username, displayName: row.display_name, role: row.role, phone: row.phone };
}

export async function revokeSession(db, tokenHash) {
  await db.prepare("UPDATE sessions SET revoked_at = ?1 WHERE token_hash = ?2 AND revoked_at IS NULL").bind(iso(Date.now()), tokenHash).run();
}

// ---------- 防暴力尝试：同一网络 15 分钟内输错 20 次就先停 ----------
export const FAIL_WINDOW_S = 15 * 60, FAIL_LIMIT = 20;
export const ipOf = request => request.headers.get("CF-Connecting-IP") || "unknown";
export async function ipKey(request, env, scope = "code-login") {
  return env.AUDIT_HASH_KEY ? hmac(`${scope}:${ipOf(request)}`, env.AUDIT_HASH_KEY) : sha256(`${scope}:${ipOf(request)}`);
}
export async function failures(db, key, now, scope = "code-network") {
  const r = await db.prepare("SELECT window_started_at, failure_count FROM login_failure_windows WHERE scope = ?2 AND key_hash = ?1").bind(key, scope).first();
  return r && now / 1000 - r.window_started_at < FAIL_WINDOW_S ? r.failure_count : 0;
}
export async function recordFailure(db, key, now, scope = "code-network") {
  const s = Math.floor(now / 1000);
  const r = await db.prepare("SELECT window_started_at, failure_count FROM login_failure_windows WHERE scope = ?2 AND key_hash = ?1").bind(key, scope).first();
  const inWin = r && s - r.window_started_at < FAIL_WINDOW_S;
  await db.prepare("INSERT INTO login_failure_windows (scope, key_hash, window_started_at, failure_count) VALUES (?4, ?1, ?2, ?3) ON CONFLICT(scope, key_hash) DO UPDATE SET window_started_at = excluded.window_started_at, failure_count = excluded.failure_count")
    .bind(key, inWin ? r.window_started_at : s, inWin ? r.failure_count + 1 : 1, scope).run();
}

/** 写操作只接受同源的 JSON 请求（防 CSRF） */
export function sameOriginJson(request) {
  const origin = request.headers.get("Origin");
  if (!origin || origin !== new URL(request.url).origin) return json({ error: "Forbidden" }, 403);
  if ((request.headers.get("Content-Type") || "").split(";")[0].trim().toLowerCase() !== "application/json") return json({ error: "Unsupported media type" }, 415);
  return null;
}
export async function readJson(request, max = 4096) {
  const text = await request.text();
  if (enc.encode(text).byteLength > max) return null;
  try { return JSON.parse(text); } catch { return null; }
}

// ---------- 产品接入：一个函数接住 /api/auth/code-login、/api/auth/me、/api/auth/logout ----------
/**
 * product：本产品在激活码里的名字（aha / quiz / class …）。
 * 登录要求激活码覆盖本产品；kronenglish 自己有 me / logout，只用 code-login（product 传 null 表示不检查产品）。
 * 返回 Response，路径不归这里管时返回 null。
 */
export async function handleAuthRoutes(request, env, { product, maxAgeSeconds = 30 * 86400, idleSeconds = 14 * 86400, ctx, now = Date.now() }) {
  const db = env.DB;
  const path = new URL(request.url).pathname.replace(/\/+$/, "");

  if (path === "/api/auth/code-login" && request.method === "POST") {
    const bad = sameOriginJson(request); if (bad) return bad;
    const key = await ipKey(request, env);
    if ((await failures(db, key, now)) >= FAIL_LIMIT) return json({ error: "尝试次数太多，请 15 分钟后再试" }, 429, { "Retry-After": "900" });
    const body = await readJson(request);
    const r = await codeLogin(db, body?.phone, body?.code, now);
    if (!r.ok) { if (r.fail) await recordFailure(db, key, now); return json({ error: r.error }, r.status); }
    const auth = { userId: r.user.id, username: r.user.username, role: r.user.role };
    if (product && !covers(r.code.products.split(","), product) && !(await access(db, auth, product, now)).ok) {
      return json({ error: "这个激活码不包含本课程，请联系老师" }, 403);
    }
    const s = await createSession(db, r.user.id, { userAgent: request.headers.get("User-Agent"), auditSecret: env.AUDIT_HASH_KEY, maxAgeSeconds, now });
    return json({ user: publicUser(r.user), csrfToken: s.csrfToken }, 200, { "Set-Cookie": sessionCookie(s.rawToken, maxAgeSeconds) });
  }

  if (path === "/api/auth/me" && request.method === "GET") {
    const auth = await authenticate(db, request, { idleSeconds, ctx, now });
    if (!auth) return json({ authenticated: false, user: null });
    const a = product ? await access(db, auth, product, now) : { ok: true, expiresAt: null };
    return json({ authenticated: true, user: publicUser({ username: auth.username, display_name: auth.displayName, role: auth.role, phone: auth.phone }), access: a.ok, expiresAt: a.expiresAt ?? null, csrfToken: auth.csrfToken });
  }

  if (path === "/api/auth/logout" && request.method === "POST") {
    const bad = sameOriginJson(request); if (bad) return bad;
    const auth = await authenticate(db, request, { now });
    if (auth) {
      if (!constantTimeEqual(request.headers.get("X-CSRF-Token") || "", auth.csrfToken)) return json({ error: "Forbidden" }, 403);
      await revokeSession(db, auth.tokenHash);
    }
    return json({ ok: true }, 200, { "Set-Cookie": clearSessionCookie() });
  }
  return null;
}

export function publicUser(u) {
  return { username: u.phone ? maskPhone(u.phone) : u.username, displayName: u.phone ? maskPhone(u.phone) : u.display_name, role: u.role, phone: u.phone ? maskPhone(u.phone) : null };
}

/**
 * 课程门禁。返回 null 表示放行；否则返回要回给浏览器的 Response。
 * 页面：没登录跳 loginPath?next=原地址；登录了但激活码不含本产品，跳 loginPath?need=product。
 * 其他资源（音频等）：401 / 403。
 */
export async function gate(request, env, { product, loginPath = "/login/", idleSeconds = 14 * 86400, ctx, now = Date.now() }) {
  const url = new URL(request.url);
  const isPage = request.method === "GET" && (request.headers.get("Accept") || "").includes("text/html");
  const auth = await authenticate(env.DB, request, { idleSeconds, ctx, now });
  const a = auth ? await access(env.DB, auth, product, now) : { ok: false };
  if (a.ok) return null;
  if (isPage) {
    const to = new URL(loginPath, url);
    to.searchParams.set("next", url.pathname + url.search);
    if (auth) to.searchParams.set("need", product);
    return Response.redirect(to.toString(), 302);
  }
  return new Response(auth ? "没有这门课的权限" : "请先登录", { status: auth ? 403 : 401, headers: { "Content-Type": "text/plain; charset=utf-8", "Cache-Control": "no-store" } });
}

// ---------- 激活码管理（只在 kronenglish 开放，要求 owner 登录） ----------
const codeRow = r => {
  const now = Date.now();
  const status = r.disabled_at ? "disabled" : !r.user_id ? "unused" : r.expires_at && Date.parse(r.expires_at) <= now ? "expired" : "active";
  return { code: r.code, products: r.products.split(","), days: r.days, note: r.note || "", createdAt: r.created_at, phone: r.phone || null, activatedAt: r.activated_at, expiresAt: r.expires_at, disabled: !!r.disabled_at, status };
};

export async function generateCodes(db, { count, days, products, note }, createdBy, now = Date.now()) {
  const n = Math.floor(Number(count)), d = Math.floor(Number(days));
  const list = parseProducts(products);
  if (!(n >= 1 && n <= 500)) throw new Error("一次生成 1~500 个");
  if (!(d >= 0 && d <= 3650)) throw new Error("有效天数 0~3650（0 = 永久）");
  if (!list) throw new Error("请选择激活码解锁的产品");
  const out = [];
  while (out.length < n) {
    const code = newCode();
    const r = await db.prepare("INSERT OR IGNORE INTO activation_codes (code, products, days, note, created_at, created_by) VALUES (?1, ?2, ?3, ?4, ?5, ?6)")
      .bind(code, list.join(","), d, String(note || "").slice(0, 200), iso(now), createdBy || null).run();
    if (r.meta?.changes === 0) continue;
    out.push(codeRow({ code, products: list.join(","), days: d, note, created_at: iso(now) }));
  }
  return out;
}

export async function listCodes(db) {
  const { results } = await db.prepare("SELECT c.*, u.phone FROM activation_codes c LEFT JOIN users u ON u.id = c.user_id ORDER BY c.created_at DESC, c.code").all();
  return (results || []).map(codeRow);
}

/**
 * disable 停用（正在用的学生下次打开课程就被拦）/ enable 恢复 /
 * unbind 解绑（学生换手机号时用，回到未使用，有效期重算）/ extend 延长 days 天
 */
export async function updateCode(db, codeInput, action, { days } = {}, now = Date.now()) {
  const code = normalizeCode(codeInput);
  const row = code && (await db.prepare("SELECT * FROM activation_codes WHERE code = ?1").bind(code).first());
  if (!row) throw new Error("激活码不存在");
  if (action === "disable") await db.prepare("UPDATE activation_codes SET disabled_at = ?1 WHERE code = ?2").bind(iso(now), code).run();
  else if (action === "enable") await db.prepare("UPDATE activation_codes SET disabled_at = NULL WHERE code = ?1").bind(code).run();
  else if (action === "unbind") await db.prepare("UPDATE activation_codes SET user_id = NULL, activated_at = NULL, expires_at = NULL WHERE code = ?1").bind(code).run();
  else if (action === "extend") {
    const d = Math.floor(Number(days));
    if (!(d >= 1 && d <= 3650)) throw new Error("延长天数 1~3650");
    if (row.user_id && row.expires_at) await db.prepare("UPDATE activation_codes SET expires_at = ?1 WHERE code = ?2").bind(iso(Math.max(Date.parse(row.expires_at), now) + d * DAY_MS), code).run();
    else if (!row.user_id && row.days > 0) await db.prepare("UPDATE activation_codes SET days = days + ?1 WHERE code = ?2").bind(d, code).run();
  } else throw new Error("未知操作");
  const r = await db.prepare("SELECT c.*, u.phone FROM activation_codes c LEFT JOIN users u ON u.id = c.user_id WHERE c.code = ?1").bind(code).first();
  return codeRow(r);
}

/** GET/POST /api/admin/codes：auth 是已登录的会话，只有 owner 能用 */
export async function handleAdminCodes(request, env, auth) {
  if (!auth || !(auth.role === "owner" || auth.username === "kron")) return json({ error: "只有老师账号能管理激活码" }, 403);
  try {
    if (request.method === "GET") return json({ codes: await listCodes(env.DB) });
    if (request.method !== "POST") return json({ error: "Method not allowed" }, 405);
    const bad = sameOriginJson(request); if (bad) return bad;
    if (!constantTimeEqual(request.headers.get("X-CSRF-Token") || "", auth.csrfToken)) return json({ error: "Forbidden" }, 403);
    const body = await readJson(request, 8192);
    if (!body) return json({ error: "请求格式不对" }, 400);
    if (body.action === "generate") return json({ codes: await generateCodes(env.DB, body, auth.userId) });
    return json({ code: await updateCode(env.DB, body.code, body.action, body) });
  } catch (e) {
    return json({ error: e instanceof Error ? e.message : String(e) }, 400);
  }
}
