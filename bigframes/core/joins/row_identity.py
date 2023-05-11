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

"""Helpers to join BigFramesExpr objects."""

from __future__ import annotations

import functools
import typing
from typing import Callable, Tuple

import ibis
import ibis.expr.types as ibis_types

import bigframes.core as core

SUPPORTED_ROW_IDENTITY_HOW = {"outer", "left", "inner"}


def join_by_row_identity(
    left: core.BigFramesExpr, right: core.BigFramesExpr, *, how: str
) -> Tuple[
    core.BigFramesExpr,
    Tuple[Callable[[str], ibis_types.Value], Callable[[str], ibis_types.Value]],
]:
    """Compute join when we are joining by row identity not a specific column."""
    if how not in SUPPORTED_ROW_IDENTITY_HOW:
        raise NotImplementedError("Only how='outer','left','inner' currently supported")

    if not left.table.equals(right.table):
        # TODO(swast): Raise a more specific exception (subclass of
        # ValueError, though) to make it easier to catch only the intended
        # failures.
        raise ValueError(
            "Cannot combine objects without an explicit join/merge key. "
            f"Left based on: {left.table.compile()}, but "
            f"right based on: {right.table.compile()}"
        )

    left_predicates = left._predicates
    right_predicates = right._predicates
    # TODO(tbergeron): Skip generating these for inner part of join
    (
        left_relative_predicates,
        right_relative_predicates,
    ) = _get_relative_predicates(left_predicates, right_predicates)

    combined_predicates = []
    if left_predicates or right_predicates:
        joined_predicates = _join_predicates(
            left_predicates, right_predicates, join_type=how
        )
        combined_predicates = list(joined_predicates)  # builder expects mutable list

    left_mask = left_relative_predicates if how in ["right", "outer"] else None
    right_mask = right_relative_predicates if how in ["left", "outer"] else None
    joined_columns = [
        _mask_value(left.get_column(key), left_mask).name(map_left_id(key))
        for key in left.column_names.keys()
    ] + [
        _mask_value(right.get_column(key), right_mask).name(map_right_id(key))
        for key in right.column_names.keys()
    ]

    new_ordering = core.ExpressionOrdering()
    if left._ordering and right._ordering:
        meta_columns = [
            left._get_meta_column(key).name(map_left_id(key))
            for key in left._meta_column_names.keys()
        ] + [
            right._get_meta_column(key).name(map_right_id(key))
            for key in right._meta_column_names.keys()
        ]
        new_ordering_id = (
            map_left_id(left._ordering.ordering_id)
            if (left._ordering.ordering_id)
            else None
        )
        # These ordering columns will be present in the BigFramesExpr, as
        # we haven't hidden any value / index column(s). Code that is aware
        # of which columns are index columns / value columns columns will
        # need to add the previous columns to hidden meta columns.
        new_ordering = left._ordering.with_ordering_columns(
            [
                col_ref.with_name(map_left_id(col_ref.column_id))
                for col_ref in left._ordering.ordering_value_columns
            ]
            + [
                col_ref.with_name(map_right_id(col_ref.column_id))
                for col_ref in right._ordering.ordering_value_columns
            ]
        )
        if new_ordering_id:
            new_ordering = new_ordering.with_ordering_id(new_ordering_id)

    joined_expr = core.BigFramesExpr(
        left._session,
        left.table,
        columns=joined_columns,
        meta_columns=meta_columns,
        ordering=new_ordering,
        predicates=combined_predicates,
    )
    return joined_expr, (
        lambda key: joined_expr.get_any_column(map_left_id(key)),
        lambda key: joined_expr.get_any_column(map_right_id(key)),
    )


def map_left_id(left_side_id):
    return f"{left_side_id}_x"


def map_right_id(right_side_id):
    return f"{right_side_id}_y"


def _mask_value(
    value: ibis_types.Value,
    predicates: typing.Optional[typing.Sequence[ibis_types.BooleanValue]] = None,
):
    if predicates:
        return (
            ibis.case()
            .when(_reduce_predicate_list(predicates), value)
            .else_(ibis.null())
            .end()
        )
    return value


def _join_predicates(
    left_predicates: typing.Collection[ibis_types.BooleanValue],
    right_predicates: typing.Collection[ibis_types.BooleanValue],
    join_type: str = "outer",
) -> typing.Tuple[ibis_types.BooleanValue, ...]:
    """Combines predicates lists for each side of a join."""
    if join_type == "outer":
        if not left_predicates:
            return ()
        if not right_predicates:
            return ()
        # TODO(tbergeron): Investigate factoring out common predicates
        joined_predicates = _reduce_predicate_list(left_predicates).__or__(
            _reduce_predicate_list(right_predicates)
        )
        return (joined_predicates,)
    if join_type == "left":
        return tuple(left_predicates)
    if join_type == "inner":
        _, right_relative_predicates = _get_relative_predicates(
            left_predicates, right_predicates
        )
        return (*left_predicates, *right_relative_predicates)
    else:
        raise ValueError("Unsupported join_type: " + join_type)


def _get_relative_predicates(
    left_predicates: typing.Collection[ibis_types.BooleanValue],
    right_predicates: typing.Collection[ibis_types.BooleanValue],
) -> tuple[
    typing.Tuple[ibis_types.BooleanValue, ...],
    typing.Tuple[ibis_types.BooleanValue, ...],
]:
    """Get predicates that apply to only one side of the join. Not strictly necessary but simplifies resulting query."""
    left_relative_predicates = tuple(left_predicates) or ()
    right_relative_predicates = tuple(right_predicates) or ()
    if left_predicates and right_predicates:
        # Factor out common predicates needed for left/right column masking
        left_relative_predicates = tuple(set(left_predicates) - set(right_predicates))
        right_relative_predicates = tuple(set(right_predicates) - set(left_predicates))
    return (left_relative_predicates, right_relative_predicates)


def _reduce_predicate_list(
    predicate_list: typing.Collection[ibis_types.BooleanValue],
) -> ibis_types.BooleanValue:
    """Converts a list of predicates BooleanValues into a single BooleanValue."""
    if len(predicate_list) == 0:
        raise ValueError("Cannot reduce empty list of predicates")
    if len(predicate_list) == 1:
        (item,) = predicate_list
        return item
    return functools.reduce(lambda acc, pred: acc.__and__(pred), predicate_list)