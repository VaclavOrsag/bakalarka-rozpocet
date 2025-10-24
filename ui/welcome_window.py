import os

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox

import config 
from app import database as db
from app import file_importer


class WelcomeWindow:
    def __init__(self, root):
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

    def clear_frame(self):
        """Smaže veškerý obsah z hlavního rámu."""
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def show_initial_choice(self):
        """Zobrazí první, úvodní otázku."""
        self.clear_frame()
        ttk.Label(self.main_frame, text="Máte již vytvořený profil?", font=("Arial", 14)).pack(pady=10)
        
        ttk.Button(self.main_frame, text="Ano, vybrat ze seznamu", command=self.show_profile_list).pack(fill="x", pady=5)
        ttk.Button(self.main_frame, text="Ne, vytvořit nový", command=self.confirm_create_empty).pack(fill="x", pady=5)

    def show_profile_list(self):
        """Zobrazí seznam existujících .db souborů."""
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

    def show_create_options(self):
        """Zobrazí možnosti pro vytvoření nového profilu."""
        self.clear_frame()
        ttk.Label(self.main_frame, text="Jak chcete vytvořit nový profil?", font=("Arial", 12)).pack(pady=10)
        
        ttk.Button(self.main_frame, text="Vytvořit prázdný profil", command=self.confirm_create_empty).pack(fill="x", pady=5)
        ttk.Button(self.main_frame, text="Vytvořit profil z Excel souboru", command=self.confirm_create_from_excel).pack(fill="x", pady=5)
        ttk.Button(self.main_frame, text="Zpět", command=self.show_initial_choice).pack(pady=10)

    
    def confirm_open_profile(self):
        selection = self.profile_listbox.curselection()
        if not selection:
            messagebox.showinfo("Upozornění", "Vyberte platný profil.")
            return
        filename = self.profile_listbox.get(selection[0])
        self.selected_profile_path = os.path.join(self.profiles_dir, filename)
        self.action = "open"
        self.top.destroy()

    def confirm_create_empty(self):
        filepath = filedialog.asksaveasfilename(
            initialdir=self.profiles_dir,
            title="Vytvořit nový prázdný profil",
            defaultextension=".db", filetypes=[("Databázové soubory", "*.db")]
        )
        if filepath:
            self.selected_profile_path = filepath
            self.action = "create_empty"
            self.top.destroy()
            