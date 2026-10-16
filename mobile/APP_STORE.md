# Meme Fighter — iOS release and App Store Connect handoff

Status as of 2026-10-16: **Expo mobile source and game/relay CI are verified. An Apple-signed build, physical-device QA, and App Store Connect upload are NOT verified.**

## Product identity

- App name: Meme Fighter
- Subtitle (candidate): Arcade Battles With Friends
- Bundle ID (provisional): `com.bthedream.memefighter`
- Expo owner: `bferrell514`
- Current mobile version: `0.1.0`
- Production online game + relay: `https://meme-fighter-online.onrender.com`
- Support URL: `https://meme-fighter-online.onrender.com/support`
- Privacy URL: `https://meme-fighter-online.onrender.com/privacy`
- App icon: `mobile/assets/icon.png` (original *provisional candidate*, requires final visual approval)

## Public description (candidate)

**Settle the comments in Meme Fighter!**

Pick from four meme-inspired fighters, master signature specials, and battle through the Comment Section or This Is Fine Room. Face the CPU on Easy, Normal, or Hard, or challenge a friend in a private online two-player match using a shareable room code.

- Four distinct fighting styles, fast combos, dashes and ultimates
- Offline solo arcade with no account required
- Online private 1v1 rooms with ready-up and rematch
- On-screen controls and native-feeling haptics
- Best-of-three rounds, sudden death and comeback moments

Meme Fighter is a casual arcade game. There is no real-money wagering, account registration, or in-app purchasing in this beta. Multiplayer requires an internet connection. Room sessions may reset if the server restarts.

## TestFlight "What to Test" (candidate)

Please test on a physical iPhone:

1. Launch the app, select Play Solo, rotate to landscape, pick fighters and CPU difficulty.
2. Complete matches using the on-screen left/right, jump, dash, light/heavy, special and ultimate buttons.
3. Exit a fight and verify the native menu returns to portrait, then relaunch the fight.
4. Start an online private room on iPhone A. Share or read its six-character room code.
5. Join with iPhone B; both players select fighters and tap Ready to Fight.
6. Play a complete match, then test rematch. Check control latency and that each phone shows consistent health, time, scoring and end-of-match state.
7. While a match runs, interrupt the app (screen lock, phone call or app switch) and reconnect.
8. With no internet, verify offline CPU works and online errors give a usable fallback.
9. Report frozen controls, rotations, UI clipping, crashes, audio issues and inaccurate match synchronization.

**The live protocol smoke test is not a substitute for the above physical-device checks.**

## Apple App Review information (candidate)

- **Login:** No account or credentials are needed.
- **Review path:** Launch → Play Solo → choose two fighters → select stage/difficulty → Let's Fight. To inspect multiplayer, install on two devices; one taps Create Online Room and shares its room code, the second taps Join Room using that code, then both tap Ready to Fight.
- **Server:** Online relay is `https://meme-fighter-online.onrender.com`. The free-tier service may need a warm-up and rooms are in-memory.
- **Purchases / betting:** No in-app purchases, payments, real-money prizes or betting.
- **Data practices:** Review `/privacy` and complete App Store Connect privacy disclosures based on the actual shipped binary, libraries and hosting practices.

## Before an EAS or Apple upload

- [ ] Confirm the bundle ID is assigned to the intended App Store Connect app. Avoid collisions with earlier apps.
- [ ] Link to the correct EAS project in `mobile/` via `eas init`, and commit the resulting `expo.extra.eas.projectId`.
- [ ] Confirm Expo/Apple distribution credentials and team identity. Set `EXPO_TOKEN` in GitHub repo secrets only if using the manual GitHub workflow.
- [ ] Approve icon appearance and ownership; ensure all fighter names/likenesses and other IP are cleared for distribution.
- [ ] Run `npm install`, `npm run check:icon`, `npm run check:game`, `npm run test:shell`, `npm run test:rooms`, `npm run typecheck`, `npx expo-doctor`, `npm run export:ios`, and `npm run preflight:ios`.
- [ ] Run a signed preview/build and physically test solo + two-phone online gameplay, landscape, interruptions and retry on latest iOS.
- [ ] Prepare actual-device screenshots in App Store Connect-required sizes; do not use synthetic UI screenshots as evidence of live functionality.
- [ ] Verify support and privacy URLs are live, and confirm final policy copy with product owner.
- [ ] Confirm App Store Connect app numeric `ascAppId` if automating submission; enter it under `submit.production.ios.ascAppId` in `eas.json`.
- [ ] For an already-used version, inspect Apple's highest accepted *build number* and sync EAS's remote number so the next one is strictly higher.
- [ ] Run **Actions → Meme Fighter iOS TestFlight (manual)**, confirm the Apple identity checkbox. Leave Submit unchecked for signed build only; check it only when the whole TestFlight upload is authorized and configured. Signed builds may cost EAS credits.
- [ ] Recheck App Store Connect upload and status independently. No automatic claim of Apple review approval.

## Current release blockers

The repository does **not** yet contain an EAS project ID or App Store Connect numeric ID, and a physically tested/signed build is not established. Those require account-side identity and/or iPhone QA. Do not substitute a passing JavaScript export for a real IPA or TestFlight availability.
