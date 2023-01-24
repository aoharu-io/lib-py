"Rext Lib Cacher Impl - Set Cacher"

from __future__ import annotations

from typing import TypeVar, Generic, Any
from collections.abc import Iterator, Hashable, MutableSet

from time import time

from ..common import Container, Cache, _TEDIOUS


__all__ = ("MutableSetCache",)


ValueT = TypeVar("ValueT", bound=Hashable)
class MutableSetCache(Cache, Generic[ValueT], MutableSet[ValueT]):
    "集合のように使える`.Cacher`の実装です。"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.data = set[Container[ValueT]]()

    def on_dead(self, value: ValueT) -> Any:
        super().on_dead(value)

    def delete_bypass_on_dead(self, value: ValueT) -> None:
        self._remove(value, False)

    def get_raw(self, value: ValueT) -> Container[ValueT]:
        for cache in self.data:
            if cache.body == value:
                return cache
        raise KeyError("値が見つかりませんでした。")

    def update_deadline(
        self, seconds: float | None,
        value: ValueT,
        *args: Any,
        **kwargs: Any
    ) -> None:
        self.get_raw(value).update_deadline(
            seconds or self.lifetime or 0.,
            *args, **kwargs
        )

    def update_deadline_for_core(
        self, value: ValueT,
        *args: Any, **kwargs: Any
    ) -> None:
        if self.auto_update_deadline and self.lifetime is not None:
            self.update_deadline(None, value, *args, **kwargs)

    def set_deadline(self, value: ValueT, *args: Any, **kwargs: Any) -> None:
        self.get_raw(value).set_deadline(*args, **kwargs)

    def clean(self) -> None:
        now = time()
        for cache in {cache for cache in self.data if cache.is_dead(now)}:
            self.remove(cache.body)
        super().clean()

    def __contains__(self, value: ValueT) -> bool:
        return any(value == cache.body for cache in self.data)

    def __iter__(self) -> Iterator[ValueT]:
        return (cache.body for cache in self.data)

    def __len__(self) -> int:
        return len(self.data)

    def __le__(self, *_, **__): raise _TEDIOUS
    def __lt__(self, *_, **__): raise _TEDIOUS
    
    def __eq__(self, other: MutableSetCache) -> bool:
        return self.data == other.data
    def __ne__(self, other: MutableSetCache) -> bool:
        return self.data != other.data
    
    def __gt__(self, *_, **__): raise _TEDIOUS
    def __ge__(self, *_, **__): raise _TEDIOUS
    def __and__(self, *_, **__): raise _TEDIOUS
    def __or__(self, *_, **__): raise _TEDIOUS
    def __sub__(self, *_, **__): raise _TEDIOUS
    def __xor__(self, *_, **__): raise _TEDIOUS
    def isdisjoint(self, *_, **__): raise _TEDIOUS

    def discard(self, value: ValueT) -> None:
        try:
            self.remove(value)
        except KeyError:
            pass

    def _remove(self, value: ValueT, call_on_dead: bool = True) -> None:
        for tentative in self.data:
            if tentative.body == value:
                self.data.remove(tentative)
                if call_on_dead:
                    self.on_dead(tentative.body)
                break
        else:
            raise KeyError("値が見つかりませんでした。")

    def remove(self, value: ValueT) -> None:
        for tentative in self.data:
            if tentative.body == value:
                self.on_dead(tentative.body)
                break
        else:
            raise KeyError("値が見つかりませんでした。")

    def add(self, value: ValueT) -> None:
        self.data.add(self.make_container(value))

    def __ior__(self, *_, **__): raise _TEDIOUS
    def __iand__(self, *_, **__): raise _TEDIOUS
    def __ixor__(self, *_, **__): raise _TEDIOUS
    def __isub__(self, *_, **__): raise _TEDIOUS

    def __str__(self) -> str:
        return self.new_special_str(f"data={self.data}")