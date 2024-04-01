import yandex_music

from streamings.abstract_streaming import AbstractStreaming, SongResult


class YandexMusic(AbstractStreaming):

    def __init__(self):
        self.client = yandex_music.Client()

    def search(self, req: str) -> list[SongResult]:
        results = self.client.search(text=req)

        if not results.tracks:
            return []

        song_results = map(lambda song: SongResult(
            song.title,
            song.artists[0].name,
            f"https://music.yandex.ru/album/{song.albums[0].id}/track/{song.id}",
            song.get_cover_url()
        ), results.tracks.results)

        return list(song_results)
