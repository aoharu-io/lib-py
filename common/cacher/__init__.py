# rextlib - Cacher, キャッシュ管理

from __future__ import annotations

from typing import TypeVar, Any

from threading import Thread
from asyncio import Event

from dataclasses import dataclass

from time import sleep

from .common import Container, Cache
from .impl.dict_ import DictCache
from .impl.set_ import MutableSetCache


__all__ = ("Container", "Cache", "DictCache", "MutableSetCache", "Cacher")


@dataclass
class CountableEvent(Event):
    "回数を数えて何回目で`set`するみたいなことができる`.Event`です。"

    first_count: int
    count_to_set: int

    def __post_init__(self) -> None:
        self.count = self.first_count
        super().__init__()

    def set(self) -> None:
        self.count += 1
        if self.count == self.count_to_set:
            self.count = self.first_count
            super().set()


TpcT = TypeVar("TpcT", bound=Cache)
class Cacher(Thread):
    """`.Cacher`を管理するためのクラスです。
    これは`.Thread`を継承していて、それを動かすことで、登録した`.Cacher`のキャッシュの期限切れデータを自動で削除するようになります。"""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.caches = list[Cache]()
        self._close = False
        kwargs.setdefault("daemon", True)
        super().__init__(*args, **kwargs)

    def register(self, cache: TpcT) -> TpcT:
        "Cacherを生み出します。"
        self.caches.append(cache)
        return cache

    def delete(self, cache: Cache) -> None:
        "指定されたCacherを削除します。"
        self.caches.remove(cache)

    def close(self) -> None:
        "CacherPoolのお片付けをします。"
        self._close = True
        self.join()

    def run(self):
        while not self._close:
            for cacher in self.caches:
                if self._close:
                    break
                cacher.clean()
            else:
                sleep(0.5)
                continue

    def __str__(self) -> str:
        return f"<Cacher caches={self.caches} thread={super()}>"