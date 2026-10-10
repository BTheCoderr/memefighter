"""Regression tests for recovery, presence and WebSocket origin checks."""
from aiohttp import WSServerHandshakeError
from test_relay import RelayTests

class RecoveryTests(RelayTests):
    # Inherit the validated aiohttp test fixture and utilities, but do not
    # rerun the base class tests as tests on this subclass.
    __test__ = False

    async def test_guest_recovery(self):
        host = await self.socket()
        await self.put(host, t='create')
        h = await self.msg(host, 'seat'); await self.msg(host, 'room')
        guest = await self.socket()
        await self.put(guest, t='join', code=h['code'])
        g = await self.msg(guest, 'seat')
        await self.msg(guest, 'room'); await self.msg(host, 'room')
        # Connected guests cannot be kicked by the recovery action.
        await self.put(host, t='reopen')
        self.assertIn('must be disconnected', (await self.msg(host, 'error'))['message'])
        await self.put(guest, t='reopen')
        self.assertEqual((await self.msg(guest, 'error'))['t'], 'error')
        await self.put(host, t='ready', ready=True)
        await self.msg(host, 'room'); await self.msg(guest, 'room')
        await self.put(guest, t='ready', ready=True)
        await self.msg(host, 'room'); await self.msg(guest, 'room')
        await self.msg(host, 'begin'); await self.msg(guest, 'begin')
        await guest.close()
        self.assertEqual((await self.msg(host, 'peer_left'))['role'], 'guest')
        status = await self.msg(host, 'room')
        self.assertEqual(status['phase'], 'fighting')
        self.assertFalse(status['guest']['online'])
        await self.put(host, t='reopen')
        status = await self.msg(host, 'room')
        self.assertEqual(status['phase'], 'lobby')
        self.assertIsNone(status['guest'])
        self.assertFalse(status['host']['ready'])
        # Old tokens cannot steal the newly available seat.
        old = await self.socket()
        await self.put(old, t='resume', code=h['code'], token=g['token'])
        self.assertIn('expired', (await self.msg(old, 'error'))['message'])
        replacement = await self.socket()
        await self.put(replacement, t='join', code=h['code'])
        new_seat = await self.msg(replacement, 'seat')
        await self.msg(replacement, 'room')
        await self.msg(host, 'room')
        self.assertNotEqual(new_seat['token'], g['token'])

    async def test_cross_site_websocket_is_rejected(self):
        with self.assertRaises(WSServerHandshakeError) as raised:
            await self.client.ws_connect(
                f'http://127.0.0.1:{self.port}/ws',
                headers={'Origin': 'https://not-our-game.example'})
        self.assertEqual(raised.exception.status, 403)
        same = await self.client.ws_connect(
            f'http://127.0.0.1:{self.port}/ws',
            headers={'Origin': f'http://127.0.0.1:{self.port}'})
        self.sockets.append(same)
        await self.put(same, t='create')
        await self.msg(same, 'seat'); await self.msg(same, 'room')
