"""
Dialog pro výběr nebo vytvoření profilu při spuštění aplikace.
"""
import os
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox

import config 


class WelcomeDialog:
    """
    Dialogové okno zobrazené při startu aplikace.
    Umožňuje uživateli vybrat existující profil (databázi) nebo vytvořit nový.
    """

    def __init__(self, root: tk.Tk) -> None:
        """
        Inicializuje uvítací dialog.
        
        Args:
            root: Hlavní okno aplikace (rodič).
        """
        self.top = tk.Toplevel(root)
        self.top.title("Vítejte v Nástroji pro tvorbu rozpočtu")

        # Získáme a uložíme si cestu k adresáři s profily
        self.profiles_dir = config.get_profiles_directory()

        self.selected_profile_path = None # Zde bude výsledek
        self.action = None # Zde si uložíme, co se má stát dál

        # Vytvoříme hlavní rám
        self.main_frame = ttk.Frame(self.top, padding="20")
        self.main_frame.pack(expand=True, fill="both")

        self.show_initial_choice()

    def clear_frame(self) -> None:
        """Smaže veškerý obsah z hlavního rámu."""
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def show_initial_choice(self) -> None:
        """Zobrazí první, úvodní otázku (Existující vs. Nový profil)."""
        self.clear_frame()
        ttk.Label(self.main_frame, text="Máte již vytvořený profil?", font=("Arial", 14)).pack(pady=10)
        
        ttk.Button(self.main_frame, text="Ano, vybrat ze seznamu", command=self.show_profile_list).pack(fill="x", pady=5)
        ttk.Button(self.main_frame, text="Ne, vytvořit nový", command=self.confirm_create_empty).pack(fill="x", pady=5)

    def show_profile_list(self) -> None:
        """Zobrazí seznam existujících .db souborů v adresáři profilů."""
        self.clear_frame()
        ttk.Label(self.main_frame, text="Vyberte existující profil:").pack(pady=10)
        
        # Listbox a scrollbar
        list_frame = ttk.Frame(self.main_frame)
        list_frame.pack(fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical")
        self.profile_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, width=50)
        scrollbar.config(command=self.profile_listbox.yview)
        
        scrollbar.pack(side="right", fill="y")
        self.profile_listbox.pack(side="left", fill="both", expand=True)

        # Načteme profily
        try:
            files = [f for f in os.listdir(self.profiles_dir) if f.endswith('.db')]
            for file in files:
                self.profile_listbox.insert(tk.END, file)
        except Exception as e:
            print(f"Chyba při načítání profilů: {e}")

        # Tlačítka
        ttk.Button(self.main_frame, text="Otevřít vybraný", command=self.confirm_open_profile).pack(pady=10)
        ttk.Button(self.main_frame, text="Zpět", command=self.show_initial_choice).pack()

    def confirm_open_profile(self) -> None:
        """Potvrdí výběr existujícího profilu a zavře dialog."""
        selection = self.profile_listbox.curselection()
        if not selection:
            messagebox.showinfo("Upozornění", "Vyberte platný profil.")
            return
        filename = self.profile_listbox.get(selection[0])
        self.selected_profile_path = os.path.join(self.profiles_dir, filename)
        self.action = "open"
        self.top.destroy()

    def confirm_create_empty(self) -> None:
        """Zobrazí formulář pro zadání názvu nového profilu."""
        self.clear_frame()
        ttk.Label(self.main_frame, text="Zadejte název nového profilu:", font=("Arial", 12)).pack(pady=10)
        
        self.profile_name_var = tk.StringVar()
        entry = ttk.Entry(self.main_frame, textvariable=self.profile_name_var)
        entry.pack(pady=5, padx=20, fill="x")
        entry.focus()
        
        ttk.Button(self.main_frame, text="Vytvořit", command=self._perform_create_profile).pack(pady=10)
        ttk.Button(self.main_frame, text="Zpět", command=self.show_initial_choice).pack()

    def _perform_create_profile(self) -> None:
        """Vytvoří cestu k novému profilu a zavře dialog."""
        name = self.profile_name_var.get().strip()
        if not name:
            messagebox.showwarning("Chyba", "Zadejte název profilu.")
            return
            
        # Sanitizace názvu souboru
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            if char in name:
                messagebox.showwarning("Chyba", f"Název profilu nesmí obsahovat znaky: {invalid_chars}")
                return

        if not name.endswith(".db"):
            name += ".db"
            
        filepath = os.path.join(self.profiles_dir, name)
        
        if os.path.exists(filepath):
            messagebox.showwarning("Chyba", "Profil s tímto názvem již existuje.")
            return
            
        self.selected_profile_path = filepath
        self.action = "create_empty"
        self.top.destroy()
            