import numpy
import pandas
import pytest
import pandas as pd


@pytest.mark.parametrize(
    ["col_name", "expected_dtype"],
    [
        # TODO(swast): Use pandas.BooleanDtype() to represent nullable bool.
        ("bool_col", numpy.dtype("object")),
        # TODO(swast): Use a more efficient type.
        ("bytes_col", numpy.dtype("object")),
        # TODO(swast): Update ibis-bigquery backend to use
        # db_dtypes.DateDtype() when available.
        ("date_col", numpy.dtype("datetime64[ns]")),
        ("datetime_col", numpy.dtype("datetime64[ns]")),
        ("float64_col", numpy.dtype("float64")),
        ("geography_col", numpy.dtype("object")),
        # TODO(swast): Don't accidentally discard data if NULL is present by
        # casting to float.
        ("int64_col", numpy.dtype("float64")),
        # TODO(swast): Use a more efficient type.
        ("numeric_col", numpy.dtype("object")),
        # TODO(swast): Use a consistent dtype for integers whether NULL is
        # present or not.
        ("rowindex", numpy.dtype("int64")),
        # TODO(swast): Use a more efficient type.
        ("string_col", numpy.dtype("object")),
        # TODO(swast): Update ibis-bigquery backend to use
        # db_dtypes.TimeDtype() when available.
        ("time_col", numpy.dtype("object")),
        # TODO(swast): Make sure timestamps are associated with UTC timezone.
        ("timestamp_col", numpy.dtype("datetime64[ns]")),
    ],
)
def test_get_column(scalars_df, scalars_load_job, col_name, expected_dtype):
    series = scalars_df[col_name]
    series_pandas = series.compute()
    assert series_pandas.dtype == expected_dtype
    # TODO(swast): Compare lengths with DataFrame length computed by Bigframes.
    assert series_pandas.shape[0] == scalars_load_job.output_rows


def test_lower(scalars_df):
    col_name = "string_col"
    series = scalars_df[col_name]
    series_pandas = series.lower().compute()
    pd.testing.assert_series_equal(
        series_pandas, pd.Series(["hello, world!", "こんにちは", None], name=col_name)
    )


def test_upper(scalars_df):
    col_name = "string_col"
    series = scalars_df[col_name]
    series_pandas = series.upper().compute()
    pd.testing.assert_series_equal(
        series_pandas, pd.Series(["HELLO, WORLD!", "こんにちは", None], name=col_name)
    )

@pytest.mark.parametrize(
    ("other",),
    [
        (3,),
        (-6.2,),
        (
            pandas.Series(
                [
                    1,
                    1,
                    1,
                ],
                index=["a", "b", "c"],
            ),
        ),
    ],
)
def test_series_add(scalars_df, other):
    result = scalars_df["float64_col"] + other
    # TODO: how to check result?
    assert result == ""


@pytest.mark.parametrize(
    ("other",),
    [
        ("str",),
        (numpy.array([1, 2, 3, 4]),),
        (pandas.Series(["f", "j", "h"], index=["a", "b", "c"]),),
    ],
)
def test_series_add_invalid_type_error(scalars_df, other):
    result = scalars_df["float64_col"] + other
    # TODO: how to check result?
    assert result == ""
