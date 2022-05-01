# rtlib - Utils

from collections.abc import AsyncIterator

from traceback import TracebackException

from aiomysql import Cursor


__all__ = ("make_error_message", "code_block")


def make_error_message(error: Exception) -> str:
    "渡されたエラーから全文を作ります。"
    return "".join(TracebackException.from_exception(error).format())


def code_block(code: str, type_: str = "") -> str:
    "渡された文字列をコードブロックで囲みます。"
    return f"```{type_}\n{code}\n```"