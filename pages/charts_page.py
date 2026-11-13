import customtkinter as ctk
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter

from core.analysis import breakdown, budget_vs_actual
from pages.base_page import BasePage

PALETTE = ["#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f",
           "#edc948", "#b07aa1", "#ff9da7", "#9c755f", "#bab0ac"]
MAX_SLICES = 8   # donut: more slices than this get merged into "Other"


class ChartsPage(BasePage):
    title = "Charts"

    def build(self):
        ctk.CTkLabel(
            self, text="Charts", font=ctk.CTkFont(size=24, weight="bold")
        ).pack(anchor="w", pady=(0, 10))

        self.message = ctk.CTkLabel(self, text="", anchor="w")
        self.message.pack(fill="x")

        self.content = ctk.CTkFrame(self, fg_color="transparent")

        # --- controls ---
        controls = ctk.CTkFrame(self.content, fg_color="transparent")
        controls.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(controls, text="Chart:").pack(side="left")
        self.chart_menu = ctk.CTkOptionMenu(
            controls, values=["-"], width=160, command=lambda _: self._on_chart_change())
        self.chart_menu.pack(side="left", padx=(8, 20))
        ctk.CTkLabel(controls, text="Group by:").pack(side="left")
        self.group_menu = ctk.CTkOptionMenu(
            controls, values=["-"], width=180, command=lambda _: self.draw())
        self.group_menu.pack(side="left", padx=8)

        # --- the matplotlib figure, embedded as a normal widget ---
        self.fig = Figure(figsize=(8, 5), layout="constrained")
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.content)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        self.app.data_store.subscribe(self.refresh)
        self.refresh()

    # ---------- what is available for this file? ----------

    def refresh(self):
        store = self.app.data_store
        if not store.has_data:
            self.content.pack_forget()
            self.message.configure(text="No data loaded yet. Go to 'Load Data' first.")
            return

        # only offer charts that the mapped roles can support
        self.group_columns = [c for c in (store.column("group"), store.column("category")) if c]
        charts = []
        if self.group_columns:
            charts.append("Bar chart")
        if store.column("date"):
            charts.append("Line chart")
        if self.group_columns:
            charts.append("Donut chart")
            if store.has_budget and store.column("group") and store.column("date"):
                charts.append("Budget vs. actual")

        if not charts:
            self.content.pack_forget()
            self.message.configure(
                text="Map a Group, Category or Date column on 'Load Data' to see charts.")
            return

        previous_chart = self.chart_menu.get()
        previous_group = self.group_menu.get()

        self.message.configure(text=f"Source: {store.source_name}")
        self.content.pack(fill="both", expand=True)
        self.chart_menu.configure(values=charts)
        self.chart_menu.set(previous_chart if previous_chart in charts else charts[0])
        if self.group_columns:
            self.group_menu.configure(values=self.group_columns)
            self.group_menu.set(previous_group if previous_group in self.group_columns
                                else self.group_columns[0])
        self._on_chart_change()

    def _on_chart_change(self):
        # these charts have a fixed grouping, so "Group by" does not apply
        no_group = self.chart_menu.get() in ("Line chart", "Budget vs. actual")
        self.group_menu.configure(state="disabled" if no_group else "normal")
        self.draw()

    # ---------- drawing ----------

    def draw(self):
        dark = ctk.get_appearance_mode() == "Dark"
        self.bg = "#2b2b2b" if dark else "#ffffff"
        self.fg = "#dce4ee" if dark else "#1a1a1a"
        self.grid_color = "#444444" if dark else "#dddddd"

        self.fig.clear()                       # reuse the same figure every time
        self.fig.patch.set_facecolor(self.bg)
        ax = self.fig.add_subplot(111)
        ax.set_facecolor(self.bg)
        ax.tick_params(colors=self.fg)
        for side, spine in ax.spines.items():
            spine.set_color(self.grid_color)
            spine.set_visible(side in ("left", "bottom"))

        drawers = {"Bar chart": self._bar, "Line chart": self._line,
                   "Donut chart": self._donut, "Budget vs. actual": self._budget}
        # Error management shows a message in Charts page instead of showing just in console
        try:
            title = drawers[self.chart_menu.get()](ax)
        except Exception as e:
            self.fig.clear()
            self.fig.patch.set_facecolor(self.bg)
            self.fig.text(0.5, 0.5, f"Could not draw this chart:\n{e}",
                          ha="center", va="center", color="#e06c75")
            self.canvas.draw()
            return
        ax.set_title(title, color=self.fg, fontsize=13, pad=12)
        self.canvas.draw()

    def _bar(self, ax):
        store = self.app.data_store
        col = self.group_menu.get()
        result = breakdown(store.df, store.column("amount"), "column", col, None)

        # horizontal bars: long names stay readable
        bars = ax.barh(result.index.astype(str), result["sum"], color=PALETTE[0])
        ax.invert_yaxis()                      # biggest bar on top
        ax.bar_label(bars, labels=[f"{v:,.0f}" for v in result["sum"]],
                     color=self.fg, padding=4)
        ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:,.0f}"))
        ax.xaxis.grid(True, color=self.grid_color)
        ax.set_axisbelow(True)                 # grid lines behind the bars
        ax.margins(x=0.12)                     # room for the value labels
        return f"Total {store.column('amount')} by {col}"

    def _line(self, ax):
        store = self.app.data_store
        result = breakdown(store.df, store.column("amount"), "month",
                           None, store.column("date"))

        x = list(range(len(result)))
        ax.plot(x, result["sum"], marker="o", linewidth=2, color=PALETTE[0])

        # with many months, only label every few of them
        step = max(1, len(result) // 10)
        ax.set_xticks(x[::step])
        ax.set_xticklabels(result.index[::step], rotation=45, ha="right")
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
        ax.yaxis.grid(True, color=self.grid_color)
        ax.set_axisbelow(True)
        return f"Total {store.column('amount')} per month"

    def _donut(self, ax):
        store = self.app.data_store
        col = self.group_menu.get()
        sums = breakdown(store.df, store.column("amount"), "column", col, None)["sum"]

        # too many slices are unreadable: keep the biggest, merge the rest
        if len(sums) > MAX_SLICES:
            other = sums.iloc[MAX_SLICES - 1:].sum()
            sums = pd.concat([sums.iloc[:MAX_SLICES - 1], pd.Series({"Other": other})])

        total = sums.sum()
        wedges, _ = ax.pie(
            sums, colors=PALETTE[:len(sums)], startangle=90, counterclock=False,
            wedgeprops=dict(width=0.4, edgecolor=self.bg))   # width < 1 makes the hole
        ax.legend(wedges, [f"{name}  {v / total * 100:.1f} %" for name, v in sums.items()],
                  loc="center left", bbox_to_anchor=(1, 0.5),
                  frameon=False, labelcolor=self.fg)
        ax.text(0, 0, f"{total:,.0f}", ha="center", va="center",
                fontsize=16, fontweight="bold", color=self.fg)
        return f"Share of total by {col}"

    def _budget(self, ax):
        store = self.app.data_store
        bm = store.budget_mapping
        group = store.column("group")
        result, months = budget_vs_actual(
            store.df, store.column("amount"), group, store.column("date"),
            store.budget_df, bm["group"], bm["budget"])

        x = list(range(len(result)))
        width = 0.38
        ax.bar([i - width / 2 for i in x], result["budget"], width,
               label="Budget", color=PALETTE[0])
        actual_bars = ax.bar([i + width / 2 for i in x], result["actual"], width,
                             label="Actual", color=PALETTE[1])

        # percent of budget used, written above each actual bar
        labels = ["n/a" if pd.isna(u) else f"{u:.0f} %" for u in result["used"]]
        ax.bar_label(actual_bars, labels=labels, color=self.fg, padding=3)

        ax.set_xticks(x)
        ax.set_xticklabels(result.index)
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
        ax.yaxis.grid(True, color=self.grid_color)
        ax.set_axisbelow(True)
        ax.margins(y=0.12)
        ax.legend(frameon=False, labelcolor=self.fg)
        return f"Budget vs. actual by {group} ({months} months)"