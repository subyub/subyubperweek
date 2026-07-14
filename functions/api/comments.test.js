import { test } from "node:test";
import assert from "node:assert/strict";
import {
  validateGetParams,
  validatePostPayload,
  verifyTurnstile,
  MAX_BODY_LENGTH,
  MAX_NICKNAME_LENGTH,
  MAX_EPISODE_ID_LENGTH,
} from "./comments.js";

test("validateGetParams rejects missing episodeId", () => {
  const result = validateGetParams(new URLSearchParams());
  assert.equal(result.valid, false);
  assert.equal(result.error, "episodeId is required");
});

test("validateGetParams accepts present episodeId", () => {
  const result = validateGetParams(new URLSearchParams({ episodeId: "abc-123" }));
  assert.equal(result.valid, true);
  assert.equal(result.episodeId, "abc-123");
});

test("validatePostPayload rejects missing episodeId", () => {
  const result = validatePostPayload({ body: "hello" });
  assert.equal(result.valid, false);
  assert.equal(result.error, "episodeId is required");
});

test("validatePostPayload rejects empty body", () => {
  const result = validatePostPayload({ episodeId: "abc", body: "   " });
  assert.equal(result.valid, false);
  assert.equal(result.error, "body is required");
});

test("validatePostPayload rejects body over max length", () => {
  const longBody = "x".repeat(MAX_BODY_LENGTH + 1);
  const result = validatePostPayload({ episodeId: "abc", body: longBody });
  assert.equal(result.valid, false);
  assert.equal(result.error, `body exceeds ${MAX_BODY_LENGTH} characters`);
});

test("validatePostPayload accepts body at exactly max length", () => {
  const maxBody = "x".repeat(MAX_BODY_LENGTH);
  const result = validatePostPayload({ episodeId: "abc", body: maxBody });
  assert.equal(result.valid, true);
  assert.equal(result.body, maxBody);
});

test("validatePostPayload trims nickname and treats blank nickname as null", () => {
  const blank = validatePostPayload({ episodeId: "abc", body: "hi", nickname: "   " });
  assert.equal(blank.valid, true);
  assert.equal(blank.nickname, null);

  const named = validatePostPayload({ episodeId: "abc", body: "hi", nickname: "  Bob  " });
  assert.equal(named.valid, true);
  assert.equal(named.nickname, "Bob");
});

test("validatePostPayload treats missing nickname as null", () => {
  const result = validatePostPayload({ episodeId: "abc", body: "hi" });
  assert.equal(result.valid, true);
  assert.equal(result.nickname, null);
});

test("validatePostPayload rejects nickname over max length", () => {
  const longNickname = "x".repeat(MAX_NICKNAME_LENGTH + 1);
  const result = validatePostPayload({ episodeId: "abc", body: "hi", nickname: longNickname });
  assert.equal(result.valid, false);
  assert.equal(result.error, `nickname exceeds ${MAX_NICKNAME_LENGTH} characters`);
});

test("validatePostPayload accepts nickname at exactly max length", () => {
  const maxNickname = "x".repeat(MAX_NICKNAME_LENGTH);
  const result = validatePostPayload({ episodeId: "abc", body: "hi", nickname: maxNickname });
  assert.equal(result.valid, true);
  assert.equal(result.nickname, maxNickname);
});

test("validatePostPayload rejects episodeId over max length", () => {
  const longEpisodeId = "x".repeat(MAX_EPISODE_ID_LENGTH + 1);
  const result = validatePostPayload({ episodeId: longEpisodeId, body: "hi" });
  assert.equal(result.valid, false);
  assert.equal(result.error, `episodeId exceeds ${MAX_EPISODE_ID_LENGTH} characters`);
});

test("verifyTurnstile returns false when token is missing", async () => {
  const result = await verifyTurnstile(undefined, "secret", "1.2.3.4");
  assert.equal(result, false);
});

test("verifyTurnstile returns true when siteverify reports success", async () => {
  const fakeFetch = async (url) => {
    assert.equal(url, "https://challenges.cloudflare.com/turnstile/v0/siteverify");
    return { json: async () => ({ success: true }) };
  };
  const result = await verifyTurnstile("valid-token", "secret", "1.2.3.4", fakeFetch);
  assert.equal(result, true);
});

test("verifyTurnstile returns false when siteverify reports failure", async () => {
  const fakeFetch = async () => ({ json: async () => ({ success: false }) });
  const result = await verifyTurnstile("bad-token", "secret", "1.2.3.4", fakeFetch);
  assert.equal(result, false);
});
