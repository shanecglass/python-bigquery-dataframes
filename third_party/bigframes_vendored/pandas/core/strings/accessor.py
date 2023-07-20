import re
import typing


class StringMethods:
    """
    Vectorized string functions for Series and Index.

    NAs stay NA unless handled otherwise by a particular method.
    Patterned after Python's string methods, with some inspiration from
    R's stringr package.
    """

    def find(self, sub, start: int = 0, end=None):
        """Return lowest indexes in each strings in the Series/Index.

        Each of returned indexes corresponds to the position where the
        substring is fully contained between [start:end]. Return -1 on
        failure. Equivalent to standard :meth:`str.find`.

        Args:
            sub:
                Substring being searched.
            start:
                Left edge index.
            end:
                Right edge index.

        Returns:
            Series or Index of int.
        """

        raise NotImplementedError("abstract method")

    def len(self):
        """Compute the length of each element in the Series/Index.

        The element may be a sequence (such as a string, tuple or list) or a collection
        (such as a dictionary).

        Returns:
            Series or Index of int
            A Series or Index of integer values indicating the length of each
            element in the Series or Index.
        """

        raise NotImplementedError("abstract method")

    def lower(self):
        """Convert strings in the Series/Index to lowercase.

        Equivalent to :meth:`str.lower`.

        Returns:
            Series or Index of object
        """

        raise NotImplementedError("abstract method")

    def slice(self, start=None, stop=None):
        """Slice substrings from each element in the Series or Index.

        Args:
            start : int, optional
                Start position for slice operation.
            stop : int, optional
                Stop position for slice operation.
            step : int, optional
                Step size for slice operation.

        Returns:
            Series or Index of object
                Series or Index from sliced substring from original string object.
        """

        raise NotImplementedError("abstract method")

    def strip(self):
        """Remove leading and trailing characters.

        Strip whitespaces (including newlines) or a set of specified characters
        from each string in the Series/Index from left and right sides.
        Replaces any non-strings in Series with NaNs.
        Equivalent to :meth:`str.strip`.

        Returns:
            Series or Index of object
        """

        raise NotImplementedError("abstract method")

    def upper(self):
        """Convert strings in the Series/Index to uppercase.

        Equivalent to :meth:`str.upper`.

        Returns:
            Series or Index of object
        """

        raise NotImplementedError("abstract method")

    def isnumeric(self):
        """Check whether all characters in each string are numeric.

        This is equivalent to running the Python string method
        :meth:`str.isnumeric` for each element of the Series/Index. If a string
        has zero characters, ``False`` is returned for that check.

        Returns:
            Series or Index of bool
                Series or Index of boolean values with the same length as the original
                Series/Index.
        """

        raise NotImplementedError("abstract method")

    def rstrip(self):
        """Remove trailing characters.

        Strip whitespaces (including newlines) or a set of specified characters
        from each string in the Series/Index from right side.
        Replaces any non-strings in Series with NaNs.
        Equivalent to :meth:`str.rstrip`.

        Returns:
            Series or Index of object
        """

        raise NotImplementedError("abstract method")

    def lstrip(self):
        """Remove leading characters.

        Strip whitespaces (including newlines) or a set of specified characters
        from each string in the Series/Index from left side.
        Replaces any non-strings in Series with NaNs.
        Equivalent to :meth:`str.lstrip`.

        Returns:
            Series or Index of object`
        """

        raise NotImplementedError("abstract method")

    def repeat(self, repeats: int):
        """Duplicate each string in the Series or Index.

        Args:
            repeats : int or sequence of int
                Same value for all (int) or different value per (sequence).

        Returns:
            Series or pandas.Index
                Series or Index of repeated string objects specified by
                input parameter repeats.
        """

        raise NotImplementedError("abstract method")

    def capitalize(self):
        """Convert strings in the Series/Index to be capitalized.

        Equivalent to :meth:`str.capitalize`.

        Returns:
            Series or Index of object
        """

        raise NotImplementedError("abstract method")

    def cat(self, others, *, join):
        """Concatenate strings in the Series/Index with given separator.

        If `others` is specified, this function concatenates the Series/Index
        and elements of `others` element-wise.

        Args:
            others : Series

            join : {'left', 'outer'}, default 'left'
                Determines the join-style between the calling Series and any
                Series in `others` (objects without an index need
                to match the length of the calling Series). To disable
                alignment, use `.values` on any Series/Index/DataFrame in `others`.

        Returns:
            Series
        """

        raise NotImplementedError("abstract method")

    def contains(self, pat, case: bool = True, flags: int = 0, *, regex: bool = True):
        """
        Test if pattern or regex is contained within a string of a Series or Index.

        Return boolean Series or Index based on whether a given pattern or regex is
        contained within a string of a Series or Index.

        Parameters
        ----------
        pat:
            Character sequence or regular expression.
        case:
            If True, case sensitive.
        flags:
            Flags to pass through to the re module, e.g. re.IGNORECASE.
        regex:
            If True, assumes the pat is a regular expression.

            If False, treats the pat as a literal string.

        Returns:
            A Series or Index of boolean values indicating whether the
            given pattern is contained within the string of each element
            of the Series or Index.
        """
        raise NotImplementedError("abstract method")

    def replace(
        self,
        pat: typing.Union[str, re.Pattern],
        repl: str,
        *,
        case: typing.Optional[bool] = None,
        flags: int = 0,
        regex: bool = False,
    ):
        """
        Replace each occurrence of pattern/regex in the Series/Index.

        Equivalent to :meth:`str.replace` or :func:`re.sub`, depending on
        the regex value.

        Args:
            pat:
                String can be a character sequence or regular expression.
            repl:
                Replacement string.
            case:
                Determines if replace is case sensitive:

                - If True, case sensitive (the default if `pat` is a string)
                - Set to False for case insensitive
                - Cannot be set if `pat` is a compiled regex.

            flags:
                Regex module flags, e.g. re.IGNORECASE. Cannot be set if `pat` is a compiled
                regex.
            regex:
                Determines if the passed-in pattern is a regular expression:

                - If True, assumes the passed-in pattern is a regular expression.
                - If False, treats the pattern as a literal string
                - Cannot be set to False if `pat` is a compiled regex or `repl` is
                    a callable.

        Returns:
            A copy of the object with all matching occurrences of `pat` replaced by
            `repl`.

        """
        raise NotImplementedError("abstract method")

    def startswith(
        self,
        pat: typing.Union[str, tuple[str, ...]],
    ):
        """
        Test if the start of each string element matches a pattern.

        Args:
            pat:
                Character sequence or tuple of strings. Regular expressions are not
                accepted.

        Returns:
            A Series of booleans indicating whether the given pattern matches
            the start of each string element.
        """
        raise NotImplementedError("abstract method")

    def endswith(
        self,
        pat: typing.Union[str, tuple[str, ...]],
    ):
        """
        Test if the end of each string element matches a pattern.

        Args:
            pat:
                Character sequence or tuple of strings. Regular expressions are not
                accepted.

        Returns:
            A Series of booleans indicating whether the given pattern matches
            the end of each string element.
        """
        raise NotImplementedError("abstract method")
