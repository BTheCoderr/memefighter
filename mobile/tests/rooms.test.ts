import assert from "node:assert/strict";
import { test } from "node:test";
import { normalizeRoom, roomFromDeepLink, roomInviteUrl, safeOnlineOrigin } from "../src/rooms.ts";

test("accepts only the relay's six-character room alphabet", () => {
  assert.equal(normalizeRoom(" abcd23 "), "ABCD23");
  for (const bad of ["ABCI23", "ABCO23", "ABC123", "ABCD20", "ABCD2", "AAAAAAA", "?room=ABCD23"]) {
    assert.equal(normalizeRoom(bad), null, bad);
  }
});

test("production online servers must be HTTPS origins, not arbitrary paths", () => {
  assert.equal(safeOnlineOrigin("https://meme.example.com/"), "https://meme.example.com");
  for (const bad of ["http://meme.example.com", "https://meme.example.com/evil", "https://user:pass@meme.example.com", "https://meme.example.com?room=ABCDEF", "javascript:alert(1)", ""]) {
    assert.equal(safeOnlineOrigin(bad), null);
  }
});

test("accepts native invitations and only links from the configured server", () => {
  const origin = "https://meme.example.com";
  assert.equal(roomFromDeepLink("memefighter://room/ABCD23", origin), "ABCD23");
  assert.equal(roomFromDeepLink(origin + "/?room=abcd23", origin), "ABCD23");
  assert.equal(roomFromDeepLink("https://evil.example.com/?room=ABCD23", origin), null);
  assert.equal(roomFromDeepLink(origin + "/other?room=ABCD23", origin), null);
  assert.equal(roomFromDeepLink("memefighter://evil/ABCD23", origin), null);
  assert.equal(roomFromDeepLink("https://meme.example.com/?room=ABCI23", origin), null);
});

test("room invitation links use the same configured server", () => {
  assert.equal(roomInviteUrl("https://meme.example.com", "abcd23"), "https://meme.example.com/?room=ABCD23");
  assert.throws(() => roomInviteUrl("https://meme.example.com", "NOPE"));
});
