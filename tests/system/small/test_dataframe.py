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

import operator

import geopandas as gpd  # type: ignore
import numpy as np
import pandas as pd
import pandas.testing
import pyarrow as pa  # type: ignore
import pytest

from tests.system.utils import (
    assert_pandas_df_equal_ignore_ordering,
    assert_series_equal_ignoring_order,
)


def test_get_column(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs
    col_name = "int64_col"
    series = scalars_df[col_name]
    bf_result = series.compute()
    pd_result = scalars_pandas_df[col_name]
    assert_series_equal_ignoring_order(bf_result, pd_result)


def test_hasattr(scalars_dfs):
    scalars_df, _ = scalars_dfs
    assert hasattr(scalars_df, "int64_col")
    assert hasattr(scalars_df, "head")
    assert not hasattr(scalars_df, "not_exist")


def test_head_with_custom_column_labels(scalars_df_index, scalars_pandas_df_index):
    rename_mapping = {
        "int64_col": "Integer Column",
        "string_col": "言語列",
    }
    bf_df = scalars_df_index.rename(columns=rename_mapping).head(3)
    bf_result = bf_df.compute()
    pd_result = scalars_pandas_df_index.rename(columns=rename_mapping).head(3)
    pandas.testing.assert_frame_equal(bf_result, pd_result)


def test_get_column_by_attr(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs
    series = scalars_df.int64_col
    bf_result = series.compute()
    pd_result = scalars_pandas_df.int64_col
    assert_series_equal_ignoring_order(bf_result, pd_result)


def test_get_columns(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs
    col_names = ["bool_col", "float64_col", "int64_col"]
    df_subset = scalars_df[col_names]
    df_pandas = df_subset.compute()
    pd.testing.assert_index_equal(
        df_pandas.columns, scalars_pandas_df[col_names].columns
    )


def test_drop_column(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs
    col_name = "int64_col"
    df_pandas = scalars_df.drop(columns=col_name).compute()
    pd.testing.assert_index_equal(
        df_pandas.columns, scalars_pandas_df.drop(columns=col_name).columns
    )


def test_drop_columns(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs
    col_names = ["int64_col", "geography_col", "time_col"]
    df_pandas = scalars_df.drop(columns=col_names).compute()
    pd.testing.assert_index_equal(
        df_pandas.columns, scalars_pandas_df.drop(columns=col_names).columns
    )


def test_drop_with_custom_column_labels(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs
    rename_mapping = {
        "int64_col": "Integer Column",
        "string_col": "言語列",
    }
    dropped_columns = [
        "言語列",
        "timestamp_col",
    ]
    bf_df = scalars_df.rename(columns=rename_mapping).drop(columns=dropped_columns)
    bf_result = bf_df.compute()
    pd_result = scalars_pandas_df.rename(columns=rename_mapping).drop(
        columns=dropped_columns
    )
    assert_pandas_df_equal_ignore_ordering(bf_result, pd_result)


def test_rename(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs
    col_name_dict = {"bool_col": "boolean_col"}
    df_pandas = scalars_df.rename(columns=col_name_dict).compute()
    pd.testing.assert_index_equal(
        df_pandas.columns, scalars_pandas_df.rename(columns=col_name_dict).columns
    )


def test_repr_w_all_rows(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs
    scalars_df = scalars_df.copy()

    if scalars_pandas_df.index.name is None:
        # Note: Not quite the same as no index / default index, but hopefully
        # simulates it well enough while being consistent enough for string
        # comparison to work.
        scalars_df = scalars_df.set_index("rowindex", drop=False).sort_index()
        scalars_df.index.name = None

    # When there are 10 or fewer rows, the outputs should be identical.
    actual = repr(scalars_df.head(10))
    expected = repr(scalars_pandas_df.head(10))
    assert actual == expected


def test_repr_html_w_all_rows(scalars_dfs):
    scalars_df, _ = scalars_dfs
    # get a pandas df of the expected format
    pandas_df = scalars_df._block.compute().set_axis(scalars_df._col_labels, axis=1)
    pandas_df.index.name = scalars_df.index.name

    # When there are 10 or fewer rows, the outputs should be identical except for the extra note.
    actual = scalars_df.head(10)._repr_html_()
    expected = (
        pandas_df.head(10)._repr_html_()
        + f"[{len(pandas_df.index)} rows x {len(pandas_df.columns)} columns in total]"
    )
    assert actual == expected


def test_df_column_name_with_space(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs
    col_name_dict = {"bool_col": "bool  col"}
    df_pandas = scalars_df.rename(columns=col_name_dict).compute()
    pd.testing.assert_index_equal(
        df_pandas.columns, scalars_pandas_df.rename(columns=col_name_dict).columns
    )


def test_df_column_name_duplicate(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs
    col_name_dict = {"int64_too": "int64_col"}
    df_pandas = scalars_df.rename(columns=col_name_dict).compute()
    pd.testing.assert_index_equal(
        df_pandas.columns, scalars_pandas_df.rename(columns=col_name_dict).columns
    )


def test_get_df_column_name_duplicate(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs
    col_name_dict = {"int64_too": "int64_col"}

    bf_result = scalars_df.rename(columns=col_name_dict)["int64_col"].compute()
    pd_result = scalars_pandas_df.rename(columns=col_name_dict)["int64_col"]
    pd.testing.assert_index_equal(bf_result.columns, pd_result.columns)


def test_filter_df(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs

    bf_bool_series = scalars_df["bool_col"]
    bf_result = scalars_df[bf_bool_series].compute()

    pd_bool_series = scalars_pandas_df["bool_col"]
    pd_result = scalars_pandas_df[pd_bool_series]

    assert_pandas_df_equal_ignore_ordering(bf_result, pd_result)


def test_assign_new_column(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs
    kwargs = {"new_col": 2}
    df = scalars_df.assign(**kwargs)
    bf_result = df.compute()
    pd_result = scalars_pandas_df.assign(**kwargs)

    # Convert default pandas dtypes `int64` to match BigFrames dtypes.
    pd_result["new_col"] = pd_result["new_col"].astype("Int64")

    assert_pandas_df_equal_ignore_ordering(bf_result, pd_result)


def test_assign_existing_column(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs
    kwargs = {"int64_col": 2}
    df = scalars_df.assign(**kwargs)
    bf_result = df.compute()
    pd_result = scalars_pandas_df.assign(**kwargs)

    # Convert default pandas dtypes `int64` to match BigFrames dtypes.
    pd_result["int64_col"] = pd_result["int64_col"].astype("Int64")

    assert_pandas_df_equal_ignore_ordering(bf_result, pd_result)


def test_assign_series(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs
    column_name = "int64_col"
    df = scalars_df.assign(new_col=scalars_df[column_name])
    bf_result = df.compute()
    pd_result = scalars_pandas_df.assign(new_col=scalars_pandas_df[column_name])

    assert_pandas_df_equal_ignore_ordering(bf_result, pd_result)


def test_assign_sequential(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs
    kwargs = {"int64_col": 2, "new_col": 3, "new_col2": 4}
    df = scalars_df.assign(**kwargs)
    bf_result = df.compute()
    pd_result = scalars_pandas_df.assign(**kwargs)

    # Convert default pandas dtypes `int64` to match BigFrames dtypes.
    pd_result["int64_col"] = pd_result["int64_col"].astype("Int64")
    pd_result["new_col"] = pd_result["new_col"].astype("Int64")
    pd_result["new_col2"] = pd_result["new_col2"].astype("Int64")

    assert_pandas_df_equal_ignore_ordering(bf_result, pd_result)


# Require an index so that the self-join is consistent each time.
def test_assign_same_table_different_index_performs_self_join(
    scalars_df_index, scalars_pandas_df_index
):
    column_name = "int64_col"
    bf_df = scalars_df_index.assign(
        alternative_index=scalars_df_index["rowindex_2"] + 2
    )
    pd_df = scalars_pandas_df_index.assign(
        alternative_index=scalars_pandas_df_index["rowindex_2"] + 2
    )
    bf_df_2 = bf_df.set_index("alternative_index")
    pd_df_2 = pd_df.set_index("alternative_index")
    bf_result = bf_df.assign(new_col=bf_df_2[column_name] * 10).compute()
    pd_result = pd_df.assign(new_col=pd_df_2[column_name] * 10)

    pandas.testing.assert_frame_equal(bf_result, pd_result)


# Different table expression must have Index
def test_assign_different_df(
    scalars_df_index, scalars_df_2_index, scalars_pandas_df_index
):
    column_name = "int64_col"
    df = scalars_df_index.assign(new_col=scalars_df_2_index[column_name])
    bf_result = df.compute()
    # Doesn't matter to pandas if it comes from the same DF or a different DF.
    pd_result = scalars_pandas_df_index.assign(
        new_col=scalars_pandas_df_index[column_name]
    )

    assert_pandas_df_equal_ignore_ordering(bf_result, pd_result)


def test_dropna(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs
    df = scalars_df.dropna()
    bf_result = df.compute()
    pd_result = scalars_pandas_df.dropna()

    assert_pandas_df_equal_ignore_ordering(bf_result, pd_result)


@pytest.mark.parametrize(
    ("merge_how",),
    [
        ("inner",),
        ("outer",),
        ("left",),
        ("right",),
    ],
)
def test_merge(scalars_dfs, merge_how):
    scalars_df, scalars_pandas_df = scalars_dfs
    on = "rowindex_2"
    left_columns = ["int64_col", "float64_col", "rowindex_2"]
    right_columns = ["int64_col", "bool_col", "string_col", "rowindex_2"]

    left = scalars_df[left_columns]
    # Offset the rows somewhat so that outer join can have an effect.
    right = scalars_df[right_columns].assign(rowindex_2=scalars_df["rowindex_2"] + 2)
    df = left.merge(right, merge_how, on)
    bf_result = df.compute()

    pd_result = scalars_pandas_df[left_columns].merge(
        scalars_pandas_df[right_columns].assign(
            rowindex_2=scalars_pandas_df["rowindex_2"] + 2
        ),
        merge_how,
        on,
    )

    assert_pandas_df_equal_ignore_ordering(bf_result, pd_result)


@pytest.mark.parametrize(
    ("merge_how",),
    [
        ("inner",),
        ("outer",),
        ("left",),
        ("right",),
    ],
)
def test_merge_custom_col_name(scalars_dfs, merge_how):
    scalars_df, scalars_pandas_df = scalars_dfs
    left_columns = ["int64_col", "float64_col"]
    right_columns = ["int64_col", "bool_col", "string_col"]
    on = "int64_col"
    rename_columns = {"float64_col": "f64_col"}

    left = scalars_df[left_columns]
    left = left.rename(columns=rename_columns)
    right = scalars_df[right_columns]
    df = left.merge(right, merge_how, on)
    bf_result = df.compute()

    pandas_left_df = scalars_pandas_df[left_columns]
    pandas_left_df = pandas_left_df.rename(columns=rename_columns)
    pandas_right_df = scalars_pandas_df[right_columns]
    pd_result = pandas_left_df.merge(pandas_right_df, merge_how, on)

    assert_pandas_df_equal_ignore_ordering(bf_result, pd_result)


def test_get_dtypes(scalars_df_default_index):
    dtypes = scalars_df_default_index.dtypes
    pd.testing.assert_series_equal(
        dtypes,
        pd.Series(
            {
                "bool_col": pd.BooleanDtype(),
                "bytes_col": np.dtype("O"),
                "date_col": pd.ArrowDtype(pa.date32()),
                "datetime_col": pd.ArrowDtype(pa.timestamp("us")),
                "geography_col": gpd.array.GeometryDtype(),
                "int64_col": pd.Int64Dtype(),
                "int64_too": pd.Int64Dtype(),
                "numeric_col": np.dtype("O"),
                "float64_col": pd.Float64Dtype(),
                "rowindex": pd.Int64Dtype(),
                "rowindex_2": pd.Int64Dtype(),
                "string_col": pd.StringDtype(storage="pyarrow"),
                "time_col": pd.ArrowDtype(pa.time64("us")),
                "timestamp_col": pd.ArrowDtype(pa.timestamp("us", tz="UTC")),
            }
        ),
    )


def test_get_dtypes_array_struct(session):
    """We may upgrade struct and array to proper arrow dtype support in future. For now,
    we return python objects"""
    df = session.read_gbq(
        """SELECT
        [1, 3, 2] AS array_column,
        STRUCT(
            "a" AS string_field,
            1.2 AS float_field) AS struct_column"""
    )

    dtypes = df.dtypes
    pd.testing.assert_series_equal(
        dtypes,
        pd.Series({"array_column": np.dtype("O"), "struct_column": np.dtype("O")}),
    )


def test_shape(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs
    bf_result = scalars_df.shape
    pd_result = scalars_pandas_df.shape

    assert bf_result == pd_result


def test_size(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs
    bf_result = scalars_df.size
    pd_result = scalars_pandas_df.size

    assert bf_result == pd_result


def test_ndim(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs
    bf_result = scalars_df.ndim
    pd_result = scalars_pandas_df.ndim

    assert bf_result == pd_result


def test_empty_false(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs

    bf_result = scalars_df.empty
    pd_result = scalars_pandas_df.empty

    assert bf_result == pd_result


def test_empty_true(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs

    bf_result = scalars_df[[]].empty
    pd_result = scalars_pandas_df[[]].empty

    assert bf_result == pd_result


@pytest.mark.parametrize(
    ("drop",),
    ((True,), (False,)),
)
def test_reset_index(scalars_df_index, scalars_pandas_df_index, drop):
    df = scalars_df_index.reset_index(drop=drop)
    assert df.index.name is None

    bf_result = df.compute()
    pd_result = scalars_pandas_df_index.reset_index(drop=drop)

    # Pandas uses int64 instead of Int64 (nullable) dtype.
    pd_result.index = pd_result.index.astype(pd.Int64Dtype())

    # reset_index should maintain the original ordering.
    pandas.testing.assert_frame_equal(bf_result, pd_result)


def test_reset_index_then_filter(
    scalars_df_index,
    scalars_pandas_df_index,
):
    bf_filter = scalars_df_index["bool_col"].fillna(True)
    bf_df = scalars_df_index.reset_index()[bf_filter]
    bf_result = bf_df.compute()
    pd_filter = scalars_pandas_df_index["bool_col"].fillna(True)
    pd_result = scalars_pandas_df_index.reset_index()[pd_filter]

    # Pandas uses int64 instead of Int64 (nullable) dtype.
    pd_result.index = pd_result.index.astype(pd.Int64Dtype())

    # reset_index should maintain the original ordering and index keys
    # post-filter will have gaps.
    pandas.testing.assert_frame_equal(bf_result, pd_result)


def test_reset_index_with_unnamed_index(
    scalars_df_index,
    scalars_pandas_df_index,
):
    scalars_df_index = scalars_df_index.copy()
    scalars_pandas_df_index = scalars_pandas_df_index.copy()

    scalars_df_index.index.name = None
    scalars_pandas_df_index.index.name = None
    df = scalars_df_index.reset_index(drop=False)
    assert df.index.name is None

    # reset_index(drop=False) creates a new column "index".
    assert df.columns[0] == "index"

    bf_result = df.compute()
    pd_result = scalars_pandas_df_index.reset_index(drop=False)

    # Pandas uses int64 instead of Int64 (nullable) dtype.
    pd_result.index = pd_result.index.astype(pd.Int64Dtype())

    # reset_index should maintain the original ordering.
    pandas.testing.assert_frame_equal(bf_result, pd_result)


def test_reset_index_with_unnamed_index_and_index_column(
    scalars_df_index,
    scalars_pandas_df_index,
):
    scalars_df_index = scalars_df_index.copy()
    scalars_pandas_df_index = scalars_pandas_df_index.copy()

    scalars_df_index.index.name = None
    scalars_pandas_df_index.index.name = None
    df = scalars_df_index.assign(index=scalars_df_index["int64_col"]).reset_index(
        drop=False
    )
    assert df.index.name is None

    # reset_index(drop=False) creates a new column "level_0" if the "index" column already exists.
    assert df.columns[0] == "level_0"

    bf_result = df.compute()
    pd_result = scalars_pandas_df_index.assign(
        index=scalars_pandas_df_index["int64_col"]
    ).reset_index(drop=False)

    # Pandas uses int64 instead of Int64 (nullable) dtype.
    pd_result.index = pd_result.index.astype(pd.Int64Dtype())

    # reset_index should maintain the original ordering.
    pandas.testing.assert_frame_equal(bf_result, pd_result)


@pytest.mark.parametrize(
    ("drop",),
    (
        (True,),
        (False,),
    ),
)
@pytest.mark.parametrize(
    ("index_column",),
    (("int64_too",), ("string_col",), ("timestamp_col",)),
)
def test_set_index(scalars_dfs, index_column, drop):
    scalars_df, scalars_pandas_df = scalars_dfs
    df = scalars_df.set_index(index_column, drop=drop)
    bf_result = df.compute()
    pd_result = scalars_pandas_df.set_index(index_column, drop=drop)

    # Sort to disambiguate when there are duplicate index labels.
    # Note: Doesn't use assert_pandas_df_equal_ignore_ordering because we get
    # "ValueError: 'timestamp_col' is both an index level and a column label,
    # which is ambiguous" when trying to sort by a column with the same name as
    # the index.
    bf_result = bf_result.sort_values("rowindex_2")
    pd_result = pd_result.sort_values("rowindex_2")

    pandas.testing.assert_frame_equal(bf_result, pd_result)


def test_df_abs(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs
    columns = ["int64_col", "int64_too", "float64_col"]

    bf_result = scalars_df[columns].abs().compute()
    pd_result = scalars_pandas_df[columns].abs()

    assert_pandas_df_equal_ignore_ordering(bf_result, pd_result)


def test_df_isnull(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs

    columns = ["int64_col", "int64_too", "string_col", "bool_col"]
    bf_result = scalars_df[columns].isnull().compute()
    pd_result = scalars_pandas_df[columns].isnull()

    # One of dtype mismatches to be documented. Here, the `bf_result.dtype` is
    # `BooleanDtype` but the `pd_result.dtype` is `bool`.
    pd_result["int64_col"] = pd_result["int64_col"].astype(pd.BooleanDtype())
    pd_result["int64_too"] = pd_result["int64_too"].astype(pd.BooleanDtype())
    pd_result["string_col"] = pd_result["string_col"].astype(pd.BooleanDtype())
    pd_result["bool_col"] = pd_result["bool_col"].astype(pd.BooleanDtype())

    assert_pandas_df_equal_ignore_ordering(bf_result, pd_result)


def test_df_notnull(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs

    columns = ["int64_col", "int64_too", "string_col", "bool_col"]
    bf_result = scalars_df[columns].notnull().compute()
    pd_result = scalars_pandas_df[columns].notnull()

    # One of dtype mismatches to be documented. Here, the `bf_result.dtype` is
    # `BooleanDtype` but the `pd_result.dtype` is `bool`.
    pd_result["int64_col"] = pd_result["int64_col"].astype(pd.BooleanDtype())
    pd_result["int64_too"] = pd_result["int64_too"].astype(pd.BooleanDtype())
    pd_result["string_col"] = pd_result["string_col"].astype(pd.BooleanDtype())
    pd_result["bool_col"] = pd_result["bool_col"].astype(pd.BooleanDtype())

    assert_pandas_df_equal_ignore_ordering(bf_result, pd_result)


@pytest.mark.parametrize(
    ("op"),
    [
        operator.add,
        operator.sub,
        operator.mul,
        operator.truediv,
        operator.floordiv,
        operator.gt,
        operator.ge,
        operator.lt,
        operator.le,
    ],
    ids=[
        "add",
        "subtract",
        "multiply",
        "true_divide",
        "floor_divide",
        "gt",
        "ge",
        "lt",
        "le",
    ],
)
# TODO(garrettwu): deal with NA values
@pytest.mark.parametrize(("other_scalar"), [1, 2.5, 0, 0.0])
@pytest.mark.parametrize(("reverse_operands"), [True, False])
def test_scalar_binop(scalars_dfs, op, other_scalar, reverse_operands):
    scalars_df, scalars_pandas_df = scalars_dfs
    columns = ["int64_col", "float64_col"]

    maybe_reversed_op = (lambda x, y: op(y, x)) if reverse_operands else op

    bf_result = maybe_reversed_op(scalars_df[columns], other_scalar).compute()
    pd_result = maybe_reversed_op(scalars_pandas_df[columns], other_scalar)

    assert_pandas_df_equal_ignore_ordering(bf_result, pd_result)


@pytest.mark.parametrize(("other_scalar"), [1, -2])
def test_mod(scalars_dfs, other_scalar):
    # Zero case excluded as pandas produces 0 result for Int64 inputs rather than NA/NaN.
    # This is likely a pandas bug as mod 0 is undefined in other dtypes, and most programming languages.
    scalars_df, scalars_pandas_df = scalars_dfs

    bf_result = (scalars_df[["int64_col", "int64_too"]] % other_scalar).compute()
    pd_result = scalars_pandas_df[["int64_col", "int64_too"]] % other_scalar

    assert_pandas_df_equal_ignore_ordering(bf_result, pd_result)


def test_scalar_binop_str_exception(scalars_dfs):
    scalars_df, _ = scalars_dfs
    columns = ["string_col"]
    with pytest.raises(TypeError):
        (scalars_df[columns] + 1).compute()


@pytest.mark.parametrize(
    ("op"),
    [
        (lambda x, y: x.add(y, axis="index")),
        (lambda x, y: x.radd(y, axis="index")),
        (lambda x, y: x.sub(y, axis="index")),
        (lambda x, y: x.rsub(y, axis="index")),
        (lambda x, y: x.mul(y, axis="index")),
        (lambda x, y: x.rmul(y, axis="index")),
        (lambda x, y: x.truediv(y, axis="index")),
        (lambda x, y: x.rtruediv(y, axis="index")),
        (lambda x, y: x.floordiv(y, axis="index")),
        (lambda x, y: x.floordiv(y, axis="index")),
        (lambda x, y: x.gt(y, axis="index")),
        (lambda x, y: x.ge(y, axis="index")),
        (lambda x, y: x.lt(y, axis="index")),
        (lambda x, y: x.le(y, axis="index")),
    ],
    ids=[
        "add",
        "radd",
        "sub",
        "rsub",
        "mul",
        "rmul",
        "truediv",
        "rtruediv",
        "floordiv",
        "rfloordiv",
        "gt",
        "ge",
        "lt",
        "le",
    ],
)
def test_series_binop_axis_index(
    scalars_dfs,
    op,
):
    scalars_df, scalars_pandas_df = scalars_dfs
    df_columns = ["int64_col", "float64_col"]
    series_column = "int64_too"

    bf_result = op(scalars_df[df_columns], scalars_df[series_column]).compute()
    pd_result = op(scalars_pandas_df[df_columns], scalars_pandas_df[series_column])

    assert_pandas_df_equal_ignore_ordering(bf_result, pd_result)


# Differnt table will only work for explicit index, since default index orders are arbitrary.
def test_series_binop_add_different_table(
    scalars_df_index, scalars_pandas_df_index, scalars_df_2_index
):
    df_columns = ["int64_col", "float64_col"]
    series_column = "int64_too"

    bf_result = (
        scalars_df_index[df_columns]
        .add(scalars_df_2_index[series_column], axis="index")
        .compute()
    )
    pd_result = scalars_pandas_df_index[df_columns].add(
        scalars_pandas_df_index[series_column], axis="index"
    )

    assert_pandas_df_equal_ignore_ordering(bf_result, pd_result)


# TODO(garrettwu): Test series binop with different index

all_joins = pytest.mark.parametrize(
    ("how",),
    (
        ("outer",),
        ("left",),
        ("right",),
        ("inner",),
    ),
)


@all_joins
def test_join_same_table(scalars_dfs, how):
    bf_df, pd_df = scalars_dfs
    if how == "right" and pd_df.index.name != "rowindex":
        pytest.skip("right join not supported without an index")

    bf_df_a = bf_df[["string_col", "int64_col"]]
    bf_df_b = bf_df[["float64_col"]]
    bf_result = bf_df_a.join(bf_df_b, how=how).compute()
    pd_df_a = pd_df[["string_col", "int64_col"]]
    pd_df_b = pd_df[["float64_col"]]
    pd_result = pd_df_a.join(pd_df_b, how=how)
    assert_pandas_df_equal_ignore_ordering(bf_result, pd_result)


@all_joins
def test_join_different_table(
    scalars_df_index, scalars_df_2_index, scalars_pandas_df_index, how
):
    bf_df_a = scalars_df_index[["string_col", "int64_col"]]
    bf_df_b = scalars_df_2_index.dropna()[["float64_col"]]
    bf_result = bf_df_a.join(bf_df_b, how=how).compute()
    pd_df_a = scalars_pandas_df_index[["string_col", "int64_col"]]
    pd_df_b = scalars_pandas_df_index.dropna()[["float64_col"]]
    pd_result = pd_df_a.join(pd_df_b, how=how)
    assert_pandas_df_equal_ignore_ordering(bf_result, pd_result)


def test_join_duplicate_columns_raises_not_implemented(scalars_dfs):
    scalars_df, _ = scalars_dfs
    df_a = scalars_df[["string_col", "float64_col"]]
    df_b = scalars_df[["float64_col"]]
    with pytest.raises(NotImplementedError):
        df_a.join(df_b, how="outer").compute()


@pytest.mark.parametrize(
    ("by", "ascending", "na_position"),
    [
        ("int64_col", True, "first"),
        (["bool_col", "int64_col"], True, "last"),
        ("int64_col", False, "first"),
        (["bool_col", "int64_col"], [False, True], "last"),
        (["bool_col", "int64_col"], [True, False], "first"),
    ],
)
def test_dataframe_sort_values(
    scalars_df_index, scalars_pandas_df_index, by, ascending, na_position
):
    # Test needs values to be unique
    bf_result = scalars_df_index.sort_values(
        by, ascending=ascending, na_position=na_position
    ).compute()
    pd_result = scalars_pandas_df_index.sort_values(
        by, ascending=ascending, na_position=na_position
    )

    pandas.testing.assert_frame_equal(
        bf_result,
        pd_result,
    )


@pytest.mark.parametrize(
    ("operator", "columns"),
    [
        pytest.param(lambda x: x.cumsum(), ["float64_col", "int64_too"]),
        pytest.param(lambda x: x.cumprod(), ["float64_col", "int64_too"]),
        pytest.param(
            lambda x: x.cumprod(),
            ["string_col"],
            marks=pytest.mark.xfail(
                raises=ValueError,
            ),
        ),
    ],
    ids=[
        "cumsum",
        "cumprod",
        "non-numeric",
    ],
)
def test_dataframe_numeric_analytic_op(
    scalars_df_index, scalars_pandas_df_index, operator, columns
):
    # TODO: Add nullable ints (pandas 1.x has poor behavior on these)
    bf_series = operator(scalars_df_index[columns])
    pd_series = operator(scalars_pandas_df_index[columns])
    bf_result = bf_series.compute()
    pd.testing.assert_frame_equal(pd_series, bf_result, check_dtype=False)


@pytest.mark.parametrize(
    ("operator"),
    [
        (lambda x: x.cummin()),
        (lambda x: x.cummax()),
        (lambda x: x.shift(2)),
        (lambda x: x.shift(-2)),
    ],
    ids=[
        "cummin",
        "cummax",
        "shiftpostive",
        "shiftnegative",
    ],
)
def test_dataframe_general_analytic_op(
    scalars_df_index, scalars_pandas_df_index, operator
):
    col_names = ["int64_too", "float64_col", "int64_col", "bool_col"]
    bf_series = operator(scalars_df_index[col_names])
    pd_series = operator(scalars_pandas_df_index[col_names])
    bf_result = bf_series.compute()
    pd.testing.assert_frame_equal(
        pd_series,
        bf_result,
    )


def test_ipython_key_completions_with_drop(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs
    col_names = "string_col"
    bf_dataframe = scalars_df.drop(columns=col_names)
    pd_dataframe = scalars_pandas_df.drop(columns=col_names)
    expected = pd_dataframe.columns.tolist()

    results = bf_dataframe._ipython_key_completions_()

    assert col_names not in results
    assert results == expected
    # _ipython_key_completions_ is called with square brackets
    # so only column names are relevant with tab completion
    assert "to_gbq" not in results
    assert "merge" not in results
    assert "drop" not in results


def test_ipython_key_completions_with_rename(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs
    col_name_dict = {"string_col": "a_renamed_column"}
    bf_dataframe = scalars_df.rename(columns=col_name_dict)
    pd_dataframe = scalars_pandas_df.rename(columns=col_name_dict)
    expected = pd_dataframe.columns.tolist()

    results = bf_dataframe._ipython_key_completions_()

    assert "string_col" not in results
    assert "a_renamed_column" in results
    assert results == expected
    # _ipython_key_completions_ is called with square brackets
    # so only column names are relevant with tab completion
    assert "to_gbq" not in results
    assert "merge" not in results
    assert "drop" not in results


def test__dir__with_drop(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs
    col_names = "string_col"
    bf_dataframe = scalars_df.drop(columns=col_names)
    pd_dataframe = scalars_pandas_df.drop(columns=col_names)
    expected = pd_dataframe.columns.tolist()

    results = dir(bf_dataframe)

    assert col_names not in results
    assert frozenset(expected) <= frozenset(results)
    # __dir__ is called with a '.' and displays all methods, columns names, etc.
    assert "to_gbq" in results
    assert "merge" in results
    assert "drop" in results


def test__dir__with_rename(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs
    col_name_dict = {"string_col": "a_renamed_column"}
    bf_dataframe = scalars_df.rename(columns=col_name_dict)
    pd_dataframe = scalars_pandas_df.rename(columns=col_name_dict)
    expected = pd_dataframe.columns.tolist()

    results = dir(bf_dataframe)

    assert "string_col" not in results
    assert "a_renamed_column" in results
    assert frozenset(expected) <= frozenset(results)
    # __dir__ is called with a '.' and displays all methods, columns names, etc.
    assert "to_gbq" in results
    assert "merge" in results
    assert "drop" in results
