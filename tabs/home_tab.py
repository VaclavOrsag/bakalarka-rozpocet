import tkinter as tk
from tkinter import ttk

class HomeTab:
    def __init__(self, tab_frame, app_controller):
        """
        Inicializuje obsah záložky 'Home' (Dashboard).
        """
        self.app = app_controller

        # Dočasný text pro hlavní přehled
        ttk.Label(
            tab_frame, 
            text="Vítejte! Zde bude váš hlavní přehled (Dashboard).", 
            font=("Arial", 16)
        ).pack(pady=50)