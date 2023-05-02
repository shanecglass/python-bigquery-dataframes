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

"""Matrix Decomposition models. This module is styled after Scikit-Learn's decomposition module:
https://scikit-learn.org/stable/modules/decomposition.html"""

from __future__ import annotations

from typing import cast, Optional, TYPE_CHECKING

from google.cloud import bigquery

if TYPE_CHECKING:
    import bigframes

import bigframes.ml.api_primitives
import bigframes.ml.core


class PCA(bigframes.ml.api_primitives.BaseEstimator):
    def __init__(self, n_components=3):
        self.n_components = n_components
        self._bqml_model: Optional[bigframes.ml.core.BqmlModel] = None

    @staticmethod
    def _from_bq(session: bigframes.Session, model: bigquery.Model) -> PCA:
        assert model.model_type == "PCA"

        kwargs = {}

        # See https://cloud.google.com/bigquery/docs/reference/rest/v2/models#trainingrun
        last_fitting = model.training_runs[-1]["trainingOptions"]
        if "numPrincipalComponents" in last_fitting:
            kwargs["n_components"] = int(last_fitting["numPrincipalComponents"])

        new_pca = PCA(**kwargs)
        new_pca._bqml_model = bigframes.ml.core.BqmlModel(session, model)
        return new_pca

    def fit(self, X: bigframes.DataFrame):
        self._bqml_model = bigframes.ml.core.create_bqml_model(
            train_X=X,
            options={
                "model_type": "PCA",
                "num_principal_components": self.n_components,
            },
        )

    def predict(self, X: bigframes.DataFrame) -> bigframes.DataFrame:
        """Predict the closest cluster for each sample in X"""
        if not self._bqml_model:
            raise RuntimeError("A model must be fitted before predict")

        return cast(
            bigframes.dataframe.DataFrame,
            self._bqml_model.predict(X)[
                ["principal_component_" + str(i + 1) for i in range(self.n_components)]
            ],
        )

    def to_gbq(self, model_name: str, replace: bool = False) -> PCA:
        if not self._bqml_model:
            raise RuntimeError("A model must be fitted before it can be saved")

        new_model = self._bqml_model.copy(model_name, replace)
        return new_model.session.read_gbq_model(self._bqml_model.model_name)