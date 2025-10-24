import os
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import tkinter.messagebox as messagebox

from app import database as db
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
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)

        # --- KROK 2: Vytvoření rámů pro jednotlivé záložky ---
        self.tab_home = ttk.Frame(self.notebook)
        self.tab_sources = ttk.Frame(self.notebook)
        self.tab_budget = ttk.Frame(self.notebook)
        self.tab_analysis = ttk.Frame(self.notebook)
        self.tab_accounting = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_home, text='Home')   

        # --- Naplnění záložek obsahem ---
        # Vytvoříme instance VŠECH manažerů hned na začátku
        self.home_ui = HomeTab(self.tab_home, self)
        self.sources_ui = SourcesTab(self.tab_sources, self)
        self.budget_ui = BudgetTab(self.tab_budget, self)
        self.analysis_ui = AnalysisTab(self.tab_analysis, self)
        self.accounting_ui = AccountingStructureTab(self.tab_accounting, self)

        # Po spuštění zkontrolujeme stav a zobrazíme správné záložky
        self.root.after(100, self.update_tabs_visibility)

    def _center_window(self, win):
        # ... (metoda zůstává stejná)
        win.update_idletasks()
        root_x, root_y, root_w, root_h = self.root.winfo_x(), self.root.winfo_y(), self.root.winfo_width(), self.root.winfo_height()
        win_w, win_h = win.winfo_width(), win.winfo_height()
        x = root_x + (root_w - win_w) // 2
        y = root_y + (root_h - win_h) // 2
        win.geometry(f"+{x}+{y}")
    
    def switch_to_tab(self, tab_name: str):
        """Programově přepne na záložku se zadaným názvem."""
        # 'tabs()' vrátí seznam ID všech záložek.
        # 'tab(id, "text")' vrátí název záložky pro dané ID.
        for i, _ in enumerate(self.notebook.tabs()):
            if self.notebook.tab(i, "text") == tab_name:
                self.notebook.select(i) # 'select(i)' přepne na záložku s daným indexem
                break

    def export_csv(self):
        # ... (metoda zůstává stejná)
        filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV soubory", "*.csv")])
        if filepath:
            if file_exporter.export_to_csv(filepath, self.profile_path):
                messagebox.showinfo("Export úspěšný", f"Data byla úspěšně exportována.")
            else:
                messagebox.showerror("Chyba exportu", "Při exportu dat nastala chyba.")

    def import_excel(self):
        """Zpracovává import transakcí z Excelu do aktuálního profilu."""
        filepath = filedialog.askopenfilename(
            filetypes=[("Excel soubory", "*.xlsx *.xlsm")]
        )
        if not filepath:
            return

        choice = messagebox.askyesnocancel(
            "Možnosti importu", 
            "Přidat data k existujícím (Ano),\nnebo přepsat všechna data (Ne)?"
        )

        if choice is None: # Uživatel klikl na Storno
            return
        
        if choice is False: # Uživatel zvolil "Ne" - přepsat
            # ✅ KROK 1: Přidáme potvrzovací dialog pro bezpečnost
            if not messagebox.askyesno("Potvrdit přepsání", "Opravdu chcete smazat VŠECHNY existující transakce?\n\nVaše vytvořená účetní osnova zůstane zachována."):
                return # Pokud uživatel klikne na Ne, operaci zrušíme
            db.delete_all_items(self.profile_path)
        
        # Samotný import
        if file_importer.import_from_excel(filepath, self.profile_path):
            # ✅ KROK 2: Po importu se pokusíme automaticky zařadit nová data
            db.reapply_all_categories(self.profile_path)
            
            # Obnovíme všechny relevantní záložky
            self.sources_ui.load_items()
            self.sources_ui.update_total()
            # hasattr() je bezpečnostní kontrola pro případ, že by UI ještě neexistovalo
            if hasattr(self, 'accounting_ui'):
                self.accounting_ui.refresh_data()

            # ✅ KROK 3: Vylepšená zpráva pro uživatele
            messagebox.showinfo("Import úspěšný", "Data byla úspěšně naimportována a automaticky zařazena podle vaší osnovy.")
        else:
            messagebox.showerror("Chyba importu", "Při importu dat nastala chyba.")


    def update_tabs_visibility(self):
        """
        Zkontroluje stav profilu a dynamicky zobrazí nebo skryje záložky.
        """
        # Skryjeme všechny záložky kromě 'Home'
        for tab in [self.tab_sources, self.tab_budget, self.tab_analysis, self.tab_accounting]:
            try:
                self.notebook.hide(tab)
            except tk.TclError:
                pass # Ignorujeme chybu, pokud záložka ještě není přidána

        # Podmíněně "odemkneme" další záložky
        if db.has_transactions(self.profile_path):
            self.notebook.add(self.tab_sources, text='Zdroje')
            self.notebook.add(self.tab_accounting, text='Účetní osnova')

        if db.has_categories(self.profile_path):
            self.notebook.add(self.tab_budget, text='Rozpočet')

        # a tak dále... (tuto logiku budeme postupně doplňovat)

        # Na konci vždy obnovíme stav v 'Home'
        self.home_ui.check_profile_state()