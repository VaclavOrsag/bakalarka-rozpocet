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

    def import_excel(self, is_current):
        """Zpracovává import transakcí z Excelu do aktuálního profilu."""
        filepath = filedialog.askopenfilename(
            filetypes=[("Excel soubory", "*.xlsx *.xlsm")]
        )
        if not filepath:
            return

        # Zeptáme se na přepsání pouze pokud importujeme historická data A NĚJAKÁ UŽ EXISTUJÍ.
        if is_current == 0 and db.has_transactions(self.profile_path, is_current=0):
            choice = messagebox.askyesnocancel(
                "Možnosti importu historických dat", 
                "Přidat data k existujícím (Ano),\nnebo přepsat všechna historická data (Ne)?"
            )
            if choice is None: return # Storno
            if choice is False: # Přepsat
                if not messagebox.askyesno("Potvrdit přepsání", "Opravdu chcete smazat VŠECHNY existující historické transakce?"):
                    return
                db.delete_all_items(self.profile_path, is_current=0)
        
        # Samotný import
        if file_importer.import_from_excel(filepath, self.profile_path, is_current):
            # Po importu se pokusíme automaticky zařadit nová data
            db.reapply_all_categories(self.profile_path)
            
            # Obnovíme všechny relevantní záložky
            self.sources_ui.load_items()
            self.sources_ui.update_total()
            if hasattr(self, 'accounting_ui'):
                self.accounting_ui.refresh_data()
            if hasattr(self, 'budget_ui'):
                self.budget_ui.load_data()

            # Po importu musíme zkontrolovat, zda se mají zobrazit nové záložky
            self.update_tabs_visibility()

            messagebox.showinfo("Import úspěšný", "Data byla úspěšně naimportována a automaticky zařazena podle vaší osnovy.")
        else:
            messagebox.showerror("Chyba importu", "Při importu dat nastala chyba.")


    def update_tabs_visibility(self):
        """
        Zkontroluje stav profilu a dynamicky zobrazí nebo skryje záložky.
        """
        # Zapamatujeme si aktuálně vybranou záložku, abychom ji po úpravách obnovili
        try:
            _prev_selected = self.notebook.select()
            prev_selected_text = self.notebook.tab(_prev_selected, "text") if _prev_selected else None
        except tk.TclError:
            prev_selected_text = None

        # Skryjeme všechny záložky kromě 'Home'
        for tab in [self.tab_sources, self.tab_budget, self.tab_analysis, self.tab_accounting]:
            try:
                self.notebook.hide(tab)
            except tk.TclError:
                pass # Ignorujeme chybu, pokud záložka ještě není přidána

        # Podmíněně "odemkneme" další záložky
        if db.has_transactions(self.profile_path, is_current=0):
            self.notebook.add(self.tab_sources, text='Transakce')
            self.notebook.add(self.tab_accounting, text='Účetní osnova')

        if db.has_categories(self.profile_path):
            self.notebook.add(self.tab_budget, text='Rozpočet')
        # a tak dále... (tuto logiku budeme postupně doplňovat)

        # Obnovíme dříve vybranou záložku, pokud stále existuje
        if prev_selected_text:
            try:
                for tab_id in self.notebook.tabs():
                    if self.notebook.tab(tab_id, "text") == prev_selected_text:
                        self.notebook.select(tab_id)
                        break
            except tk.TclError:
                # Pokud by záložka mezitím zmizela (což by se nemělo stát), nic se nestane
                pass
        
        # Volání check_profile_state zde není ideální, protože se volá i když nejsme na Home.
        # Lepší je, aby si HomeTab obnovoval stav sám, když je zobrazen.
        # Prozatím ponecháme, ale budeme refaktorovat.
        self.home_ui.check_profile_state()