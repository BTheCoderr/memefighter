"""Meme Fighter private-room relay and static website, Python 3.11+ / aiohttp.

The host's browser simulates the match; this relay owns room membership and
forwards controls and snapshots. This is not a cheat-resistant ranked server.
"""
import asyncio
import json
import os
import re
import secrets
import time
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit
from aiohttp import WSMsgType, web

ROOT = Path(__file__).resolve().parent
ALPHABET = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
CODE = re.compile(r'^[A-HJ-NP-Z2-9]{6}$')
VALID_KEYS = {'left','right','jump','block','dash','light','heavy','special','ultimate'}
VALID_STAGES = {'comments','fire'}
ROOMS = {}
MAX_ROOMS = 400
MAX_MESSAGE = 12_000
IDLE_SECONDS = 1800

@dataclass
class Seat:
    token: str = field(default_factory=lambda: secrets.token_urlsafe(32))
    ws: object = None
    fighter: int = 0
    ready: bool = False

@dataclass
class Room:
    code: str
    host: Seat
    guest: Seat | None = None
    stage: str = 'comments'
    phase: str = 'lobby'
    last_seen: float = field(default_factory=time.monotonic)
    last_snapshot: float = 0
    last_input: float = 0
    snapshot: dict | None = None
    recovering: bool = False

    def summary(self):
        return {'t':'room','code':self.code,'phase':self.phase,'stage':self.stage,
                'host':{'fighter':self.host.fighter,'ready':self.host.ready,'online':is_open(self.host.ws)},
                'guest':None if not self.guest else {'fighter':self.guest.fighter,'ready':self.guest.ready,'online':is_open(self.guest.ws)},
                'recovering':self.recovering}


def is_open(ws):
    return bool(ws is not None and not ws.closed)

async def send(ws, data):
    if is_open(ws):
        await ws.send_json(data)

async def tell(room, data):
    await asyncio.gather(send(room.host.ws, data), send(room.guest.ws if room.guest else None, data))

async def lobby(room):
    await tell(room, room.summary())

async def attach(room, role, token, ws):
    seat = room.host if role == 'host' else room.guest
    if seat is None or not secrets.compare_digest(token, seat.token):
        return False
    if is_open(seat.ws) and seat.ws is not ws:
        await seat.ws.close(code=4001, message=b'Another tab resumed this seat')
    seat.ws = ws
    room.last_seen = time.monotonic()
    await send(ws, {'t':'seat','role':role,'code':room.code,'token':seat.token})
    await lobby(room)
    # A newly loaded guest gets the last validated state immediately.
    if role == 'guest' and room.phase == 'fighting' and room.snapshot:
        await send(ws, {'t':'snapshot','state':room.snapshot})
    return True

async def websocket(request):
    origin = request.headers.get('Origin')
    if origin:
        parsed = urlsplit(origin)
        if parsed.scheme not in ('http', 'https') or parsed.netloc.lower() != request.host.lower() or parsed.path not in ('', '/') or parsed.query or parsed.fragment:
            raise web.HTTPForbidden(text='Cross-origin WebSocket requests are not allowed')
    ws = web.WebSocketResponse(heartbeat=24, max_msg_size=MAX_MESSAGE)
    await ws.prepare(request)
    current = None
    role = None
    seat = None
    try:
        async for incoming in ws:
            if incoming.type != WSMsgType.TEXT:
                continue
            try:
                data = json.loads(incoming.data)
                if not isinstance(data,dict):
                    raise ValueError('message must be an object')
            except (ValueError,TypeError):
                await send(ws, {'t':'error','message':'Invalid message'})
                continue
            op = data.get('t')
            if op in ('create','join','resume') and current is None:
                if op == 'create':
                    if len(ROOMS) >= MAX_ROOMS:
                        await send(ws, {'t':'error','message':'Rooms are busy, try again later'})
                        continue
                    code = ''.join(secrets.choice(ALPHABET) for _ in range(6))
                    while code in ROOMS:
                        code = ''.join(secrets.choice(ALPHABET) for _ in range(6))
                    current = Room(code, Seat(fighter=0))
                    ROOMS[code] = current
                    role = 'host'
                    await attach(current, role, current.host.token, ws)
                else:
                    code = str(data.get('code','')).strip().upper()
                    room = ROOMS.get(code) if CODE.fullmatch(code) else None
                    if room is None:
                        await send(ws, {'t':'error','message':'Room not found or expired'})
                        continue
                    if op == 'resume':
                        token = data.get('token')
                        if not isinstance(token,str):
                            await send(ws, {'t':'error','message':'Cannot resume without seat token'})
                            continue
                        claimed = ('host' if secrets.compare_digest(token,room.host.token)
                                   else 'guest' if room.guest and secrets.compare_digest(token,room.guest.token)
                                   else None)
                        if not claimed:
                            await send(ws, {'t':'error','message':'Seat expired'})
                            continue
                        # A host browser refresh can recover from a relay-held snapshot.
                        # If no snapshot has reached the relay, return to lobby safely.
                        if claimed == 'host' and room.phase == 'fighting':
                            if room.snapshot:
                                room.recovering = True
                            else:
                                room.phase = 'lobby'
                                room.recovering = False
                                room.host.ready = False
                                if room.guest: room.guest.ready = False
                        current, role = room, claimed
                        await attach(room, role, token, ws)
                        if role == 'host' and room.phase == 'fighting' and room.snapshot:
                            await send(ws, {'t':'recover','state':room.snapshot})
                    elif room.guest:
                        await send(ws, {'t':'error','message':'Room is full (2 players max)'})
                    elif room.phase != 'lobby':
                        await send(ws, {'t':'error','message':'This match has already started'})
                    else:
                        room.guest = Seat(fighter=1)
                        current, role = room, 'guest'
                        await attach(room, role, room.guest.token, ws)
                if current is not None:
                    seat = current.host if role == 'host' else current.guest
                continue
            if not current or not seat or seat.ws is not ws:
                await send(ws, {'t':'error','message':'Create or join a room first'})
                continue
            current.last_seen = time.monotonic()
            if op == 'fighter' and current.phase == 'lobby':
                fighter = data.get('fighter')
                if type(fighter) is int and 0 <= fighter <= 3:
                    seat.fighter = fighter
                    seat.ready = False
                    await lobby(current)
            elif op == 'stage' and role == 'host' and current.phase == 'lobby':
                if data.get('stage') in VALID_STAGES:
                    current.stage = data['stage']
                    current.host.ready = False
                    await lobby(current)
            elif op == 'ready' and current.phase == 'lobby':
                seat.ready = bool(data.get('ready'))
                await lobby(current)
                if current.guest and current.host.ready and current.guest.ready and is_open(current.host.ws) and is_open(current.guest.ws):
                    current.phase = 'fighting'
                    current.snapshot = None
                    current.recovering = False
                    current.last_snapshot = current.last_input = 0
                    await tell(current, {'t':'begin','stage':current.stage,'fighters':[current.host.fighter,current.guest.fighter]})
            elif op == 'reopen' and role == 'host':
                if current.guest is None or is_open(current.guest.ws):
                    await send(ws, {'t':'error','message':'The guest must be disconnected before reopening their seat'})
                else:
                    current.guest = None
                    current.host.ready = False
                    current.phase = 'lobby'
                    current.last_snapshot = current.last_input = 0
                    current.snapshot = None
                    current.recovering = False
                    await lobby(current)
            elif op == 'resume_ready' and role == 'host' and current.phase == 'fighting' and current.recovering and current.snapshot:
                current.recovering = False
                await lobby(current)
                if current.guest:
                    await send(current.guest.ws, {'t':'snapshot','state':current.snapshot})
            elif op == 'input' and role == 'guest' and current.phase == 'fighting' and not current.recovering:
                keys = data.get('keys')
                if isinstance(keys,list) and len(keys) <= 9 and all(isinstance(k,str) and k in VALID_KEYS for k in keys):
                    now = time.monotonic()
                    if now-current.last_input >= 1/65:
                        current.last_input = now
                        await send(current.host.ws, {'t':'input','keys':keys})
            elif op == 'snapshot' and role == 'host' and current.phase == 'fighting' and not current.recovering:
                snap = data.get('state')
                now = time.monotonic()
                if (isinstance(snap,dict) and isinstance(snap.get('players'),list)
                    and len(snap['players']) == 2 and all(isinstance(p,dict) for p in snap['players'])
                    and now-current.last_snapshot >= 1/45):
                    current.last_snapshot = now
                    current.snapshot = snap
                    await send(current.guest.ws if current.guest else None, {'t':'snapshot','state':snap})
            elif op == 'finished' and role == 'host' and current.phase == 'fighting':
                current.phase = 'finished'
                current.recovering = False
                await tell(current, {'t':'finished'})
            elif op == 'rematch' and current.phase == 'finished':
                current.phase = 'lobby'
                current.recovering = False
                current.snapshot = None
                current.host.ready = False
                if current.guest: current.guest.ready = False
                await lobby(current)
            elif op == 'leave':
                if role == 'host':
                    ROOMS.pop(current.code, None)
                    await send(current.guest.ws if current.guest else None, {'t':'closed','message':'Host closed the room'})
                else:
                    current.guest = None
                    current.phase = 'lobby'
                    current.recovering = False
                    current.snapshot = None
                    current.host.ready = False
                    await send(current.host.ws, {'t':'peer_left'})
                    await lobby(current)
                current, role, seat = None, None, None
            else:
                await send(ws, {'t':'error','message':'Action unavailable in current match'})
    finally:
        if current and seat and seat.ws is ws:
            seat.ws = None
            seat.ready = False
            if role == 'host' and current.phase == 'fighting':
                current.recovering = True
            await tell(current, {'t':'peer_left','role':role})
            await lobby(current)
    return ws

async def index(request):
    return web.FileResponse(ROOT / 'index.html', headers={'Cache-Control':'no-cache'})

async def health(request):
    return web.json_response({'ok':True,'rooms':len(ROOMS)})

async def cleanup(app):
    async def worker():
        while True:
            await asyncio.sleep(60)
            now = time.monotonic()
            for code,room in list(ROOMS.items()):
                if now-room.last_seen > IDLE_SECONDS:
                    ROOMS.pop(code,None)
                    await tell(room, {'t':'closed','message':'Room expired after inactivity'})
    task = asyncio.create_task(worker())
    yield
    task.cancel()
    try: await task
    except asyncio.CancelledError: pass

def create_app():
    app = web.Application(client_max_size=MAX_MESSAGE)
    app.router.add_get('/',index)
    app.router.add_get('/healthz',health)
    app.router.add_get('/ws',websocket)
    app.cleanup_ctx.append(cleanup)
    return app

app = create_app()
if __name__ == '__main__':
    web.run_app(app,host='0.0.0.0',port=int(os.environ.get('PORT','8080')))