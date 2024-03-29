__all__ = ("Container", "CountableEvent", "Cache")

from typing import TypeVar, Self, Generic, Any
from collections.abc import Callable

from abc import ABC, abstractmethod
from dataclasses import dataclass

from asyncio import Event

from time import time


_TEDIOUS = NotImplementedError("めんどいので、この関数は実装されていません。")


DataT = TypeVar("DataT")
class Container(Generic[DataT]):
    "キャッシュのデータを格納するためのクラスです。"

    def __init__(self, body: DataT, deadline: float | None = None):
        self.body, self.deadline = body, deadline

    def set_deadline(self, deadline: float) -> Self:
        "寿命を上書きします。"
        self.deadline = deadline
        return self

    def update_deadline(self, seconds: float, now: float | None = None) -> Self:
        "寿命を更新します。(加算されます。)"
        self.deadline = (now or time()) + seconds
        return self

    def is_dead(self, time_: float | None = None) -> bool:
        "死んだキャッシュかどうかをチェックします。"
        return self.deadline is not None and (time_ or time()) > self.deadline

    def __str__(self) -> str:
        return f"<Container (of Cache) body={type(self.body)} deadline={self.deadline}>"

    def __repr__(self) -> str:
        return str(self)

    def __hash__(self) -> int:
        return hash(self.body)


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


class Cache(ABC):
    """キャッシュを管理するためのクラスの基底クラスですです。
    キャッシュのデータ構造に応じて実装を施す必要があります"""

    data: Any

    def __init__(
        self, lifetime: float | None, *,
        auto_update_deadline: bool = True,
        on_dead: Callable[..., None] | None = None
    ) -> None:
        self.lifetime, self.auto_update_deadline = lifetime, auto_update_deadline
        self.cleaned = CountableEvent(0, 2)
        self.cleaned.set()

        if on_dead is not None:
            self.don_dead = on_dead


    def on_dead(self, *args: Any, **kwargs: Any) -> Any:
        """キャッシュの寿命がつきた際に呼ばれる関数です。
        デフォルトの実装では`.delete`を呼び出すだけです。"""
        self.delete(*args, **kwargs)

    @abstractmethod
    def update_deadline(
        self, seconds: float | None,
        *args: Any, **kwargs: Any
    ) -> None:
        """期限を更新します。
        引数`.seconds`は、実行時の時間に加算される秒数で、`None`の場合は`.lifetime`（もしそれも`None`なら`0.`）が使われます。"""

    @abstractmethod
    def update_deadline_for_core(self, *args: Any, **kwargs: Any) -> None:
        """心臓部のための`.update_deadline`です。
        `.auto_update_deadline`が`False`の場合はこの関数は何もしないです。"""

    @abstractmethod
    def set_deadline(self, *args: Any, **kwargs: Any) -> None:
        "期限を設定します。"

    def clean(self) -> None:
        """掃除をします。
        デフォルトの実装では`.cleaned`の`set`メソッドを実行した後、`clear`メソッドを実行します。
        このデフォルトの実装は絶対実行されるべきです。"""
        self.cleaned.set()
        self.cleaned.clear()

    @abstractmethod
    def delete(self, *args: Any, **kwargs: Any) -> None:
        """データを消すのに使う関数です。
        キャッシュのデータを消す際は、これが呼ばれるべきです。
        例えば辞書で言うのなら`del data[key]`のようなときです。"""

    def make_deadline(self) -> float | None:
        "キャッシュのインスタンスの設定に合わせた期限を作成します。"
        return None if self.lifetime is None else time() + self.lifetime

    def make_container(
        self, value: DataT, deadline:
            float | None = None
    ) -> Container[DataT]:
        "キャッシュのコンテナを作ります。"
        return Container(value, deadline or self.make_deadline())

    def new_special_str(self, additional: str) -> str:
        """`Cache.__str__`の返す文字列の最後の`>`の左に空白と引数`additional`の値を入れます。
        `__str__`の実装に使ってください。"""
        return f'{Cache.__str__(self)[:-1]} {additional}>'

    def __str__(self) -> str:
        return "<%s lifetime=%s auto_update_deadline=%s cleaned=%s>" % (
            self.__class__.__name__, self.lifetime,
            self.auto_update_deadline, self.cleaned
        )