"Rext Lib Cacher Impl - Dict Cacher"

from __future__ import annotations

from typing import TypeVar, Generic, Any, overload
from collections.abc import Iterator, Hashable, KeysView, ValuesView, \
    ItemsView, MutableMapping, Callable

from collections import defaultdict
from time import time

from ..common import Container, Cache, _TEDIOUS


__all__ = ("DictCache", "ValuesViewForDictCache", "ItemsViewForDictCache")


KeyT, ValueT = TypeVar("KeyT", bound=Hashable), TypeVar("ValueT")


class ValuesViewForDictCache(Generic[ValueT], ValuesView[ValueT]):
    "`.DictCache`のための`.ValuesView`の実装です。"

    def __init__(self, original: ValuesView[Container[ValueT]]) -> None:
        self.original = original

    def __contains__(self, value: ValueT) -> bool:
        return any(value == cache.body for cache in self.original)

    def __iter__(self) -> Iterator[ValueT]:
        return (cache.body for cache in self.original)

class ItemsViewForDictCache(Generic[KeyT, ValueT], ItemsView[KeyT, ValueT]):
    "`.DictCache`のための`.ItemsView`の実装です。"

    def __init__(self, original: ItemsView[KeyT, Container[ValueT]]) -> None:
        self.original = original

    def __contains__(self, value: tuple[KeyT, ValueT]) -> bool:
        return any(
            value[0] == key and value[1] == cache.body
            for key, cache in self.original
        )

    def __iter__(self) -> Iterator[tuple[KeyT, ValueT]]:
        return ((key, cache.body) for key, cache in self.original)

Undefined, DCgT = type("Undefined", (), {}), TypeVar("DCgT")
class DictCache(Cache, Generic[KeyT, ValueT], MutableMapping[KeyT, ValueT]):
    "辞書のように使える用に実装した`.Cache`のサブクラスです。"

    def __init__(
        self, *args: Any,
        data_cls: Callable[
            [], dict | defaultdict
        ] = dict,
        **kwargs: Any
    ) -> None:
        super().__init__(*args, **kwargs)
        self.data: MutableMapping[KeyT, Container[ValueT]] = data_cls()

    def on_dead(self, key: KeyT, value: ValueT) -> Any:
        pass

    def delete_bypass_on_dead(self, key: KeyT) -> None:
        del self.data[key]

    def update_deadline(
        self, seconds: float | None, key: KeyT,
        *args: Any, **kwargs: Any
    ) -> None:
        self.data[key].update_deadline(
            seconds or self.lifetime or 0.,
            *args, **kwargs
        )

    def update_deadline_for_core(
        self, key: KeyT,
        *args: Any,
        **kwargs: Any
    ) -> None:
        if self.auto_update_deadline and self.lifetime is not None:
            self.update_deadline(None, key, *args, **kwargs)

    def set_deadline(self, key: KeyT, *args: Any, **kwargs: Any) -> None:
        self.data[key].set_deadline(*args, **kwargs)

    def clean(self) -> None:
        now = time()
        for key in {key for key in self.keys() if self.data[key].is_dead(now)}:
            del self[key]

    def __getitem__(self, key: KeyT) -> ValueT:
        self.update_deadline_for_core(key)
        return self.data[key].body

    def __setitem__(self, key: KeyT, value: ValueT) -> None:
        if key in self.data:
            self.data[key].body = value
            self.update_deadline_for_core(key)
        else:
            self.data[key] = self.make_container(value)

    def __delitem__(self, key: KeyT) -> None:
        self.on_dead(key, self.data.pop(key).body)

    def __iter__(self) -> KeysView[KeyT]:
        return self.keys()

    def keys(self) -> KeysView[KeyT]:
        return self.data.keys()

    def values(self) -> ValuesViewForDictCache[ValueT]:
        return ValuesViewForDictCache(self.data.values())

    def __contains__(self, key: KeyT) -> bool:
        return key in self.data

    def __len__(self) -> int:
        return len(self.data)

    def items(self) -> ItemsViewForDictCache:
        return ItemsViewForDictCache(self.data.items())

    @overload
    def get(
        self, key: KeyT,
        default: type[Undefined]
            = Undefined
    ) -> ValueT | None: ...
    @overload
    def get(
        self, key: KeyT,
        default: DCgT
    ) -> ValueT | DCgT: ...
    def get(
        self, key: KeyT,
        default: DCgT | type[Undefined]
            = Undefined
    ) -> ValueT | DCgT:
        if key not in self.data:
            if default == Undefined:
                default = None # type: ignore
            return default # type: ignore
        self.update_deadline_for_core(key)
        return self.data[key].body

    def __eq__(self, other: DictCache) -> bool:
        return self.data == other.data

    def __ne__(self, other: DictCache) -> bool:
        return self.data != other.data

    @overload
    def pop(
        self, key: KeyT,
        default: type[Undefined]
            = Undefined
    ) -> ValueT: ...
    @overload
    def pop(
        self, key: KeyT,
        default: DCgT
    ) -> ValueT | DCgT: ...
    def pop(
        self, key: KeyT, default:
            DCgT | type[Undefined]
                = Undefined
    ) -> ValueT | DCgT:
        if (value := self.get(key, default)) == default:
            return default # type: ignore
        del self.data[key]
        return value # type: ignore

    def popitem(self) -> tuple[KeyT, ValueT]:
        key, value = self.data.popitem()
        return key, value.body

    def clear(self) -> None:
        for key in self.keys():
            del self[key]

    def update(self, *_: Any, **__: Any) -> None:
        raise _TEDIOUS

    def setdefault(self) -> None:
        raise _TEDIOUS

    def __str__(self) -> str:
        return self.new_special_str(f"data={self.data}")