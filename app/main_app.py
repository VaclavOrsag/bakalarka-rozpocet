import os
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import tkinter.messagebox as messagebox

from . import database as db
from . import file_exporter
from . import file_importer

from ui.tabs.home_tab import HomeTab
from ui.tabs.sources_tab import SourcesTab
from ui.tabs.budget_tab import BudgetTab
from ui.tabs.analysis_tab import AnalysisTab
from ui.tabs.accounting_structure_tab import AccountingStructureTab

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
        tab_home = ttk.Frame(notebook)
        tab_sources = ttk.Frame(notebook)
        tab_budget = ttk.Frame(notebook)
        tab_analysis = ttk.Frame(notebook)
        tab_accounting = ttk.Frame(notebook)

        notebook.add(tab_home, text='Home')
        notebook.add(tab_sources, text='Zdroje')
        notebook.add(tab_budget, text='Rozpočet')
        notebook.add(tab_analysis, text='Analýza')
        notebook.add(tab_accounting, text='Učetní osnova')

        # --- KROK 3: Naplnění záložek obsahem ---
        self.home_ui = HomeTab(tab_home, self)
        self.sources_ui = SourcesTab(tab_sources, self)
        self.budget_ui = BudgetTab(tab_budget, self)
        self.analysis_ui = AnalysisTab(tab_analysis, self)
        self.accounting_ui = AccountingStructureTab(tab_accounting, self)

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
            if file_exporter.export_to_csv(filepath, self.profile_path):
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
                self.sources_ui.load_items()
                self.sources_ui.update_total()
                self.accounting_ui.refresh_data()
                messagebox.showinfo("Import úspěšný", "Data byla úspěšně naimportována.")
            else:
                messagebox.showerror("Chyba importu", "Při importu dat nastala chyba.")