import math

import db_dtypes  # type: ignore
import numpy
import pandas as pd
import pytest

import bigframes.core.indexes


def assert_series_equal_ignoring_order(left: pd.Series, right: pd.Series, **kwargs):
    if isinstance(left.index, pd.RangeIndex) or isinstance(right.index, pd.RangeIndex):
        left = left.sort_values().reset_index(drop=True)
        right = right.sort_values().reset_index(drop=True)
    else:
        left = left.sort_index()
        right = right.sort_index()

    pd.testing.assert_series_equal(left, right, **kwargs)


@pytest.mark.parametrize(
    ["col_name", "expected_dtype"],
    [
        ("bool_col", pd.BooleanDtype()),
        # TODO(swast): Use a more efficient type.
        ("bytes_col", numpy.dtype("object")),
        ("date_col", db_dtypes.DateDtype()),
        ("datetime_col", numpy.dtype("datetime64[ns]")),
        ("float64_col", pd.Float64Dtype()),
        # TODO(swast): Use a more efficient type.
        ("geography_col", pd.StringDtype(storage="pyarrow")),
        ("int64_col", pd.Int64Dtype()),
        # TODO(swast): Use a more efficient type.
        ("numeric_col", numpy.dtype("object")),
        ("int64_too", pd.Int64Dtype()),
        ("string_col", pd.StringDtype(storage="pyarrow")),
        ("time_col", db_dtypes.TimeDtype()),
        # TODO(chelsealin): Should be "us" rather than "ns" after b/275417413.
        ("timestamp_col", pd.DatetimeTZDtype(unit="ns", tz="UTC")),
    ],
)
def test_get_column(scalars_dfs, col_name, expected_dtype):
    scalars_df, scalars_pandas_df = scalars_dfs
    series = scalars_df[col_name]
    series_pandas = series.compute()
    assert series_pandas.dtype == expected_dtype
    assert series_pandas.shape[0] == scalars_pandas_df.shape[0]


@pytest.mark.parametrize(
    ("col_name",),
    (
        ("float64_col",),
        ("int64_too",),
    ),
)
def test_abs(scalars_dfs, col_name):
    scalars_df, scalars_pandas_df = scalars_dfs
    bf_result = scalars_df[col_name].abs().compute()
    pd_result = scalars_pandas_df[col_name].abs()

    assert_series_equal_ignoring_order(pd_result, bf_result)


def test_find(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs
    col_name = "string_col"
    bf_result = scalars_df[col_name].find("W").compute()
    pd_result = scalars_pandas_df[col_name].str.find("W")

    # One of type mismatches to be documented. Here, the `bf_result.dtype` is `Int64` but
    # the `pd_result.dtype` is `float64`: https://github.com/pandas-dev/pandas/issues/51948
    assert_series_equal_ignoring_order(
        pd_result.astype(pd.Int64Dtype()),
        bf_result,
    )


def test_fillna(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs
    col_name = "string_col"
    bf_result = scalars_df[col_name].fillna("Missing").compute()
    pd_result = scalars_pandas_df[col_name].fillna("Missing")
    assert_series_equal_ignoring_order(
        pd_result,
        bf_result,
    )


def test_len(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs
    col_name = "string_col"
    bf_result = scalars_df[col_name].len().compute()
    pd_result = scalars_pandas_df[col_name].str.len()

    # One of dtype mismatches to be documented. Here, the `bf_result.dtype` is `Int64` but
    # the `pd_result.dtype` is `float64`: https://github.com/pandas-dev/pandas/issues/51948
    assert_series_equal_ignoring_order(
        pd_result.astype(pd.Int64Dtype()),
        bf_result,
    )


def test_lower(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs
    col_name = "string_col"
    bf_result = scalars_df[col_name].lower().compute()
    pd_result = scalars_pandas_df[col_name].str.lower()

    assert_series_equal_ignoring_order(
        pd_result,
        bf_result,
    )


@pytest.mark.parametrize(
    ("col_name",),
    (
        ("string_col",),
        ("int64_col",),
    ),
)
def test_max(scalars_dfs, col_name):
    scalars_df, scalars_pandas_df = scalars_dfs
    bf_result = scalars_df[col_name].max().compute()
    pd_result = scalars_pandas_df[col_name].max()
    assert pd_result == bf_result


@pytest.mark.parametrize(
    ("col_name",),
    (
        ("string_col",),
        ("int64_col",),
    ),
)
def test_min(scalars_dfs, col_name):
    scalars_df, scalars_pandas_df = scalars_dfs
    bf_result = scalars_df[col_name].min().compute()
    pd_result = scalars_pandas_df[col_name].min()
    assert pd_result == bf_result


def test_upper(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs
    col_name = "string_col"
    bf_result = scalars_df[col_name].upper().compute()
    pd_result = scalars_pandas_df[col_name].str.upper()

    assert_series_equal_ignoring_order(
        pd_result,
        bf_result,
    )


def test_strip(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs
    col_name = "string_col"
    bf_result = scalars_df[col_name].strip().compute()
    pd_result = scalars_pandas_df[col_name].str.strip()

    assert_series_equal_ignoring_order(
        pd_result,
        bf_result,
    )


@pytest.mark.parametrize(
    ("operator"),
    [
        (lambda x, y: x + y),
        (lambda x, y: x - y),
        (lambda x, y: x * y),
        (lambda x, y: x / y),
        (lambda x, y: x // y),
        (lambda x, y: x % y),
        (lambda x, y: x < y),
        (lambda x, y: x > y),
        (lambda x, y: x <= y),
        (lambda x, y: x >= y),
    ],
    ids=[
        "add",
        "subtract",
        "multiply",
        "divide",
        "floordivide",
        "modulo",
        "less_than",
        "greater_than",
        "less_than_equal",
        "greater_than_equal",
    ],
)
@pytest.mark.parametrize(("other_scalar"), [-1, 0, 14, pd.NA])
@pytest.mark.parametrize(("reverse_operands"), [True, False])
def test_series_int_int_operators_scalar(
    scalars_dfs, operator, other_scalar, reverse_operands
):
    scalars_df, scalars_pandas_df = scalars_dfs

    maybe_reversed_op = (lambda x, y: operator(y, x)) if reverse_operands else operator

    bf_result = maybe_reversed_op(scalars_df["int64_col"], other_scalar).compute()
    pd_result = maybe_reversed_op(scalars_pandas_df["int64_col"], other_scalar)

    assert_series_equal_ignoring_order(pd_result, bf_result)


@pytest.mark.parametrize(
    ("operator"),
    [
        (lambda x, y: x + y),
        (lambda x, y: x - y),
        (lambda x, y: x * y),
        (lambda x, y: x / y),
        (lambda x, y: x < y),
        (lambda x, y: x > y),
        (lambda x, y: x <= y),
        (lambda x, y: x >= y),
        (lambda x, y: x % y),
        (lambda x, y: x // y),
    ],
    ids=[
        "add",
        "subtract",
        "multiply",
        "divide",
        "less_than",
        "greater_than",
        "less_than_equal",
        "greater_than_equal",
        "modulo",
        "floordivide",
    ],
)
def test_series_int_int_operators_series(scalars_dfs, operator):
    scalars_df, scalars_pandas_df = scalars_dfs
    bf_result = operator(scalars_df["int64_col"], scalars_df["int64_too"]).compute()
    pd_result = operator(scalars_pandas_df["int64_col"], scalars_pandas_df["int64_too"])

    assert_series_equal_ignoring_order(pd_result, bf_result)


@pytest.mark.parametrize(
    ("other",),
    [
        (3,),
        (-6.2,),
    ],
)
def test_series_add_scalar(scalars_dfs, other):
    scalars_df, scalars_pandas_df = scalars_dfs
    bf_result = (scalars_df["float64_col"] + other).compute()
    pd_result = scalars_pandas_df["float64_col"] + other

    assert_series_equal_ignoring_order(pd_result, bf_result)


@pytest.mark.parametrize(
    ("left_col", "right_col"),
    [
        ("float64_col", "float64_col"),
        ("int64_col", "float64_col"),
        ("int64_col", "int64_col"),
        ("int64_col", "int64_too"),
    ],
)
def test_series_add_bigframes_series(scalars_dfs, left_col, right_col):
    scalars_df, scalars_pandas_df = scalars_dfs
    bf_result = (scalars_df[left_col] + scalars_df[right_col]).compute()
    pd_result = scalars_pandas_df[left_col] + scalars_pandas_df[right_col]

    assert_series_equal_ignoring_order(pd_result, bf_result)


@pytest.mark.parametrize(
    ("left_col", "right_col", "righter_col"),
    [
        ("float64_col", "float64_col", "float64_col"),
        ("int64_col", "int64_col", "int64_col"),
    ],
)
def test_series_add_bigframes_series_nested(
    scalars_dfs, left_col, right_col, righter_col
):
    """Test that we can correctly add multiple times."""
    scalars_df, scalars_pandas_df = scalars_dfs
    bf_result = (
        (scalars_df[left_col] + scalars_df[right_col]) + scalars_df[righter_col]
    ).compute()
    pd_result = (
        scalars_pandas_df[left_col] + scalars_pandas_df[right_col]
    ) + scalars_pandas_df[righter_col]

    assert_series_equal_ignoring_order(pd_result, bf_result)


def test_series_add_different_table_no_index_value_error(
    scalars_df_no_index, scalars_df_2_no_index
):
    with pytest.raises(ValueError, match="scalars_too"):
        # Error should happen right away, not just at compute() time.
        scalars_df_no_index["float64_col"] + scalars_df_2_no_index["float64_col"]


def test_series_add_different_table_with_index(
    scalars_df_index, scalars_df_2_index, scalars_pandas_df_index
):
    scalars_pandas_df = scalars_pandas_df_index
    bf_result = scalars_df_index["float64_col"] + scalars_df_2_index["int64_col"]
    # When index values are unique, we can emulate with values from the same
    # DataFrame.
    pd_result = scalars_pandas_df["float64_col"] + scalars_pandas_df["int64_col"]
    pd.testing.assert_series_equal(bf_result.compute(), pd_result)


def test_series_add_pandas_series_not_implemented(scalars_dfs):
    scalars_df, _ = scalars_dfs
    with pytest.raises(TypeError):
        (
            scalars_df["float64_col"]
            + pd.Series(
                [1, 1, 1, 1],
            )
        ).compute()


def test_reverse(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs
    col_name = "string_col"
    bf_result = scalars_df[col_name].reverse().compute()
    pd_result = scalars_pandas_df[col_name].copy()
    for i in pd_result.index:
        cell = pd_result.loc[i]
        if pd.isna(cell):
            pd_result.loc[i] = None
        else:
            pd_result.loc[i] = cell[::-1]

    assert_series_equal_ignoring_order(
        pd_result,
        bf_result,
    )


def test_isnull(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs
    col_name = "float64_col"
    bf_series = scalars_df[col_name].isnull().compute()
    pd_series = scalars_pandas_df[col_name].isnull()

    # One of dtype mismatches to be documented. Here, the `bf_series.dtype` is `BooleanDtype` but
    # the `pd_series.dtype` is `bool`.
    assert_series_equal_ignoring_order(pd_series.astype(pd.BooleanDtype()), bf_series)


def test_notnull(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs
    col_name = "string_col"
    bf_series = scalars_df[col_name].notnull().compute()
    pd_series = scalars_pandas_df[col_name].notnull()

    # One of dtype mismatches to be documented. Here, the `bf_series.dtype` is `BooleanDtype` but
    # the `pd_series.dtype` is `bool`.
    assert_series_equal_ignoring_order(pd_series.astype(pd.BooleanDtype()), bf_series)


def test_round(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs
    col_name = "float64_col"
    bf_result = scalars_df[col_name].round().compute()
    pd_result = scalars_pandas_df[col_name].round()

    assert_series_equal_ignoring_order(pd_result, bf_result)


def test_eq_scalar(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs
    col_name = "int64_too"
    bf_result = scalars_df[col_name].eq(0).compute()
    pd_result = scalars_pandas_df[col_name].eq(0)

    assert_series_equal_ignoring_order(pd_result, bf_result)


def test_eq_wider_type_scalar(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs
    col_name = "int64_too"
    bf_result = scalars_df[col_name].eq(1.0).compute()
    pd_result = scalars_pandas_df[col_name].eq(1.0)

    assert_series_equal_ignoring_order(pd_result, bf_result)


def test_ne_scalar(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs
    col_name = "int64_too"
    bf_result = (scalars_df[col_name] != 0).compute()
    pd_result = scalars_pandas_df[col_name] != 0

    assert_series_equal_ignoring_order(pd_result, bf_result)


def test_eq_int_scalar(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs
    col_name = "int64_too"
    bf_result = (scalars_df[col_name] == 0).compute()
    pd_result = scalars_pandas_df[col_name] == 0

    assert_series_equal_ignoring_order(pd_result, bf_result)


@pytest.mark.parametrize(
    ("col_name",),
    (
        ("string_col",),
        ("float64_col",),
        ("int64_too",),
    ),
)
def test_eq_same_type_series(scalars_dfs, col_name):
    scalars_df, scalars_pandas_df = scalars_dfs
    col_name = "string_col"
    bf_result = (scalars_df[col_name] == scalars_df[col_name]).compute()
    pd_result = scalars_pandas_df[col_name] == scalars_pandas_df[col_name]

    # One of dtype mismatches to be documented. Here, the `bf_series.dtype` is `BooleanDtype` but
    # the `pd_series.dtype` is `bool`.
    assert_series_equal_ignoring_order(pd_result.astype(pd.BooleanDtype()), bf_result)


def test_loc_setitem_cell(scalars_df_index, scalars_pandas_df_index):
    bf_original = scalars_df_index["string_col"]
    bf_series = scalars_df_index["string_col"]
    pd_original = scalars_pandas_df_index["string_col"]
    pd_series = scalars_pandas_df_index["string_col"].copy()
    bf_series.loc[2] = "This value isn't in the test data."
    pd_series.loc[2] = "This value isn't in the test data."
    bf_result = bf_series.compute()
    pd_result = pd_series
    pd.testing.assert_series_equal(bf_result, pd_result)
    # Per Copy-on-Write semantics, other references to the original DataFrame
    # should remain unchanged.
    pd.testing.assert_series_equal(bf_original.compute(), pd_original)


def test_ne_obj_series(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs
    col_name = "string_col"
    bf_result = (scalars_df[col_name] != scalars_df[col_name]).compute()
    pd_result = scalars_pandas_df[col_name] != scalars_pandas_df[col_name]

    # One of dtype mismatches to be documented. Here, the `bf_series.dtype` is `BooleanDtype` but
    # the `pd_series.dtype` is `bool`.
    assert_series_equal_ignoring_order(pd_result.astype(pd.BooleanDtype()), bf_result)


def test_indexing_using_unselected_series(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs
    col_name = "string_col"
    bf_result = scalars_df[col_name][scalars_df["int64_too"].eq(0)].compute()
    pd_result = scalars_pandas_df[col_name][scalars_pandas_df["int64_too"].eq(0)]

    assert_series_equal_ignoring_order(
        pd_result,
        bf_result,
    )


def test_indexing_using_selected_series(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs
    col_name = "string_col"
    bf_result = scalars_df[col_name][
        scalars_df["string_col"].eq("Hello, World!")
    ].compute()
    pd_result = scalars_pandas_df[col_name][
        scalars_pandas_df["string_col"].eq("Hello, World!")
    ]

    assert_series_equal_ignoring_order(
        pd_result,
        bf_result,
    )


def test_nested_filter(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs
    string_col = scalars_df["string_col"]
    int64_too = scalars_df["int64_too"]
    bool_col = scalars_df["bool_col"]
    bf_result = string_col[int64_too == 0][~bool_col].compute()

    pd_string_col = scalars_pandas_df["string_col"]
    pd_int64_too = scalars_pandas_df["int64_too"]
    pd_bool_col = scalars_pandas_df["bool_col"] == bool(
        True
    )  # Convert from nullable bool to nonnullable bool usable as indexer
    pd_result = pd_string_col[pd_int64_too == 0][~pd_bool_col]

    assert_series_equal_ignoring_order(
        pd_result,
        bf_result,
    )


def test_binop_opposite_filters(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs
    int64_col1 = scalars_df["int64_col"]
    int64_col2 = scalars_df["int64_col"]
    bool_col = scalars_df["bool_col"]
    bf_result = (int64_col1[bool_col] + int64_col2[bool_col.__invert__()]).compute()

    pd_int64_col1 = scalars_pandas_df["int64_col"]
    pd_int64_col2 = scalars_pandas_df["int64_col"]
    pd_bool_col = scalars_pandas_df["bool_col"]
    pd_result = pd_int64_col1[pd_bool_col] + pd_int64_col2[pd_bool_col.__invert__()]

    assert_series_equal_ignoring_order(
        bf_result,
        pd_result,
    )


def test_binop_left_filtered(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs
    int64_col = scalars_df["int64_col"]
    float64_col = scalars_df["float64_col"]
    bool_col = scalars_df["bool_col"]
    bf_result = (int64_col[bool_col] + float64_col).compute()

    pd_int64_col = scalars_pandas_df["int64_col"]
    pd_float64_col = scalars_pandas_df["float64_col"]
    pd_bool_col = scalars_pandas_df["bool_col"]
    pd_result = pd_int64_col[pd_bool_col] + pd_float64_col

    assert_series_equal_ignoring_order(
        bf_result,
        pd_result,
    )


def test_binop_right_filtered(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs
    int64_col = scalars_df["int64_col"]
    float64_col = scalars_df["float64_col"]
    bool_col = scalars_df["bool_col"]
    bf_result = (float64_col + int64_col[bool_col]).compute()

    pd_int64_col = scalars_pandas_df["int64_col"]
    pd_float64_col = scalars_pandas_df["float64_col"]
    pd_bool_col = scalars_pandas_df["bool_col"]
    pd_result = pd_float64_col + pd_int64_col[pd_bool_col]

    assert_series_equal_ignoring_order(
        bf_result,
        pd_result,
    )


def test_mean(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs
    col_name = "int64_col"
    bf_result = scalars_df[col_name].mean().compute()
    pd_result = scalars_pandas_df[col_name].mean()
    assert math.isclose(pd_result, bf_result)


def test_repr(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs
    if scalars_pandas_df.index.name != "rowindex":
        pytest.skip("Require index & ordering for consistent repr.")

    col_name = "int64_col"
    bf_series = scalars_df[col_name]
    pd_series = scalars_pandas_df[col_name]
    assert repr(bf_series) == repr(pd_series)


def test_sum(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs
    col_name = "int64_col"
    bf_result = scalars_df[col_name].sum().compute()
    pd_result = scalars_pandas_df[col_name].sum()
    assert pd_result == bf_result


def test_count(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs
    col_name = "int64_col"
    bf_result = scalars_df[col_name].count().compute()
    pd_result = scalars_pandas_df[col_name].count()
    assert pd_result == bf_result


def test_all(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs
    col_name = "int64_col"
    bf_result = scalars_df[col_name].all().compute()
    pd_result = scalars_pandas_df[col_name].all()
    assert pd_result == bf_result


def test_any(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs
    col_name = "int64_col"
    bf_result = scalars_df[col_name].any().compute()
    pd_result = scalars_pandas_df[col_name].any()
    assert pd_result == bf_result


def test_groupby_sum(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs
    col_name = "int64_too"
    bf_series = scalars_df[col_name].groupby(scalars_df["string_col"]).sum()
    pd_series = (
        scalars_pandas_df[col_name].groupby(scalars_pandas_df["string_col"]).sum()
    )
    # TODO(swast): Update groupby to use index based on group by key(s).
    bf_result = bf_series.compute()
    assert_series_equal_ignoring_order(
        pd_series,
        bf_result,
        check_exact=False,
    )


def test_groupby_level_sum(scalars_dfs):
    # TODO(tbergeron): Use a non-unique index once that becomes possible in tests
    scalars_df, scalars_pandas_df = scalars_dfs
    col_name = "int64_too"
    if scalars_pandas_df.index.name != "rowindex":
        pytest.skip("Require index for groupby level.")

    bf_series = scalars_df[col_name].groupby(level=0).sum()
    pd_series = scalars_pandas_df[col_name].groupby(level=0).sum()
    # TODO(swast): Update groupby to use index based on group by key(s).
    pd.testing.assert_series_equal(
        pd_series.sort_index(),
        bf_series.compute().sort_index(),
    )


def test_groupby_level_list_sum(scalars_dfs):
    # TODO(tbergeron): Use a non-unique index once that becomes possible in tests
    scalars_df, scalars_pandas_df = scalars_dfs
    col_name = "int64_too"
    if scalars_pandas_df.index.name != "rowindex":
        pytest.skip("Require index for groupby level.")

    bf_series = scalars_df[col_name].groupby(level=["rowindex"]).sum()
    pd_series = scalars_pandas_df[col_name].groupby(level=["rowindex"]).sum()
    # TODO(swast): Update groupby to use index based on group by key(s).
    pd.testing.assert_series_equal(
        pd_series.sort_index(),
        bf_series.compute().sort_index(),
    )


def test_groupby_mean(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs
    col_name = "int64_too"
    bf_series = (
        scalars_df[col_name].groupby(scalars_df["string_col"], dropna=False).mean()
    )
    pd_series = (
        scalars_pandas_df[col_name]
        .groupby(scalars_pandas_df["string_col"], dropna=False)
        .mean()
    )
    # TODO(swast): Update groupby to use index based on group by key(s).
    bf_result = bf_series.compute()
    assert_series_equal_ignoring_order(
        pd_series,
        bf_result,
    )


@pytest.mark.parametrize(
    ("operator"),
    [
        (lambda x: x.cumsum()),
        (lambda x: x.cumcount()),
        (lambda x: x.cummin()),
        (lambda x: x.cummax()),
    ],
    ids=[
        "cumsum",
        "cumcount",
        "cummin",
        "cummax",
    ],
)
def test_groupby_cumulative_ops(scalars_df_index, scalars_pandas_df_index, operator):
    col_name = "int64_col"
    group_key = "int64_too"  # has some duplicates values, good for grouping
    bf_series = (
        operator(scalars_df_index[col_name].groupby(scalars_df_index[group_key]))
    ).compute()
    pd_series = operator(
        scalars_pandas_df_index[col_name].groupby(scalars_pandas_df_index[group_key])
    ).astype(pd.Int64Dtype())
    print(pd_series)
    print(bf_series)
    pd.testing.assert_series_equal(
        pd_series,
        bf_series,
    )


@pytest.mark.parametrize(
    ["start", "stop"], [(0, 1), (3, 5), (100, 101), (None, 1), (0, 12), (0, None)]
)
def test_slice(scalars_dfs, start, stop):
    scalars_df, scalars_pandas_df = scalars_dfs
    col_name = "string_col"
    bf_series = scalars_df[col_name]
    bf_result = bf_series.slice(start, stop).compute()
    pd_series = scalars_pandas_df[col_name]
    pd_result = pd_series.str.slice(start, stop)

    assert_series_equal_ignoring_order(
        pd_result,
        bf_result,
    )


def test_head(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs

    if not isinstance(scalars_df.index, bigframes.core.indexes.Index):
        pytest.skip("Require explicit index for offset ops.")

    bf_result = scalars_df["string_col"].head(2).compute()
    pd_result = scalars_pandas_df["string_col"].head(2)

    assert_series_equal_ignoring_order(
        pd_result,
        bf_result,
    )


def test_head_then_scalar_operation(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs

    if not isinstance(scalars_df.index, bigframes.core.indexes.Index):
        pytest.skip("Require explicit index for offset ops.")

    bf_result = (scalars_df["float64_col"].head(1) + 4).compute()
    pd_result = scalars_pandas_df["float64_col"].head(1) + 4

    pd.testing.assert_series_equal(
        bf_result,
        pd_result,
    )


def test_head_then_series_operation(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs

    if not isinstance(scalars_df.index, bigframes.core.indexes.Index):
        pytest.skip("Require explicit index for offset ops.")

    bf_result = (
        scalars_df["float64_col"].head(4) + scalars_df["float64_col"].head(2)
    ).compute()
    pd_result = scalars_pandas_df["float64_col"].head(4) + scalars_pandas_df[
        "float64_col"
    ].head(2)

    pd.testing.assert_series_equal(
        bf_result,
        pd_result,
    )


def test_cumsum_int(scalars_df_index, scalars_pandas_df_index):
    if pd.__version__.startswith("1."):
        pytest.skip("Series.cumsum NA mask are different in pandas 1.x.")

    col_name = "int64_col"
    bf_result = scalars_df_index[col_name].cumsum().compute()
    # cumsum does not behave well on nullable ints in pandas, produces object type and never ignores NA
    pd_result = scalars_pandas_df_index[col_name].cumsum().astype(pd.Int64Dtype())

    pd.testing.assert_series_equal(
        bf_result,
        pd_result,
    )


def test_cumsum_int_filtered(scalars_df_index, scalars_pandas_df_index):
    col_name = "int64_col"

    bf_col = scalars_df_index[col_name]
    bf_result = bf_col[bf_col > -2].cumsum().compute()

    pd_col = scalars_pandas_df_index[col_name]
    # cumsum does not behave well on nullable ints in pandas, produces object type and never ignores NA
    pd_result = pd_col[pd_col > -2].cumsum().astype(pd.Int64Dtype())

    pd.testing.assert_series_equal(
        bf_result,
        pd_result,
    )


def test_cumsum_float(scalars_df_index, scalars_pandas_df_index):
    col_name = "float64_col"
    bf_result = scalars_df_index[col_name].cumsum().compute()
    # cumsum does not behave well on nullable floats in pandas, produces object type and never ignores NA
    pd_result = scalars_pandas_df_index[col_name].cumsum().astype(pd.Float64Dtype())

    pd.testing.assert_series_equal(
        bf_result,
        pd_result,
    )


def test_cummin_int(scalars_df_index, scalars_pandas_df_index):
    col_name = "int64_col"
    bf_result = scalars_df_index[col_name].cummin().compute()
    pd_result = scalars_pandas_df_index[col_name].cummin()

    pd.testing.assert_series_equal(
        bf_result,
        pd_result,
    )


def test_cummax_int(scalars_df_index, scalars_pandas_df_index):
    col_name = "int64_col"
    bf_result = scalars_df_index[col_name].cummax().compute()
    pd_result = scalars_pandas_df_index[col_name].cummax()

    pd.testing.assert_series_equal(
        bf_result,
        pd_result,
    )


def test_value_counts(scalars_dfs):
    scalars_df, scalars_pandas_df = scalars_dfs
    col_name = "int64_too"

    bf_result = scalars_df[col_name].value_counts().compute()
    pd_result = scalars_pandas_df[col_name].value_counts()

    # Older pandas version may not have these values, bigframes tries to emulate 2.0+
    pd_result.name = "count"
    pd_result.index.name = col_name

    pd.testing.assert_series_equal(
        bf_result,
        pd_result,
    )


def test_iloc_nested(scalars_df_index, scalars_pandas_df_index):

    bf_result = scalars_df_index["string_col"].iloc[1:].iloc[1:].compute()
    pd_result = scalars_pandas_df_index["string_col"].iloc[1:].iloc[1:]

    pd.testing.assert_series_equal(
        bf_result,
        pd_result,
    )


@pytest.mark.parametrize(
    ("start", "stop", "step"),
    [
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
def test_iloc(scalars_df_index, scalars_pandas_df_index, start, stop, step):
    bf_result = scalars_df_index["string_col"].iloc[start:stop:step].compute()
    pd_result = scalars_pandas_df_index["string_col"].iloc[start:stop:step]

    # Pandas may assign non-object dtype to empty series and series index
    if pd_result.empty:
        pd_result = pd_result.astype("object")
        pd_result.index = pd_result.index.astype("object")

    pd.testing.assert_series_equal(
        bf_result,
        pd_result,
    )
