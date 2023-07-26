# Authors: Andreas Mueller <amueller@ais.uni-bonn.de>
#          Joris Van den Bossche <jorisvandenbossche@gmail.com>
# License: BSD 3 clause

from third_party.bigframes_vendored.sklearn.base import BaseEstimator


class OneHotEncoder(BaseEstimator):
    """Encode categorical features as a one-hot format.

    The input to this transformer should be an array-like of integers or
    strings, denoting the values taken on by categorical (discrete) features.
    The features are encoded using a one-hot (aka 'one-of-K' or 'dummy')
    encoding scheme.

    Note that this method deviates from Scikit-Learn; instead of producing sparse
    binary columns, the encoding is a single column of STRUCT<index INT64, value DOUBLE>

    Args:
        drop:
            Specifies a methodology to use to drop one of the categories per feature.
            This is useful in situations where perfectly collinear features cause problems,
            such as when feeding the resulting data into an unregularized linear regression model.

            However, dropping one category breaks the symmetry of the original representation
            and can therefore induce a bias in downstream models, for instance for penalized
            linear classification or regression models.

            Default None: retain all the categories.
            "most_frequent": Drop the most frequent category found in the string expression.
            Selecting this value causes the function to use dummy encoding.
        min_frequency:
            Specifies the minimum frequency below which a category will be considered infrequent.

            Default None.
            int: categories with a smaller cardinality will be considered infrequent as index 0.
        max_categories:
            Specifies an upper limit to the number of output features for each input feature
            when considering infrequent categories. If there are infrequent categories,
            max_categories includes the category representing the infrequent categories along with the frequent categories.

            Default None, set limit to 1,000,000.
    """

    def fit(self, X):
        """Fit OneHotEncoder to X.

        Args:
            X:
                A dataframe with training data.

        Returns:
                Fitted encoder.
        """
        raise NotImplementedError("abstract method")

    def transform(self, X):
        """Transform X using one-hot encoding.

        Args:
            X:
                The DataFrame to be transformed.

        Returns:
            Transformed result. The result is categorized as index: number, value: number.
            Where index is the position of the dict that seeing the category, and value is 0 or 1."""
        raise NotImplementedError("abstract method")
