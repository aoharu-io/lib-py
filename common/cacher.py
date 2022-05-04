# RT - Cacher, キャッシュ管理

from __future__ import annotations

from typing import Generic, TypeVar, Any, Optional
from collections.abc import Iterator, Callable, Hashable

from time import time

from discord.ext import tasks


__all__ = ("Cache", "Cacher", "CacherPool")


DataT = TypeVar("DataT")
class Cache(Generic[DataT]):
    "キャッシュのデータを格納するためのクラスです。"

    def __init__(self, data: DataT, deadline: Optional[float] = None):
        self.data, self.deadline = data, deadline

    def update_deadline(self, seconds: float, now: Optional[float] = None) -> None:
        "寿命を更新します。"
        self.deadline = (now or time()) + seconds

    def is_dead(self, time_: Optional[float] = None) -> bool:
        "死んだキャッシュかどうかをチェックします。"
        return self.deadline is None or (time_ or time()) > self.deadline

    def __str__(self) -> str:
        return f"<Cache data={type(self.data)} deadline={self.deadline}>"

    def __repr__(self) -> str:
        return str(self)


KeyT, ValueT = TypeVar("KeyT", bound=Hashable), TypeVar("ValueT")
class Cacher(Generic[KeyT, ValueT]):
    "キャッシュを管理するためのクラスです。\n注意：引数`lifetime`を使用する場合は、CacherPoolと兼用しないとデータは自然消滅しません。"

    def __init__(self, lifetime: Optional[float] = None, default: Optional[Callable[[], Any]] = None):
        self.data: dict[KeyT, Cache[ValueT]] = {}
        self.lifetime, self.default = lifetime, default

        self.pop = self.data.pop
        self.keys = self.data.keys

    def set(self, key: KeyT, data: ValueT, lifetime: Optional[float] = None) -> None:
        "値を設定します。\n別のライフタイムを指定することができます。"
        self.data[key] = Cache(
            data, None if self.lifetime is None and lifetime is None
            else time() + (lifetime or self.lifetime) # type: ignore
        )

    def __contains__(self, key: KeyT) -> bool:
        return key in self.data

    def _default(self, key: KeyT):
        if self.default is not None and key not in self.data:
            self.set(key, self.default())

    def update_deadline(self, key: KeyT, additional: Optional[float] = None) -> None:
        "指定されたデータの寿命を更新します。"
        if (new := additional or self.lifetime) is not None:
            self.data[key].update_deadline(new)

    def __getitem__(self, key: KeyT) -> ValueT:
        self._default(key)
        self.update_deadline(key)
        return self.data[key].data

    def __getattr__(self, key: KeyT) -> ValueT:
        return self[key]

    def __delitem__(self, key: KeyT) -> None:
        del self.data[key]

    def __delattr__(self, key: str) -> None:
        del self[key] # type: ignore

    def __setitem__(self, key: KeyT, value: ValueT) -> None:
        self.set(key, value)

    def values(self, mode_list: bool = False) -> Iterator[ValueT]:
        for value in list(self.data.values()) if mode_list else self.data.values():
            yield value.data

    def items(self, mode_list: bool = False) -> Iterator[tuple[KeyT, ValueT]]:
        for key, value in list(self.data.items()) if mode_list else self.data.items():
            yield (key, value.data)

    def get(self, key: KeyT, default: Any = None) -> ValueT:
        try: return self.data[key].data
        except KeyError: return default

    def get_raw(self, key: KeyT) -> Cache[ValueT]:
        "データが格納されたCacheを取得します。"
        self._default(key)
        return self.data[key]

    def __str__(self) -> str:
        return f"<Cacher data={type(self.data)} defaultLifetime={self.lifetime}>"

    def __repr__(self) -> str:
        return str(self)


class CacherPool:
    "Cacherのプールです。"

    def __init__(self):
        self.cachers: list[Cacher[Any, Any]] = []
        self._cache_remover.start()

    def acquire(
        self, lifetime: Optional[float] = None,
        default: Optional[Callable[[], Any]] = None
    ) -> Cacher[Any, Any]:
        "Cacherを生み出します。"
        self.cachers.append(Cacher(lifetime, default))
        return self.cachers[-1]

    def release(self, cacher: Cacher[Any, Any]) -> None:
        "指定されたCacherを削除します。"
        self.cachers.remove(cacher)

    @tasks.loop(seconds=5)
    async def _cache_remover(self):
        now = time()
        for cacher in self.cachers:
            for key, value in list(cacher.data.items()):
                if value.is_dead(now):
                    del cacher[key]

    def __del__(self):
        if self._cache_remover.is_running():
            self._cache_remover.cancel()