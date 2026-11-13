from tkinter import ttk

import customtkinter as ctk
import pandas as pd

from core.styles import apply_tree_style
from pages.base_page import BasePage


MAX_ROWS = 1000  # Treeview gets slow with huge tables, so we only draw the first rows


class TablePage(BasePage):
    title = "Table"

    def build(self):
        self.df = None
        self.sort_col = None
        self.sort_asc = True

        ctk.CTkLabel(
            self, text="Table", font=ctk.CTkFont(size=24, weight="bold")
        ).pack(anchor="w", pady=(0, 10))

        self.info_label = ctk.CTkLabel(self, text="", anchor="w")
        self.info_label.pack(fill="x", pady=(0, 10))

        # table + scrollbars live in their own frame
        self.table_frame = ctk.CTkFrame(self)
        self.table_frame.grid_rowconfigure(0, weight=1)
        self.table_frame.grid_columnconfigure(0, weight=1)

        apply_tree_style()
        self.tree = ttk.Treeview(self.table_frame, style="Data.Treeview",
                                 show="headings", selectmode="browse")
        y_scroll = ctk.CTkScrollbar(self.table_frame, command=self.tree.yview)
        x_scroll = ctk.CTkScrollbar(self.table_frame, orientation="horizontal",
                                    command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")

        # re-render whenever new data is applied on the Load Data page
        self.app.data_store.subscribe(self.refresh)
        self.refresh()

    # ---------- data -> table ----------

    def refresh(self):
        # Called on start and whenever the DataStore changes.
        store = self.app.data_store
        if not store.has_data:
            self.table_frame.pack_forget()
            self.info_label.configure(text="No data loaded yet. Go to 'Load Data' first.")
            return

        self.df = store.df
        self.sort_col = None
        self.sort_asc = True
        self.table_frame.pack(fill="both", expand=True)
        self._render()

    def sort_by(self, column):
        if self.sort_col == column:
            self.sort_asc = not self.sort_asc   # second click flips the direction
        else:
            self.sort_col, self.sort_asc = column, True
        self._render()

    def _render(self):
        df = self.df
        if self.sort_col is not None:
            df = df.sort_values(self.sort_col, ascending=self.sort_asc)
        shown = df.head(MAX_ROWS)

        # rebuild columns and headings
        self.tree.delete(*self.tree.get_children())
        columns = [str(c) for c in df.columns]
        self.tree.configure(columns=columns)
        for col in columns:
            arrow = ""
            if col == self.sort_col:
                arrow = "  ▲" if self.sort_asc else "  ▼"
            numeric = pd.api.types.is_numeric_dtype(df[col])
            self.tree.heading(col, text=col + arrow,
                              command=lambda c=col: self.sort_by(c))
            self.tree.column(col, width=130, minwidth=80,
                             anchor="e" if numeric else "w")

        # insert rows, formatting values only for what we actually draw
        for row in shown.itertuples(index=False, name=None):
            self.tree.insert("", "end", values=[self._fmt(v) for v in row])

        text = f"{self.app.data_store.source_name}: {len(df):,} rows"
        if len(df) > MAX_ROWS:
            text += f" (showing the first {MAX_ROWS:,})"
        self.info_label.configure(text=text)

    @staticmethod
    def _fmt(value):
        if pd.isna(value):
            return ""
        if isinstance(value, pd.Timestamp):
            return value.strftime("%Y-%m-%d")
        if isinstance(value, float):
            return f"{value:,.2f}"
        return str(value)