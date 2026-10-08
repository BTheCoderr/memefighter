"""Run: python -m unittest discover -s tests -v"""
import asyncio
import json
import unittest
from aiohttp import ClientSession, WSMsgType, web
import server

class RelayTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        server.ROOMS.clear()
        self.runner = web.AppRunner(server.create_app())
        await self.runner.setup()
        self.site = web.TCPSite(self.runner,'127.0.0.1',0)
        await self.site.start()
        self.port = self.site._server.sockets[0].getsockname()[1]
        self.client = ClientSession()
        self.sockets = []

    async def asyncTearDown(self):
        for sock in self.sockets:
            await sock.close()
        await self.client.close()
        await self.runner.cleanup()
        server.ROOMS.clear()

    async def socket(self):
        sock = await self.client.ws_connect(f'http://127.0.0.1:{self.port}/ws')
        self.sockets.append(sock)
        return sock

    async def put(self, socket, **fields):
        await socket.send_str(json.dumps(fields))

    async def msg(self,socket,kind):
        for _ in range(12):
            data = await asyncio.wait_for(socket.receive(),2)
            self.assertEqual(data.type,WSMsgType.TEXT)
            obj = json.loads(data.data)
            if obj['t']==kind:
                return obj
        self.fail(f'Missing message {kind}')

    async def test_private_room_full_match_rematch_and_reconnect(self):
        host=await self.socket()
        await self.put(host,t='create')
        h=await self.msg(host,'seat');await self.msg(host,'room')
        self.assertEqual(len(h['code']),6)
        guest=await self.socket()
        await self.put(guest,t='join',code=h['code'])
        g=await self.msg(guest,'seat');await self.msg(guest,'room');await self.msg(host,'room')
        self.assertNotEqual(h['token'],g['token'])
        other=await self.socket()
        await self.put(other,t='join',code=h['code'])
        self.assertIn('full',(await self.msg(other,'error'))['message'])
        await self.put(guest,t='stage',stage='fire')
        self.assertEqual((await self.msg(guest,'error'))['t'],'error')
        await self.put(host,t='stage',stage='fire')
        await self.msg(host,'room');await self.msg(guest,'room')
        await self.put(host,t='fighter',fighter=3)
        await self.msg(host,'room');await self.msg(guest,'room')
        await self.put(guest,t='fighter',fighter=2)
        await self.msg(host,'room');await self.msg(guest,'room')
        await self.put(host,t='ready',ready=True)
        await self.msg(host,'room');await self.msg(guest,'room')
        await self.put(guest,t='ready',ready=True)
        await self.msg(host,'room');await self.msg(guest,'room')
        begin=await self.msg(host,'begin');await self.msg(guest,'begin')
        self.assertEqual(begin['fighters'],[3,2])
        self.assertEqual(begin['stage'],'fire')
        await self.put(guest,t='input',keys=['left','block'])
        self.assertEqual((await self.msg(host,'input'))['keys'],['left','block'])
        await self.put(host,t='snapshot',state={'players':[{'hp':71},{'hp':42}]})
        self.assertEqual((await self.msg(guest,'snapshot'))['state']['players'][1]['hp'],42)
        await self.put(host,t='finished')
        await self.msg(host,'finished');await self.msg(guest,'finished')
        await self.put(guest,t='rematch')
        self.assertEqual((await self.msg(host,'room'))['phase'],'lobby')
        await self.msg(guest,'room')
        await guest.close()
        await self.msg(host,'peer_left');await self.msg(host,'room')
        rejoin=await self.socket()
        await self.put(rejoin,t='resume',code=h['code'],token=g['token'])
        self.assertEqual((await self.msg(rejoin,'seat'))['role'],'guest')
        await self.msg(rejoin,'room');await self.msg(host,'room')
        await self.put(host,t='leave')
        self.assertEqual((await self.msg(rejoin,'closed'))['t'],'closed')

    async def test_host_refresh_returns_room_to_lobby(self):
        host=await self.socket();await self.put(host,t='create')
        h=await self.msg(host,'seat');await self.msg(host,'room')
        guest=await self.socket();await self.put(guest,t='join',code=h['code'])
        await self.msg(guest,'seat');await self.msg(guest,'room');await self.msg(host,'room')
        await self.put(host,t='ready',ready=True)
        await self.msg(host,'room');await self.msg(guest,'room')
        await self.put(guest,t='ready',ready=True)
        await self.msg(host,'room');await self.msg(guest,'room')
        await self.msg(host,'begin');await self.msg(guest,'begin')
        await host.close()
        await self.msg(guest,'peer_left')
        resumed=await self.socket()
        await self.put(resumed,t='resume',code=h['code'],token=h['token'],playing=False)
        await self.msg(resumed,'seat')
        self.assertEqual((await self.msg(resumed,'room'))['phase'],'lobby')
        self.assertEqual((await self.msg(guest,'room'))['phase'],'lobby')

if __name__=='__main__': unittest.main()