"""Network smoke check for the deployed public Meme Fighter relay, not a full gameplay test.

Requires the same aiohttp dependency as server.py.
Creates and closes one disposable private room; tests the public HTTPS and
WebSocket endpoints, not physical iPhone rendering or touch controls.
"""
import asyncio
import json
import os
import sys
from urllib.parse import urlsplit

from aiohttp import ClientSession, ClientTimeout, WSMsgType

ORIGIN = os.environ.get("MEME_FIGHTER_ORIGIN", "https://meme-fighter-online.onrender.com").rstrip("/")
DEADLINE = 15


def validate_origin(value):
    u = urlsplit(value)
    if u.scheme != "https" or not u.hostname or u.username or u.password or u.query or u.fragment or u.path not in ("", "/"):
        raise ValueError("Only a bare HTTPS game/relay origin is allowed")


async def wait_for_service(session):
    for attempt in range(9):
        try:
            async with session.get(ORIGIN + "/healthz", timeout=ClientTimeout(total=20)) as response:
                if response.status != 200:
                    raise RuntimeError(f"Health endpoint HTTP {response.status}")
                health = await response.json()
                if health.get("ok") is not True or not isinstance(health.get("rooms"), int):
                    raise RuntimeError("Health endpoint response invalid")
            async with session.get(ORIGIN + "/", timeout=ClientTimeout(total=20)) as response:
                page = await response.text()
                if response.status != 200 or 'id="create-room"' not in page or 'id="game"' not in page:
                    raise RuntimeError("Hosted page is not the Meme Fighter game")
            for path, phrase in (("/privacy", "Your fights. Your privacy."),
                                 ("/support", "Need backup in the arena?")):
                async with session.get(ORIGIN + path, timeout=ClientTimeout(total=20)) as response:
                    html = await response.text()
                    if response.status != 200 or phrase not in html:
                        raise RuntimeError(f"Public {path} unavailable or invalid: HTTP {response.status}")
            print("PASS public HTTPS /healthz, game HTML, privacy and support")
            return
        except Exception as exc:
            if attempt == 8:
                raise
            print(f"Service not ready (attempt {attempt+1}/9): {type(exc).__name__}: {exc}")
            await asyncio.sleep(10)


async def recv_type(ws, want):
    async with asyncio.timeout(DEADLINE):
        while True:
            msg = await ws.receive()
            if msg.type != WSMsgType.TEXT:
                raise RuntimeError(f"WebSocket closed while waiting for {want}: {msg.type}")
            data = json.loads(msg.data)
            if data.get("t") == "error":
                raise RuntimeError(f"Relay error: {data.get('message')}")
            if data.get("t") == want:
                return data


async def check_room(session):
    ws_url = "wss://" + urlsplit(ORIGIN).netloc + "/ws"
    async with session.ws_connect(ws_url, origin=ORIGIN, timeout=ClientTimeout(total=20)) as host:
        await host.send_json({"t": "create"})
        seat = await recv_type(host, "seat")
        code = seat.get("code")
        if not code or len(code) != 6 or seat.get("role") != "host":
            raise RuntimeError("Host was not assigned a valid private room")
        async with session.ws_connect(ws_url, origin=ORIGIN, timeout=ClientTimeout(total=20)) as guest:
            await guest.send_json({"t": "join", "code": code})
            guest_seat = await recv_type(guest, "seat")
            if guest_seat.get("role") != "guest" or guest_seat.get("code") != code:
                raise RuntimeError("Guest did not join the correct private room")
            await host.send_json({"t": "ready", "ready": True})
            await guest.send_json({"t": "ready", "ready": True})
            await recv_type(host, "begin")
            await recv_type(guest, "begin")
            print("PASS private room create/join and two-player ready/fight start")
            await host.send_json({"t": "snapshot", "state": {"players": [{"hp": 100}, {"hp": 100}], "round": 1}})
            snap = await recv_type(guest, "snapshot")
            if snap.get("state", {}).get("round") != 1:
                raise RuntimeError("Guest did not receive combat snapshot")
            await guest.send_json({"t": "input", "keys": ["light"]})
            guest_input = await recv_type(host, "input")
            if guest_input.get("keys") != ["light"]:
                raise RuntimeError("Host did not receive guest controls")
            print("PASS remote controls and host-to-guest state relay")
            await host.send_json({"t": "finished"})
            await recv_type(guest, "finished")
            await host.send_json({"t": "leave"})
            await recv_type(guest, "closed")
            print("PASS finish and disposable room cleanup")


async def main():
    validate_origin(ORIGIN)
    async with ClientSession(timeout=ClientTimeout(total=30)) as session:
        await wait_for_service(session)
        await check_room(session)
    print("LIVE RELAY SMOKE: PASSED (not a substitute for 2-phone tests)")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        print(f"LIVE RELAY SMOKE: FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(1)
