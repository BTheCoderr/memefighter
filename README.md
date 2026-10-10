# MEME FIGHTER · Online Beta v0.4.1

A browser arcade fighting game with 4 original vector-art meme-inspired fighters.

## Modes

- Solo against easy/normal/hard CPU
- Two players on one keyboard
- **Private online 1v1**, two devices, room code + invite URL, no login
- Character selection, 2 arenas, best-of-three, combo chains, dash, character specials, Virality ultimate, overtime
- Room reconnect over transient WebSocket disconnects with private session tokens

## How online play works

1. Open the hosted site and select **CREATE ROOM**.
2. Share **COPY INVITE LINK** with your friend, or send them the 6-character room code.
3. The friend visits the same site, chooses **JOIN ROOM** (or uses your link), selects the fighter in the right column.
4. Host selects the fighter in the left column and chooses the arena.
5. Both press **READY TO FIGHT**. Match launches on both devices.
6. After a match, choose **REMATCH LOBBY**, then both press READY again.

Each player uses their own screen buttons on phones, or Player 1 keyboard controls on desktop (`A/D/W/S/Space/J/K/L/I`). The host's browser simulates the fight, and the server relays guest controls and state snapshots. This is a **casual multiplayer beta**, not a cheat-proof authoritative server. No accounts or persistent online leaderboards.

## Run locally

Requires Python 3.11+. Works on Windows, Mac, and Linux.

```sh
python -m pip install -r requirements.txt
python server.py
```

Open http://localhost:8080. To test two players locally, open two browser tabs (or use another device on the same network via your computer's IP address) and create/join a room.

Note: plain HTTP served over your LAN is for testing only. Production hosting should use HTTPS/WSS.

## Deploy to Render

Create a GitHub repository containing these files (named `meme-fighter` is recommended) and connect it to a **Render Web Service**. The included `render.yaml` can supply the deployment settings:

- Runtime: Python
- Build command: `pip install -r requirements.txt`
- Start command: `python server.py`
- Health check path: `/healthz`
- Port: provided by Render's `PORT` variable automatically

The *same* web service hosts the HTML game and WebSocket rooms. **A static Netlify/GitHub Pages deploy alone cannot run this multiplayer relay.** On Render's free tier, the service may sleep when inactive; the first visitor can encounter a startup delay, and websocket connections can be interrupted. Reconnects within a live server process retain room seats. Refreshing the **host** during a fight resets the room to its lobby, because the host runs the simulation; refreshing a guest re-attaches to the current match after the next snapshot. When the service restarts/sleeps, in-memory rooms disappear.

For public scaling/competitive multiplayer, move the game engine to an authoritative dedicated server, add durable rooms/rejoin semantics, abuse prevention, anti-cheat, and multi-instance coordination.

## Repository structure

```
index.html        # Arcade client + online room UI and browser game engine
server.py         # HTTP web server + WebSocket room relay
requirements.txt  # Pinned aiohttp runtime
render.yaml       # Render Blueprint
.gitignore        # Local ignored artifacts
```

## Room recovery

If your opponent loses connection or closes the browser, their seat stays
reserved so they can reconnect. The host sees **REOPEN GUEST SEAT** when that
guest is offline. Pressing it returns the game to the lobby and frees the
guest seat without changing the room code. It invalidates the previous guest's
reconnect token, and it cannot remove a still-connected guest.

The server broadcasts presence changes even during fights. Browser WebSocket
connections are checked against the game site's origin; tab switching also
releases locally held movement/attack keys. GitHub Actions runs Python relay
tests and validates the inline browser JavaScript syntax.

## Security / limits

- CSPRNG-generated room codes and per-seat reconnect tokens; tokens are **not** in invite links.
- Two players per room and server-side seat identity checked for sensitive actions.
- Message size caps and allowlisted move actions; snapshot updates accepted from host only.
- Idle rooms expire, and connections are kept alive by server WebSocket heartbeat.
- Host-authoritative: the room host can tamper with their local state. Do not use for bets, prizes, or ranked competitive play.
- The Render Blueprint has auto-deploy disabled by default; manually deploy updates after review.
- The service is in-memory and single-instance; rooms cannot survive process restarts or deployment replacements.
- Third-party meme character naming/likeness may require IP review prior to commercial use.

## License

No external gameplay art is included; artwork uses the game's existing original canvas shapes. No license grant is asserted for meme-character identities. Choose a license before distributing the source openly.