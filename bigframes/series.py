"""Series is a 1 dimensional data structure."""

from __future__ import annotations

import typing
from typing import Optional

import ibis.expr.types as ibis_types
import pandas
from google.cloud import bigquery

import bigframes.core


class Series:
    """A 1D data structure, representing data and deferred computation.

    .. warning::
        This constructor is **private**. Use a public method such as
        ``DataFrame[column_name]`` to construct a Series.
    """

    def __init__(
        self,
        expr: bigframes.core.BigFramesExpr,
        value: ibis_types.Value,
    ):
        self._expr = expr
        self._value = value

    def _to_ibis_expr(self):
        """Creates an Ibis table expression representing the Series."""
        expr = self._expr.projection([self._value])
        return expr.to_ibis_expr()[self._value.get_name()]

    def _execute_query(self) -> bigquery.QueryJob:
        """Execute a query and return metadata about the results."""
        # TODO(swast): Cache the job ID so we can look it up again if they ask
        # for the results? We'd need a way to invalidate the cache if DataFrame
        # becomes mutable, though. Or move this method to the immutable
        # expression class.
        # TODO(swast): We might want to move this method to Session and/or
        # provide our own minimal metadata class. Tight coupling to the
        # BigQuery client library isn't ideal, especially if we want to support
        # a LocalSession for unit testing.
        # TODO(swast): Add a timeout here? If the query is taking a long time,
        # maybe we just print the job metadata that we have so far?
        return self._to_ibis_expr().execute()

    def compute(self) -> pandas.Series:
        """Executes deferred operations and downloads the results."""
        value = self._to_ibis_expr()
        return value.execute()

    def head(self, max_results: Optional[int] = 5) -> pandas.DataFrame:
        """Limits DataFrame to a specific number of rows."""
        # TOOD(swast): This will be deferred once more opportunistic style
        # execution is implemented.
        value = self._to_ibis_expr()
        return value.execute()

    def lower(self) -> "Series":
        """Convert strings in the Series to lowercase."""
        return Series(
            self._expr,
            typing.cast(ibis_types.StringValue, self._value)
            .lower()
            .name(self._value.get_name()),
        )

    def upper(self) -> "Series":
        """Convert strings in the Series to uppercase."""
        return Series(
            self._expr,
            typing.cast(ibis_types.StringValue, self._value)
            .upper()
            .name(self._value.get_name()),
        )

    def __add__(self, other: float | int | Series | pandas.Series) -> Series:
        if isinstance(other, Series):
            return Series(
                self._expr,
                typing.cast(ibis_types.NumericValue, self._value)
                .__add__(typing.cast(ibis_types.NumericValue, other._value))
                .name(self._value.get_name()),
            )
        else:
            return Series(
                self._expr,
                typing.cast(
                    ibis_types.NumericValue, self._value + other  # type: ignore
                ).name(self._value.get_name()),
            )

    def abs(self) -> "Series":
        """Calculate absolute value of numbers in the Series."""
        return Series(
            self._expr,
            typing.cast(ibis_types.NumericValue, self._value)
            .abs()
            .name(self._value.get_name()),
        )

    def reverse(self) -> "Series":
        """Reverse strings in the Series."""
        return Series(
            self._expr,
            typing.cast(ibis_types.StringValue, self._value)
            .reverse()
            .name(self._value.get_name()),
        )

    def round(self, decimals=0) -> "Series":
        """Round each value in a Series to the given number of decimals."""
        return Series(
            self._expr,
            typing.cast(ibis_types.NumericValue, self._value)
            .round(digits=decimals)
            .name(self._value.get_name()),
        )
