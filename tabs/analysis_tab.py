import tkinter as tk
from tkinter import ttk

class AnalysisTab:
    def __init__(self, tab_frame, app_controller):
        """
        Inicializuje obsah záložky 'Analýza'.
        """
        self.app = app_controller

        # Dočasný text, který později nahradíme grafy a reporty
        ttk.Label(
            tab_frame, 
            text="Tato sekce je ve vývoji.\nZde budou grafy a analýzy plnění rozpočtu.", 
            font=("Arial", 16),
            justify=tk.CENTER
        ).pack(pady=50)