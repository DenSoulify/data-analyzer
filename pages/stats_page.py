from tkinter import ttk

import customtkinter as ctk

from core.styles import apply_tree_style
from pages.base_page import BasePage
from core.analysis import breakdown

CARDS = ("Total", "Average", "Median", "Largest", "Rows")


class StatsPage(BasePage):
    title = "Statistics"

    def build(self):
        self.card_values = {}
        self.choices = {}   # dropdown label -> ("column", name) or ("month", None)

        ctk.CTkLabel(
            self, text="Statistics", font=ctk.CTkFont(size=24, weight="bold")
        ).pack(anchor="w", pady=(0, 10))

        self.message = ctk.CTkLabel(self, text="", anchor="w")
        self.message.pack(fill="x")

        # everything below lives in one frame so we can hide it when there is no data
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self._build_cards()
        self._build_breakdown()

        self.app.data_store.subscribe(self.refresh)
        self.refresh()

    # ---------- layout ----------

    def _build_cards(self):
        row = ctk.CTkFrame(self.content, fg_color="transparent")
        row.pack(fill="x", pady=(0, 15))
        for i, name in enumerate(CARDS):
            row.grid_columnconfigure(i, weight=1, uniform="cards")
            card = ctk.CTkFrame(row)
            card.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 8, 0))
            ctk.CTkLabel(card, text=name, text_color="gray70").pack(
                anchor="w", padx=12, pady=(10, 0))
            value = ctk.CTkLabel(card, text="-", font=ctk.CTkFont(size=20, weight="bold"))
            value.pack(anchor="w", padx=12, pady=(0, 10))
            self.card_values[name] = value

    def _build_breakdown(self):
        self.breakdown_frame = ctk.CTkFrame(self.content, fg_color="transparent")

        header = ctk.CTkFrame(self.breakdown_frame, fg_color="transparent")
        header.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(header, text="Break down by:").pack(side="left")
        self.choice_menu = ctk.CTkOptionMenu(
            header, values=["-"], width=220, command=lambda _: self._render_breakdown())
        self.choice_menu.pack(side="left", padx=10)

        table_frame = ctk.CTkFrame(self.breakdown_frame)
        table_frame.pack(fill="both", expand=True)
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        apply_tree_style()
        columns = ("name", "total", "average", "count", "share")
        self.tree = ttk.Treeview(table_frame, style="Data.Treeview",
                                 columns=columns, show="headings", selectmode="browse")
        scroll = ctk.CTkScrollbar(table_frame, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")

        for col, text in zip(columns, ("", "Total", "Average", "Count", "Share")):
            self.tree.heading(col, text=text)
            self.tree.column(col, width=140, anchor="w" if col == "name" else "e")

    # ---------- refresh ----------

    def refresh(self):
        store = self.app.data_store
        if not store.has_data:
            self.content.pack_forget()
            self.message.configure(text="No data loaded yet. Go to 'Load Data' first.")
            return

        self.message.configure(text=f"Source: {store.source_name}")
        self.content.pack(fill="both", expand=True)
        self._render_cards()

        # offer only the breakdowns that the mapped roles allow
        self.choices = {}
        for role in ("group", "category"):
            col = store.column(role)
            if col:
                self.choices[f"By {col}"] = ("column", col)
        if store.column("date"):
            self.choices["By month"] = ("month", None)

        if self.choices:
            labels = list(self.choices)
            self.choice_menu.configure(values=labels)
            self.choice_menu.set(labels[0])
            self.breakdown_frame.pack(fill="both", expand=True)
            self._render_breakdown()
        else:
            self.breakdown_frame.pack_forget()

    def _render_cards(self):
        store = self.app.data_store
        amount = store.df[store.column("amount")]
        values = {
            "Total": f"{amount.sum():,.2f}",
            "Average": f"{amount.mean():,.2f}",
            "Median": f"{amount.median():,.2f}",
            "Largest": f"{amount.max():,.2f}",
            "Rows": f"{len(amount):,}",
        }
        for name, text in values.items():
            self.card_values[name].configure(text=text)

    def _render_breakdown(self):
        store = self.app.data_store
        kind, col = self.choices[self.choice_menu.get()]
        result = breakdown(store.df, store.column("amount"),
                           kind, col, store.column("date"))

        self.tree.delete(*self.tree.get_children())
        self.tree.heading("name", text=self.choice_menu.get().replace("By ", ""))
        for name, row in result.iterrows():
            self.tree.insert("", "end", values=(
                name, f"{row['sum']:,.2f}", f"{row['mean']:,.2f}",
                f"{int(row['count']):,}", f"{row['share']:.1f} %"))