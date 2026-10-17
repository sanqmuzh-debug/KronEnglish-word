// 新词的 alex 录音：/au/<词>.mp3、/au/<词>-<n>.mp3 从 R2 桶 kronword-images 的 au/ 下读（scripts/make_fish_audio.py 生成后上传）。
// 登录门禁在 _middleware.js 先跑（.mp3 受保护），这里只管取文件。
export async function onRequestGet({ params, env, request }) {
  const name = [].concat(params.path || []).join("/");
  if (!/^[a-z0-9-]+\.mp3$/.test(name)) return new Response("Not found", { status: 404 });
  const obj = await env.IMG.get("au/" + name, { onlyIf: request.headers });
  if (!obj) return new Response("Not found", { status: 404 });
  const headers = new Headers();
  obj.writeHttpMetadata(headers);
  headers.set("etag", obj.httpEtag);
  headers.set("content-type", "audio/mpeg");
  if (!("body" in obj)) return new Response(null, { status: 304, headers });
  return new Response(obj.body, { headers });
}
