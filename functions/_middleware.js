import { acceptHandoff, HANDOFF_PATH, privateCache, siteGate } from "./_lib/kron-handoff.js";

// 整站都要 Kron 账号登录、且激活码包含 Word。没登录或没开通的页面一律跳到 kronenglish 登录，登录后带一次性通行证回来；
// 词表数据没权限返回 401/403。账号库是 kronenglish 的 D1（wrangler.toml 绑定 DB），流程见 kronenglish 仓库 docs/kron-handoff.md。
// 环境变量 AUTH_GATE=off 可以临时关掉门禁。
const SITE = "word";
const PROTECTED = /\.(json|mp3|webp|png|jpg)$/i;

export async function onRequest(context) {
  const { request, env, next } = context;
  const url = new URL(request.url);
  if (url.pathname === HANDOFF_PATH) return acceptHandoff(request, env, { site: SITE });
  if (env.AUTH_GATE === "off" || url.pathname.startsWith("/api/")) return next();
  const isPage = (request.headers.get("Accept") || "").includes("text/html");
  if (!isPage && !PROTECTED.test(url.pathname)) return next(); // 网站自己的脚本、样式
  const denied = await siteGate(request, env, { site: SITE, ctx: context });
  return denied || privateCache(request, await next());
}
