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

import bigframes
import bigframes._config.display_options as display_options
import bigframes.dataframe as dataframe
from tests.system.utils import (
    assert_pandas_df_equal_ignore_ordering,
    assert_series_equal_ignoring_order,
)


def test_df_construct_copy(scalars_dfs):
    columns = ["int64_col", "string_col", "float64_col"]
    scalars_df, scalars_pandas_df = scalars_dfs
    bf_result = dataframe.DataFrame(scalars_df, columns=columns).compute()
    pd_result = pd.DataFrame(scalars_pandas_df, columns=columns)
    pandas.testing.assert_frame_equal(bf_result, pd_result)


def test_df_construct_pandas(scalars_dfs):
    columns = ["int64_too", "int64_col", "float64_col", "bool_col", "string_col"]
    _, scalars_pandas_df = scalars_dfs
    bf_result = dataframe.DataFrame(scalars_pandas_df, columns=columns).compute()
    pd_result = pd.DataFrame(scalars_pandas_df, columns=columns)
    pandas.testing.assert_frame_equal(bf_result, pd_result)


def test_df_construct_pandas_set_dtype(scalars_dfs):
    columns = [
        "int64_too",
        "int64_col",
        "float64_col",
        "bool_col",
    ]
    _, scalars_pandas_df = scalars_dfs
    bf_result = dataframe.DataFrame(
        scalars_pandas_df, columns=columns, dtype="Float64"
    ).compute()
    pd_result = pd.DataFrame(scalars_pandas_df, columns=columns, dtype="Float64")
    pandas.testing.assert_frame_equal(bf_result, pd_result)


def test_df_construct_from_series(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs
    bf_result = dataframe.DataFrame(
        {"a": scalars_df["int64_col"], "b": scalars_df["string_col"]},
        dtype="string[pyarrow]",
    ).compute()
    pd_result = pd.DataFrame(
        {"a": scalars_pandas_df["int64_col"], "b": scalars_pandas_df["string_col"]},
        dtype="string[pyarrow]",
    )
    pandas.testing.assert_frame_equal(bf_result, pd_result)


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


def test_tail_with_custom_column_labels(scalars_df_index, scalars_pandas_df_index):
    rename_mapping = {
        "int64_col": "Integer Column",
        "string_col": "言語列",
    }
    bf_df = scalars_df_index.rename(columns=rename_mapping).tail(3)
    bf_result = bf_df.compute()
    pd_result = scalars_pandas_df_index.rename(columns=rename_mapping).tail(3)
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
    df_subset = scalars_df.get(col_names)
    df_pandas = df_subset.compute()
    pd.testing.assert_index_equal(
        df_pandas.columns, scalars_pandas_df[col_names].columns
    )


def test_get_columns_default(scalars_dfs):
    scalars_df, _ = scalars_dfs
    col_names = ["not", "column", "names"]
    result = scalars_df.get(col_names, "default_val")
    assert result == "default_val"


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

    # Remove columns with flaky formatting, like NUMERIC columns (which use the
    # object dtype). Also makes a copy so that mutating the index name doesn't
    # break other tests.
    scalars_df = scalars_df.drop(columns=["numeric_col"])
    scalars_pandas_df = scalars_pandas_df.drop(columns=["numeric_col"])

    if scalars_pandas_df.index.name is None:
        # Note: Not quite the same as no index / default index, but hopefully
        # simulates it well enough while being consistent enough for string
        # comparison to work.
        scalars_df = scalars_df.set_index("rowindex", drop=False).sort_index()
        scalars_df.index.name = None

    # When there are 10 or fewer rows, the outputs should be identical.
    actual = repr(scalars_df.head(10))

    with display_options.pandas_repr(bigframes.options.display):
        expected = repr(scalars_pandas_df.head(10))

    assert actual == expected


def test_repr_html_w_all_rows(scalars_dfs):
    scalars_df, _ = scalars_dfs
    # get a pandas df of the expected format
    df, _ = scalars_df._block.compute()
    pandas_df = df.set_axis(scalars_df._block.column_labels, axis=1)
    pandas_df.index.name = scalars_df.index.name

    # When there are 10 or fewer rows, the outputs should be identical except for the extra note.
    actual = scalars_df.head(10)._repr_html_()
    with display_options.pandas_repr(bigframes.options.display):
        pandas_repr = pandas_df.head(10)._repr_html_()

    expected = (
        pandas_repr
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

    # Convert default pandas dtypes `int64` to match BigQuery DataFrame dtypes.
    pd_result["new_col"] = pd_result["new_col"].astype("Int64")

    assert_pandas_df_equal_ignore_ordering(bf_result, pd_result)


def test_assign_existing_column(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs
    kwargs = {"int64_col": 2}
    df = scalars_df.assign(**kwargs)
    bf_result = df.compute()
    pd_result = scalars_pandas_df.assign(**kwargs)

    # Convert default pandas dtypes `int64` to match BigQuery DataFrame dtypes.
    pd_result["int64_col"] = pd_result["int64_col"].astype("Int64")

    assert_pandas_df_equal_ignore_ordering(bf_result, pd_result)


def test_assign_series(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs
    column_name = "int64_col"
    df = scalars_df.assign(new_col=scalars_df[column_name])
    bf_result = df.compute()
    pd_result = scalars_pandas_df.assign(new_col=scalars_pandas_df[column_name])

    assert_pandas_df_equal_ignore_ordering(bf_result, pd_result)


def test_assign_series_overwrite(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs
    column_name = "int64_col"
    df = scalars_df.assign(**{column_name: scalars_df[column_name] + 3})
    bf_result = df.compute()
    pd_result = scalars_pandas_df.assign(
        **{column_name: scalars_pandas_df[column_name] + 3}
    )

    assert_pandas_df_equal_ignore_ordering(bf_result, pd_result)


def test_assign_sequential(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs
    kwargs = {"int64_col": 2, "new_col": 3, "new_col2": 4}
    df = scalars_df.assign(**kwargs)
    bf_result = df.compute()
    pd_result = scalars_pandas_df.assign(**kwargs)

    # Convert default pandas dtypes `int64` to match BigQuery DataFrame dtypes.
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

    df = left.merge(right, merge_how, on, sort=True)
    bf_result = df.compute()

    pd_result = scalars_pandas_df[left_columns].merge(
        scalars_pandas_df[right_columns].assign(
            rowindex_2=scalars_pandas_df["rowindex_2"] + 2
        ),
        merge_how,
        on,
        sort=True,
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
    df = left.merge(right, merge_how, on, sort=True)
    bf_result = df.compute()

    pandas_left_df = scalars_pandas_df[left_columns]
    pandas_left_df = pandas_left_df.rename(columns=rename_columns)
    pandas_right_df = scalars_pandas_df[right_columns]
    pd_result = pandas_left_df.merge(pandas_right_df, merge_how, on, sort=True)

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
    ("append",),
    (
        (True,),
        (False,),
    ),
)
@pytest.mark.parametrize(
    ("index_column",),
    (("int64_too",), ("string_col",), ("timestamp_col",)),
)
def test_set_index(scalars_dfs, index_column, drop, append):
    scalars_df, scalars_pandas_df = scalars_dfs
    df = scalars_df.set_index(index_column, append=append, drop=drop)
    bf_result = df.compute()
    pd_result = scalars_pandas_df.set_index(index_column, append=append, drop=drop)

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
def test_dataframe_binop_axis_index_throws_not_implemented(
    scalars_dfs,
    op,
):
    scalars_df, scalars_pandas_df = scalars_dfs
    df_columns = ["int64_col", "float64_col"]
    other_df_columns = ["int64_too"]

    with pytest.raises(NotImplementedError):
        op(scalars_df[df_columns], scalars_df[other_df_columns]).compute()


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


@pytest.mark.parametrize(
    ("start", "stop", "step"),
    [
        (0, 0, None),
        (None, None, None),
        (1, None, None),
        (None, 4, None),
        (None, None, 2),
        (None, 50000000000, 1),
        (5, 4, None),
        (3, None, 2),
        (1, 7, 2),
        (1, 7, 50000000000),
    ],
)
def test_iloc_slice(scalars_df_index, scalars_pandas_df_index, start, stop, step):
    bf_result = scalars_df_index.iloc[start:stop:step].compute()
    pd_result = scalars_pandas_df_index.iloc[start:stop:step]

    # Pandas may assign non-object dtype to empty series and series index
    # dtypes of empty columns are a known area of divergence from pandas
    for column in pd_result.columns:
        if (
            pd_result[column].empty and column != "geography_col"
        ):  # for empty geography_col, bigframes assigns non-object dtype
            pd_result[column] = pd_result[column].astype("object")
            pd_result.index = pd_result.index.astype("object")

    pd.testing.assert_frame_equal(
        bf_result,
        pd_result,
    )


def test_iloc_slice_zero_step(scalars_df_index):
    with pytest.raises(ValueError):
        scalars_df_index.iloc[0:0:0]


def test_iloc_slice_nested(scalars_df_index, scalars_pandas_df_index):
    bf_result = scalars_df_index.iloc[1:].iloc[1:].compute()
    pd_result = scalars_pandas_df_index.iloc[1:].iloc[1:]

    pd.testing.assert_frame_equal(
        bf_result,
        pd_result,
    )


@pytest.mark.parametrize(
    "index",
    [0, 5],
)
def test_iloc_single_integer(scalars_df_index, scalars_pandas_df_index, index):
    bf_result = scalars_df_index.iloc[index]
    pd_result = scalars_pandas_df_index.iloc[index]

    pd.testing.assert_series_equal(
        bf_result,
        pd_result,
    )


def test_iloc_single_integer_out_of_bound_error(
    scalars_df_index, scalars_pandas_df_index
):
    with pytest.raises(IndexError, match="single positional indexer is out-of-bounds"):
        scalars_df_index.iloc[99]


def test_loc_bool_series_explicit_index(scalars_df_index, scalars_pandas_df_index):
    bf_result = scalars_df_index.loc[scalars_df_index.bool_col].compute()
    pd_result = scalars_pandas_df_index.loc[scalars_pandas_df_index.bool_col]

    pd.testing.assert_frame_equal(
        bf_result,
        pd_result,
    )


def test_loc_bool_series_default_index(
    scalars_df_default_index, scalars_pandas_df_default_index
):
    bf_result = scalars_df_default_index.loc[
        scalars_df_default_index.bool_col
    ].compute()
    pd_result = scalars_pandas_df_default_index.loc[
        scalars_pandas_df_default_index.bool_col
    ]

    assert_pandas_df_equal_ignore_ordering(
        bf_result,
        pd_result,
    )


@pytest.mark.parametrize(
    ("op"),
    [
        (lambda x: x.sum(numeric_only=True)),
        (lambda x: x.mean(numeric_only=True)),
        (lambda x: x.min(numeric_only=True)),
        (lambda x: x.max(numeric_only=True)),
        (lambda x: x.std(numeric_only=True)),
        (lambda x: x.var(numeric_only=True)),
    ],
    ids=[
        "sum",
        "mean",
        "min",
        "max",
        "std",
        "var",
    ],
)
def test_dataframe_aggregates(scalars_df_index, scalars_pandas_df_index, op):
    col_names = ["int64_too", "float64_col", "int64_col", "bool_col", "string_col"]
    bf_series = op(scalars_df_index[col_names])
    pd_series = op(scalars_pandas_df_index[col_names])
    bf_result = bf_series.compute()

    # Pandas may produce narrower numeric types, but bigframes always produces Float64
    pd_series = pd_series.astype("Float64")
    # Pandas has object index type
    pd.testing.assert_series_equal(pd_series, bf_result, check_index_type=False)


@pytest.mark.parametrize(
    ("frac", "n", "random_state"),
    [
        (None, 4, None),
        (0.5, None, None),
        (None, 4, 10),
        (0.5, None, 10),
        (None, None, None),
    ],
    ids=[
        "n_wo_random_state",
        "frac_wo_random_state",
        "n_w_random_state",
        "frac_w_random_state",
        "n_default",
    ],
)
def test_sample(scalars_dfs, frac, n, random_state):
    scalars_df, _ = scalars_dfs
    df = scalars_df.sample(frac=frac, n=n, random_state=random_state)
    bf_result = df.compute()

    n = 1 if n is None else n
    expected_sample_size = round(frac * scalars_df.shape[0]) if frac is not None else n
    assert bf_result.shape[0] == expected_sample_size
    assert bf_result.shape[1] == scalars_df.shape[1]


def test_sample_raises_value_error(scalars_dfs):
    scalars_df, _ = scalars_dfs
    with pytest.raises(
        ValueError, match="Only one of 'n' or 'frac' parameter can be specified."
    ):
        scalars_df.sample(frac=0.5, n=4)


@pytest.mark.parametrize(
    ("axis",),
    [
        (0,),
        (1,),
    ],
)
def test_df_add_prefix(scalars_df_index, scalars_pandas_df_index, axis):
    if pd.__version__.startswith("1."):
        pytest.skip("add_prefix axis parameter not supported in pandas 1.x.")
    bf_result = scalars_df_index.add_prefix("prefix_", axis).compute()

    pd_result = scalars_pandas_df_index.add_prefix("prefix_", axis)

    pd.testing.assert_frame_equal(
        bf_result,
        pd_result,
        check_index_type=False,
    )


@pytest.mark.parametrize(
    ("axis",),
    [
        (0,),
        (1,),
    ],
)
def test_df_add_suffix(scalars_df_index, scalars_pandas_df_index, axis):
    if pd.__version__.startswith("1."):
        pytest.skip("add_prefix axis parameter not supported in pandas 1.x.")
    bf_result = scalars_df_index.add_suffix("_suffix", axis).compute()

    pd_result = scalars_pandas_df_index.add_suffix("_suffix", axis)

    pd.testing.assert_frame_equal(
        bf_result,
        pd_result,
        check_index_type=False,
    )


def test_df_values(scalars_df_index, scalars_pandas_df_index):
    bf_result = scalars_df_index.values

    pd_result = scalars_pandas_df_index.values
    # Numpy isn't equipped to compare non-numeric objects, so convert back to dataframe
    pd.testing.assert_frame_equal(
        pd.DataFrame(bf_result), pd.DataFrame(pd_result), check_dtype=False
    )


def test_df_to_numpy(scalars_df_index, scalars_pandas_df_index):
    bf_result = scalars_df_index.to_numpy()

    pd_result = scalars_pandas_df_index.to_numpy()
    # Numpy isn't equipped to compare non-numeric objects, so convert back to dataframe
    pd.testing.assert_frame_equal(
        pd.DataFrame(bf_result), pd.DataFrame(pd_result), check_dtype=False
    )


def test_df___array__(scalars_df_index, scalars_pandas_df_index):
    bf_result = scalars_df_index.__array__()

    pd_result = scalars_pandas_df_index.__array__()
    # Numpy isn't equipped to compare non-numeric objects, so convert back to dataframe
    pd.testing.assert_frame_equal(
        pd.DataFrame(bf_result), pd.DataFrame(pd_result), check_dtype=False
    )


def test_getattr_not_implemented(scalars_df_index):
    with pytest.raises(NotImplementedError):
        scalars_df_index.asof()


def test_getattr_attribute_error(scalars_df_index):
    with pytest.raises(AttributeError):
        scalars_df_index.not_a_method()


def test_loc_list_string_index(scalars_df_index, scalars_pandas_df_index):
    index_list = scalars_pandas_df_index.string_col.iloc[[0, 1, 1, 5]].values

    scalars_df_index = scalars_df_index.set_index("string_col")
    scalars_pandas_df_index = scalars_pandas_df_index.set_index("string_col")

    bf_result = scalars_df_index.loc[index_list]
    pd_result = scalars_pandas_df_index.loc[index_list]

    pd.testing.assert_frame_equal(
        bf_result.compute(),
        pd_result,
    )


def test_loc_list_integer_index(scalars_df_index, scalars_pandas_df_index):
    index_list = [3, 2, 1, 3, 2, 1]

    bf_result = scalars_df_index.loc[index_list]
    pd_result = scalars_pandas_df_index.loc[index_list]

    pd.testing.assert_frame_equal(
        bf_result.compute(),
        pd_result,
    )


def test_iloc_list(scalars_df_index, scalars_pandas_df_index):
    index_list = [0, 0, 0, 5, 4, 7]

    bf_result = scalars_df_index.iloc[index_list]
    pd_result = scalars_pandas_df_index.iloc[index_list]

    pd.testing.assert_frame_equal(
        bf_result.compute(),
        pd_result,
    )


def test_iloc_empty_list(scalars_df_index, scalars_pandas_df_index):
    index_list = []

    bf_result = scalars_df_index.iloc[index_list]
    pd_result = scalars_pandas_df_index.iloc[index_list]

    bf_result = bf_result.compute()
    assert bf_result.shape == pd_result.shape  # types are known to be different


def test_rename_axis(scalars_df_index, scalars_pandas_df_index):
    bf_result = scalars_df_index.rename_axis("newindexname")
    pd_result = scalars_pandas_df_index.rename_axis("newindexname")

    pd.testing.assert_frame_equal(
        bf_result.compute(),
        pd_result,
    )


def test_loc_bf_series_string_index(scalars_df_index, scalars_pandas_df_index):
    pd_string_series = scalars_pandas_df_index.string_col.iloc[[0, 5, 1, 1, 5]]
    bf_string_series = scalars_df_index.string_col.iloc[[0, 5, 1, 1, 5]]

    scalars_df_index = scalars_df_index.set_index("string_col")
    scalars_pandas_df_index = scalars_pandas_df_index.set_index("string_col")

    bf_result = scalars_df_index.loc[bf_string_series]
    pd_result = scalars_pandas_df_index.loc[pd_string_series]

    pd.testing.assert_frame_equal(
        bf_result.compute(),
        pd_result,
    )


def test_loc_bf_index_integer_index(scalars_df_index, scalars_pandas_df_index):
    pd_index = scalars_pandas_df_index.iloc[[0, 5, 1, 1, 5]].index
    bf_index = scalars_df_index.iloc[[0, 5, 1, 1, 5]].index

    bf_result = scalars_df_index.loc[bf_index]
    pd_result = scalars_pandas_df_index.loc[pd_index]

    pd.testing.assert_frame_equal(
        bf_result.compute(),
        pd_result,
    )


def test_loc_bf_index_integer_index_renamed_col(
    scalars_df_index, scalars_pandas_df_index
):
    scalars_df_index = scalars_df_index.rename(columns={"int64_col": "rename"})
    scalars_pandas_df_index = scalars_pandas_df_index.rename(
        columns={"int64_col": "rename"}
    )

    pd_index = scalars_pandas_df_index.iloc[[0, 5, 1, 1, 5]].index
    bf_index = scalars_df_index.iloc[[0, 5, 1, 1, 5]].index

    bf_result = scalars_df_index.loc[bf_index]
    pd_result = scalars_pandas_df_index.loc[pd_index]

    pd.testing.assert_frame_equal(
        bf_result.compute(),
        pd_result,
    )


@pytest.mark.parametrize(
    ("subset"),
    [
        None,
        ["bool_col", "int64_too"],
    ],
)
@pytest.mark.parametrize(
    ("keep",),
    [
        ("first",),
        ("last",),
        (False,),
    ],
)
def test_df_drop_duplicates(scalars_df_index, scalars_pandas_df_index, keep, subset):
    columns = ["bool_col", "int64_too", "int64_col"]
    bf_series = scalars_df_index[columns].drop_duplicates(subset, keep=keep).compute()
    pd_series = scalars_pandas_df_index[columns].drop_duplicates(subset, keep=keep)
    pd.testing.assert_frame_equal(
        pd_series,
        bf_series,
    )


@pytest.mark.parametrize(
    ("subset"),
    [
        None,
        ["bool_col"],
    ],
)
@pytest.mark.parametrize(
    ("keep",),
    [
        ("first",),
        ("last",),
        (False,),
    ],
)
def test_df_duplicated(scalars_df_index, scalars_pandas_df_index, keep, subset):
    columns = ["bool_col", "int64_too", "int64_col"]
    bf_series = scalars_df_index[columns].duplicated(subset, keep=keep).compute()
    pd_series = scalars_pandas_df_index[columns].duplicated(subset, keep=keep)
    pd.testing.assert_series_equal(pd_series, bf_series, check_dtype=False)


@pytest.mark.parametrize(
    ("subset", "normalize", "ascending", "dropna"),
    [
        (None, False, False, False),
        (None, True, True, True),
        ("bool_col", True, False, True),
    ],
)
def test_df_value_counts(scalars_dfs, subset, normalize, ascending, dropna):
    scalars_df, scalars_pandas_df = scalars_dfs

    bf_result = (
        scalars_df[["string_col", "bool_col"]]
        .value_counts(subset, normalize=normalize, ascending=ascending, dropna=dropna)
        .compute()
    )
    pd_result = scalars_pandas_df[["string_col", "bool_col"]].value_counts(
        subset, normalize=normalize, ascending=ascending, dropna=dropna
    )

    # Older pandas version may not have these values, bigframes tries to emulate 2.0+
    pd_result.name = "count"
    pd_result.index.names = bf_result.index.names

    pd.testing.assert_series_equal(
        bf_result, pd_result, check_dtype=False, check_index_type=False
    )


def test_df_bool_interpretation_error(scalars_df_index):
    with pytest.raises(ValueError):
        True if scalars_df_index else False
