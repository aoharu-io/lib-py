# rextlib - Cacher, キャッシュ管理

from __future__ import annotations

from typing import Generic, TypeVar, Any, overload, cast
from collections.abc import Iterator, Callable, Hashable

from threading import Thread
from asyncio import Event

from dataclasses import dataclass

from time import time, sleep


__all__ = ("Cache", "Cacher", "CacherPool")


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


DataT = TypeVar("DataT")
class Cache(Generic[DataT]):
    "キャッシュのデータを格納するためのクラスです。"

    def __init__(self, data: DataT, deadline: float | None = None):
        self.data, self.deadline = data, deadline

    def set_deadline(self, deadline: float) -> None:
        "寿命を上書きします。"
        self.deadline = deadline

    def update_deadline(self, seconds: float, now: float | None = None) -> None:
        "寿命を更新します。(加算されます。)"
        self.deadline = (now or time()) + seconds

    def is_dead(self, time_: float | None = None) -> bool:
        "死んだキャッシュかどうかをチェックします。"
        return self.deadline is not None and (time_ or time()) > self.deadline

    def __str__(self) -> str:
        return f"<Cache data={type(self.data)} deadline={self.deadline}>"

    def __repr__(self) -> str:
        return str(self)


KeyT, ValueT = TypeVar("KeyT", bound=Hashable), TypeVar("ValueT")
PopT, Undefined = TypeVar("PopT"), type("Undefined", (), {})
class Cacher(Generic[KeyT, ValueT]):
    """キャッシュを管理するためのクラスです。
    注意：引数`lifetime`を使用する場合は、CacherPoolと兼用しないとデータは自然消滅しません。
    `on_dead`はデフォルトではデータを消す関数が設定されます。"""

    def __init__(
        self, lifetime: float | None = None,
        default: Callable[[], Any] | None = None,
        on_dead: Callable[[KeyT, ValueT], Any] | None = None,
        auto_update_deadline: bool = True
    ):
        self.data: dict[KeyT, Cache[ValueT]] = {}
        self.lifetime, self.default = lifetime, default
        self.on_dead = on_dead or self.default_on_dead
        self.auto_update_deadline = auto_update_deadline
        self.cleaned = CountableEvent(0, 2)

        self.keys = lambda: self.data.keys()

    @overload
    def pop(
        self, key: KeyT, default: PopT = ...
    ) -> ValueT | PopT: ...
    @overload
    def pop(
        self, key: KeyT, default: type[Undefined] = Undefined
    ) -> ValueT: ...
    def pop(
        self, key: KeyT, default:
            PopT | type[Undefined]
                = Undefined
    ) -> ValueT | PopT:
        "値を消して取り出します。defaultが指定されている場合は、それが返されます。"
        try:
            data = self[key]
        except KeyError:
            if default == Undefined:
                raise KeyError(key)
            data = default
        else:
            self.on_dead(key, data)
        return data # type: ignore

    def default_on_dead(self, key: KeyT, _) -> None:
        """コンストラクタの引数`on_dead`のデフォルトの実装です。
        データを消します。"""
        del self.data[key]

    def clear(self) -> None:
        "空にします。"
        for key in set(self.data.keys()):
            self.on_dead(key, self.data[key].data)

    def set(self, key: KeyT, data: ValueT, lifetime: float | None = None) -> None:
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

    def update_deadline(self, key: KeyT, additional: float | None = None) -> None:
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


TpcT = TypeVar("TpcT", bound=Cacher)
class CacherPool(Thread):
    "Cacherのプールです。"

    def __init__(self, *args, **kwargs):
        self.cachers: list[Cacher[Any, Any]] = []
        self._close = False
        kwargs.setdefault("daemon", True)
        super().__init__(*args, **kwargs)

    def acquire(
        self, *args: Any, cls: type[TpcT]
            = Cacher, **kwargs: Any
    ) -> TpcT:
        "Cacherを生み出します。"
        self.cachers.append(cls(*args, **kwargs))
        return cast(TpcT, self.cachers[-1])

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
                cacher.cleaned.set()
                cacher.cleaned.clear()
            sleep(0.5)