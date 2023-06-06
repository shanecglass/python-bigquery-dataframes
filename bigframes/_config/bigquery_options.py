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

"""Options for BigFrames."""

from __future__ import annotations

from typing import Optional

import google.api_core.exceptions
import google.auth.credentials

SESSION_STARTED_MESSAGE = "Cannot change '{attribute}' once a session has started."


class BigQueryOptions:
    """Encapsulates configuration for working with an Session."""

    def __init__(
        self,
        credentials: Optional[google.auth.credentials.Credentials] = None,
        project: Optional[str] = None,
        location: Optional[str] = None,
        remote_udf_connection: Optional[str] = None,
        use_regional_endpoints: bool = False,
    ):
        self._credentials = credentials
        self._project = project
        self._location = location
        self._remote_udf_connection = remote_udf_connection
        self._use_regional_endpoints = use_regional_endpoints
        self._session_started = False

    @property
    def credentials(self) -> Optional[google.auth.credentials.Credentials]:
        """The OAuth2 Credentials to use for this client."""
        return self._credentials

    @credentials.setter
    def credentials(self, value: Optional[google.auth.credentials.Credentials]):
        if self._session_started:
            raise ValueError(SESSION_STARTED_MESSAGE.format(attribute="credentials"))
        self._credentials = value

    @property
    def location(self) -> Optional[str]:
        """Default location for jobs / datasets / tables.

        See: https://cloud.google.com/bigquery/docs/locations
        """
        return self._location

    @location.setter
    def location(self, value: Optional[str]):
        if self._session_started:
            raise ValueError(SESSION_STARTED_MESSAGE.format(attribute="location"))
        self._location = value

    @property
    def project(self) -> Optional[str]:
        """Google Cloud project ID to use for billing and default data project."""
        return self._project

    @project.setter
    def project(self, value: Optional[str]):
        if self._session_started:
            raise ValueError(SESSION_STARTED_MESSAGE.format(attribute="project"))
        self._project = value

    @property
    def remote_udf_connection(self) -> Optional[str]:
        """Name of the BigQuery connection for the purpose of remote UDFs.

        It should be either pre created in `location`, or the user should have
        privilege to create one.
        """
        return self._remote_udf_connection

    @remote_udf_connection.setter
    def remote_udf_connection(self, value: Optional[str]):
        if self._session_started:
            raise ValueError(
                SESSION_STARTED_MESSAGE.format(attribute="remote_udf_connection")
            )
        self._remote_udf_connection = value

    @property
    def use_regional_endpoints(self) -> bool:
        """In preview. Flag to connect to regional API endpoints.

        Requires ``location`` to also be set. For example, set
        ``location='asia-northeast1'`` and ``use_regional_endpoints=True`` to
        connect to asia-northeast1-bigquery.googleapis.com.
        """
        return self._use_regional_endpoints

    @use_regional_endpoints.setter
    def use_regional_endpoints(self, value: bool):
        if self._session_started:
            raise ValueError(
                SESSION_STARTED_MESSAGE.format(attribute="use_regional_endpoints")
            )
        self._use_regional_endpoints = value
