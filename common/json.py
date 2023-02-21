"rextlib - JSON"

__all__ = ("loads", "dumps")

from orjson import dumps as original_dumps, loads


dumps = lambda content, *args, **kwargs: \
    original_dumps(content, *args, **kwargs).decode()
"`orjson.dumps`を文字列で返すようにしたものです。"