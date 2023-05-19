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
import ibis.expr.datatypes as ibis_dtypes
import ibis.expr.types as ibis_types


class WindowOp:
    def _as_ibis(self, value: ibis_types.Column, window=None):
        raise NotImplementedError("Base class WindowOp has no implementaiton.")

    @property
    def skips_nulls(self):
        """Whether the window op skips null rows."""
        return True


class AggregateOp(WindowOp):
    def _as_ibis(self, value: ibis_types.Column, window=None):
        raise NotImplementedError("Base class AggregateOp has no implementaiton.")


def numeric_op(operation):
    def constrained_op(op, column: ibis_types.Column, window=None):
        if column.type().is_boolean():
            column = typing.cast(
                ibis_types.NumericColumn, column.cast(ibis_dtypes.int64)
            )
        if column.type().is_numeric():
            return operation(op, column, window)
        else:
            raise ValueError(
                f"Numeric operation cannot be applied to type {column.type()}"
            )

    return constrained_op


class SumOp(AggregateOp):
    @numeric_op
    def _as_ibis(
        self, column: ibis_types.NumericColumn, window=None
    ) -> ibis_types.NumericValue:
        # Will be null if all inputs are null. Pandas defaults to zero sum though.
        bq_sum = _apply_window_if_present(column.sum(), window)
        return (
            ibis.case().when(bq_sum.isnull(), ibis_types.literal(0)).else_(bq_sum).end()
        )


class MeanOp(AggregateOp):
    @numeric_op
    def _as_ibis(
        self, column: ibis_types.NumericColumn, window=None
    ) -> ibis_types.NumericValue:
        return _apply_window_if_present(column.mean(), window)


class ProductOp(AggregateOp):
    @numeric_op
    def _as_ibis(
        self, column: ibis_types.NumericColumn, window=None
    ) -> ibis_types.NumericValue:
        # Need to short-circuit as log with zeroes is illegal sql
        is_zero = typing.cast(ibis_types.BooleanColumn, (column == 0))

        # There is no product sql aggregate function, so must implement as a sum of logs, and then
        # apply power after. Note, log and power base must be equal! This impl uses base 2.
        logs = typing.cast(
            ibis_types.NumericColumn,
            ibis.case().when(is_zero, 0).else_(column.abs().log2()).end(),
        )
        logs_sum = _apply_window_if_present(logs.sum(), window)
        magnitude = typing.cast(ibis_types.NumericValue, ibis_types.literal(2)).pow(
            logs_sum
        )

        # Can't determine sign from logs, so have to determine parity of count of negative inputs
        is_negative = typing.cast(
            ibis_types.NumericColumn,
            ibis.case().when(column.sign() == -1, 1).else_(0).end(),
        )
        negative_count = _apply_window_if_present(is_negative.sum(), window)
        negative_count_parity = negative_count % typing.cast(
            ibis_types.NumericValue, ibis.literal(2)
        )  # 1 if result should be negative, otherwise 0

        any_zeroes = _apply_window_if_present(is_zero.any(), window)
        float_result = (
            ibis.case()
            .when(any_zeroes, ibis_types.literal(0))
            .else_(magnitude * pow(-1, negative_count_parity))
            .end()
        )
        return float_result.cast(column.type())


class MaxOp(AggregateOp):
    def _as_ibis(self, column: ibis_types.Column, window=None) -> ibis_types.Value:
        return _apply_window_if_present(column.max(), window)


class MinOp(AggregateOp):
    def _as_ibis(self, column: ibis_types.Column, window=None) -> ibis_types.Value:
        return _apply_window_if_present(column.min(), window)


class StdOp(AggregateOp):
    def _as_ibis(self, x: ibis_types.Column, window=None) -> ibis_types.Value:
        return _apply_window_if_present(
            typing.cast(ibis_types.NumericColumn, x).std(), window
        )


class VarOp(AggregateOp):
    def _as_ibis(self, x: ibis_types.Column, window=None) -> ibis_types.Value:
        return _apply_window_if_present(
            typing.cast(ibis_types.NumericColumn, x).var(), window
        )


class CountOp(AggregateOp):
    def _as_ibis(
        self, column: ibis_types.Column, window=None
    ) -> ibis_types.IntegerValue:
        return _apply_window_if_present(column.count(), window)

    @property
    def skips_nulls(self):
        return False


class RankOp(WindowOp):
    def _as_ibis(
        self, column: ibis_types.Column, window=None
    ) -> ibis_types.IntegerValue:
        return _apply_window_if_present(column.rank(), window)

    @property
    def skips_nulls(self):
        return False


class FirstOp(WindowOp):
    def _as_ibis(self, column: ibis_types.Column, window=None) -> ibis_types.Value:
        return _apply_window_if_present(column.first(), window)


class ShiftOp(WindowOp):
    def __init__(self, periods: int):
        self._periods = periods

    def _as_ibis(self, column: ibis_types.Column, window=None) -> ibis_types.Value:
        if self._periods == 0:  # No-op
            return column
        if self._periods > 0:
            return _apply_window_if_present(column.lag(self._periods), window)
        return _apply_window_if_present(column.lead(-self._periods), window)

    @property
    def skips_nulls(self):
        return False


class AllOp(AggregateOp):
    def _as_ibis(
        self, column: ibis_types.Column, window=None
    ) -> ibis_types.BooleanValue:
        # BQ will return null for empty column, result would be true in pandas.
        result = typing.cast(ibis_types.BooleanColumn, column != 0).all()
        return typing.cast(
            ibis_types.BooleanScalar,
            _apply_window_if_present(result, window).fillna(ibis_types.literal(True)),
        )


class AnyOp(AggregateOp):
    def _as_ibis(
        self, column: ibis_types.Column, window=None
    ) -> ibis_types.BooleanValue:
        # BQ will return null for empty column, result would be false in pandas.
        result = typing.cast(ibis_types.BooleanColumn, column != 0).any()
        return typing.cast(
            ibis_types.BooleanScalar,
            _apply_window_if_present(result, window).fillna(ibis_types.literal(True)),
        )


def _apply_window_if_present(value: ibis_types.Value, window):
    return value.over(window) if (window is not None) else value


sum_op = SumOp()
mean_op = MeanOp()
product_op = ProductOp()
max_op = MaxOp()
min_op = MinOp()
std_op = StdOp()
var_op = VarOp()
count_op = CountOp()
rank_op = RankOp()
all_op = AllOp()
any_op = AnyOp()
first_op = FirstOp()
