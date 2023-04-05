# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

import typing

import ibis
import ibis.common.exceptions
import ibis.expr.operations.generic
import ibis.expr.types as ibis_types

_ZERO = typing.cast(ibis_types.NumericValue, ibis_types.literal(0))

BinaryOp = typing.Callable[[ibis_types.Value, ibis_types.Value], ibis_types.Value]
TernaryOp = typing.Callable[
    [ibis_types.Value, ibis_types.Value, ibis_types.Value], ibis_types.Value
]


### Unary Ops
class UnaryOp:
    def _as_ibis(self, x):
        raise NotImplementedError("Base class AggregateOp has no implementaiton.")

    @property
    def is_windowed(self):
        return False


class AbsOp(UnaryOp):
    def _as_ibis(self, x: ibis_types.Value):
        return typing.cast(ibis_types.NumericValue, x).abs()


class InvertOp(UnaryOp):
    def _as_ibis(self, x: ibis_types.Value):
        return typing.cast(ibis_types.NumericValue, x).negate()


class IsNullOp(UnaryOp):
    def _as_ibis(self, x: ibis_types.Value):
        return x.isnull()


class LenOp(UnaryOp):
    def _as_ibis(self, x: ibis_types.Value):
        return typing.cast(ibis_types.StringValue, x).length()


class NotNullOp(UnaryOp):
    def _as_ibis(self, x: ibis_types.Value):
        return x.notnull()


class ReverseOp(UnaryOp):
    def _as_ibis(self, x: ibis_types.Value):
        return typing.cast(ibis_types.StringValue, x).reverse()


class LowerOp(UnaryOp):
    def _as_ibis(self, x: ibis_types.Value):
        return typing.cast(ibis_types.StringValue, x).lower()


class UpperOp(UnaryOp):
    def _as_ibis(self, x: ibis_types.Value):
        return typing.cast(ibis_types.StringValue, x).upper()


class StripOp(UnaryOp):
    def _as_ibis(self, x: ibis_types.Value):
        return typing.cast(ibis_types.StringValue, x).strip()


# Parameterized ops
class FindOp(UnaryOp):
    def __init__(self, sub, start, end):
        self._sub = sub
        self._start = start
        self._end = end

    def _as_ibis(self, x: ibis_types.Value):
        return typing.cast(ibis_types.StringValue, x).find(
            self._sub, self._start, self._end
        )


class SliceOp(UnaryOp):
    def __init__(self, start, stop):
        self._start = start
        self._stop = stop

    def _as_ibis(self, x: ibis_types.Value):
        return typing.cast(ibis_types.StringValue, x)[self._start : self._stop]


abs_op = AbsOp()
invert_op = InvertOp()
isnull_op = IsNullOp()
len_op = LenOp()
notnull_op = NotNullOp()
reverse_op = ReverseOp()
lower_op = LowerOp()
upper_op = UpperOp()
strip_op = StripOp()


### Binary Ops
def and_op(
    x: ibis_types.Value,
    y: ibis_types.Value,
):
    return typing.cast(ibis_types.BooleanValue, x) & typing.cast(
        ibis_types.BooleanValue, y
    )


def or_op(
    x: ibis_types.Value,
    y: ibis_types.Value,
):
    return typing.cast(ibis_types.BooleanValue, x) | typing.cast(
        ibis_types.BooleanValue, y
    )


def add_op(
    x: ibis_types.Value,
    y: ibis_types.Value,
):
    return typing.cast(ibis_types.NumericValue, x) + typing.cast(
        ibis_types.NumericValue, y
    )


def sub_op(
    x: ibis_types.Value,
    y: ibis_types.Value,
):
    return typing.cast(ibis_types.NumericValue, x) - typing.cast(
        ibis_types.NumericValue, y
    )


def mul_op(
    x: ibis_types.Value,
    y: ibis_types.Value,
):
    return typing.cast(ibis_types.NumericValue, x) * typing.cast(
        ibis_types.NumericValue, y
    )


def div_op(
    x: ibis_types.Value,
    y: ibis_types.Value,
):
    return typing.cast(ibis_types.NumericValue, x) / typing.cast(
        ibis_types.NumericValue, y
    )


def lt_op(
    x: ibis_types.Value,
    y: ibis_types.Value,
):
    return x < y


def le_op(
    x: ibis_types.Value,
    y: ibis_types.Value,
):
    return x <= y


def gt_op(
    x: ibis_types.Value,
    y: ibis_types.Value,
):
    return x > y


def ge_op(
    x: ibis_types.Value,
    y: ibis_types.Value,
):
    return x >= y


def floordiv_op(
    x: ibis_types.Value,
    y: ibis_types.Value,
):
    x_numeric = typing.cast(ibis_types.NumericValue, x)
    y_numeric = typing.cast(ibis_types.NumericValue, y)
    floordiv_expr = x_numeric // y_numeric
    # MOD(N, 0) will error in bigquery, but needs to return 0 in BQ so we short-circuit in this case.
    # Multiplying left by zero propogates nulls.
    return (
        ibis.case()
        .when(y_numeric == _ZERO, _ZERO * x_numeric)
        .else_(floordiv_expr)
        .end()
    )


def mod_op(
    x: ibis_types.Value,
    y: ibis_types.Value,
):
    x_numeric = typing.cast(ibis_types.NumericValue, x)
    y_numeric = typing.cast(ibis_types.NumericValue, y)
    # Hacky short-circuit to avoid passing zero-literal to sql backend, evaluate locally instead to 0.
    op = y.op()
    if isinstance(op, ibis.expr.operations.generic.Literal) and op.value == 0:
        return _ZERO * x_numeric  # Dummy op to propogate nulls and type from x arg

    bq_mod = x_numeric % y_numeric  # Bigquery will maintain x sign here
    # In BigQuery returned value has the same sign as X. In pandas, the sign of y is used, so we need to flip the result if sign(x) != sign(y)
    return (
        ibis.case()
        .when(
            y_numeric == _ZERO, _ZERO * x_numeric
        )  # Dummy op to propogate nulls and type from x arg
        .when(
            (y_numeric < _ZERO) & (bq_mod > _ZERO), (y_numeric + bq_mod)
        )  # Convert positive result to negative
        .when(
            (y_numeric > _ZERO) & (bq_mod < _ZERO), (y_numeric + bq_mod)
        )  # Convert negative result to positive
        .else_(bq_mod)
        .end()
    )


def fillna_op(
    x: ibis_types.Value,
    y: ibis_types.Value,
):
    return x.fillna(typing.cast(ibis_types.Scalar, y))


def reverse(op):
    return lambda x, y: op(y, x)


# Ternary ops


def where_op(
    original: ibis_types.Value,
    condition: ibis_types.Value,
    replacement: ibis_types.Value,
) -> ibis_types.Value:
    """Returns x if y is true, otherwise returns z."""
    return ibis.case().when(condition, original).else_(replacement).end()


def clip_op(
    original: ibis_types.Value,
    lower: ibis_types.Value,
    upper: ibis_types.Value,
) -> ibis_types.Value:
    """Clips value to lower and upper bounds."""
    if isinstance(lower, ibis_types.NullScalar) and (
        not isinstance(upper, ibis_types.NullScalar)
    ):
        return (
            ibis.case()
            .when(upper.isnull() | (original > upper), upper)
            .else_(original)
            .end()
        )
    elif (not isinstance(lower, ibis_types.NullScalar)) and isinstance(
        upper, ibis_types.NullScalar
    ):
        return (
            ibis.case()
            .when(lower.isnull() | (original < lower), lower)
            .else_(original)
            .end()
        )
    elif isinstance(lower, ibis_types.NullScalar) and (
        isinstance(upper, ibis_types.NullScalar)
    ):
        return original
    else:
        # Note: Pandas has unchanged behavior when upper bound and lower bound are flipped. This implementation requires that lower_bound < upper_bound
        return (
            ibis.case()
            .when(lower.isnull() | (original < lower), lower)
            .when(upper.isnull() | (original > upper), upper)
            .else_(original)
            .end()
        )
