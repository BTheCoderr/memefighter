"""Real WebSocket checks for host browser refresh recovery."""
import asyncio
import unittest
from test_relay import RelayTests

class HostRefreshTests(unittest.IsolatedAsyncioTestCase):
    asyncSetUp = RelayTests.asyncSetUp
    asyncTearDown = RelayTests.asyncTearDown
    socket = RelayTests.socket
    put = RelayTests.put
    msg = RelayTests.msg
    async def begin_match(self):
        host=await self.socket()
        await self.put(host,t='create')
        info=await self.msg(host,'seat'); await self.msg(host,'room')
        guest=await self.socket()
        await self.put(guest,t='join',code=info['code'])
        guest_info=await self.msg(guest,'seat'); await self.msg(guest,'room'); await self.msg(host,'room')
        await self.put(host,t='ready',ready=True)
        await self.msg(host,'room'); await self.msg(guest,'room')
        await self.put(guest,t='ready',ready=True)
        await self.msg(host,'room'); await self.msg(guest,'room')
        await self.msg(host,'begin'); await self.msg(guest,'begin')
        return host, guest, info,guest_info

    async def test_host_reload_keeps_round_health_and_timer(self):
        host,guest,info,_=await self.begin_match()
        snapshot={'players':[{'hp':37,'wins':1},{'hp':64,'wins':0}], 'time':24.1, 'pre':0,
                  'round':2,'screen':'fighting','projectiles':[],'elapsed':40}
        await self.put(host,t='snapshot',state=snapshot)
        await self.msg(guest,'snapshot')
        await host.close()
        await self.msg(guest,'peer_left')
        paused=await self.msg(guest,'room')
        self.assertTrue(paused['recovering'])
        new_host=await self.socket()
        await self.put(new_host,t='resume',code=info['code'],token=info['token'],playing=False)
        await self.msg(new_host,'seat')
        self.assertEqual((await self.msg(new_host,'room'))['phase'],'fighting')
        self.assertEqual((await self.msg(guest,'room'))['recovering'],True)
        restored=await self.msg(new_host,'recover')
        self.assertEqual(restored['state']['time'],24.1)
        self.assertEqual(restored['state']['players'][0]['hp'],37)
        self.assertEqual(restored['state']['round'],2)
        # Guest cannot unblock the host simulation.
        await self.put(guest,t='resume_ready')
        self.assertIn('unavailable',(await self.msg(guest,'error'))['message'])
        # Host may not write new snapshots during recovery phase.
        await self.put(new_host,t='snapshot',state={'players':[{'hp':0},{'hp':0}]})
        self.assertEqual(__import__('server').ROOMS[info['code']].snapshot['players'][0]['hp'],37)
        await self.put(new_host,t='resume_ready')
        self.assertFalse((await self.msg(new_host,'room'))['recovering'])
        self.assertFalse((await self.msg(guest,'room'))['recovering'])
        replay=await self.msg(guest,'snapshot')
        self.assertEqual(replay['state']['players'][1]['hp'],64)
        self.assertEqual(__import__('server').ROOMS[info['code']].snapshot['time'],24.1)

    async def test_guest_reload_gets_latest_snapshot(self):
        host,guest,info,ginfo=await self.begin_match()
        snap={'players':[{'hp':98},{'hp':12}],'time':7}
        await self.put(host,t='snapshot',state=snap)
        await self.msg(guest,'snapshot')
        await guest.close()
        await self.msg(host,'peer_left'); await self.msg(host,'room')
        new_guest=await self.socket()
        await self.put(new_guest,t='resume',code=info['code'],token=ginfo['token'])
        await self.msg(new_guest,'seat')
        summary=await self.msg(new_guest,'room')
        self.assertEqual(summary['phase'],'fighting')
        await self.msg(host,'room')
        state=await self.msg(new_guest,'snapshot')
        self.assertEqual(state['state']['players'][1]['hp'],12)

    async def test_no_snapshot_falls_back_to_lobby(self):
        host,guest,info,_=await self.begin_match()
        await host.close()
        await self.msg(guest,'peer_left'); await self.msg(guest,'room')
        new_host=await self.socket()
        await self.put(new_host,t='resume',code=info['code'],token=info['token'])
        await self.msg(new_host,'seat')
        self.assertEqual((await self.msg(new_host,'room'))['phase'],'lobby')
        self.assertEqual((await self.msg(guest,'room'))['phase'],'lobby')

if __name__=='__main__':unittest.main()