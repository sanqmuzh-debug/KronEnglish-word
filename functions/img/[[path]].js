// 词卡插画：/img/<文件名>.webp 从 R2 桶 kronword-images（wrangler.toml 绑定 IMG）读，图片在 scripts/import_legacy.py 说明里。
// 登录门禁在 _middleware.js 先跑（.webp 受保护），这里只管取图。
export async function onRequestGet({ params, env, request }) {
  const key = [].concat(params.path || []).join("/");
  if (!/^[\w.-]+\.webp$/.test(key)) return new Response("Not found", { status: 404 });
  const obj = await env.IMG.get(key, { onlyIf: request.headers });
  if (!obj) return new Response("Not found", { status: 404 });
  const headers = new Headers();
  obj.writeHttpMetadata(headers);
  headers.set("etag", obj.httpEtag);
  headers.set("content-type", "image/webp");
  if (!("body" in obj)) return new Response(null, { status: 304, headers });
  return new Response(obj.body, { headers });
}
