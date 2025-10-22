import tkinter as tk
from tkinter import ttk

class BudgetTab:
    def __init__(self, tab_frame, app_controller):
        self.app = app_controller

        # Dočasný text, který později nahradíme skutečným obsahem
        ttk.Label(tab_frame, 
                  text="Zde bude modul pro tvorbu a úpravu rozpočtu.", 
                  font=("Arial", 16)).pack(pady=50)