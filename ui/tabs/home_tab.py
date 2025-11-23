import tkinter as tk
from tkinter import ttk
from tkinter import filedialog     
import tkinter.messagebox as messagebox 
from datetime import datetime

from app import database as db
from app import file_importer 

class HomeTab:
    def __init__(self, tab_frame, app_controller):
        self.app = app_controller
        self.tab_frame = tab_frame
        
        # Při prvním zobrazení záložky zkontrolujeme stav
        self.tab_frame.bind("<Visibility>", self.check_profile_state)

    def clear_tab(self):
        for widget in self.tab_frame.winfo_children():
            widget.destroy()

    def check_profile_state(self, event=None):
        """
        Zkontroluje stav AKTUÁLNÍHO profilu a zobrazí další logický krok.
        """
        self.clear_tab()
        
        # Priorita 1: Chybí vůbec nějaká historická data?
        if not db.has_transactions(self.app.profile_path, is_current=0):
            self._show_step_import_data()
            return
        
        # Priorita 2: Chybí účetní osnova?
        if not db.has_categories(self.app.profile_path):
            self._show_step_create_structure()
            return

        # Priorita 3: Chybí rozpočet?
        if not db.has_any_budget(self.app.profile_path):
            self._show_step_create_budget()
            return
        
        # Priorita 4: Chybí aktuální transakce?
        if not db.has_transactions(self.app.profile_path, is_current=1):
            self._show_step_import_current()
            return

        # Vše je hotovo, zobrazíme hlavní dashboard
        self._show_dashboard()

    def _show_step_import_data(self):
        """Průvodce pro úplně první import dat."""
        ttk.Label(self.tab_frame, text="Vítejte!", font=("Arial", 18, "bold")).pack(pady=(20, 10))
        ttk.Label(self.tab_frame, 
                  text="Zdá se, že tento profil je prázdný.\n\nZačněte prosím importem transakcí (např. z minulého roku), ze kterých budeme vycházet.",
                  wraplength=500, justify=tk.CENTER).pack(pady=10)
        
        # Použijeme existující importní funkci z hlavní aplikace
        ttk.Button(self.tab_frame, 
                   text="Importovat transakce z Excelu...",
                   command=self.import_historical
        ).pack(pady=20)

    def _show_step_create_structure(self):
        """Průvodce pro vytvoření účetní osnovy."""
        ttk.Label(self.tab_frame, text="Krok 2: Tvorba účetní osnovy", font=("Arial", 18, "bold")).pack(pady=(20, 10))
        ttk.Label(self.tab_frame, 
                  text="Data jsou naimportována. Nyní je potřeba je roztřídit a vytvořit z nich Vaši strukturu kategorií.",
                  wraplength=500, justify=tk.CENTER).pack(pady=10)
        
        ttk.Button(self.tab_frame, 
                   text="Přejít na tvorbu osnovy",
                   command=lambda: self.app.switch_to_tab('Účetní osnova') 
        ).pack(pady=20)

    def _show_step_create_budget(self):
        """Průvodce pro vytvoření rozpočtu."""
        ttk.Label(self.tab_frame, text="Krok 3/3: Tvorba rozpočtu", font=("Arial", 18, "bold")).pack(pady=(20, 10))
        
        ttk.Label(
            self.tab_frame, 
            text="Vaše struktura kategorií je hotová. Posledním krokem je vytvoření samotného rozpočtu.",
            wraplength=500, 
            justify=tk.CENTER
        ).pack(pady=10)
        
        ttk.Button(
            self.tab_frame, 
            text="Přejít na tvorbu rozpočtu",
            command=lambda: self.app.switch_to_tab('Rozpočet')
        ).pack(pady=20)

    def _show_step_import_current(self):
        ttk.Label(self.tab_frame, text="Krok 4/4: Import aktuálních dat", font=("Arial", 18, "bold")).pack(pady=(20,10))

        ttk.Label(self.tab_frame,
                  text="Rozpočet je vytvořen. Pro zobrazení plnění a analýzy aktuálních dat můžete nyní naimportovat aktuální transakce.\nTento import lze provést i později v záložce 'Transakce'.",
                  wraplength=520, justify=tk.CENTER).pack(pady=10)
        ttk.Button(self.tab_frame,
                   text="Importovat aktuální transakce (Excel)...",
                   command=self.import_current
        ).pack(pady=20)

    def import_current(self):
        self.app.import_excel(is_current=1)
        self.check_profile_state()


    def _show_dashboard(self):
        """Vloží dashboard obsah přímo do home tabu."""
        try:
            # Import dashboard komponenty
            from ui.tabs.dashboard_tab import DashboardTab
            
            # Vytvoříme a vložíme dashboard
            self.dashboard_instance = DashboardTab(self.tab_frame, self.app)
            
            # Uložíme referenci do app pro invalidaci cache
            self.app.dashboard_ui = self.dashboard_instance
            
            
        except Exception as e:
            # Fallback při chybě načítání dashboardu
            ttk.Label(self.tab_frame, text="🏠 Dashboard", 
                    font=("Arial", 18, "bold")).pack(pady=(20,10))
            ttk.Label(self.tab_frame, text="Chyba při načítání dashboardu", 
                    foreground="red").pack(pady=10)
            ttk.Label(self.tab_frame, text=f"Detail: {str(e)}", 
                    foreground="gray", font=("Arial", 9)).pack(pady=5)
            print(f"Dashboard embedding error: {e}")


    def import_historical(self):
        """Zpracovává PRVNÍ import transakcí z Excelu do nového profilu."""
        # Zavoláme centrální importní funkci s parametrem is_current=0
        self.app.import_excel(is_current=0)
        # Po úspěšném importu se stav automaticky zkontroluje a UI se aktualizuje
        self.check_profile_state()