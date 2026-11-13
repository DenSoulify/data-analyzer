import customtkinter as ctk

from pages.base_page import BasePage


class HomePage(BasePage):
    title = "Home"

    def build(self):
        ctk.CTkLabel(
            self, text="Data Analytics App",
            font=ctk.CTkFont(size=28, weight="bold"),
        ).pack(pady=(40, 5))
        ctk.CTkLabel(
            self, text="Analyze costs across departments, categories and time.",
            font=ctk.CTkFont(size=14),
        ).pack()

        # --- what is loaded right now ---
        status = ctk.CTkFrame(self)
        status.pack(fill="x", padx=60, pady=30)
        ctk.CTkLabel(status, text="Current session",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=(10, 5))
        self.data_label = ctk.CTkLabel(status, anchor="w")
        self.data_label.pack(fill="x", padx=15)
        self.budget_label = ctk.CTkLabel(status, anchor="w")
        self.budget_label.pack(fill="x", padx=15, pady=(0, 10))

        # --- quick start ---
        steps = (
            "1.  Open 'Load Data' and choose a CSV or Excel file.\n"
            "2.  Check the column mapping and press Apply.\n"
            "3.  Optionally load a budget file for budget vs. actual.\n"
            "4.  Explore the data in Table, Statistics and Charts."
        )
        ctk.CTkLabel(self, text=steps, justify="left", anchor="w").pack(padx=60, anchor="w")

        self.app.data_store.subscribe(self.refresh)
        self.refresh()

    def refresh(self):
        store = self.app.data_store
        if store.has_data:
            self.data_label.configure(
                text=f"Data:  {store.source_name}  ({len(store.df):,} rows)")
        else:
            self.data_label.configure(text="Data:  not loaded")

        if store.has_budget:
            self.budget_label.configure(
                text=f"Budget:  {store.budget_source}  ({len(store.budget_df)} groups)")
        else:
            self.budget_label.configure(text="Budget:  not loaded")