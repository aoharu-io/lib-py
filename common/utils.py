# rtlib - Utils

from traceback import TracebackException


__all__ = ("make_error_message",)


def make_error_message(error: Exception) -> str:
    "渡されたエラーから全文を作ります。"
    return "".join(TracebackException.from_exception(error).format())