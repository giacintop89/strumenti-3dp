"""Server-side sorting for list pages."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlencode

from flask import Request
from sqlalchemy import String, or_


def _missing(expression):
    if isinstance(getattr(expression, "type", None), String):
        return or_(expression.is_(None), expression == "")
    return expression.is_(None)


@dataclass(frozen=True)
class Column:
    order: Sequence[Any]
    desc_first: bool = False


@dataclass(frozen=True)
class Sort:
    key: str
    desc: bool
    columns: Mapping[str, Column] = field(repr=False)
    others: tuple[tuple[str, str], ...] = ()
    path: str = ""

    def href(self, key: str) -> str:
        column = self.columns.get(key)
        if column is None:
            return self.path
        desc = not self.desc if key == self.key else column.desc_first
        params = [*self.others, ("sort", key), ("dir", "desc" if desc else "asc")]
        return f"{self.path}?{urlencode(params)}"

    def state(self, key: str) -> str:
        if key != self.key:
            return ""
        return "desc" if self.desc else "asc"

    def apply(self, stmt):
        if not self.key:
            return stmt
        clauses = []
        for expression in self.columns[self.key].order:
            clauses.append(_missing(expression))
            clauses.append(expression.desc() if self.desc else expression)
        return stmt.order_by(*clauses)


def of(request: Request, columns: Mapping[str, Column], default: str = "") -> Sort:
    key = request.args.get("sort", "")
    if key not in columns:
        key = default if default in columns else ""
    direction = request.args.get("dir", "")
    desc = direction == "desc" if direction in ("asc", "desc") else columns[key].desc_first
    others = tuple(
        (name, value)
        for name, value in request.args.items(multi=True)
        if name not in ("sort", "dir")
    )
    return Sort(key=key, desc=desc, columns=columns, others=others, path=request.path)
