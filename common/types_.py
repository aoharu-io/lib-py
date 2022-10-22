# rextlib - Types

from typing import TypeAlias
from collections.abc import Callable, Coroutine


CoroutineFunction: TypeAlias = Callable[..., Coroutine]