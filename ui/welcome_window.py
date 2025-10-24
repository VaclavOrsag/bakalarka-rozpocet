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

    # --- Následující metody zatím jen "předstírají" funkčnost ---
    
    def confirm_open_profile(self):
        selection = self.profile_listbox.curselection()
        if not selection:
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
            
    def confirm_create_from_excel(self):
        """
        Spustí proces vytvoření nového profilu z existujícího Excel souboru.
        """
        # Krok 1: Uživatel vybere zdrojový Excel soubor
        excel_path = filedialog.askopenfilename(
            title="Vyberte Excel soubor s historickými daty",
            filetypes=[("Excel soubory", "*.xlsx *.xlsm")]
        )
        if not excel_path: # Pokud uživatel nic nevybere
            return

        # Krok 2: Uživatel si zvolí, kam uložit nový databázový profil
        db_path = filedialog.asksaveasfilename(
            initialdir=self.profiles_dir,
            title="Uložit nový profil jako...",
            defaultextension=".db",
            filetypes=[("Databázové soubory", "*.db")]
        )
        if not db_path: # Pokud uživatel nic nevybere
            return

        try:
            # Krok 3: Vytvoříme prázdnou databázi se správnou strukturou
            db.init_db(db_path)

            # Krok 4: Spustíme náš existující importér
            success = file_importer.import_from_excel(excel_path, db_path)

            if success:
                messagebox.showinfo("Úspěch", f"Nový profil '{os.path.basename(db_path)}' byl úspěšně vytvořen z Excel souboru.")
                self.selected_profile_path = db_path
                self.action = "open" # Chceme tento nově vytvořený profil rovnou otevřít
                self.top.destroy()
            else:
                messagebox.showerror("Chyba", "Při importu dat z Excelu nastala chyba. Zkontrolujte konzoli pro více detailů.")
        except Exception as e:
            messagebox.showerror("Kritická chyba", f"Nepodařilo se vytvořit profil: {e}")