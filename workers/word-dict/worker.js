/**
 * 组词 / 成语按需生成 Worker
 *
 * 用法: GET /word?char=勇
 * 返回: { "char": "勇", "words": ["勇敢","勇气",...], "idioms": ["勇往直前",...] }
 *
 * 部署后在 Worker Settings -> Variables 中设置:
 *   AGENS_API_KEY  (Secret 类型) - agnes API key
 *
 * 通过 Cloudflare Cache API 做边缘缓存，同一汉字重复请求不会再次调用 AI。
 */

const AI_API_BASE = "https://apihub.agnes-ai.com/v1";
const AI_MODEL = "agnes-2.0-flash";

const SYSTEM_PROMPT = `你是一位资深的小学语文老师，精通汉字教学。

任务：为给定的单个汉字生成规范的组词和成语。

要求：
1. 生成 3-5 个常用组词（2-3 字词），必须包含该字
2. 如果该字有包含它的成语，生成 1-3 个成语；没有就返回空数组
3. 组词必须是真实存在的词语，不能生造
4. 成语必须是标准四字成语
5. 适合小学生理解

输出格式（严格 JSON，不要 markdown，不要任何说明文字）：
{"words": ["词1", "词2", "词3"], "idioms": ["成语1"]}`;

function jsonResponse(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
      "Cache-Control": "public, max-age=2592000",
    },
  });
}

async function generateWordDict(char, env) {
  const userPrompt = `请为汉字"${char}"生成组词和成语。`;

  const apiRes = await fetch(`${AI_API_BASE}/chat/completions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${env.AGENS_API_KEY}`,
    },
    body: JSON.stringify({
      model: AI_MODEL,
      messages: [
        { role: "system", content: SYSTEM_PROMPT },
        { role: "user", content: userPrompt },
      ],
      temperature: 0.3,
      max_tokens: 800,
    }),
  });

  if (!apiRes.ok) {
    throw new Error(`AI API ${apiRes.status}: ${await apiRes.text()}`);
  }

  const data = await apiRes.json();
  let content = data.choices[0].message.content.trim();
  // 兼容 AI 偶尔返回 ```json ... ``` 包裹
  content = content.replace(/^```(?:json)?\s*/i, "").replace(/\s*```$/i, "");
  const parsed = JSON.parse(content);

  return {
    char,
    words: (parsed.words || []).filter((w) => typeof w === "string" && w.includes(char)).slice(0, 6),
    idioms: (parsed.idioms || []).filter((w) => typeof w === "string" && w.includes(char)).slice(0, 4),
  };
}

export default {
  async fetch(request, env) {
    // CORS 预检
    if (request.method === "OPTIONS") {
      return new Response(null, {
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "GET, OPTIONS",
          "Access-Control-Allow-Headers": "Content-Type",
        },
      });
    }

    const url = new URL(request.url);

    // 健康检查
    if (url.pathname === "/" || url.pathname === "/ping") {
      return jsonResponse({ ok: true, service: "word-dict" });
    }

    if (url.pathname !== "/word") {
      return jsonResponse({ error: "not found" }, 404);
    }

    const char = (url.searchParams.get("char") || "").trim();
    if (!char || !/[\u4e00-\u9fff]/.test(char) || [...char].length !== 1) {
      return jsonResponse({ error: "param char must be a single chinese character" }, 400);
    }

    // 边缘缓存命中则直接返回
    const cache = caches.default;
    const cached = await cache.match(request);
    if (cached) {
      return cached;
    }

    try {
      const result = await generateWordDict(char, env);
      const response = jsonResponse(result);
      // 写入边缘缓存（30 天）
      await cache.put(request, response.clone());
      return response;
    } catch (e) {
      return jsonResponse({ char, words: [], idioms: [], error: String(e.message || e) }, 502);
    }
  },
};
