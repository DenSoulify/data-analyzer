from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk
import pandas as pd

from pages.base_page import BasePage

NONE = "(none)"

# role -> (label, name hints used for auto-detection)
ROLES = {
    "amount":   ("Amount (required)", ("amount", "cost", "price", "total", "value", "sum")),
    "group":    ("Group (e.g. department)", ("department", "dept", "team", "unit", "group")),
    "category": ("Category", ("category", "type", "vendor")),
    "date":     ("Date", ("date", "time", "day", "month")),
}


class DataPage(BasePage):
    title = "Load Data"

    def build(self):
        self.raw_df = None
        self.file_path = None
        self.menus = {}
        self.budget_raw = None
        self.budget_path = None
        self.budget_menus = {}

        ctk.CTkLabel(
            self, text="Load Data", font=ctk.CTkFont(size=24, weight="bold")
        ).pack(anchor="w", pady=(0, 15))

        # --- file picker ---
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x")
        ctk.CTkButton(top, text="Open file...", command=self.open_file).pack(side="left")
        self.file_label = ctk.CTkLabel(top, text="No file loaded")
        self.file_label.pack(side="left", padx=15)

        # --- column mapping ---
        mapping_frame = ctk.CTkFrame(self)
        mapping_frame.pack(fill="x", pady=15)
        ctk.CTkLabel(
            mapping_frame, text="Tell the app what each column means",
            font=ctk.CTkFont(weight="bold"),
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=15, pady=(10, 5))

        for i, (role, (label, _)) in enumerate(ROLES.items(), start=1):
            ctk.CTkLabel(mapping_frame, text=label).grid(
                row=i, column=0, sticky="w", padx=15, pady=5)
            menu = ctk.CTkOptionMenu(mapping_frame, values=[NONE], width=250)
            menu.grid(row=i, column=1, sticky="w", padx=15, pady=5)
            self.menus[role] = menu

        self.apply_button = ctk.CTkButton(
            mapping_frame, text="Apply", command=self.apply_mapping, state="disabled")
        self.apply_button.grid(row=len(ROLES) + 1, column=0, columnspan=2,
                               sticky="w", padx=15, pady=(10, 15))

        self.status = ctk.CTkLabel(self, text="", anchor="w")
        self.status.pack(fill="x")

        self._build_budget_section()

        # --- raw preview (the proper table view comes in step 4) ---
        self.preview = ctk.CTkTextbox(self, font=ctk.CTkFont(family="Consolas", size=12),
                                      wrap="none")
        self.preview.pack(fill="both", expand=True, pady=(10, 0))

    # ---------- loading ----------

    def open_file(self):
        path = filedialog.askopenfilename(
            title="Select a data file",
            filetypes=[("Data files", "*.csv *.xlsx *.xls"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            self.raw_df = self._read_file(Path(path))
        except Exception as e:
            self._set_status(f"Could not read file: {e}", error=True)
            return

        self.file_path = Path(path)
        self.file_label.configure(text=self.file_path.name)
        self._populate_menus()
        self._show_preview(self.raw_df)
        self.apply_button.configure(state="normal")
        self._set_status(
            f"Read {len(self.raw_df)} rows, {len(self.raw_df.columns)} columns. "
            "Check the column mapping and press Apply.")

    @staticmethod
    def _read_file(path: Path) -> pd.DataFrame:
        if path.suffix.lower() in (".xlsx", ".xls"):
            return pd.read_excel(path)
        # sep=None lets pandas detect the delimiter (comma, semicolon, tab...)
        return pd.read_csv(path, sep=None, engine="python")

    # ---------- column mapping ----------

    def _populate_menus(self):
        columns = [str(c) for c in self.raw_df.columns]
        for role, menu in self.menus.items():
            menu.configure(values=[NONE] + columns)
            menu.set(self._guess_column(role))

    def _guess_column(self, role):
        columns = [str(c) for c in self.raw_df.columns]

        # for amount, only consider columns that actually contain numbers
        if role == "amount":
            columns = [c for c in columns if self._is_numeric_like(self.raw_df[c])]

        # 1) try the name hints
        for hint in ROLES[role][1]:
            for col in columns:
                if hint in col.lower():
                    return col

        # 2) no name match: for amount, fall back to the first numeric column
        if role == "amount" and columns:
            return columns[0]
        return NONE

    @staticmethod
    def _is_numeric_like(series):
        # True if the column is numeric, or text that is >90% parseable as numbers. This makes sure the logic stays more solid
        if pd.api.types.is_numeric_dtype(series):
            return True
        cleaned = (series.astype(str)
                   .str.replace(r"\s", "", regex=True)
                   .str.replace(",", ".", regex=False))
        return pd.to_numeric(cleaned, errors="coerce").notna().mean() > 0.9

    def apply_mapping(self):
        mapping = {role: (m.get() if m.get() != NONE else None)
                   for role, m in self.menus.items()}

        if mapping["amount"] is None:
            self._set_status("Please choose the Amount column.", error=True)
            return

        df = self.raw_df.copy()
        before = len(df)

        # amount -> numbers (also handles "1 234,50" style values)
        amount = df[mapping["amount"]]
        if amount.dtype == object:
            amount = (amount.astype(str)
                      .str.replace(r"\s", "", regex=True)
                      .str.replace(",", ".", regex=False))
        df[mapping["amount"]] = pd.to_numeric(amount, errors="coerce")
        df = df.dropna(subset=[mapping["amount"]])

        # date -> datetime
        if mapping["date"]:
            df[mapping["date"]] = pd.to_datetime(df[mapping["date"]], errors="coerce")
            df = df.dropna(subset=[mapping["date"]])

        if df.empty:
            self._set_status("No valid rows left. Check that Amount/Date are correct.",
                             error=True)
            return

        self.app.data_store.set_data(df.reset_index(drop=True),
                                     self.file_path.name, mapping)
        dropped = before - len(df)
        msg = f"Loaded {len(df)} rows."
        if dropped:
            msg += f" {dropped} rows were dropped (invalid amount or date)."
        self._set_status(msg)

    # ---------- budget file (optional) ----------

    def _build_budget_section(self):
        frame = ctk.CTkFrame(self)
        frame.pack(fill="x", pady=(10, 0))

        ctk.CTkLabel(
            frame, text="Budget file (optional)", font=ctk.CTkFont(weight="bold")
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=15, pady=(10, 5))

        ctk.CTkButton(frame, text="Open budget file...",
                      command=self.open_budget_file).grid(
            row=1, column=0, sticky="w", padx=15, pady=5)
        self.budget_file_label = ctk.CTkLabel(frame, text="No budget loaded")
        self.budget_file_label.grid(row=1, column=1, sticky="w", padx=15)

        labels = (("group", "Group column"), ("budget", "Monthly budget column"))
        for i, (role, label) in enumerate(labels, start=2):
            ctk.CTkLabel(frame, text=label).grid(
                row=i, column=0, sticky="w", padx=15, pady=5)
            menu = ctk.CTkOptionMenu(frame, values=[NONE], width=250)
            menu.grid(row=i, column=1, sticky="w", padx=15, pady=5)
            self.budget_menus[role] = menu

        self.budget_apply = ctk.CTkButton(
            frame, text="Apply budget", command=self.apply_budget, state="disabled")
        self.budget_apply.grid(row=4, column=0, sticky="w", padx=15, pady=(10, 5))

        self.budget_status = ctk.CTkLabel(frame, text="", anchor="w")
        self.budget_status.grid(row=5, column=0, columnspan=2, sticky="w",
                                padx=15, pady=(0, 10))

    def open_budget_file(self):
        path = filedialog.askopenfilename(
            title="Select a budget file",
            filetypes=[("Data files", "*.csv *.xlsx *.xls"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            self.budget_raw = self._read_file(Path(path))
        except Exception as e:
            self._set_budget_status(f"Could not read file: {e}", error=True)
            return

        self.budget_path = Path(path)
        self.budget_file_label.configure(text=self.budget_path.name)
        columns = [str(c) for c in self.budget_raw.columns]
        for role, menu in self.budget_menus.items():
            menu.configure(values=[NONE] + columns)
            menu.set(self._guess_budget_column(role, columns))
        self.budget_apply.configure(state="normal")
        self._set_budget_status("Check the columns and press Apply budget.")

    def _guess_budget_column(self, role, columns):
        if role == "budget":
            numeric = [c for c in columns if self._is_numeric_like(self.budget_raw[c])]
            for col in numeric:
                if "budget" in col.lower():
                    return col
            return numeric[0] if numeric else NONE

        # group: try the name hints, then the first text column
        for hint in ROLES["group"][1]:
            for col in columns:
                if hint in col.lower():
                    return col
        for col in columns:
            if not self._is_numeric_like(self.budget_raw[col]):
                return col
        return NONE

    def apply_budget(self):
        group_col = self.budget_menus["group"].get()
        budget_col = self.budget_menus["budget"].get()

        if NONE in (group_col, budget_col):
            self._set_budget_status("Please choose both columns.", error=True)
            return
        if group_col == budget_col:
            self._set_budget_status("Group and budget must be different columns.",
                                    error=True)
            return

        df = self.budget_raw[[group_col, budget_col]].copy()
        df[budget_col] = self._to_number(df[budget_col])
        df = df.dropna(subset=[budget_col])
        df[group_col] = df[group_col].astype(str).str.strip()
        # if a group appears on several rows, add its budgets together
        df = df.groupby(group_col, as_index=False)[budget_col].sum()

        if df.empty:
            self._set_budget_status("No valid rows. Check the budget column.", error=True)
            return

        self.app.data_store.set_budget(
            df, self.budget_path.name, {"group": group_col, "budget": budget_col})

        msg = f"Budget loaded for {len(df)} groups."
        store = self.app.data_store
        if store.has_data and store.column("group"):
            data_groups = set(store.df[store.column("group")].astype(str).str.strip())
            missing = data_groups - set(df[group_col])
            if missing:
                msg += " No budget found for: " + ", ".join(sorted(missing)) + "."
        self._set_budget_status(msg)

    @staticmethod
    def _to_number(series):
        # Convert a column to numbers, also handling '1 234,50' style text.
        if series.dtype == object:
            series = (series.astype(str)
                      .str.replace(r"\s", "", regex=True)
                      .str.replace(",", ".", regex=False))
        return pd.to_numeric(series, errors="coerce")

    def _set_budget_status(self, text, error=False):
        self.budget_status.configure(text=text,
                                     text_color="#e06c75" if error else "#98c379")

    # ---------- helpers ----------

    def _show_preview(self, df):
        self.preview.configure(state="normal")
        self.preview.delete("1.0", "end")
        self.preview.insert("1.0", df.head(15).to_string(index=False))
        self.preview.configure(state="disabled")

    def _set_status(self, text, error=False):
        self.status.configure(text=text, text_color="#e06c75" if error else "#98c379")