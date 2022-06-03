# rtlib - Utils

from typing import Any
from collections.abc import Callable

from traceback import TracebackException


__all__ = (
    "make_error_message", "make_simple_error_text", "code_block",
    "to_dict_for_dataclass", "text_format"
)


def make_error_message(error: Exception) -> str:
    "渡されたエラーから全文を作ります。"
    return "".join(TracebackException.from_exception(error).format())


def make_simple_error_text(error: Exception) -> str:
    "渡されたエラーから名前とエラー内容の文字列にします。"
    return f"{error.__class__.__name__}: {error}"


def code_block(code: str, type_: str = "") -> str:
    "渡された文字列をコードブロックで囲みます。"
    return f"```{type_}\n{code}\n```"


to_dict_for_dataclass: Callable[..., dict[str, Any]] = lambda self: {
    key: getattr(self, key) for key in self.__class__.__annotations__.keys()
}
"データクラスのデータを辞書として出力する`to_dict`を作成します。"


def text_format(text: dict[str, str], **kwargs: str) -> dict[str, str]:
    "辞書の全ての値に`.format(**kwargs)`をします。"
    for key in text.keys():
        text[key] = text[key].format(**kwargs)
    return text