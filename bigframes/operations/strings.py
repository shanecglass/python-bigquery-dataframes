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

from __future__ import annotations

import re
from typing import cast, Literal, Optional, Union

import bigframes.operations as ops
import bigframes.operations.base
import bigframes.series as series
import third_party.bigframes_vendored.pandas.core.strings.accessor as vendorstr

# Maps from python to re2
REGEXP_FLAGS = {
    re.IGNORECASE: "i",
    re.MULTILINE: "m",
    re.DOTALL: "s",
}


class StringMethods(bigframes.operations.base.SeriesMethods, vendorstr.StringMethods):
    __doc__ = vendorstr.StringMethods.__doc__

    def find(
        self,
        sub: str,
        start: Optional[int] = None,
        end: Optional[int] = None,
    ) -> series.Series:
        return self._apply_unary_op(ops.FindOp(sub, start, end))

    def len(self) -> series.Series:
        return self._apply_unary_op(ops.len_op)

    def lower(self) -> series.Series:
        return self._apply_unary_op(ops.lower_op)

    def reverse(self) -> series.Series:
        """Reverse strings in the Series."""
        # reverse method is in ibis, not pandas.
        return self._apply_unary_op(ops.reverse_op)

    def slice(
        self,
        start: Optional[int] = None,
        stop: Optional[int] = None,
    ) -> series.Series:
        return self._apply_unary_op(ops.SliceOp(start, stop))

    def strip(self) -> series.Series:
        return self._apply_unary_op(ops.strip_op)

    def upper(self) -> series.Series:
        return self._apply_unary_op(ops.upper_op)

    def isnumeric(self) -> series.Series:
        return self._apply_unary_op(ops.isnumeric_op)

    def rstrip(self) -> series.Series:
        return self._apply_unary_op(ops.rstrip_op)

    def lstrip(self) -> series.Series:
        return self._apply_unary_op(ops.lstrip_op)

    def repeat(self, repeats: int) -> series.Series:
        return self._apply_unary_op(ops.RepeatOp(repeats))

    def capitalize(self) -> series.Series:
        return self._apply_unary_op(ops.capitalize_op)

    def contains(
        self, pat, case: bool = True, flags: int = 0, *, regex: bool = True
    ) -> series.Series:
        if not case:
            return self.contains(pat, flags=flags | re.IGNORECASE, regex=True)
        if regex:
            re2flags = _parse_flags(flags)
            if re2flags:
                pat = re2flags + pat
            return self._apply_unary_op(ops.ContainsRegexOp(pat))
        else:
            return self._apply_unary_op(ops.ContainsStringOp(pat))

    def replace(
        self,
        pat: Union[str, re.Pattern],
        repl: str,
        *,
        case: Optional[bool] = None,
        flags: int = 0,
        regex: bool = False,
    ) -> series.Series:
        is_compiled = isinstance(pat, re.Pattern)
        patstr = cast(str, pat.pattern if is_compiled else pat)  # type: ignore
        if case is False:
            return self.replace(pat, repl, flags=flags | re.IGNORECASE, regex=True)
        if regex:
            re2flags = _parse_flags(flags)
            if re2flags:
                patstr = re2flags + patstr
            return self._apply_unary_op(ops.ReplaceRegexOp(patstr, repl))
        else:
            if is_compiled:
                raise ValueError(
                    "Must set 'regex'=True if using compiled regex pattern."
                )
            return self._apply_unary_op(ops.ReplaceStringOp(patstr, repl))

    def startswith(
        self,
        pat: Union[str, tuple[str, ...]],
    ) -> series.Series:
        if not isinstance(pat, tuple):
            pat = (pat,)
        return self._apply_unary_op(ops.StartsWithOp(pat))

    def endswith(
        self,
        pat: Union[str, tuple[str, ...]],
    ) -> series.Series:
        if not isinstance(pat, tuple):
            pat = (pat,)
        return self._apply_unary_op(ops.EndsWithOp(pat))

    def cat(
        self,
        others: Union[str, series.Series],
        *,
        join: Literal["outer", "left"] = "left",
    ) -> series.Series:
        return self._apply_binary_op(others, ops.concat_op, alignment=join)


def _parse_flags(flags: int) -> Optional[str]:
    re2flags = []
    for reflag, re2flag in REGEXP_FLAGS.items():
        if flags & flags:
            re2flags.append(re2flag)
            flags = flags ^ reflag

    # Remaining flags couldn't be mapped to re2 engine
    if flags:
        raise NotImplementedError(f"Could not handle RegexFlag: {flags}")

    if re2flags:
        return "(?" + "".join(re2flags) + ")"
    else:
        return None
