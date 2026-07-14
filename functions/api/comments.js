export const MAX_BODY_LENGTH = 1000;

export function validateGetParams(searchParams) {
  const episodeId = searchParams.get("episodeId");
  if (!episodeId) {
    return { valid: false, error: "episodeId is required" };
  }
  return { valid: true, episodeId };
}

export function validatePostPayload(payload) {
  if (!payload || typeof payload.episodeId !== "string" || !payload.episodeId) {
    return { valid: false, error: "episodeId is required" };
  }

  const trimmedBody = typeof payload.body === "string" ? payload.body.trim() : "";
  if (!trimmedBody) {
    return { valid: false, error: "body is required" };
  }
  if (trimmedBody.length > MAX_BODY_LENGTH) {
    return { valid: false, error: `body exceeds ${MAX_BODY_LENGTH} characters` };
  }

  const nickname =
    typeof payload.nickname === "string" && payload.nickname.trim()
      ? payload.nickname.trim()
      : null;

  return {
    valid: true,
    episodeId: payload.episodeId,
    body: trimmedBody,
    nickname,
    turnstileToken: payload.turnstileToken,
  };
}

export async function verifyTurnstile(token, secretKey, ip, fetchImpl = fetch) {
  if (!token || typeof token !== "string") return false;

  const formData = new FormData();
  formData.append("secret", secretKey);
  formData.append("response", token);
  if (ip) formData.append("remoteip", ip);

  const res = await fetchImpl("https://challenges.cloudflare.com/turnstile/v0/siteverify", {
    method: "POST",
    body: formData,
  });
  const data = await res.json();
  return data.success === true;
}

function jsonResponse(data, status) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

export async function onRequestGet(context) {
  const { request, env } = context;
  const url = new URL(request.url);
  const check = validateGetParams(url.searchParams);
  if (!check.valid) {
    return jsonResponse({ error: check.error }, 400);
  }

  const { results } = await env.DB.prepare(
    "SELECT id, episode_id, nickname, body, created_at FROM comments WHERE episode_id = ? ORDER BY created_at DESC"
  )
    .bind(check.episodeId)
    .all();

  return jsonResponse(results, 200);
}

export async function onRequestPost(context) {
  const { request, env } = context;

  let payload;
  try {
    payload = await request.json();
  } catch (err) {
    return jsonResponse({ error: "invalid JSON body" }, 400);
  }

  const check = validatePostPayload(payload);
  if (!check.valid) {
    return jsonResponse({ error: check.error }, 400);
  }

  const ip = request.headers.get("CF-Connecting-IP");
  const verified = await verifyTurnstile(check.turnstileToken, env.TURNSTILE_SECRET_KEY, ip);
  if (!verified) {
    return jsonResponse({ error: "turnstile verification failed" }, 403);
  }

  const createdAt = new Date().toISOString();
  const result = await env.DB.prepare(
    "INSERT INTO comments (episode_id, nickname, body, created_at) VALUES (?, ?, ?, ?) RETURNING id, episode_id, nickname, body, created_at"
  )
    .bind(check.episodeId, check.nickname, check.body, createdAt)
    .first();

  return jsonResponse(result, 201);
}
