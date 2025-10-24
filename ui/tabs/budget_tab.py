import tkinter as tk
from tkinter import ttk
from datetime import datetime

class BudgetTab:
    def __init__(self, tab_frame, app_controller):
        """
        Inicializuje uživatelské rozhraní pro záložku 'Rozpočet'.
        """
        self.app = app_controller
        self.tab_frame = tab_frame

        # --- HORNÍ PANEL PRO OVLÁDÁNÍ ---
        top_frame = ttk.Frame(self.tab_frame)
        top_frame.pack(fill='x', padx=10, pady=10)

        # -- Ovládací prvky pro rok --
        ttk.Label(top_frame, text="Rok rozpočtu:", font=("Arial", 11, "bold")).pack(side='left', padx=(0, 5))
        
        # Nastavíme aktuální rok jako výchozí hodnotu
        current_year = datetime.now().year
        self.year_var = tk.StringVar(value=str(current_year))
        
        self.year_entry = ttk.Entry(top_frame, textvariable=self.year_var, width=10, font=("Arial", 11))
        self.year_entry.pack(side='left')
        
        # Zde budou později navázány události pro automatické načítání

        # -- Tlačítka pro akce --
        # Umístíme je na pravou stranu horního panelu
        action_buttons_frame = ttk.Frame(top_frame)
        action_buttons_frame.pack(side='right')

        self.create_proposal_button = ttk.Button(action_buttons_frame, text="Vytvořit návrh...")
        self.create_proposal_button.pack(side='left', padx=5)

        self.save_button = ttk.Button(action_buttons_frame, text="Uložit rozpočet")
        self.save_button.pack(side='left')

        # --- HLAVNÍ PANEL PRO ZOBRAZENÍ ROZPOČTU ---
        main_pane = ttk.PanedWindow(self.tab_frame, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # --- Levý sloupec: PŘÍJMY ---
        income_frame = ttk.LabelFrame(main_pane, text="Příjmy")
        main_pane.add(income_frame, weight=1)
        self.tree_prijmy = self._create_budget_treeview(income_frame)

        # --- Pravý sloupec: VÝDAJE ---
        expense_frame = ttk.LabelFrame(main_pane, text="Výdaje")
        main_pane.add(expense_frame, weight=1)
        self.tree_vydaje = self._create_budget_treeview(expense_frame)

    def _create_budget_treeview(self, parent_frame):
        """Pomocná metoda pro vytvoření a konfiguraci Treeview pro rozpočet."""
        
        # Vytvoříme rám pro Treeview a Scrollbar
        tree_frame = ttk.Frame(parent_frame)
        tree_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Definujeme sloupce, které bude tabulka mít
        columns = ('plan', 'skutecnost', 'rozdil')
        tree = ttk.Treeview(tree_frame, columns=columns, show='tree headings')
        
        # Nastavíme hlavičky sloupců
        tree.heading('#0', text='Kategorie')
        tree.heading('plan', text='Plánovaná částka')
        tree.heading('skutecnost', text='Skutečnost')
        tree.heading('rozdil', text='Rozdíl')
        
        # Nastavíme vlastnosti sloupců (šířka, zarovnání)
        tree.column('#0', width=120, stretch=tk.YES) 
        tree.column('plan', width=120, anchor='e') 
        tree.column('skutecnost', width=120, anchor='e')
        tree.column('rozdil', width=120, anchor='e')

        # Propojíme se scrollbarem
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        tree.pack(side="left", fill="both", expand=True)
        
        return tree