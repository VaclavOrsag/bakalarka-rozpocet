import tkinter as tk
from tkinter import ttk  # Nový import pro Treeview
import tkinter.messagebox as messagebox
from tkinter import filedialog
import database as db
import file_exporter
import file_importer
import os

from tabs.sources_tab import SourcesTab
from tabs.budget_tab import BudgetTab
from tabs.analysis_tab import AnalysisTab
from tabs.home_tab import HomeTab

class App:
    def __init__(self, root, profile_path):
        self.root = root
        self.profile_path = profile_path
        self.root.title(f"Nástroj pro tvorbu rozpočtu - {os.path.basename(profile_path)}")
        self.root.geometry("1280x800")  # Zvětšíme okno pro více sloupců

        # --- Menu (zůstává stejné) ---
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Soubor", menu=file_menu)
        file_menu.add_command(label="Exportovat do CSV...", command=self.export_csv)
        file_menu.add_command(label="Importovat z Excelu...", command=self.import_excel)
        file_menu.add_separator()
        file_menu.add_command(label="Konec", command=self.root.quit)

        # --- KROK 1: Vytvoření Notebooku (záložek) ---
        notebook = ttk.Notebook(self.root)
        notebook.pack(expand=True, fill='both', padx=10, pady=10)

        # --- KROK 2: Vytvoření rámů pro jednotlivé záložky ---
        self.tab_home = ttk.Frame(notebook)
        self.tab_sources = ttk.Frame(notebook)
        self.tab_budget = ttk.Frame(notebook)
        self.tab_analysis = ttk.Frame(notebook)
        notebook.add(self.tab_home, text='Home')
        notebook.add(self.tab_sources, text='Zdroje')
        notebook.add(self.tab_budget, text='Rozpočet')
        notebook.add(self.tab_analysis, text='Analýza')

        # --- KROK 3: Naplnění záložek obsahem ---
        self.home_ui = HomeTab(self.tab_home, self)
        self.sources_ui = SourcesTab(self.tab_sources, self)
        self.budget_ui = BudgetTab(self.tab_budget, self)
        self.analysis_ui = AnalysisTab(self.tab_analysis, self)

    def _center_window(self, win):
        # ... (metoda zůstává stejná)
        win.update_idletasks()
        root_x, root_y, root_w, root_h = self.root.winfo_x(), self.root.winfo_y(), self.root.winfo_width(), self.root.winfo_height()
        win_w, win_h = win.winfo_width(), win.winfo_height()
        x = root_x + (root_w - win_w) // 2
        y = root_y + (root_h - win_h) // 2
        win.geometry(f"+{x}+{y}")

    def export_csv(self):
        # ... (metoda zůstává stejná)
        filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV soubory", "*.csv")])
        if filepath:
            if file_exporter.export_to_csv(filepath):
                messagebox.showinfo("Export úspěšný", f"Data byla úspěšně exportována.")
            else:
                messagebox.showerror("Chyba exportu", "Při exportu dat nastala chyba.")

    def import_excel(self):
        # ... (metoda zůstává stejná)
        filepath = filedialog.askopenfilename(filetypes=[("Excel soubory", "*.xlsx *.xlsm")])
        if filepath:
            choice = messagebox.askyesnocancel("Možnosti importu", "Přidat data k existujícím (Ano),\nnebo přepsat všechna data (Ne)?")
            if choice is None: return
            if choice is False: db.delete_all_items(self.profile_path)
            if file_importer.import_from_excel(filepath, self.profile_path):
                self.load_items()
                self.update_total()
                messagebox.showinfo("Import úspěšný", "Data byla úspěšně naimportována.")
            else:
                messagebox.showerror("Chyba importu", "Při importu dat nastala chyba.")