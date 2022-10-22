# rextlib - Reply Error

from typing import Any


__all__ = ("ReplyError", "BadRequest", "NotFound")


class ReplyError(Exception):
    "エラーを発生させて返信をするというのに使うためのエラーです。"

    status = 400

    def __init__(
        self, text: str | dict[str, str] | Any,
        status: int | None = None, *args, **kwargs
    ):
        self.text = text
        if status is not None:
            self.status = status
        self.kwargs = kwargs
        super().__init__(self.text, *args)


class BadRequest(ReplyError):
    ...
class NotFound(ReplyError):
    status = 404