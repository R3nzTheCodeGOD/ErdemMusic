import aiohttp, asyncio, base64, logging, logging, time, sys
sys.path.append('../')
from config.ayarlar import client_id, client_secret

class Spotify:
    OAUTH_TOKEN_URL = 'https://accounts.spotify.com/api/token'
    API_BASE = 'https://api.spotify.com/v1/'

    def __init__(self, aiosession=None, loop=None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.aiosession = aiosession if aiosession else aiohttp.ClientSession()
        self.loop = loop if loop else asyncio.get_event_loop()

        self.token = None

        self.loop.run_until_complete(self.get_token())  

    def _make_token_auth(self, client_id, client_secret):
        auth_header = base64.b64encode((client_id + ':' + client_secret).encode('ascii'))
        return {'Authorization': 'Basic %s' % auth_header.decode('ascii')}

    async def get_track(self, uri):
        return await self.make_spotify_req(self.API_BASE + 'tracks/{0}'.format(uri))

    async def get_album(self, uri):
        return await self.make_spotify_req(self.API_BASE + 'albums/{0}'.format(uri))

    async def get_playlist(self, user, uri):
        return await self.make_spotify_req(self.API_BASE + 'users/{0}/playlists/{1}{2}'.format(user, uri))
    
    async def get_playlist_tracks(self, uri):
        return await self.make_spotify_req(self.API_BASE + 'playlists/{0}/tracks'.format(uri))

    async def make_spotify_req(self, url):
        token = await self.get_token()
        return await self.make_get(url, headers={'Authorization': 'Bearer {0}'.format(token)})

    async def make_get(self, url, headers=None):
        async with self.aiosession.get(url, headers=headers) as r:
            if r.status != 200:
                print("Make_get hata")
            return await r.json()

    async def make_post(self, url, payload, headers=None):
        async with self.aiosession.post(url, data=payload, headers=headers) as r:
            if r.status != 200:
                print("make_post hata")
            return await r.json()

    async def get_token(self):
        if self.token and not await self.check_token(self.token):
            return self.token['access_token']

        token = await self.request_token()
        if token is None:
            print("hata")
        token['expires_at'] = int(time.time()) + token['expires_in']
        self.token = token
        return self.token['access_token']

    async def check_token(self, token):
        now = int(time.time())
        return token['expires_at'] - now < 60

    async def request_token(self):
        payload = {'grant_type': 'client_credentials'}
        headers = self._make_token_auth(self.client_id, self.client_secret)
        r = await self.make_post(self.OAUTH_TOKEN_URL, payload=payload, headers=headers)
        return r
