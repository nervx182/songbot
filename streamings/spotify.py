import datetime
from base64 import b64encode

import requests

from streamings.abstract_streaming import AbstractStreaming, SongResult


class Spotify(AbstractStreaming):

    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.token_expires = None

    def get_spotify_access_token(self) -> None:
        now = datetime.datetime.now()

        response = requests.post('https://accounts.spotify.com/api/token', data='grant_type=client_credentials',
                                 headers={
                                     'Content-Type': 'application/x-www-form-urlencoded',
                                     'Authorization': 'Basic {}'.format(
                                         b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode())
                                 })

        self.access_token = response.json()['access_token']

        secs = response.json()['expires_in']
        self.token_expires = now + datetime.timedelta(seconds=secs)

    def search(self, req: str) -> list[SongResult]:
        if not self.token_expires or self.token_expires <= datetime.datetime.now():
            self.get_spotify_access_token()

        resp = requests.get('https://api.spotify.com/v1/search',
                            headers={'Authorization': f"Bearer {self.access_token}"},
                            params={"q": req, "type": "track"})

        results = []

        if resp.status_code == 200 and resp.json()['tracks']:
            results = map(lambda t: SongResult(
                t['name'],
                t['artists'][0]['name'],
                t['external_urls']['spotify'],
                t['album']['images'][-1]['url']
            ), resp.json()['tracks']['items'])

        return list(results)
