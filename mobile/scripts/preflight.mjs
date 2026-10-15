import { existsSync, readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const config = JSON.parse(readFileSync(resolve(root, "app.json"), "utf8")).expo;
const eas = JSON.parse(readFileSync(resolve(root, "eas.json"), "utf8"));
let failures = 0;
function check(ok, label) { console.log((ok ? "PASS " : "FAIL ") + label); if (!ok) failures++; }
const origin = process.env.EXPO_PUBLIC_MEME_FIGHTER_URL || "";
check(/^https:\/\/[^/\s]+\/?$/.test(origin) && !origin.includes("@"), "HTTPS game + relay origin configured");
check(Boolean(config.extra?.eas?.projectId), "EAS project ID linked");
check(Boolean(config.ios?.bundleIdentifier), "iOS bundle ID selected and verified with Apple");
check(eas.build?.production?.distribution === "store", "App Store signed production profile");
const iconPath = config.icon && resolve(root, config.icon);
let iconValid = false;
if (iconPath && existsSync(iconPath)) {
  const b = readFileSync(iconPath);
  iconValid = b.length > 30 && b.subarray(0, 8).toString("hex") === "89504e470d0a1a0a"
    && b.readUInt32BE(16) === 1024 && b.readUInt32BE(20) === 1024
    && b[24] === 8 && (b[25] === 2 || b[25] === 3);
}
check(iconValid, "Approved opaque 1024x1024 iOS app icon present");
try {
  const { execFileSync } = await import("node:child_process");
  execFileSync(process.execPath, [resolve(root, "scripts/sync-game.mjs"), "--check"], { stdio: "ignore" });
  check(true, "Offline arcade game synced to latest web engine");
} catch { check(false, "Offline arcade game synced to latest web engine"); }
if (failures) { console.error(failures + " release blocker(s). Do not sign/submit yet."); process.exit(1); }
console.log("Static preflight passed. Still physically test and verify App Store metadata.");
