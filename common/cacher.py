# rextlib - Cacher, キャッシュ管理

from __future__ import annotations

from typing import Generic, TypeVar, Any, Optional
from collections.abc import Iterator, Callable, Hashable

from threading import Thread
from time import time, sleep


__all__ = ("Cache", "Cacher", "CacherPool")


DataT = TypeVar("DataT")
class Cache(Generic[DataT]):
    "キャッシュのデータを格納するためのクラスです。"

    def __init__(self, data: DataT, deadline: Optional[float] = None):
        self.data, self.deadline = data, deadline

    def set_deadline(self, deadline: float) -> None:
        "寿命を上書きします。"
        self.deadline = deadline

    def update_deadline(self, seconds: float, now: Optional[float] = None) -> None:
        "寿命を更新します。(加算されます。)"
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

    def __init__(
        self, lifetime: Optional[float] = None,
        default: Optional[Callable[[], Any]] = None,
        on_dead: Callable[[KeyT, ValueT], Any] = lambda _, __: ...,
        auto_update_deadline: bool = True
    ):
        self.data: dict[KeyT, Cache[ValueT]] = {}
        self.lifetime, self.default = lifetime, default
        self.on_dead, self.auto_update_deadline = on_dead, auto_update_deadline

        self.pop = self.data.pop
        self.keys = self.data.keys

    def clear(self) -> None:
        "空にします。"
        for key in set(self.data.keys()):
            self.on_dead(key, self.data[key].data)
            del self.data[key]

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

    def set_deadline(self, key: KeyT, deadline: float) -> None:
        "指定されたデータの寿命を上書きします。"
        self.data[key].set_deadline(deadline)

    def __getitem__(self, key: KeyT) -> ValueT:
        self._default(key)
        data = self.data[key].data
        if self.auto_update_deadline:
            self.update_deadline(key)
        return data

    def __getattr__(self, key: KeyT) -> ValueT:
        return self[key]

    def __delitem__(self, key: KeyT) -> None:
        self.on_dead(key, self.data[key].data)
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


class CacherPool(Thread):
    "Cacherのプールです。"

    def __init__(self, *args, **kwargs):
        self.cachers: list[Cacher[Any, Any]] = []
        self._close = False
        kwargs.setdefault("daemon", True)
        super().__init__(*args, **kwargs)

    def acquire(
        self, lifetime: Optional[float] = None,
        *args: Any, **kwargs: Any
    ) -> Cacher[Any, Any]:
        "Cacherを生み出します。"
        self.cachers.append(Cacher(lifetime, *args, **kwargs))
        return self.cachers[-1]

    def release(self, cacher: Cacher[Any, Any]) -> None:
        "指定されたCacherを削除します。"
        self.cachers.remove(cacher)

    def close(self) -> None:
        "CacherPoolのお片付けをします。"
        self._close = True
        self.join()

    def run(self):
        while not self._close:
            now = time()
            for cacher in self.cachers:
                if self._close:
                    break
                for key, value in list(cacher.data.items()):
                    if value.is_dead(now):
                        del cacher[key]
            sleep(0.5)