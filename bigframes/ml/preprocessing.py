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

"""Transformers that prepare data for other estimators. This module is styled after
Scikit-Learn's preprocessing module: https://scikit-learn.org/stable/modules/preprocessing.html"""


import typing
from typing import List, Literal, Optional, Tuple

import bigframes
from bigframes.ml import base, core
from bigframes.ml import sql as ml_sql
import third_party.bigframes_vendored.sklearn.preprocessing._data
import third_party.bigframes_vendored.sklearn.preprocessing._encoder


class StandardScaler(
    third_party.bigframes_vendored.sklearn.preprocessing._data.StandardScaler,
    base.BaseEstimator,
):
    __doc__ = (
        third_party.bigframes_vendored.sklearn.preprocessing._data.StandardScaler.__doc__
    )

    def __init__(self):
        self._bqml_model: Optional[core.BqmlModel] = None

    def _compile_to_sql(self, columns: List[str]) -> List[Tuple[str, str]]:
        """Compile this transformer to a list of SQL expressions that can be included in
        a BQML TRANSFORM clause

        Args:
            columns: a list of column names to transform

        Returns: a list of tuples of (sql_expression, output_name)"""
        return [
            (
                ml_sql.ml_standard_scaler(column, f"scaled_{column}"),
                f"scaled_{column}",
            )
            for column in columns
        ]

    def fit(
        self,
        X: bigframes.dataframe.DataFrame,
    ):
        compiled_transforms = self._compile_to_sql(X.columns.tolist())
        transform_sqls = [transform_sql for transform_sql, _ in compiled_transforms]

        self._bqml_model = core.create_bqml_model(
            X,
            options={"model_type": "transform_only"},
            transforms=transform_sqls,
        )

        # The schema of TRANSFORM output is not available in the model API, so save it during fitting
        self._output_names = [name for _, name in compiled_transforms]

    def transform(
        self, X: bigframes.dataframe.DataFrame
    ) -> bigframes.dataframe.DataFrame:
        if not self._bqml_model:
            raise RuntimeError("Must be fitted before transform")

        df = self._bqml_model.transform(X)
        return typing.cast(
            bigframes.dataframe.DataFrame,
            df[self._output_names],
        )


class OneHotEncoder(
    third_party.bigframes_vendored.sklearn.preprocessing._encoder.OneHotEncoder,
    base.BaseEstimator,
):
    # BQML max value https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-one-hot-encoder#syntax
    TOP_K_DEFAULT = 1000000

    FREQUENCY_THRESHOLD_DEFAULT = 0

    __doc__ = (
        third_party.bigframes_vendored.sklearn.preprocessing._encoder.OneHotEncoder.__doc__
    )

    # All estimators must implement __init__ to document their parameters, even
    # if they don't have any
    def __init__(
        self,
        drop: Optional[Literal["most_frequent"]] = None,
        min_frequency: Optional[int] = None,
        max_categories: Optional[int] = None,
    ):
        if max_categories is not None and max_categories < 2:
            raise ValueError(
                f"max_categories has to be larger than or equal to 2, input is {max_categories}."
            )
        self.drop = drop
        self.min_frequency = min_frequency
        self.max_categories = max_categories

    def _compile_to_sql(self, columns: List[str]) -> List[Tuple[str, str]]:
        """Compile this transformer to a list of SQL expressions that can be included in
        a BQML TRANSFORM clause

        Args:
            columns:
                a list of column names to transform

        Returns: a list of tuples of (sql_expression, output_name)"""

        drop = self.drop if self.drop is not None else "none"
        # minus one here since BQML's inplimentation always includes index 0, and top_k is on top of that.
        top_k = (
            (self.max_categories - 1)
            if self.max_categories is not None
            else OneHotEncoder.TOP_K_DEFAULT
        )
        frequency_threshold = (
            self.min_frequency
            if self.min_frequency is not None
            else OneHotEncoder.FREQUENCY_THRESHOLD_DEFAULT
        )
        return [
            (
                ml_sql.ml_one_hot_encoder(
                    column, drop, top_k, frequency_threshold, f"onehotencoded_{column}"
                ),
                f"onehotencoded_{column}",
            )
            for column in columns
        ]

    def fit(
        self,
        X: bigframes.dataframe.DataFrame,
    ):
        compiled_transforms = self._compile_to_sql(X.columns.tolist())
        transform_sqls = [transform_sql for transform_sql, _ in compiled_transforms]

        self._bqml_model = core.create_bqml_model(
            X,
            options={"model_type": "transform_only"},
            transforms=transform_sqls,
        )

        # The schema of TRANSFORM output is not available in the model API, so save it during fitting
        self._output_names = [name for _, name in compiled_transforms]

    def transform(
        self, X: bigframes.dataframe.DataFrame
    ) -> bigframes.dataframe.DataFrame:
        if not self._bqml_model:
            raise RuntimeError("Must be fitted before transform")

        df = self._bqml_model.transform(X)
        return typing.cast(
            bigframes.dataframe.DataFrame,
            df[self._output_names],
        )
