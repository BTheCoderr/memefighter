import unittest
from aiohttp.test_utils import AioHTTPTestCase
from server import create_app


class PublicPagesTest(AioHTTPTestCase):
    async def get_application(self):
        return create_app()

    async def test_privacy_notice_is_accessible_without_login(self):
        resp = await self.client.request('GET', '/privacy')
        self.assertEqual(resp.status, 200)
        content = await resp.text()
        self.assertIn("Your fights. Your privacy.", content)
        self.assertIn("room code", content)

    async def test_support_page_is_accessible_without_login(self):
        resp = await self.client.request('GET', '/support')
        self.assertEqual(resp.status, 200)
        content = await resp.text()
        self.assertIn("Need backup in the arena?", content)
        self.assertIn("github.com/BTheCoderr/memefighter/issues", content)
