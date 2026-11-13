from tkinter import ttk

import customtkinter as ctk


def apply_tree_style():
    # ttk widgets don't follow CustomTkinter's theme, so I styled them myself.
    dark = ctk.get_appearance_mode() == "Dark"
    bg = "#2b2b2b" if dark else "#ffffff"
    fg = "#dce4ee" if dark else "#1a1a1a"
    head_bg = "#1f538d"

    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Data.Treeview", background=bg, fieldbackground=bg,
                    foreground=fg, rowheight=26, borderwidth=0)
    style.map("Data.Treeview", background=[("selected", head_bg)],
              foreground=[("selected", "white")])
    style.configure("Data.Treeview.Heading", background=head_bg, foreground="white",
                    relief="flat", font=("Segoe UI", 10, "bold"))
    style.map("Data.Treeview.Heading", background=[("active", "#2a6bb5")])