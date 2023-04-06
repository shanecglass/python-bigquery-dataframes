import pandas

import bigframes.ml.cluster
from tests.system.utils import assert_pandas_df_equal_ignore_ordering


def test_cluster_configure_fit_predict(session, penguins_df_no_index, dataset_id):
    model = bigframes.ml.cluster.KMeans(n_clusters=3)

    df = penguins_df_no_index.dropna()[
        [
            "culmen_length_mm",
            "culmen_depth_mm",
            "flipper_length_mm",
            "sex",
        ]
    ]
    model.fit(df)

    pd_new_penguins = pandas.DataFrame.from_dict(
        {
            "test1": {
                "species": "Adelie Penguin (Pygoscelis adeliae)",
                "island": "Dream",
                "culmen_length_mm": 37.5,
                "culmen_depth_mm": 18.5,
                "flipper_length_mm": 199,
                "body_mass_g": 4475,
                "sex": "MALE",
            },
            "test2": {
                "species": "Chinstrap penguin (Pygoscelis antarctica)",
                "island": "Dream",
                "culmen_length_mm": 55.8,
                "culmen_depth_mm": 19.8,
                "flipper_length_mm": 207,
                "body_mass_g": 4000,
                "sex": "MALE",
            },
            "test3": {
                "species": "Adelie Penguin (Pygoscelis adeliae)",
                "island": "Biscoe",
                "culmen_length_mm": 39.7,
                "culmen_depth_mm": 18.9,
                "flipper_length_mm": 184,
                "body_mass_g": 3550,
                "sex": "MALE",
            },
            "test4": {
                "species": "Gentoo penguin (Pygoscelis papua)",
                "island": "Biscoe",
                "culmen_length_mm": 43.8,
                "culmen_depth_mm": 13.9,
                "flipper_length_mm": 208,
                "body_mass_g": 4300,
                "sex": "FEMALE",
            },
        },
        orient="index",
    )
    pd_new_penguins.index.name = "observation"

    new_penguins = session.read_pandas(pd_new_penguins)
    result = model.predict(new_penguins).compute()
    expected = pandas.DataFrame(
        {"CENTROID_ID": [2, 3, 1, 2]},
        dtype="Int64",
        index=pandas.Index(
            ["test1", "test2", "test3", "test4"], dtype="string[pyarrow]"
        ),
    )
    expected.index.name = "observation"
    assert_pandas_df_equal_ignore_ordering(result, expected)

    # save, load, check n_clusters to ensure configuration was kept
    reloaded_model = model.to_gbq(
        f"{dataset_id}.temp_configured_cluster_model", replace=True
    )
    assert reloaded_model.n_clusters == 3