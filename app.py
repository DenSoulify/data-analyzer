import customtkinter as ctk
from pages.home_page import HomePage
from core.data_store import DataStore
from pages.data_page import DataPage
from pages.table_page import TablePage
from pages.stats_page import StatsPage
from pages.charts_page import ChartsPage

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.data_store = DataStore()
        self.title("Data Analytics App")
        self.geometry("1100x700")

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.pages = {}
        self._register_pages([HomePage, DataPage, TablePage, StatsPage, ChartsPage])
        self.show_page(HomePage)

    def _register_pages(self, page_classes):
        for page_class in page_classes:
            page = page_class(self.container, self)
            page.grid(row=0, column=0, sticky="nsew")
            self.pages[page_class] = page

            ctk.CTkButton(
                self.sidebar, text=page_class.title,
                command=lambda p=page_class: self.show_page(p),
            ).pack(padx=15, pady=(15, 0), fill="x")

    def show_page(self, page_class):
        page = self.pages[page_class]
        page.tkraise()
        page.on_show()