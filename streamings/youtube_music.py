from ytmusicapi import YTMusic

from streamings.abstract_streaming import AbstractStreaming, SongResult


class YoutubeMusic(AbstractStreaming):

    def __init__(self):
        self.client = YTMusic()

    def command_code(self) -> str:
        return 'YT'

    def search(self, req: str) -> list[SongResult]:
        results = self.client.search(req, filter='songs')

        if not results:
            return []

        song_results = map(lambda song: SongResult(
            song['title'],
            song['artists'][0]['name'],
            f"https://music.youtube.com/watch?v={song['videoId']}",
            song['thumbnails'][-1]['url']
        ), results)

        return list(song_results)
