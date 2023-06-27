# Contains code from https://github.com/pandas-dev/pandas/blob/main/pandas/core/indexes/base.py


class Index:
    """Immutable sequence used for indexing and alignment.

    The basic object storing axis labels for all objects.
    """

    @property
    def name(self):
        """Return Index name."""
        raise NotImplementedError("abstract method")