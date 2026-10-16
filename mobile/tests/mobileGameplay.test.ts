import assert from "node:assert/strict";
import {test} from "node:test";
import { makeArcadeHtml, makeBridgeScript, MOBILE_GAME_CSS } from "../src/mobileGameplay.ts";

const documentHtml = '<html><head></head><body><canvas id="game"></canvas></body></html>';
test("bundles the existing arcade canvas and mobile landscape layout for offline fights", () => {
  const result = makeArcadeHtml(documentHtml, true);
  assert.match(result, /id="game"/);
  assert.match(result, /orientation:landscape/);
  assert.match(result, /online-box\{display:none!important\}/);
  assert.equal(result.match(/<style>/g)?.length, 1);
});
test("rejects a broken arcade export instead of displaying an empty WebView", () => {
  assert.throws(() => makeArcadeHtml("<html></html>", true), /missing/);
});
test("native online room creation happens once when no invite is supplied", () => {
  assert.match(makeBridgeScript(true), /create\.click\(\)/);
  assert.doesNotMatch(makeBridgeScript(false), /create\.click\(\)/);
  assert.match(makeBridgeScript(true), /__memeFighterNativeBridge/);
  assert.ok(MOBILE_GAME_CSS.includes("touch-action:none"));
});
