# Meme Fighter iPhone/Android beta

This is the native Expo client for the existing Meme Fighter v0.5 game. The website and
WebSocket relay stay in the repository root; do not replace them.

## What is playable

- **Offline solo** loads a bundled copy of the actual HTML/Canvas combat engine. CPU
  easy/normal/hard, four fighters, both arenas, combos and on-screen touch controls
  do not depend on Render, Expo Go, or an internet connection.
- **Online private 1v1** loads the existing HTTPS game from its real hosting origin, which
  also must serve /ws. Both phones use the established WebSocket relay, not a fake match.
- Native start screen, join-room code field, invite deep links (memefighter://room/CODE),
  iOS/Android share sheet for room links, touch/result haptics, restart and offline fallback.
- The browser game is still the rendering engine inside WebView. This is a genuine
  installable Expo client with a bundled offline game and native features, but not
  a full React Native/Skia combat-engine rewrite. Apple may request additional native
  functionality under Guideline 4.2. Do not claim review acceptance or TestFlight upload.

## Development

Requires Node 20.19+ (prefer Node 22 LTS) and Expo/EAS CLI.

```sh
cd mobile
npm install
cp .env.example .env
# The tracked .env.example already points to the existing Render HTTPS game and /ws relay.
npm run test:rooms
npm run check:game
npm run typecheck
npm run export:ios
npx expo start
```

When root index.html changes, run `npm run sync:game` and commit
`src/game.generated.ts`. CI rejects a stale generated game.

The installed Expo Go version on current physical iPhones may not support SDK 54.
Use an EAS **preview** build for reliable physical-phone checks.

## TestFlight blockers

1. The existing free Render service is `https://meme-fighter-online.onrender.com` in **My Workspace**. The production and preview EAS profiles now embed this public HTTPS origin. Its last known live deployment is the v0.5 server (`bc2975a`). Run the automated live-relay smoke check (`python scripts/smoke_live_relay.py`) and play a match on two physical phones. A successful health endpoint alone is not an end-to-end match test. The free service may cold-start or lose in-memory matches after restarts.
2. Add reviewed original, rights-cleared 1024 x 1024 nontransparent app artwork as
   `mobile/assets/icon.png`, then set `expo.icon` in `mobile/app.json`.
3. Confirm the provisional bundle ID `com.bthedream.memefighter` with Apple; run
   `eas init` from `mobile/` and record the existing or new EAS project ID. Never
   link to another app's EAS project.
4. Both EAS profiles declare the public `EXPO_PUBLIC_MEME_FIGHTER_URL`; no account secrets are included. Do not change it to a static-only site or put credentials in an `EXPO_PUBLIC_` value.
5. Run `npm run preflight:ios`, `npm run typecheck`, `npx expo-doctor`, and an
   iOS export. Verify music, touch input, crash recovery, offline CPU, live online
   rooms, invite/share, and app relaunch on two physical iPhones.
6. Confirm store privacy disclosures, support URL, App Store screenshots, and ownership
   of all character names and artwork. No iOS store build has been authorized here.

After those gates, the normal release route is
`eas build --platform ios --profile production` then
`eas submit --platform ios --profile production --latest`.
These may consume EAS credits. Do not submit an older or wrong-bundle .ipa.

## Known online beta limits

Current online rooms are in memory on one server; a Render restart loses rooms.
The host simulates combat and can theoretically cheat. Do not add cash stakes or
competitive rewards. No user accounts or real purchases exist.
