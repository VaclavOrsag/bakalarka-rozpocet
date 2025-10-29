import tkinter as tk
from tkinter import ttk

from app import database as db

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
        # Tato událost zajistí, že se data načtou vždy, když se na záložku přepnete.
        self.tab_frame.bind("<Visibility>", self.load_data)

    def _create_budget_treeview(self, parent_frame):
        """Pomocná metoda pro vytvoření a konfiguraci Treeview pro rozpočet."""
        
        # Vytvoříme rám pro Treeview a Scrollbar
        tree_frame = ttk.Frame(parent_frame)
        tree_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Definujeme sloupce, které bude tabulka mít
        columns = ('plan', 'rozpocet', 'plneni')
        tree = ttk.Treeview(tree_frame, columns=columns, show='tree headings')
        
        # Nastavíme hlavičky sloupců
        tree.heading('#0', text='Kategorie')
        tree.heading('plan', text='Minulé období')
        tree.heading('rozpocet', text='Rozpočet')
        tree.heading('plneni', text='Plnění')
        
        # Nastavíme vlastnosti sloupců (šířka, zarovnání)
        tree.column('#0', width=120, stretch=tk.YES) 
        tree.column('plan', width=120, anchor='e') 
        tree.column('rozpocet', width=120, anchor='e')
        tree.column('plneni', width=120, anchor='e')

        # Propojíme se scrollbarem
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        tree.pack(side="left", fill="both", expand=True)
        
        return tree
    
    def load_data(self, event=None):
        """
        Načte účetní osnovu a skutečné součty z transakcí a zobrazí je.
        """
        # Vyčistíme oba stromy od starých dat
        for tree in [self.tree_prijmy, self.tree_vydaje]:
            tree.delete(*tree.get_children())

        # Načteme potřebná data z databáze
        all_categories = db.get_all_categories(self.app.profile_path)
        historical_sums = db.calculate_sums_by_category(self.app.profile_path, is_current=0)
        current_sums = db.calculate_sums_by_category(self.app.profile_path, is_current=1)

        # Připravíme data pro stavbu stromu
        to_process = {cat[0]: cat for cat in all_categories}
        tree_items = {}

        # Spolehlivě sestavíme stromy patro po patru
        items_added_in_pass = -1
        while items_added_in_pass != 0:
            items_added_in_pass = 0
            for cat_id, cat_data in list(to_process.items()):
                nazev, typ, parent_id = cat_data[1], cat_data[2], cat_data[3]

                # Získáme skutečné součty pro tuto kategorii
                historical_sum = historical_sums.get(cat_id, 0.0)
                current_sum = current_sums.get(cat_id, 0.0)
                
                # Zobrazíme součty ve správných sloupcích
                values_tuple = (f"{historical_sum:,.2f} Kč", "", f"{current_sum:,.2f} Kč")

                # Rozhodneme, do kterého stromu položka patří
                tree = self.tree_prijmy if typ == 'příjem' else self.tree_vydaje

                # Vložíme do stromu (hlavní kategorie nebo podkategorie)
                if parent_id is None:
                    iid = tree.insert('', 'end', text=nazev, values=values_tuple, open=True)
                    tree_items[cat_id] = iid
                    del to_process[cat_id]
                    items_added_in_pass += 1
                elif parent_id in tree_items:
                    parent_iid = tree_items[parent_id]
                    iid = tree.insert(parent_iid, 'end', text=nazev, values=values_tuple, open=True)
                    tree_items[cat_id] = iid
                    del to_process[cat_id]
                    items_added_in_pass += 1
        self._update_parent_sums(self.tree_prijmy)
        self._update_parent_sums(self.tree_vydaje)

    def _update_parent_sums(self, tree):
        """
        Projde zadaný strom a rekurzivně sečte hodnoty z podkategorií
        do jejich nadřazených kategorií.
        """
        # Projdeme všechny hlavní kategorie (ty na nejvyšší úrovni)
        for parent_iid in tree.get_children():
            self._recursive_sum(tree, parent_iid)

    def _recursive_sum(self, tree, item_iid):
        """
        Pomocná rekurzivní funkce, která správně sečte hodnoty zdola nahoru.
        """
        # Zjistíme, jestli má položka nějaké "děti" (podkategorie)
        children = tree.get_children(item_iid)
        
        # Získáme PŮVODNÍ hodnoty položky, které byly vloženy v 'load_data'.
        values = tree.item(item_iid, 'values')
        try:
            # Převedeme textové hodnoty zpět na čísla
            direct_value_plan_str = values[0].replace(' Kč', '').replace(',', '')
            direct_value_plan = float(direct_value_plan_str)
            direct_value_plneni_str = values[2].replace(' Kč', '').replace(',', '')
            direct_value_plneni = float(direct_value_plneni_str)
        except (ValueError, IndexError):
            direct_value_plan = 0.0
            direct_value_plneni = 0.0

        # Pokud položka nemá žádné děti, její hodnoty jsou finální.
        if not children:
            return direct_value_plan, direct_value_plneni

        # Pokud MÁ položka děti, její finální hodnoty jsou její PŘÍMÉ HODNOTY
        # plus součet finálních hodnot všech jejích dětí.
        total_sum_of_children_plan = 0
        total_sum_of_children_plneni = 0
        for child_iid in children:
            child_plan, child_plneni = self._recursive_sum(tree, child_iid)
            total_sum_of_children_plan += child_plan
            total_sum_of_children_plneni += child_plneni
        
        final_total_plan = direct_value_plan + total_sum_of_children_plan
        final_total_plneni = direct_value_plneni + total_sum_of_children_plneni

        # Aktualizujeme zobrazené hodnoty pro rodičovskou položku
        values = list(tree.item(item_iid, 'values'))
        values[0] = f"{final_total_plan:,.2f} Kč"
        values[2] = f"{final_total_plneni:,.2f} Kč"
        tree.item(item_iid, values=values)

        # Vrátíme finální spočítané hodnoty, aby je mohl použít rodič o úroveň výš
        return final_total_plan, final_total_plneni