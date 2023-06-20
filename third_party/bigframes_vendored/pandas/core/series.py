"""
Data structure for 1-dimensional cross-sectional and time series data
"""
from __future__ import annotations

from typing import Hashable, IO, Literal, Mapping, Sequence, TYPE_CHECKING

import numpy as np
from pandas._libs import lib
from pandas._typing import Axis, FilePath, NaPosition, WriteBuffer
import pandas.io.formats.format as fmt

from third_party.bigframes_vendored.pandas.core.generic import NDFrame

if TYPE_CHECKING:
    from pandas.core.groupby.generic import SeriesGroupBy

    from third_party.bigframes_vendored.pandas.core.frame import DataFrame


class Series(NDFrame):  # type: ignore[misc]
    @property
    def dt(self):
        """
        Accessor object for datetimelike properties of the Series values.
        """
        raise NotImplementedError("abstract property")

    @property
    def index(self):
        """The index (axis labels) of the Series."""
        raise NotImplementedError("abstract property")

    @property
    def shape(self):
        """Return a tuple of the shape of the underlying data."""
        raise NotImplementedError("abstract property")

    @property
    def dtype(self):
        """
        Return the dtype object of the underlying data.
        """
        raise NotImplementedError("abstract property")

    @property
    def dtypes(self):
        """
        Return the dtype object of the underlying data.
        """
        raise NotImplementedError("abstract property")

    @property
    def name(self) -> Hashable:
        """
        Return the name of the Series.

        The name of a Series becomes its index or column name if it is used
        to form a DataFrame. It is also used whenever displaying the Series
        using the interpreter.

        Returns
        -------
        label (hashable object)
            The name of the Series, also the column name if part of a DataFrame.
        """
        raise NotImplementedError("abstract property")

    def reset_index(
        self,
        *,
        drop: bool = False,
        name=lib.no_default,
    ) -> DataFrame | Series | None:
        """
        Generate a new DataFrame or Series with the index reset.

        This is useful when the index needs to be treated as a column, or
        when the index is meaningless and needs to be reset to the default
        before another operation.

        Parameters
        ----------
        drop : bool, default False
            Just reset the index, without inserting it as a column in
            the new DataFrame.
        name : object, optional
            The name to use for the column containing the original Series
            values. Uses ``self.name`` by default. This argument is ignored
            when `drop` is True.

        Returns
        -------
        Series or DataFrame or None
            When `drop` is False (the default), a DataFrame is returned.
            The newly created columns will come first in the DataFrame,
            followed by the original Series values.
            When `drop` is True, a `Series` is returned.
            In either case, if ``inplace=True``, no value is returned.

        """
        raise NotImplementedError("abstract method")

    def __repr__(self) -> str:
        """
        Return a string representation for a particular Series.
        """
        raise NotImplementedError("abstract method")

    # ----------------------------------------------------------------------
    # IO methods (to / from other formats)

    def to_string(
        self,
        buf: FilePath | WriteBuffer[str] | None = None,
        na_rep: str = "NaN",
        float_format: str | None = None,
        header: bool = True,
        index: bool = True,
        length: bool = False,
        dtype: bool = False,
        name: bool = False,
        max_rows: int | None = None,
        min_rows: int | None = None,
    ) -> str | None:
        """
        Render a string representation of the Series.

        Parameters
        ----------
        buf : StringIO-like, optional
            Buffer to write to.
        na_rep : str, optional
            String representation of NaN to use, default 'NaN'.
        float_format : one-parameter function, optional
            Formatter function to apply to columns' elements if they are
            floats, default None.
        header : bool, default True
            Add the Series header (index name).
        index : bool, optional
            Add index (row) labels, default True.
        length : bool, default False
            Add the Series length.
        dtype : bool, default False
            Add the Series dtype.
        name : bool, default False
            Add the Series name if not None.
        max_rows : int, optional
            Maximum number of rows to show before truncating. If None, show
            all.
        min_rows : int, optional
            The number of rows to display in a truncated repr (when number
            of rows is above `max_rows`).

        Returns
        -------
        str or None
            String representation of Series if ``buf=None``, otherwise None.
        """
        formatter = fmt.SeriesFormatter(
            self,
            name=name,
            length=length,
            header=header,
            index=index,
            dtype=dtype,
            na_rep=na_rep,
            float_format=float_format,
            min_rows=min_rows,
            max_rows=max_rows,
        )
        result = formatter.to_string()

        # catch contract violations
        raise NotImplementedError("abstract method")

    def to_markdown(
        self,
        buf: IO[str] | None = None,
        mode: str = "wt",
        index: bool = True,
        **kwargs,
    ) -> str | None:
        """
        Print {klass} in Markdown-friendly format.

        Parameters
        ----------
        buf : str, Path or StringIO-like, optional, default None
            Buffer to write to. If None, the output is returned as a string.
        mode : str, optional
            Mode in which file is opened, "wt" by default.
        index : bool, optional, default True
            Add index (row) labels.
        Returns
        -------
        str
            {klass} in Markdown-friendly format.
        """
        raise NotImplementedError("abstract method")

    def to_dict(self, into: type[dict] = dict) -> Mapping:
        """
        Convert Series to {label -> value} dict or dict-like object.

        Parameters
        ----------
        into : class, default dict
            The collections.abc.Mapping subclass to use as the return
            object. Can be the actual class or an empty
            instance of the mapping type you want.  If you want a
            collections.defaultdict, you must pass it initialized.

        Returns
        -------
        collections.abc.Mapping
            Key-value representation of Series.
        """
        raise NotImplementedError("abstract method")

    def to_frame(self) -> DataFrame:
        """
        Convert Series to DataFrame.

        Returns
        -------
        DataFrame
            DataFrame representation of Series.
        """
        raise NotImplementedError("abstract method")

    def to_excel(self, excel_writer, sheet_name):
        """
        Write Series to an Excel sheet.

        To write a single Series to an Excel .xlsx file it is only necessary to
        specify a target file name. To write to multiple sheets it is necessary to
        create an `ExcelWriter` object with a target file name, and specify a sheet
        in the file to write to.

        Multiple sheets may be written to by specifying unique `sheet_name`.
        With all data written to the file it is necessary to save the changes.
        Note that creating an `ExcelWriter` object with a file name that already
        exists will result in the contents of the existing file being erased.

        Parameters
        ----------
        excel_writer : path-like, file-like, or ExcelWriter object
            File path or existing ExcelWriter.
        sheet_name : str, default 'Sheet1'
            Name of sheet which will contain DataFrame.
        """
        raise NotImplementedError("abstract method")

    def to_latex(self, buf=None, columns=None, header=True, index=True, **kwargs):
        """
        Render object to a LaTeX tabular, longtable, or nested table.

        Parameters
        ----------
        buf : str, Path or StringIO-like, optional, default None
            Buffer to write to. If None, the output is returned as a string.
        columns : list of label, optional
            The subset of columns to write. Writes all columns by default.
        header : bool or list of str, default True
            Write out the column names. If a list of strings is given,
            it is assumed to be aliases for the column names.
        index : bool, default True
            Write row names (index).


        Returns
        -------
        str or None
            If buf is None, returns the result as a string. Otherwise returns None.
        """
        raise NotImplementedError("abstract method")

    def tolist(self) -> list:
        """
        Return a list of the values.

        These are each a scalar type, which is a Python scalar
        (for str, int, float) or a pandas scalar
        (for Timestamp/Timedelta/Interval/Period)

        Returns
        -------
        list
        """
        raise NotImplementedError("abstract method")

    to_list = tolist

    def to_numpy(self, dtype, copy=False, na_value=None):
        """
        A NumPy ndarray representing the values in this Series or Index.

        Parameters
        ----------
        dtype : str or numpy.dtype, optional
            The dtype to pass to :meth:`numpy.asarray`.
        copy : bool, default False
            Whether to ensure that the returned value is not a view on
            another array. Note that ``copy=False`` does not *ensure* that
            ``to_numpy()`` is no-copy. Rather, ``copy=True`` ensure that
            a copy is made, even if not strictly necessary.
        na_value : Any, optional
            The value to use for missing values. The default value depends
            on `dtype` and the type of the array.
        **kwargs
            Additional keywords passed through to the ``to_numpy`` method
            of the underlying array (for extension arrays).

        Returns
        -------
        numpy.ndarray
        """
        raise NotImplementedError("abstract method")

    def to_pickle(self, path, **kwargs):
        """
        Pickle (serialize) object to file.

        Parameters
        ----------
        path : str, path object, or file-like object
            String, path object (implementing ``os.PathLike[str]``), or file-like
            object implementing a binary ``write()`` function. File path where
            the pickled object will be stored.
        """
        raise NotImplementedError("abstract method")

    def to_xarray(self):
        """
        Return an xarray object from the pandas object.

        Returns
        -------
        xarray.DataArray or xarray.Dataset
            Data in the pandas structure converted to Dataset if the object is
            a DataFrame, or a DataArray if the object is a Series.
        """
        raise NotImplementedError("abstract method")

    def to_json(
        self,
        path_or_buf=None,
        orient: Literal[
            "split", "records", "index", "columns", "values", "table"
        ] = "columns",
        **kwarg,
    ) -> str | None:
        """
        Convert the object to a JSON string.

        Note NaN's and None will be converted to null and datetime objects
        will be converted to UNIX timestamps.

        Parameters
        ----------
        path_or_buf : str, path object, file-like object, or None, default None
            String, path object (implementing os.PathLike[str]), or file-like
            object implementing a write() function. If None, the result is
            returned as a string.
        orient:
            Indication of expected JSON string format.

            * Series:

                - default is 'index'
                - allowed values are: {{'split', 'records', 'index', 'table'}}.

            * DataFrame:

                - default is 'columns'
                - allowed values are: {{'split', 'records', 'index', 'columns',
                    'values', 'table'}}.

            * The format of the JSON string:

                - 'split' : dict like {{'index' -> [index], 'columns' -> [columns],
                    'data' -> [values]}}
                - 'records' : list like [{{column -> value}}, ... , {{column -> value}}]
                - 'index' : dict like {{index -> {{column -> value}}}}
                - 'columns' : dict like {{column -> {{index -> value}}}}
                - 'values' : just the values array
                - 'table' : dict like {{'schema': {{schema}}, 'data': {{data}}}}

                Describing the data, where data component is like ``orient='records'``.

        Returns
        -------
        None or str
            If path_or_buf is None, returns the resulting json format as a
            string. Otherwise returns None.
        """
        raise NotImplementedError("abstract method")

    def to_csv(self, path_or_buf: str, *, index: bool = True) -> str | None:
        """
        Write object to a comma-separated values (csv) file.

        Parameters
        ----------
        path_or_buf : str, path object, file-like object, or None, default None
            String, path object (implementing os.PathLike[str]), or file-like
            object implementing a write() function. If None, the result is
            returned as a string. If a non-binary file object is passed, it should
            be opened with `newline=''`, disabling universal newlines. If a binary
            file object is passed, `mode` might need to contain a `'b'`.

        Returns
        -------
        None or str
            If path_or_buf is None, returns the resulting csv format as a
            string. Otherwise returns None.
        """
        raise NotImplementedError("abstract method")

    def count(self):
        """
        Return number of non-NA/null observations in the Series.

        Returns
        -------
        int or Series (if level specified)
            Number of non-null values in the Series.
        """
        raise NotImplementedError("abstract method")

    def mode(self) -> Series:
        """
        Return the mode(s) of the Series.

        The mode is the value that appears most often. There can be multiple modes.

        Always returns Series even if only one value is returned.

        Returns
        -------
        Series
            Modes of the Series in sorted order.
        """
        raise NotImplementedError("abstract method")

    def drop_duplicates(
        self,
        *,
        keep="first",
    ) -> Series | None:
        """
        Return Series with duplicate values removed.

        Parameters
        ----------
        keep : {'first', 'last', ``False``}, default 'first'
            Method to handle dropping duplicates:

            - 'first' : Drop duplicates except for the first occurrence.
            - 'last' : Drop duplicates except for the last occurrence.
            - ``False`` : Drop all duplicates.

        Returns
        -------
        Series or None
            Series with duplicates dropped or None if ``inplace=True``.
        """
        raise NotImplementedError("abstract method")

    def round(self, decimals: int = 0) -> Series:
        """
        Round each value in a Series to the given number of decimals.

        Parameters
        ----------
        decimals : int, default 0
            Number of decimal places to round to. If decimals is negative,
            it specifies the number of positions to the left of the decimal point.

        Returns
        -------
        Series
            Rounded values of the Series.
        """
        raise NotImplementedError("abstract method")

    def diff(self) -> Series:
        """
        First discrete difference of element.

        Calculates the difference of a {klass} element compared with another
        element in the {klass} (default is element in previous row).

        Returns
        -------
        {klass}
            First differences of the Series.
        """
        raise NotImplementedError("abstract method")

    def dot(self, other) -> Series | np.ndarray:
        """
        Compute the dot product between the Series and the columns of other.

        This method computes the dot product between the Series and another
        one, or the Series and each columns of a DataFrame, or the Series and
        each columns of an array.

        It can also be called using `self @ other` in Python >= 3.5.

        Parameters
        ----------
        other : Series, DataFrame or array-like
            The other object to compute the dot product with its columns.

        Returns
        -------
        scalar, Series or numpy.ndarray
            Return the dot product of the Series and other if other is a
            Series, the Series of the dot product of Series and each rows of
            other if other is a DataFrame or a numpy.ndarray between the Series
            and each columns of the numpy array.

        Notes
        -----
        The Series and other has to share the same index if other is a Series
        or a DataFrame.

        """
        raise NotImplementedError("abstract method")

    def __matmul__(self, other):
        """
        Matrix multiplication using binary `@` operator in Python>=3.5.
        """
        raise NotImplementedError("abstract method")

    def __rmatmul__(self, other):
        """
        Matrix multiplication using binary `@` operator in Python>=3.5.
        """
        raise NotImplementedError("abstract method")

    def sort_values(
        self,
        *,
        axis: Axis = 0,
        ascending: bool | int | Sequence[bool] | Sequence[int] = True,
        na_position: str = "last",
    ) -> Series | None:
        """
        Sort by the values.

        Sort a Series in ascending or descending order by some
        criterion.

        Parameters
        ----------
        axis : {0 or 'index'}
            Unused. Parameter needed for compatibility with DataFrame.
        ascending : bool or list of bools, default True
            If True, sort values in ascending order, otherwise descending.
        na_position : {'first' or 'last'}, default 'last'
            Argument 'first' puts NaNs at the beginning, 'last' puts NaNs at
            the end.

        Returns
        -------
        Series or None
            Series ordered by values or None if ``inplace=True``.
        """
        raise NotImplementedError("abstract method")

    def sort_index(
        self,
        *,
        axis: Axis = 0,
        ascending: bool | Sequence[bool] = True,
        na_position: NaPosition = "last",
    ) -> Series | None:
        """
        Sort Series by index labels.

        Returns a new Series sorted by label if `inplace` argument is
        ``False``, otherwise updates the original series and returns None.

        Parameters
        ----------
        axis : {0 or 'index'}
            Unused. Parameter needed for compatibility with DataFrame.
        ascending : bool or list-like of bools, default True
            Sort ascending vs. descending. When the index is a MultiIndex the
            sort direction can be controlled for each level individually.
        na_position : {'first', 'last'}, default 'last'
            If 'first' puts NaNs at the beginning, 'last' puts NaNs at the end.
            Not implemented for MultiIndex.

        Returns
        -------
        Series or None
            The original Series sorted by the labels or None if ``inplace=True``.

        """

        raise NotImplementedError("abstract method")

    def nlargest(
        self, n: int = 5, keep: Literal["first", "last", "all"] = "first"
    ) -> Series:
        """
        Return the largest `n` elements.

        Parameters
        ----------
        n : int, default 5
            Return this many descending sorted values.
        keep : {'first', 'last', 'all'}, default 'first'
            When there are duplicate values that cannot all fit in a
            Series of `n` elements:

            - ``first`` : return the first `n` occurrences in order
              of appearance.
            - ``last`` : return the last `n` occurrences in reverse
              order of appearance.
            - ``all`` : keep all occurrences. This can result in a Series of
              size larger than `n`.

        Returns
        -------
        Series
            The `n` largest values in the Series, sorted in decreasing order.
        """
        raise NotImplementedError("abstract method")

    def nsmallest(self, n: int = 5, keep: str = "first") -> Series:
        """
        Return the smallest `n` elements.

        Parameters
        ----------
        n : int, default 5
            Return this many ascending sorted values.
        keep : {'first', 'last', 'all'}, default 'first'
            When there are duplicate values that cannot all fit in a
            Series of `n` elements:

            - ``first`` : return the first `n` occurrences in order
              of appearance.
            - ``last`` : return the last `n` occurrences in reverse
              order of appearance.
            - ``all`` : keep all occurrences. This can result in a Series of
              size larger than `n`.

        Returns
        -------
        Series
            The `n` smallest values in the Series, sorted in increasing order.
        """
        raise NotImplementedError("abstract method")

    # ----------------------------------------------------------------------
    # function application

    def apply(
        self,
        func,
    ) -> DataFrame | Series:
        """
        Invoke function on values of Series.

        Can be ufunc (a NumPy function that applies to the entire Series)
        or a Python function that only works on single values.

        Parameters
        ----------
        func : function
            Python function or NumPy ufunc to apply.
        Returns
        -------
        Series or DataFrame
            If func returns a Series object the result will be a DataFrame.
        """
        raise NotImplementedError("abstract method")

    def groupby(
        self,
        by=None,
        axis: Axis = 0,
        level=None,
        as_index: bool = True,
        *,
        dropna: bool = True,
    ) -> SeriesGroupBy:
        """Group Series using a mapper or by a Series of columns.

        A groupby operation involves some combination of splitting the
        object, applying a function, and combining the results. This can be
        used to group large amounts of data and compute operations on these
        groups.

        Parameters
        ----------
        by : mapping, function, label, pd.Grouper or list of such
            Used to determine the groups for the groupby.
            If ``by`` is a function, it's called on each value of the object's
            index. If a dict or Series is passed, the Series or dict VALUES
            will be used to determine the groups (the Series' values are first
            aligned; see ``.align()`` method). If a list or ndarray of length
            equal to the selected axis is passed (see the `groupby user guide
            <https://pandas.pydata.org/pandas-docs/stable/user_guide/groupby.html#splitting-an-object-into-groups>`_),
            the values are used as-is to determine the groups. A label or list
            of labels may be passed to group by the columns in ``self``.
            Notice that a tuple is interpreted as a (single) key.
        axis : {0 or 'index', 1 or 'columns'}, default 0
            Split along rows (0) or columns (1). For `Series` this parameter
            is unused and defaults to 0.
        level : int, level name, or sequence of such, default None
            If the axis is a MultiIndex (hierarchical), group by a particular
            level or levels. Do not specify both ``by`` and ``level``.
        as_index : bool, default True
            Return object with group labels as the
            index. Only relevant for DataFrame input. as_index=False is
            effectively "SQL-style" grouped output. This argument has no effect
            on filtrations (see the `filtrations in the user guide
            <https://pandas.pydata.org/docs/dev/user_guide/groupby.html#filtration>`_),
            such as ``head()``, ``tail()``, ``nth()`` and in transformations
            (see the `transformations in the user guide
            <https://pandas.pydata.org/docs/dev/user_guide/groupby.html#transformation>`_).
        dropna : bool, default True
            If True, and if group keys contain NA values, NA values together
            with row/column will be dropped.
            If False, NA values will also be treated as the key in groups.

        Returns
        -------
        SeriesGroupBy
            Returns a groupby object that contains information about the groups.
        """
        raise NotImplementedError("abstract method")

    def drop(
        self,
        labels=None,
    ) -> Series | None:
        """
        Return Series with specified index labels removed.

        Remove elements of a Series based on specifying the index labels.
        When using a multi-index, labels on different levels can be removed
        by specifying the level.

        Parameters
        ----------
        labels : single label or list-like
            Index labels to drop.

        Returns
        -------
        Series or None
            Series with specified index labels removed or None if ``inplace=True``.

        Raises
        ------
        KeyError
            If none of the labels are found in the index.
        """
        raise NotImplementedError("abstract method")

    def fillna(
        self,
        value=None,
    ) -> Series | None:
        raise NotImplementedError("abstract method")

    def between(
        self,
        left,
        right,
        inclusive: Literal["both", "neither", "left", "right"] = "both",
    ) -> Series:
        """
        Return boolean Series equivalent to left <= series <= right.

        This function returns a boolean vector containing `True` wherever the
        corresponding Series element is between the boundary values `left` and
        `right`. NA values are treated as `False`.

        Parameters
        ----------
        left : scalar or list-like
            Left boundary.
        right : scalar or list-like
            Right boundary.
        inclusive : {"both", "neither", "left", "right"}
            Include boundaries. Whether to set each bound as closed or open.

        Returns
        -------
        Series
            Series representing whether each element is between left and
            right (inclusive).

        """
        raise NotImplementedError("abstract method")

    def cumsum(self):
        """
        Return cumulative sum over a DataFrame or Series axis.

        Returns a DataFrame or Series of the same size containing the cumulative
        sum.

        Parameters
        ----------
        axis : {{0 or 'index', 1 or 'columns'}}, default 0
            The index or the name of the axis. 0 is equivalent to None or 'index'.
            For `Series` this parameter is unused and defaults to 0.

        Returns
        -------
        scalar or Series
            Return cumulative sum of scalar or Series.
        """
        raise NotImplementedError("abstract method")

    def cummax(self):
        """
        Return cumulative maximum over a DataFrame or Series axis.

        Returns a DataFrame or Series of the same size containing the cumulative
        maximum.

        Parameters
        ----------
        axis : {{0 or 'index', 1 or 'columns'}}, default 0
            The index or the name of the axis. 0 is equivalent to None or 'index'.
            For `Series` this parameter is unused and defaults to 0.

        Returns
        -------
        scalar or Series
            Return cumulative maximum of scalar or Series.
        """
        raise NotImplementedError("abstract method")

    def cummin(self):
        """
        Return cumulative minimum over a DataFrame or Series axis.

        Returns a DataFrame or Series of the same size containing the cumulative
        minimum.

        Parameters
        ----------
        axis : {{0 or 'index', 1 or 'columns'}}, default 0
            The index or the name of the axis. 0 is equivalent to None or 'index'.
            For `Series` this parameter is unused and defaults to 0.
        skipna : bool, default True
            Exclude NA/null values. If an entire row/column is NA, the result
            will be NA.
        *args, **kwargs
            Additional keywords have no effect but might be accepted for
            compatibility with NumPy.

        Returns
        -------
        scalar or Series
            Return cumulative minimum of scalar or Series.
        """
        raise NotImplementedError("abstract method")

    def eq(self, other) -> Series:
        """Return Equal of series and other, element-wise (binary operator eq).

        Equivalent to ``other == series``, but with support to substitute a fill_value for
        missing data in either one of the inputs.

        Args:
            other: Series, or scalar value

        Returns:
            Series. The result of the operation.

        """
        raise NotImplementedError("abstract method")

    def ne(self, other) -> Series:
        """Return Not equal of series and other, element-wise (binary operator ne).

        Equivalent to ``other != series``, but with support to substitute a fill_value for
        missing data in either one of the inputs.

        Args:
            other: Series, or scalar value

        Returns:
            Series. The result of the comparison.

        """
        raise NotImplementedError("abstract method")

    def le(self, other) -> Series:
        """Get 'less than or equal to' of series and other, element-wise (binary operator `<=`).

        Equivalent to ``series <= other``, but with support to substitute a fill_value for
        missing data in either one of the inputs.

        Args:
            other: Series, or scalar value

        Returns:
            Series. The result of the comparison.

        """
        raise NotImplementedError("abstract method")

    def lt(self, other) -> Series:
        """Get 'less than' of series and other, element-wise (binary operator `<`).

        Equivalent to ``series < other``, but with support to substitute a fill_value for
        missing data in either one of the inputs.

        Args:
            other: Series, or scalar value

        Returns:
            Series. The result of the comparison.

        """
        raise NotImplementedError("abstract method")

    def ge(self, other) -> Series:
        """Get 'greater than or equal to' of series and other, element-wise (binary operator `>=`).

        Equivalent to ``series >= other``, but with support to substitute a fill_value for
        missing data in either one of the inputs.

        Args:
            other: Series, or scalar value

        Returns:
            Series. The result of the comparison.

        """
        raise NotImplementedError("abstract method")

    def gt(self, other) -> Series:
        """Get 'less than or equal to' of series and other, element-wise (binary operator `<=`).

        Equivalent to ``series <= other``, but with support to substitute a fill_value for
        missing data in either one of the inputs.

        Args:
            other: Series, or scalar value

        Returns:
            Series. The result of the operation.

        """
        raise NotImplementedError("abstract method")

    def add(self, other) -> Series:
        """Return Addition of series and other, element-wise (binary operator add).

        Equivalent to ``series + other``, but with support to substitute a fill_value for
        missing data in either one of the inputs.

        Args:
            other: Series, or scalar value

        Returns:
            Series. The result of the operation.

        """
        raise NotImplementedError("abstract method")

    def sub(
        self,
        other,
    ) -> Series:
        """Return Subtraction of series and other, element-wise (binary operator sub).

        Equivalent to ``series - other``, but with support to substitute a fill_value for
        missing data in either one of the inputs.

        Args:
            other: Series, or scalar value

        Returns:
            Series. The result of the operation.

        """
        raise NotImplementedError("abstract method")

    def rsub(self, other) -> Series:
        """Return Subtraction of series and other, element-wise (binary operator rsub).

        Equivalent to ``other - series``, but with support to substitute a fill_value for
        missing data in either one of the inputs.

        Args:
            other: Series, or scalar value

        Returns:
            Series. The result of the operation.

        """
        raise NotImplementedError("abstract method")

    def mul(self, other) -> Series:
        """Return Multiplication of series and other, element-wise (binary operator mul).

        Equivalent to ``other * series``, but with support to substitute a fill_value for
        missing data in either one of the inputs.

        Args:
            other: Series, or scalar value

        Returns:
            Series. The result of the operation.

        """
        raise NotImplementedError("abstract method")

    def truediv(self, other) -> Series:
        """Return Floating division of series and other, element-wise (binary operator truediv).

        Equivalent to ``series / other``, but with support to substitute a fill_value for
        missing data in either one of the inputs.

        Args:
            other: Series, or scalar value

        Returns:
            Series. The result of the operation.

        """
        raise NotImplementedError("abstract method")

    def rtruediv(self, other) -> Series:
        """Return Floating division of series and other, element-wise (binary operator rtruediv).

        Equivalent to ``other / series``, but with support to substitute a fill_value for
        missing data in either one of the inputs.

        Args:
            other: Series, or scalar value

        Returns:
            Series. The result of the operation.

        """
        raise NotImplementedError("abstract method")

    def floordiv(self, other) -> Series:
        """Return Integer division of series and other, element-wise (binary operator floordiv).

        Equivalent to ``series // other``, but with support to substitute a fill_value for
        missing data in either one of the inputs.

        Args:
            other: Series, or scalar value

        Returns:
            Series. The result of the operation.

        """
        raise NotImplementedError("abstract method")

    def rfloordiv(self, other) -> Series:
        """Return Integer division of series and other, element-wise (binary operator rfloordiv).

        Equivalent to ``other // series``, but with support to substitute a fill_value for
        missing data in either one of the inputs.

        Args:
            other: Series, or scalar value

        Returns:
            Series. The result of the operation.

        """
        raise NotImplementedError("abstract method")

    def mod(self, other) -> Series:
        """Return Modulo of series and other, element-wise (binary operator mod).

        Equivalent to ``series % other``, but with support to substitute a fill_value for
        missing data in either one of the inputs.

        Args:
            other: Series, or scalar value

        Returns:
            Series. The result of the operation.

        """
        raise NotImplementedError("abstract method")

    def rmod(self, other) -> Series:
        """Get Modulo of series and other, element-wise (binary operator `rmod`).

        Equivalent to ``other % series``, but with support to substitute a fill_value for
        missing data in either one of the inputs.

        Args:
            other: Series, or scalar value

        Returns:
            Series. The result of the operation.

        """
        raise NotImplementedError("abstract method")

    def all(
        self,
    ):
        """
        Return whether all elements are True, potentially over an axis.

        Returns True unless there at least one element within a series or along a
        Dataframe axis that is False or equivalent (e.g. zero or empty).


        Returns
        -------
        scalar or Series
            If level is specified, then, Series is returned; otherwise, scalar
            is returned.
        """
        raise NotImplementedError("abstract method")

    def any(
        self,
    ):
        """
        Return whether any element is True, potentially over an axis.

        Returns False unless there is at least one element within a series or along
        a Dataframe axis that is True or equivalent (e.g. non-zero or non-empty).


        Returns
        -------
        scalar or Series
            If level is specified, then, Series is returned; otherwise, scalar
            is returned.
        """
        raise NotImplementedError("abstract method")

    def max(
        self,
    ):
        """
        Return the maximum of the values over the requested axis.

        If you want the index of the maximum, use ``idxmax``. This is the equivalent
        of the ``numpy.ndarray`` method ``argmax``.


        Returns
        -------
        scalar or scalar
        """
        raise NotImplementedError("abstract method")

    def min(
        self,
    ):
        """
        Return the maximum of the values over the requested axis.

        If you want the index of the minimum, use ``idxmin``. This is the equivalent
        of the ``numpy.ndarray`` method ``argmin``.


        Returns
        -------
        scalar or scalar
        """
        raise NotImplementedError("abstract method")

    def std(
        self,
    ):
        """
        Return sample standard deviation over requested axis.

        Normalized by N-1 by default. This can be changed using the ddof argument.


        Returns
        -------
        scalar or Series (if level specified)
        """
        raise NotImplementedError("abstract method")

    def var(
        self,
    ):
        """
        Return unbiased variance over requested axis.

        Normalized by N-1 by default. This can be changed using the ddof argument.


        Returns
        -------
        scalar or Series (if level specified)
        """
        raise NotImplementedError("abstract method")

    def sum(self):
        """Return the sum of the values over the requested axis.

        This is equivalent to the method ``numpy.sum``.

        Returns:
            scalar
        """
        raise NotImplementedError("abstract method")

    def mean(self):
        """Return the mean of the values over the requested axis.

        Returns:
            scalar
        """
        raise NotImplementedError("abstract method")

    def prod(self):
        """Return the product of the values over the requested axis.

        Returns:
            scalar
        """
        raise NotImplementedError("abstract method")

    def kurt(self):
        """Return unbiased kurtosis over requested axis.

        Kurtosis obtained using Fisher’s definition of kurtosis (kurtosis of normal == 0.0). Normalized by N-1.

        Returns
        -------
        scalar or scalar
        """
        raise NotImplementedError("abstract method")

    def where(self, cond, other):
        """Replace values where the condition is False.

        Parameters
        ----------
        cond: bool Series/DataFrame, array-like, or callable
            Where cond is True, keep the original value. Where False, replace
            with corresponding value from other. If cond is callable, it is
            computed on the Series/DataFrame and should return boolean
            Series/DataFrame or array. The callable must not change input
            Series/DataFrame (though pandas doesn’t check it).
        other: scalar, Series/DataFrame, or callable
            Entries where cond is False are replaced with corresponding value
            from other. If other is callable, it is computed on the
            Series/DataFrame and should return scalar or Series/DataFrame.
            The callable must not change input Series/DataFrame (though pandas
            doesn’t check it). If not specified, entries will be filled with
            the corresponding NULL value (np.nan for numpy dtypes, pd.NA for
            extension dtypes).

        Returns
        -------
        Series
        """
        raise NotImplementedError("abstract method")

    def mask(self, cond, other):
        """Replace values where the condition is True.

        Parameters
        ----------
        cond: bool Series/DataFrame, array-like, or callable
            Where cond is False, keep the original value. Where True, replace
            with corresponding value from other. If cond is callable, it is
            computed on the Series/DataFrame and should return boolean
            Series/DataFrame or array. The callable must not change input
            Series/DataFrame (though pandas doesn’t check it).
        other: scalar, Series/DataFrame, or callable
            Entries where cond is True are replaced with corresponding value
            from other. If other is callable, it is computed on the
            Series/DataFrame and should return scalar or Series/DataFrame.
            The callable must not change input Series/DataFrame (though pandas
            doesn’t check it). If not specified, entries will be filled with
            the corresponding NULL value (np.nan for numpy dtypes, pd.NA for
            extension dtypes).

        Returns
        -------
        Series
        """
        raise NotImplementedError("abstract method")

    def clip(self):
        """Trim values at input threshold(s).

        Assigns values outside boundary to boundary values. Thresholds can be
        singular values or array like, and in the latter case the clipping is
        performed element-wise in the specified axis.

        Parameters
        ----------

        lower: float or array-like, default None
            Minimum threshold value. All values below this threshold will be set to it. A missing threshold (e.g NA) will not clip the value.

        upper: float or array-like, default None
            Maximum threshold value. All values above this threshold will be set to it. A missing threshold (e.g NA) will not clip the value.

        Returns
        -------
        Series
        """
        raise NotImplementedError("abstract method")

    def argmax(self):
        """
        Return int position of the smallest value in the Series.

        If the minimum is achieved in multiple locations, the first row position is returned.

        Returns
        -------
        Series
            Row position of the maximum value.
        """
        raise NotImplementedError("abstract method")

    def argmin(self):
        """
        Return int position of the largest value in the Series.

        If the maximum is achieved in multiple locations, the first row position is returned.

        Returns
        -------
        Series
            Row position of the minimum value.
        """
        raise NotImplementedError("abstract method")

    def rename(self, index, **kwargs) -> Series | None:
        """
        Alter Series index labels or name.

        Function / dict values must be unique (1-to-1). Labels not contained in
        a dict / Series will be left as-is. Extra labels listed don't throw an
        error.

        Alternatively, change ``Series.name`` with a scalar value.

        See the :ref:`user guide <basics.rename>` for more.

        Parameters
        ----------
        index : scalar, hashable sequence, dict-like or function optional
            Functions or dict-like are transformations to apply to
            the index.
            Scalar or hashable sequence-like will alter the ``Series.name``
            attribute.

        Returns
        -------
        Series
            Series with index labels

        """
        raise NotImplementedError("abstract method")

    def rename_axis(self, mapper, **kwargs):
        """
        Set the name of the axis for the index or columns.

        Parameters
        ----------
        mapper : scalar, list-like, optional
            Value to set the axis name attribute.

        Returns
        -------
        Series
        """
        raise NotImplementedError("abstract method")

    def rolling(
        self,
        window,
        min_periods: int | None = None,
    ):
        """
        Provide rolling window calculations.

        Parameters
        ----------
        window : int, timedelta, str, offset, or BaseIndexer subclass
            Size of the moving window.

            If an integer, the fixed number of observations used for
            each window.

            If a timedelta, str, or offset, the time period of each window. Each
            window will be a variable sized based on the observations included in
            the time-period. This is only valid for datetimelike indexes.
            To learn more about the offsets & frequency strings, please see `this link
            <https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#offset-aliases>`__.

            If a BaseIndexer subclass, the window boundaries
            based on the defined ``get_window_bounds`` method. Additional rolling
            keyword arguments, namely ``min_periods``, ``center``, ``closed`` and
            ``step`` will be passed to ``get_window_bounds``.

        min_periods : int, default None
            Minimum number of observations in window required to have a value;
            otherwise, result is ``np.nan``.

            For a window that is specified by an offset, ``min_periods`` will default to 1.

            For a window that is specified by an integer, ``min_periods`` will default
            to the size of the window.

        Returns
        -------
        ``Window`` subclass if a ``win_type`` is passed

        ``Rolling`` subclass if ``win_type`` is not passed
        """
        raise NotImplementedError("abstract method")

    def expanding(self, min_periods=1):
        """
        Provide expanding window calculations.

        Parameters
        ----------
        min_periods : int, default 1
            Minimum number of observations in window required to have a value;
            otherwise, result is ``np.nan``.

        Returns
        -------
        ``Expanding`` subclass
        """
        raise NotImplementedError("abstract method")

    @property
    def str(self):
        """
        Vectorized string functions for Series and Index.

        NAs stay NA unless handled otherwise by a particular method. Patterned
        after Python’s string methods, with some inspiration from R’s stringr package.
        """
        raise NotImplementedError("abstract property")
