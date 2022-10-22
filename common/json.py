# rextlib - JSON

from orjson import dumps as odumps, loads


dumps = lambda content, *args, **kwargs: odumps(content, *args, **kwargs).decode()
"`orjson.dumps`を文字列で返すようにしたものです。"