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

"""Mappings for Pandas dtypes supported by BigQuery DataFrames package"""

import typing
from typing import Any, Dict, Iterable, Literal, Tuple, Union

import geopandas as gpd  # type: ignore
import ibis
import ibis.expr.datatypes as ibis_dtypes
import ibis.expr.types as ibis_types
import numpy as np
import pandas as pd
import pyarrow as pa

# Type hints for Pandas dtypes supported by BigQuery DataFrame
Dtype = Union[
    pd.BooleanDtype,
    pd.Float64Dtype,
    pd.Int64Dtype,
    pd.StringDtype,
    pd.ArrowDtype,
]

# Corresponds to the pandas concept of numeric type (such as when 'numeric_only' is specified in an operation)
NUMERIC_BIGFRAMES_TYPES = [pd.BooleanDtype(), pd.Float64Dtype(), pd.Int64Dtype()]

# Type hints for dtype strings supported by BigQuery DataFrame
DtypeString = Literal[
    "boolean",
    "Float64",
    "Int64",
    "string",
    "string[pyarrow]",
    "timestamp[us, tz=UTC][pyarrow]",
    "timestamp[us][pyarrow]",
    "date32[day][pyarrow]",
    "time64[us][pyarrow]",
]

# Type hints for Ibis data types supported by BigQuery DataFrame
IbisDtype = Union[
    ibis_dtypes.Boolean,
    ibis_dtypes.Float64,
    ibis_dtypes.Int64,
    ibis_dtypes.String,
    ibis_dtypes.Date,
    ibis_dtypes.Time,
    ibis_dtypes.Timestamp,
]

# Several operations are restricted to these types.
NUMERIC_BIGFRAMES_TYPES = [pd.BooleanDtype(), pd.Float64Dtype(), pd.Int64Dtype()]

# Type hints for Ibis data types that can be read to Python objects by BigQuery DataFrame
ReadOnlyIbisDtype = Union[
    ibis_dtypes.Binary,
    ibis_dtypes.JSON,
    ibis_dtypes.Decimal,
    ibis_dtypes.GeoSpatial,
    ibis_dtypes.Array,
    ibis_dtypes.Struct,
]

BIDIRECTIONAL_MAPPINGS: Iterable[Tuple[IbisDtype, Dtype]] = (
    (ibis_dtypes.boolean, pd.BooleanDtype()),
    (ibis_dtypes.float64, pd.Float64Dtype()),
    (ibis_dtypes.int64, pd.Int64Dtype()),
    (ibis_dtypes.string, pd.StringDtype(storage="pyarrow")),
    (ibis_dtypes.date, pd.ArrowDtype(pa.date32())),
    (ibis_dtypes.time, pd.ArrowDtype(pa.time64("us"))),
    (ibis_dtypes.Timestamp(timezone=None), pd.ArrowDtype(pa.timestamp("us"))),
    (
        ibis_dtypes.Timestamp(timezone="UTC"),
        pd.ArrowDtype(pa.timestamp("us", tz="UTC")),
    ),
)

BIGFRAMES_TO_IBIS: Dict[Dtype, IbisDtype] = {
    pandas: ibis for ibis, pandas in BIDIRECTIONAL_MAPPINGS
}

IBIS_TO_BIGFRAMES: Dict[
    Union[IbisDtype, ReadOnlyIbisDtype], Union[Dtype, np.dtype[Any]]
] = {ibis: pandas for ibis, pandas in BIDIRECTIONAL_MAPPINGS}
# Allow REQUIRED fields to map correctly.
IBIS_TO_BIGFRAMES.update(
    {ibis.copy(nullable=False): pandas for ibis, pandas in BIDIRECTIONAL_MAPPINGS}
)
IBIS_TO_BIGFRAMES.update(
    {
        ibis_dtypes.binary: np.dtype("O"),
        ibis_dtypes.json: np.dtype("O"),
        ibis_dtypes.Decimal(precision=38, scale=9, nullable=True): np.dtype("O"),
        ibis_dtypes.Decimal(precision=76, scale=38, nullable=True): np.dtype("O"),
        ibis_dtypes.GeoSpatial(
            geotype="geography", srid=4326, nullable=True
        ): gpd.array.GeometryDtype(),
        # TODO: Interval
    }
)

BIGFRAMES_STRING_TO_BIGFRAMES: Dict[DtypeString, Dtype] = {
    typing.cast(DtypeString, dtype.name): dtype for dtype in BIGFRAMES_TO_IBIS.keys()
}

# special case - string[pyarrow] doesn't include the storage in its name, and both
# "string" and "string[pyarrow] are accepted"
BIGFRAMES_STRING_TO_BIGFRAMES["string[pyarrow]"] = pd.StringDtype(storage="pyarrow")


def ibis_dtype_to_bigframes_dtype(
    ibis_dtype: Union[IbisDtype, ReadOnlyIbisDtype]
) -> Union[Dtype, np.dtype[Any]]:
    """Converts an Ibis dtype to a BigQuery DataFrames dtype

    Args:
        ibis_dtype: The ibis dtype used to represent this type, which
        should in turn correspond to an underlying BigQuery type

    Returns:
        The supported BigQuery DataFrames dtype, which may be provided by
        pandas, numpy, or db_types

    Raises:
        ValueError: if passed an unexpected type
    """
    # Special cases: Ibis supports variations on these types, but currently
    # our IO returns them as objects. Eventually, we should support them as
    # ArrowDType (and update the IO accordingly)
    if isinstance(ibis_dtype, ibis_dtypes.Array) or isinstance(
        ibis_dtype, ibis_dtypes.Struct
    ):
        return np.dtype("O")

    if ibis_dtype in IBIS_TO_BIGFRAMES:
        return IBIS_TO_BIGFRAMES[ibis_dtype]
    else:
        raise ValueError(f"Unexpected Ibis data type {type(ibis_dtype)}")


def ibis_value_to_canonical_type(value: ibis_types.Value) -> ibis_types.Value:
    """Converts an Ibis expression to canonical type.

    This is useful in cases where multiple types correspond to the same BigFrames dtype.
    """
    ibis_type = value.type()
    # Allow REQUIRED fields to be joined with NULLABLE fields.
    nullable_type = ibis_type.copy(nullable=True)
    return value.cast(nullable_type).name(value.get_name())


def ibis_table_to_canonical_types(table: ibis_types.Table) -> ibis_types.Table:
    """Converts an Ibis table expression to canonical types.

    This is useful in cases where multiple types correspond to the same BigFrames dtype.
    """
    casted_columns = []
    for column_name in table.columns:
        column = typing.cast(ibis_types.Value, table[column_name])
        casted_columns.append(ibis_value_to_canonical_type(column))
    return table.select(*casted_columns)


def bigframes_dtype_to_ibis_dtype(
    bigframes_dtype: Union[DtypeString, Dtype]
) -> IbisDtype:
    """Converts a BigQuery DataFrames supported dtype to an Ibis dtype.

    Args:
        bigframes_dtype: A dtype supported by BigQuery DataFrame

    Returns:
        The corresponding Ibis type

    Raises:
        ValueError:
            If passed a dtype not supported by BigQuery DataFrames.
    """
    type_string = str(bigframes_dtype)
    if type_string in BIGFRAMES_STRING_TO_BIGFRAMES:
        bigframes_dtype = BIGFRAMES_STRING_TO_BIGFRAMES[
            typing.cast(DtypeString, type_string)
        ]
    else:
        raise ValueError(f"Unexpected data type {bigframes_dtype}")

    return BIGFRAMES_TO_IBIS[bigframes_dtype]


def literal_to_ibis_scalar(
    literal, force_dtype: typing.Optional[Dtype] = None, validate: bool = True
):
    """Accept any literal and, if possible, return an Ibis Scalar
    expression with a BigQuery DataFrames compatible data type

    Args:
        literal: any value accepted by Ibis
        force_dtype: force the value to a specific dtype
        validate:
            If true, will raise ValueError if type cannot be stored in a
            BigQuery DataFrames object. If used as a subexpression, this should
            be disabled.

    Returns:
        An ibis Scalar supported by BigQuery DataFrame

    Raises:
        ValueError: if passed literal cannot be coerced to a
        BigQuery DataFrames compatible scalar
    """
    ibis_dtype = BIGFRAMES_TO_IBIS[force_dtype] if force_dtype else None

    if pd.api.types.is_list_like(literal):
        if validate:
            raise ValueError("List types can't be stored in BigQuery DataFrames")
        # "correct" way would be to use ibis.array, but this produces invalid BQ SQL syntax
        return tuple(literal)
    if not pd.api.types.is_list_like(literal) and pd.isna(literal):
        if ibis_dtype:
            return ibis.null().cast(ibis_dtype)
        else:
            return ibis.null()

    scalar_expr = ibis.literal(literal)
    if ibis_dtype:
        scalar_expr = ibis.literal(literal, ibis_dtype)
    elif scalar_expr.type().is_floating():
        scalar_expr = ibis.literal(literal, ibis_dtypes.float64)
    elif scalar_expr.type().is_integer():
        scalar_expr = ibis.literal(literal, ibis_dtypes.int64)

    # TODO(bmil): support other literals that can be coerced to compatible types
    if validate and (scalar_expr.type() not in BIGFRAMES_TO_IBIS.values()):
        raise ValueError(f"Literal did not coerce to a supported data type: {literal}")

    return scalar_expr


def cast_ibis_value(value: ibis_types.Value, to_type: IbisDtype) -> ibis_types.Value:
    """Perform compatible type casts of ibis values

    Args:
        value: Ibis value, which could be a literal, scalar, or column

        to_type: The Ibis type to cast to

    Returns:
        A new Ibis value of type to_type

    Raises:
        TypeError: if the type cast cannot be executed"""
    if value.type() == to_type:
        return value
    # casts that just work
    # TODO(bmil): add to this as more casts are verified
    good_casts = {
        ibis_dtypes.bool: (ibis_dtypes.int64,),
        ibis_dtypes.int64: (
            ibis_dtypes.bool,
            ibis_dtypes.float64,
            ibis_dtypes.string,
        ),
        ibis_dtypes.float64: (ibis_dtypes.string,),
        ibis_dtypes.string: (),
        ibis_dtypes.date: (),
        ibis_dtypes.time: (),
        ibis_dtypes.timestamp: (ibis_dtypes.Timestamp(timezone="UTC"),),
        ibis_dtypes.Timestamp(timezone="UTC"): (ibis_dtypes.timestamp,),
    }

    value = ibis_value_to_canonical_type(value)
    if value.type() in good_casts:
        if to_type in good_casts[value.type()]:
            return value.cast(to_type)
    else:
        # this should never happen
        raise TypeError(f"Unexpected value type {value.type()}")

    # casts that need some encouragement

    # BigQuery casts bools to lower case strings. Capitalize the result to match Pandas
    # TODO(bmil): remove this workaround after fixing Ibis
    if value.type() == ibis_dtypes.bool and to_type == ibis_dtypes.string:
        return typing.cast(ibis_types.StringValue, value.cast(to_type)).capitalize()

    raise TypeError(f"Unsupported cast {value.type()} to {to_type}")
