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

import google.api_core.exceptions
import pytest

import bigframes.pandas as bpd


@pytest.fixture(autouse=True)
def reset_default_session_and_location():
    bpd.reset_session()
    bpd.options.bigquery.location = None


@pytest.mark.parametrize(
    ("read_method", "query_prefix"),
    [
        (bpd.read_gbq, None),
        (bpd.read_gbq, "SELECT COUNT(1) FROM "),
        (bpd.read_gbq_table, None),
        (bpd.read_gbq_query, "SELECT COUNT(1) FROM "),
    ],
    ids=[
        "read_gbq-on-table-name",
        "read_gbq-on-sql",
        "read_gbq_table-on-table-name",
        "read_gbq_query-on-sql",
    ],
)
def test_read_gbq_start_sets_session_location(
    test_data_tables_tokyo,
    dataset_id_permanent_tokyo,
    tokyo_location,
    test_data_tables,
    dataset_id_permanent,
    read_method,
    query_prefix,
):
    # Form query as a table name or a SQL depending on the test scenario
    query_tokyo = test_data_tables_tokyo["scalars"]
    query = test_data_tables["scalars"]
    if query_prefix:
        query_tokyo = f"{query_prefix} {query_tokyo}"
        query = f"{query_prefix} {query}"

    # Initially there is no location set in the bigquery options
    assert not bpd.options.bigquery.location

    # Starting user journey with read_gbq* should work for a table in any
    # location, in this case tokyo
    df = read_method(query_tokyo)
    assert df is not None

    # Now bigquery options location should be set to tokyo
    assert bpd.options.bigquery.location == tokyo_location

    # Now read_gbq* from another location should fail
    with pytest.raises(
        google.api_core.exceptions.NotFound,
        match=f"404 Not found: Dataset {dataset_id_permanent} was not found in location {tokyo_location}",
    ):
        read_method(query)

    # Reset global session to start over
    bpd.reset_session()

    # There should still be the previous location set in the bigquery options
    assert bpd.options.bigquery.location == tokyo_location

    # Starting over the user journey with read_gbq* should work for a table
    # in another location, in this case US
    df = read_method(query)
    assert df is not None

    # Now bigquery options location should be set to US
    assert bpd.options.bigquery.location == "US"

    # Now read_gbq* from another location should fail
    with pytest.raises(
        google.api_core.exceptions.NotFound,
        match=f"404 Not found: Dataset {dataset_id_permanent_tokyo} was not found in location US",
    ):
        read_method(query_tokyo)


@pytest.mark.parametrize(
    ("read_method", "query_prefix"),
    [
        (bpd.read_gbq, None),
        (bpd.read_gbq, "SELECT COUNT(1) FROM "),
        (bpd.read_gbq_table, None),
        (bpd.read_gbq_query, "SELECT COUNT(1) FROM "),
    ],
    ids=[
        "read_gbq-on-table-name",
        "read_gbq-on-sql",
        "read_gbq_table-on-table-name",
        "read_gbq_query-on-sql",
    ],
)
def test_read_gbq_after_session_start_must_comply_with_default_location(
    scalars_pandas_df_index,
    test_data_tables,
    test_data_tables_tokyo,
    dataset_id_permanent_tokyo,
    read_method,
    query_prefix,
):
    # Form query as a table name or a SQL depending on the test scenario
    query_tokyo = test_data_tables_tokyo["scalars"]
    query = test_data_tables["scalars"]
    if query_prefix:
        query_tokyo = f"{query_prefix} {query_tokyo}"
        query = f"{query_prefix} {query}"

    # Initially there is no location set in the bigquery options
    assert not bpd.options.bigquery.location

    # Starting user journey with anything other than read_gbq*, such as
    # read_pandas would bind the session to default location US
    df = bpd.read_pandas(scalars_pandas_df_index)
    assert df is not None

    # Doing read_gbq* from a table in another location should fail
    with pytest.raises(
        google.api_core.exceptions.NotFound,
        match=f"404 Not found: Dataset {dataset_id_permanent_tokyo} was not found in location US",
    ):
        read_method(query_tokyo)

    # read_gbq* from a table in the default location should work
    df = read_method(query)
    assert df is not None


def test_reset_session_after_bq_session_ended():
    # Use a simple test query to verify that default session works to interact
    # with BQ
    test_query = "SELECT 1"

    # Confirm that there is a session id in the default session
    session = bpd.get_global_session()
    assert session._session_id

    # Confirm that session works as usual
    df = bpd.read_gbq(test_query)
    assert df is not None

    # Abort the session to simulate the auto-expiration
    # https://cloud.google.com/bigquery/docs/sessions-terminating#auto-terminate_a_session
    abort_session_query = "CALL BQ.ABORT_SESSION()"
    query_job = session.bqclient.query(abort_session_query)
    query_job.result()  # blocks until finished

    # Confirm that session is unusable to run any jobs
    with pytest.raises(
        google.api_core.exceptions.BadRequest,
        match=f"Session {session._session_id} has expired and is no longer available.",
    ):
        query_job = session.bqclient.query(test_query)
        query_job.result()  # blocks until finished

    # Confirm that as a result bigframes.pandas interface is unusable
    with pytest.raises(
        google.api_core.exceptions.BadRequest,
        match=f"Session {session._session_id} has expired and is no longer available.",
    ):
        bpd.read_gbq(test_query)

    # Now try to reset session and verify that it works
    bpd.reset_session()
    assert bpd._global_session is None

    # Now verify that use is able to start over
    df = bpd.read_gbq(test_query)
    assert df is not None
