# rextlib - Utils

from typing import TypeVar, TypedDict, Any
from collections.abc import Callable, Iterator, Sized

from traceback import TracebackException

from psutil import cpu_percent, virtual_memory


__all__ = (
    "make_error_message", "make_simple_error_text", "code_block",
    "to_dict_for_dataclass", "format_text", "map_length",
    "PerformanceStatistics", "take_performance_statistics"
)


def make_error_message(error: BaseException) -> str:
    "渡されたエラーから全文を作ります。"
    return "".join(TracebackException.from_exception(error).format())


def make_simple_error_text(error: BaseException) -> str:
    "渡されたエラーから名前とエラー内容の文字列にします。"
    return f"{error.__class__.__name__}: {error}"


def code_block(code: str, type_: str = "") -> str:
    "渡された文字列をコードブロックで囲みます。"
    return f"```{type_}\n{code}\n```"


to_dict_for_dataclass: Callable[..., dict[str, Any]] = lambda self: {
    key: getattr(self, key) for key in self.__class__.__annotations__.keys()
}
"データクラスのデータを辞書として出力する`to_dict`を作成します。"


def format_text(text: dict[str, str], **kwargs: str) -> dict[str, str]:
    "辞書の全ての値に`.format(**kwargs)`をします。"
    for key in text.keys():
        text[key] = text[key].format(**kwargs)
    return text


KeyT, ValueT = TypeVar("KeyT"), TypeVar("ValueT", bound=Sized)
def map_length(data: dict[KeyT, ValueT]) -> Iterator[tuple[tuple[KeyT, ValueT], int]]:
    "渡された辞書の`.items`で返されるタプルと値の大きさの整数を入れたタプルを返すイテレーターを返します。"
    return map(lambda key: ((key, data[key]), len(data[key])), data.keys())


class PerformanceStatistics(TypedDict):
    "サーバーの動作状況をまとめた辞書の型です。"

    cpu: float
    "CPU使用率"
    memory: tuple[float, float, float]
    "メモリ使用量と未使用量、そして合計の三つが格納されたタプル"

def take_performance_statistics() -> PerformanceStatistics:
    "現在のサーバーの動作状況をまとめた辞書を返します。"
    memory = virtual_memory()
    return PerformanceStatistics(
        cpu=cpu_percent(interval=1),
        memory=(
            memory.used,
            memory.free,
            memory.total
        )
    )