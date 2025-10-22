import tkinter as tk
from tkinter import ttk

class AccountingStructureTab:
    def __init__(self, tab_frame, app_controller):
        """
        Inicializuje obsah záložky 'Účetní Osnova'.
        """
        self.app = app_controller

        ttk.Label(
            tab_frame, 
            text="Zde bude nástroj pro správu hierarchie kategorií.", 
            font=("Arial", 16)
        ).pack(pady=50)