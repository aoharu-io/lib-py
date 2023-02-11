"Rext Lib Cacher Impl - List"

from typing import TypeVar, Generic, Self, Any, overload
from collections.abc import MutableSequence, Callable, Iterator

from ..common import Container, Cache


ValueT = TypeVar("ValueT")
class ListCache(Cache, MutableSequence[ValueT], Generic[ValueT]):
    def __init__(
        self, *args: Any, data_cls: Callable[[Self],
            MutableSequence[Container[Any]]
        ] = list, **kwargs: Any
    ) -> None:
        super().__init__(*args, **kwargs)
        self.data_cls = data_cls
        self.data: MutableSequence[Container[ValueT]] = data_cls(self)

    def get_raw(self, index_or_slice: int | slice) -> Iterator[Container[ValueT]]:
        "生データを取得します。"
        raw = self.data[index_or_slice]
        if isinstance(raw, Container):
            raw = (raw,)
        for c in raw:
            yield c

    def update_deadline(
        self, seconds: float | None,
        index_or_slice_or_container: int
            | slice | Container[ValueT]
    ) -> None:
        seconds = seconds or self.lifetime or 0.
        if isinstance(index_or_slice_or_container, Container):
            index_or_slice_or_container.update_deadline(seconds)
        else:
            for c in self.get_raw(index_or_slice_or_container):
                c.update_deadline(seconds)

    def update_deadline_for_core(
        self, index_or_slice_or_container:
            int | slice | Container[ValueT]
    ) -> None:
        if self.auto_update_deadline and self.lifetime is not None:
            self.update_deadline(self.lifetime, index_or_slice_or_container)

    def set_deadline(
        self, index_or_slice: int | slice,
        *args: Any, **kwargs: Any
    ) -> None:
        for c in self.get_raw(index_or_slice):
            c.set_deadline(*args, **kwargs)

    def delete_bypass_on_dead(self, index_or_slice: int | slice) -> None:
        del self.data[index_or_slice]

    @overload
    def __getitem__(self, index_or_slice: slice) -> MutableSequence[ValueT]: ...
    @overload
    def __getitem__(self, index_or_slice: int) -> ValueT: ...
    def __getitem__(self, index_or_slice: int | slice) \
            -> ValueT | MutableSequence[ValueT]:
        if isinstance(index_or_slice, int):
            self.update_deadline_for_core(self.data[index_or_slice])
            return self.data[index_or_slice].body
        else:
            return self.data_cls(self).extend(map(
                lambda c: c.body, self.get_raw(index_or_slice)
                # type: ignore
            ))