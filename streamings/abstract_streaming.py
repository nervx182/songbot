from abc import ABC, abstractmethod


class SongResult:
    def __init__(self, name, artist, url, image):
        self.name = name
        self.artist = artist
        self.url = url
        self.image = image


class AbstractStreaming(ABC):
    @abstractmethod
    def search(self, req: str) -> list[SongResult]:
        raise NotImplementedError

    @abstractmethod
    def command_code(self) -> str:
        raise NotImplementedError