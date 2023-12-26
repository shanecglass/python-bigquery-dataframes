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


def test_kmeans_sample():
    # [START bigquery_dataframes_bqml_kmeans]
    import datetime

    import bigframes
    import bigframes.pandas as bpd

    bigframes.options.bigquery.project = "salemb-testing"
    # You must compute in the EU multi-region to query the London bicycles dataset.
    bigframes.options.bigquery.location = "EU"

    # Extract the information you'll need to train the k-means model later in this tutorial. Use the
    # read_gbq function to represent cycle hires data as a DataFrame.
    h = bpd.read_gbq(
        "bigquery-public-data.london_bicycles.cycle_hire",
        col_order =[  
            "start_station_name",  
            "start_station_id", 
            "start_date",
            "duration"
        ],
    ).rename(
            columns={
                "start_station_name": "station_name",
                "start_station_id": "station_id",
            }
        )
    
    s = bpd.read_gbq(
        # Use ST_GEOPOINT and ST_DISTANCE to analyze geographical data.
        # These functions determine spatial relationships between the geographical features.
        """
        SELECT
        id,
        ST_DISTANCE(
            ST_GEOGPOINT(s.longitude, s.latitude),
            ST_GEOGPOINT(-0.1, 51.5)
        ) / 1000 AS distance_from_city_center
        FROM
        `bigquery-public-data.london_bicycles.cycle_stations` s
        """
    )

    # Define Python datetime objects in the UTC timezone for range comparison, because BigQuery stores 
    # timestamp data in the UTC timezone.
    sample_time = datetime.datetime(2015, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
    sample_time2 = datetime.datetime(2016, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)

    h = h.loc[(h["start_date"] >= sample_time) & (h["start_date"] <= sample_time2)]

    # Replace each day-of-the-week number with the corresponding "weekday" or "weekend" label by using the 
    # Series.map method.
    h = h.assign(
        isweekday = h.start_date.dt.dayofweek.map(
        {
            0: "weekday",
            1: "weekday",
            2: "weekday",
            3: "weekday",
            4: "weekday",
            5: "weekend",
            6: "weekend",
        }
    ))

    # Supplement each trip in "h" with the station distance information from "s" by 
    # merging the two DataFrames by station ID.
    merged_df = h.merge(
        right=s,
        how="inner",
        left_on="station_id",
        right_on="id",
    )

    # Engineer features to cluster the stations. For each station, find the average trip duration, number of 
    # trips, and distance from city center.
    stationstats = merged_df.groupby(["station_name", "isweekday"]).agg(
    {"duration": ["mean", "count"], "distance_from_city_center": "max"}
    )
    stationstats.columns=["duration","num_trips","distance_from_city_center"]
    stationstats.sort_values(by="distance_from_city_center", ascending=True)

#Expected output results: >>> stationstats.head(3)
#                                                          duration	        num_trips	    distance_from_city_center
#       station_name	                    isweekday			
#       Abbey Orchard Street, Westminster	weekday	    1139.686075	        14908	                2.231931
#                                           weekend	    1538.533802	        2278	                2.231931
#       Abbotsbury Road, Holland Park	    weekday	    1110.262258	2631	7.338276
# 3 rows × 3 columns

    # [END bigquery_dataframes_bqml_kmeans]

    # [START bigquery_dataframes_bqml_kmeans_fit]

    from bigframes.ml.cluster import KMeans

    # To determine an optimal number of clusters, you would run the CREATE MODEL query for different values of
    # num_clusters, find the error measure, and pick the point at which the error measure is at its minimum value.
    cluster_model = KMeans(n_clusters=4)
    cluster_model.fit(stationstats)

    # [END bigquery_dataframes_bqml_kmeans_fit]

    # [START bigquery_dataframes_bqml_kmeans_predict]

    # Use 'contains' function to predict which clusters contain the stations with string "Kennington".
    stationstats = stationstats.contains("Kennington")

    result = cluster_model.predict(stationstats)
    #Expected output results:   >>>results.head(2)
    #                                                    CENTROID_ID     NEAREST_CENTROIDS_DISTANCE	          duration	num_trips	distance_from_city_center
    #                   station_name	    isweekday					
    #   Abbey Orchard Street, Westminster	weekday        2	        [{'CENTROID_ID': 2, 'DISTANCE': 0.695970380477...	1139.686075	14908	2.231931
    #                                       weekend	       1	        [{'CENTROID_ID': 1, 'DISTANCE': 0.467343170961...	1538.533802	2278	2.231931
    # 2 rows × 5 columns

    # [END bigquery_dataframes_bqml_kmeans_predict]

    assert result is not None
