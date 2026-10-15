import { acceptHandoff, HANDOFF_PATH, kronLoginUrl, privateCache, siteGate } from "./_lib/kron-handoff.js";
import { handleAuthRoutes } from "./_lib/kron-account.js";

// 整站都要 Kron 账号登录、且激活码包含 Word。没登录或没开通的页面一律跳到 kronenglish 登录，登录后带一次性通行证回来；
// 词表数据没权限返回 401/403。账号库是 kronenglish 的 D1（wrangler.toml 绑定 DB），流程见 kronenglish 仓库 docs/kron-handoff.md。
// 环境变量 AUTH_GATE=off 可以临时关掉门禁。
const SITE = "word";
const PROTECTED = /\.(json|mp3|webp|png|jpg)$/i;

export async function onRequest(context) {
  const { request, env, next } = context;
  const url = new URL(request.url);
  // 本站自己的登录页不再用：一律去 kronenglish 统一登录
  if (url.pathname === "/login" || url.pathname === "/login/") return Response.redirect(kronLoginUrl(SITE, url.searchParams.get("next") || "/"), 302);
  if (url.pathname === HANDOFF_PATH) return acceptHandoff(request, env, { site: SITE });
  // 书架顶栏右上角「登录」显示打码手机号用 /api/auth/me（demo/kron-word.html）
  if (url.pathname.startsWith("/api/auth/")) {
    const auth = await handleAuthRoutes(request, env, { product: SITE, ctx: context });
    if (auth) return auth;
  }
  if (env.AUTH_GATE === "off" || url.pathname.startsWith("/api/")) return next();
  const isPage = (request.headers.get("Accept") || "").includes("text/html");
  if (!isPage && !PROTECTED.test(url.pathname)) return next(); // 网站自己的脚本、样式
  const denied = await siteGate(request, env, { site: SITE, ctx: context });
  return denied || privateCache(request, await next());
}
