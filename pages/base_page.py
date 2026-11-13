import customtkinter as ctk


class BasePage(ctk.CTkFrame):
    # Base class that every page inherits.

    title = "Page"

    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app  # access to the main app and shared data
        self.build()

    def build(self):
        # Create the page's widgets here (override in subclasses).
        pass

    def on_show(self):
        # Called every time the page is brought to the front.
        pass