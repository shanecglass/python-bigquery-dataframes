# Contains code from https://github.com/pandas-dev/pandas/blob/main/pandas/core/generic.py
from __future__ import annotations

from typing import Literal, Optional

from third_party.bigframes_vendored.pandas.core import indexing


class NDFrame(indexing.IndexingMixin):
    """
    N-dimensional analogue of DataFrame. Store multi-dimensional in a
    size-mutable, labeled data structure
    """

    # ----------------------------------------------------------------------
    # Axis

    @property
    def ndim(self) -> int:
        """Return an int representing the number of axes / array dimensions.

        Return 1 if Series. Otherwise return 2 if DataFrame.
        """
        raise NotImplementedError("abstract method")

    @property
    def size(self) -> int:
        """Return an int representing the number of elements in this object.

        Return the number of rows if Series. Otherwise return the number of
        rows times number of columns if DataFrame.
        """
        raise NotImplementedError("abstract method")

    # -------------------------------------------------------------------------
    # Unary Methods

    def abs(self):
        """Return a Series/DataFrame with absolute numeric value of each element.

        This function only applies to elements that are all numeric.

        Returns:
            Series/DataFrame containing the absolute value of each element.
        """
        raise NotImplementedError("abstract method")

    def astype(self, dtype):
        """
        Cast a pandas object to a specified dtype ``dtype``.

        Parameters
        ----------
        dtype : str, data type, Series or Mapping of column name -> data type
            Use a str, numpy.dtype, pandas.ExtensionDtype or Python type to
            cast entire pandas object to the same type. Alternatively, use a
            mapping, e.g. {col: dtype, ...}, where col is a column label and dtype is
            a numpy.dtype or Python type to cast one or more of the DataFrame's
            columns to column-specific types.

        Returns
        -------
        same type as caller

        """
        raise NotImplementedError("abstract method")

    # ----------------------------------------------------------------------
    # Iteration

    @property
    def empty(self) -> bool:
        """Indicator whether Series/DataFrame is empty.

        True if Series/DataFrame is entirely empty (no items), meaning any of the
        axes are of length 0.

        Returns:
            If Series/DataFrame is empty, return True, if not return False.

        Note:
            If Series/DataFrame contains only NA values, it is still not
            considered empty.
        """
        raise NotImplementedError("abstract method")

    # ----------------------------------------------------------------------
    # I/O Methods

    def to_json(
        self,
        path_or_buf: str,
        orient: Literal[
            "split", "records", "index", "columns", "values", "table"
        ] = "columns",
        *,
        index: bool = True,
        lines: bool = False,
    ) -> str | None:
        """Convert the object to a JSON string, written to GCS.

        Note NaN's and None will be converted to null and datetime objects
        will be converted to UNIX timestamps.

        Args:
            path_or_buf:
                A destination URI of GCS files(s) to store the extracted dataframe
                in format of ``gs://<bucket_name>/<object_name_or_glob>``.

                If the data size is more than 1GB, you must use a wildcard to
                export the data into multiple files and the size of the files
                varies.

                None, file-like objects or local file paths not yet supported.
            orient:
                Indication of expected JSON string format.

                .. note::

                    In BigQuery DataFrame, only `orient='records'` is supported so far.

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

            lines:
                If 'orient' is 'records' write out line-delimited json format. Will
                throw ValueError if incorrect 'orient' since others are not
                list-like.

                .. note::

                   BigQuery DataFrame only supports ``lines=True`` so far.

            index:
                If True, write row names (index).

        Returns:
            None. String output not yet supported.
        """
        raise NotImplementedError("abstract method")

    def to_csv(self, path_or_buf: str, *, index: bool = True) -> str | None:
        """Write object to a comma-separated values (csv) file on GCS.

        Args:
            path_or_buf:
                A destination URI of GCS files(s) to store the extracted dataframe
                in format of ``gs://<bucket_name>/<object_name_or_glob>``.

                If the data size is more than 1GB, you must use a wildcard to
                export the data into multiple files and the size of the files
                varies.

                None, file-like objects or local file paths not yet supported.

            index:
                If True, write row names (index).

        Returns:
            None. String output not yet supported.
        """
        raise NotImplementedError("abstract method")

    # ----------------------------------------------------------------------
    # Unsorted

    def get(self, key, default=None):
        """
        Get item from object for given key (ex: DataFrame column).

        Returns default value if not found.

        Args:
            key: object

        Returns:
            same type as items contained in object
        """
        try:
            return self[key]
        except (KeyError, ValueError, IndexError):
            return default

    def add_prefix(self, prefix: str, axis: int | str | None = None):
        """Prefix labels with string `prefix`.

        For Series, the row labels are prefixed.
        For DataFrame, the column labels are prefixed.

        Args:
            prefix:
                The string to add before each label.
            axis:
                ``{{0 or 'index', 1 or 'columns', None}}``, default None. Axis
                to add prefix on

        Returns:
            New Series or DataFrame with updated labels.
        """
        raise NotImplementedError("abstract method")

    def add_suffix(self, suffix: str, axis: int | str | None = None):
        """Suffix labels with string `suffix`.

        For Series, the row labels are suffixed.
        For DataFrame, the column labels are suffixed.

        Args:
            suffix:
                The string to add after each label.
            axis:
                ``{{0 or 'index', 1 or 'columns', None}}``, default None. Axis
                to add suffix on

        Returns:
            New Series or DataFrame with updated labels.
        """
        raise NotImplementedError("abstract method")

    def head(self, n: int = 5):
        """Return the first `n` rows.

        This function returns the first `n` rows for the object based
        on position. It is useful for quickly testing if your object
        has the right type of data in it.

        **Not yet supported** For negative values of `n`, this function returns
        all rows except the last `|n|` rows, equivalent to ``df[:n]``.

        If n is larger than the number of rows, this function returns all rows.

        Args:
            n:
                Default 5. Number of rows to select.

        Returns:
            The first `n` rows of the caller object.
        """
        raise NotImplementedError("abstract method")

    def tail(self, n: int = 5):
        """Return the last `n` rows.

        This function returns last `n` rows from the object based on
        position. It is useful for quickly verifying data, for example,
        after sorting or appending rows.

        For negative values of `n`, this function returns all rows except
        the first `|n|` rows, equivalent to ``df[|n|:]``.

        If n is larger than the number of rows, this function returns all rows.

        Args:
            n: int, default 5.  Number of rows to select.

        Returns:
            The last `n` rows of the caller object.
        """
        raise NotImplementedError("abstract method")

    def sample(
        self,
        n: Optional[int] = None,
        frac: Optional[float] = None,
        *,
        random_state: Optional[int] = None,
    ):
        """Return a random sample of items from an axis of object.

        You can use `random_state` for reproducibility.

        Args:
            n:
                Number of items from axis to return. Cannot be used with `frac`.
                Default = 1 if `frac` = None.
            frac:
                Fraction of axis items to return. Cannot be used with `n`.
            random_state:
                Seed for random number generator.

        Returns:
            A new object of same type as caller containing `n` items randomly
            sampled from the caller object.
        """
        raise NotImplementedError("abstract method")

    # ----------------------------------------------------------------------
    # Internal Interface Methods

    @property
    def dtypes(self):
        """Return the dtypes in the DataFrame.

        This returns a Series with the data type of each column.
        The result's index is the original DataFrame's columns. Columns
        with mixed types aren't supported yet in BigQuery DataFrame.

        Returns:
            A *pandas* Series with the data type of each column.
        """
        raise NotImplementedError("abstract method")

    def copy(self):
        """Make a copy of this object's indices and data.

        A new object will be created with a copy of the calling object's data
        and indices. Modifications to the data or indices of the copy will not
        be reflected in the original object.

        Returns:
            Object type matches caller.
        """
        raise NotImplementedError("abstract method")

    # ----------------------------------------------------------------------
    # Action Methods

    def isna(self) -> NDFrame:
        """Detect missing values.

        Return a boolean same-sized object indicating if the values are NA.
        NA values get mapped to True values. Everything else gets mapped to
        False values. Characters such as empty strings ``''`` or
        :attr:`numpy.inf` are not considered NA values.

        Returns:
            Mask of bool values for each element that indicates whether an
            element is an NA value.
        """
        raise NotImplementedError("abstract method")

    isnull = isna

    def notna(self) -> NDFrame:
        """Detect existing (non-missing) values.

        Return a boolean same-sized object indicating if the values are not NA.
        Non-missing values get mapped to True. Characters such as empty
        strings ``''`` or :attr:`numpy.inf` are not considered NA values.
        NA values get mapped to False values.

        Returns:
            Mask of bool values for each element that indicates whether an
            element is not an NA value.
        """
        raise NotImplementedError("abstract method")

    notnull = notna

    def shift(
        self,
        periods: int = 1,
    ) -> NDFrame:
        """Shift index by desired number of periods.

        Shifts the index without realigning the data.

        Args:
            periods:
                Number of periods to shift. Can be positive or negative.

        Returns:
            Copy of input object, shifted.
        """
        raise NotImplementedError("abstract method")

    def rank(
        self,
        axis=0,
        method: str = "average",
        na_option: str = "keep",
    ):
        """
        Compute numerical data ranks (1 through n) along axis.

        By default, equal values are assigned a rank that is the average of the
        ranks of those values.

        Parameters
        ----------
        method : {'average', 'min', 'max', 'first', 'dense'}, default 'average'
            How to rank the group of records that have the same value (i.e. ties):

            * average: average rank of the group
            * min: lowest rank in the group
            * max: highest rank in the group
            * first: ranks assigned in order they appear in the array
            * dense: like 'min', but rank always increases by 1 between groups.


        na_option : {'keep', 'top', 'bottom'}, default 'keep'
            How to rank NaN values:

            * keep: assign NaN rank to NaN values
            * top: assign lowest rank to NaN values
            * bottom: assign highest rank to NaN values

        Returns
        -------
        same type as caller
            Return a Series or DataFrame with data ranks as values.
        """
        raise NotImplementedError("abstract method")
