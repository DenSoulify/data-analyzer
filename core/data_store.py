import pandas as pd


class DataStore:
    """Holds the loaded DataFrame, the column role mapping, and notifies pages."""

    ROLES = ("date", "group", "category", "amount")

    def __init__(self):
        self._df = None
        self.source_name = None
        self.mapping = {}          # role -> column name (or None)

        # optional second table: budget per group
        self.budget_df = None
        self.budget_source = None
        self.budget_mapping = {}   # {"group": column name, "budget": column name}

        self._listeners = []

    @property
    def df(self):
        return self._df

    @property
    def has_data(self):
        return self._df is not None

    @property
    def has_budget(self):
        return self.budget_df is not None

    def column(self, role):
        """Return the actual column name for a role, or None if not mapped."""
        return self.mapping.get(role)

    def set_data(self, df: pd.DataFrame, source_name: str = "", mapping=None):
        self._df = df
        self.source_name = source_name
        self.mapping = mapping or {}
        self._notify()

    def clear(self):
        self._df = None
        self.source_name = None
        self.mapping = {}
        self._notify()

    def set_budget(self, df: pd.DataFrame, source_name: str = "", mapping=None):
        self.budget_df = df
        self.budget_source = source_name
        self.budget_mapping = mapping or {}
        self._notify()

    def clear_budget(self):
        self.budget_df = None
        self.budget_source = None
        self.budget_mapping = {}
        self._notify()

    def subscribe(self, callback):
        self._listeners.append(callback)

    def _notify(self):
        for callback in self._listeners:
            callback()