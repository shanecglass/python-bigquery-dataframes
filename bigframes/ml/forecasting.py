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

from typing import cast, Dict, List, Optional, Union

from google.cloud import bigquery

import bigframes
from bigframes.ml import base, core, utils
import bigframes.pandas as bpd

_PREDICT_OUTPUT_COLUMNS = ["forecast_timestamp", "forecast_value"]


class ARIMAPlus(base.TrainablePredictor):
    """Time Series ARIMA Plus model."""

    def __init__(self):
        self._bqml_model: Optional[core.BqmlModel] = None

    @classmethod
    def _from_bq(cls, session: bigframes.Session, model: bigquery.Model) -> ARIMAPlus:
        assert model.model_type == "ARIMA_PLUS"

        kwargs: Dict[str, str | int | bool | float | List[str]] = {}

        new_arima_plus = cls(**kwargs)
        new_arima_plus._bqml_model = core.BqmlModel(session, model)
        return new_arima_plus

    @property
    def _bqml_options(self) -> Dict[str, str | int | bool | float | List[str]]:
        """The model options as they will be set for BQML."""
        return {"model_type": "ARIMA_PLUS"}

    def fit(
        self,
        X: Union[bpd.DataFrame, bpd.Series],
        y: Union[bpd.DataFrame, bpd.Series],
        transforms: Optional[List[str]] = None,
    ):
        """Fit the model to training data

        Args:
            X (BigQuery DataFrame):
                A dataframe of training timestamp.

            y (BigQuery DataFrame):
                Target values for training."""
        X, y = utils.convert_to_dataframe(X, y)

        self._bqml_model = core.create_bqml_time_series_model(
            X,
            y,
            transforms=transforms,
            options=self._bqml_options,
        )

    def predict(self, X=None) -> bpd.DataFrame:
        """Predict the closest cluster for each sample in X.

        Args:
            X (default None):
                ignored, to be compatible with other APIs.
        Returns:
            BigQuery DataFrame: The predicted BigQuery DataFrames. Which
                contains 2 columns "forecast_timestamp" and "forecast_value".
        """
        if not self._bqml_model:
            raise RuntimeError("A model must be fitted before predict")

        return cast(
            bpd.DataFrame,
            self._bqml_model.forecast()[_PREDICT_OUTPUT_COLUMNS],
        )

    def score(
        self,
        X: Union[bpd.DataFrame, bpd.Series],
        y: Union[bpd.DataFrame, bpd.Series],
    ) -> bpd.DataFrame:
        """Calculate evaluation metrics of the model.

        Args:
            X (BigQuery DataFrame or Series):
                A BigQuery DataFrame only contains 1 column as
                evaluation timestamp. The timestamp must be within the horizon
                of the model, which by default is 1000 data points.
            y (BigQuery DataFrame or Series):
                A BigQuery DataFrame only contains 1 column as
                evaluation numeric values.

        Returns:
            BigQuery DataFrame: A BigQuery DataFrame as evaluation result.
        """
        if not self._bqml_model:
            raise RuntimeError("A model must be fitted before score")
        X, y = utils.convert_to_dataframe(X, y)

        input_data = X.join(y, how="outer")
        return self._bqml_model.evaluate(input_data)

    def to_gbq(self, model_name: str, replace: bool = False) -> ARIMAPlus:
        """Save the model to Google Cloud BigQuery.

        Args:
            model_name (str):
                the name of the model.
            replace (bool, default False):
                whether to replace if the model already exists. Default to False.

        Returns:
            ARIMAPlus: saved model."""
        if not self._bqml_model:
            raise RuntimeError("A model must be fitted before it can be saved")

        new_model = self._bqml_model.copy(model_name, replace)
        return new_model.session.read_gbq_model(model_name)
