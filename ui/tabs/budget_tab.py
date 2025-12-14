"""
Záložka Rozpočet - Zobrazení a editace plánovaných rozpočtů.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Optional, Tuple, Dict, Set

from app import database as db
from app.utils import format_money, parse_money


class BudgetTab:
    """
    Třída reprezentující záložku 'Rozpočet'.
    Zobrazuje hierarchický přehled příjmů a výdajů s porovnáním
    minulého období, plánovaného rozpočtu a aktuálního plnění.
    Umožňuje editaci rozpočtu pro listové kategorie.
    """

    def __init__(self, tab_frame: ttk.Frame, app_controller: Any) -> None:
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

        # Mapy a stav pro editaci (oddělené mapy pro oba stromy, aby se nepletla iid)
        self._iid_to_catid_income = {}
        self._iid_to_catid_expense = {}
        self._cats_with_children = set()
        self._active_editor = None  # (entry, tree, iid)

        # Tato událost zajistí, že se data načtou vždy, když se na záložku přepnete.
        self.tab_frame.bind("<Visibility>", self.load_data)

        # Dvojklik pro editaci rozpočtu (jen sloupec Rozpočet a jen listové kategorie)
        self.tree_prijmy.bind('<Double-1>', lambda e, t=self.tree_prijmy: self._on_double_click_budget(e, t))
        self.tree_vydaje.bind('<Double-1>', lambda e, t=self.tree_vydaje: self._on_double_click_budget(e, t))

    def _create_budget_treeview(self, parent_frame: ttk.Frame) -> ttk.Treeview:
        """Pomocná metoda pro vytvoření a konfiguraci Treeview pro rozpočet."""
        
        # Vytvoříme rám pro Treeview a Scrollbar
        tree_frame = ttk.Frame(parent_frame)
        tree_frame.pack(fill='both', expand=True, padx=5, pady=(5, 0))
        
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
        
        # --- FOOTER PRO CELKOVÉ SOUČTY ---
        footer_frame = ttk.Frame(parent_frame, relief='solid', borderwidth=1)
        footer_frame.pack(fill='x', padx=5, pady=(2, 5))
        
        # Label pro "CELKEM:"
        celkem_label = ttk.Label(footer_frame, text="CELKEM:", font=('TkDefaultFont', 9, 'bold'))
        celkem_label.grid(row=0, column=0, sticky='w', padx=(5, 0))
        
        # Labels pro hodnoty (zarovnané se sloupci treeview)
        sum_past_label = ttk.Label(footer_frame, text="0,00 Kč", font=('TkDefaultFont', 9, 'bold'), anchor='e')
        sum_past_label.grid(row=0, column=1, sticky='ew', padx=5)
        
        sum_budget_label = ttk.Label(footer_frame, text="0,00 Kč", font=('TkDefaultFont', 9, 'bold'), anchor='e')
        sum_budget_label.grid(row=0, column=2, sticky='ew', padx=5)
        
        sum_current_label = ttk.Label(footer_frame, text="0,00 Kč", font=('TkDefaultFont', 9, 'bold'), anchor='e')
        sum_current_label.grid(row=0, column=3, sticky='ew', padx=5)
        
        # Konfigurace grid weights pro zarovnání
        footer_frame.columnconfigure(0, weight=1, minsize=120)  # Kategorie sloupec
        footer_frame.columnconfigure(1, weight=0, minsize=120)  # Minulé období
        footer_frame.columnconfigure(2, weight=0, minsize=120)  # Rozpočet
        footer_frame.columnconfigure(3, weight=0, minsize=120)  # Plnění
        
        # Uložíme reference na footer labels pro pozdější update
        tree.footer_labels = {
            'past': sum_past_label,
            'budget': sum_budget_label,
            'current': sum_current_label
        }
        
        return tree
    
    def load_data(self, event: Optional[tk.Event] = None) -> None:
        """
        Načte kompletní přehled z databáze (agregace řeší SQL) a zobrazí jej.
        """
        # Vyčistíme oba stromy od starých dat
        for tree in [self.tree_prijmy, self.tree_vydaje]:
            tree.delete(*tree.get_children())
        self._iid_to_catid_income.clear()
        self._iid_to_catid_expense.clear()
        self._cats_with_children.clear()

    # Jediný dotaz do DB, který vrátí vše potřebné včetně agregací nad podstromy
        overview = db.get_budget_overview(self.app.profile_path)

        # Připravíme data pro stavbu dvou stromů (příjmy/výdaje)
        # Formát záznamu: {id, nazev, typ, parent_id, sum_past, sum_current, budget_plan}
        by_id = {row['id']: row for row in overview}
        # Zjistíme rodiče (kategorie, které mají potomky) – tam nebudeme povolovat přímou editaci
        for row in overview:
            if row['parent_id'] is not None:
                self._cats_with_children.add(row['parent_id'])
        to_process = set(by_id.keys())
        tree_items = {}

        # Vkládáme patro po patru, až dokud nevložíme všechny položky
        items_added_in_pass = -1
        while items_added_in_pass != 0 and to_process:
            items_added_in_pass = 0
            for cat_id in list(to_process):
                row = by_id[cat_id]
                nazev = row['nazev']
                typ = row['typ']
                parent_id = row['parent_id']

                # Z databáze už máme finální agregované hodnoty
                values_tuple = (
                    # Všechny tři sloupce zobrazujeme kladně
                    format_money(abs(row['sum_past'])),
                    format_money(abs(row['budget_plan'])),
                    format_money(abs(row['sum_current'])),
                )

                tree = self.tree_prijmy if typ == 'příjem' else self.tree_vydaje

                if parent_id is None:
                    # Zobrazení s ikonou pro custom kategorie
                    display_text = f"📁 {nazev}" if row.get('is_custom') == 1 else nazev
                    iid = tree.insert('', 'end', text=display_text, values=values_tuple, open=True)
                    
                    # Přidáme tag pro červenou barvu
                    if row.get('is_custom') == 1:
                        tree.item(iid, tags=('custom',))
                    
                    if tree is self.tree_prijmy:
                        self._iid_to_catid_income[iid] = cat_id
                    else:
                        self._iid_to_catid_expense[iid] = cat_id
                    tree_items[cat_id] = iid
                    to_process.remove(cat_id)
                    items_added_in_pass += 1
                elif parent_id in tree_items:
                    parent_iid = tree_items[parent_id]
                    # Zobrazení s ikonou pro custom kategorie
                    display_text = f"📁 {nazev}" if row.get('is_custom') == 1 else nazev
                    iid = tree.insert(parent_iid, 'end', text=display_text, values=values_tuple, open=True)
                    
                    # Přidáme tag pro červenou barvu
                    if row.get('is_custom') == 1:
                        tree.item(iid, tags=('custom',))
                    
                    if tree is self.tree_prijmy:
                        self._iid_to_catid_income[iid] = cat_id
                    else:
                        self._iid_to_catid_expense[iid] = cat_id
                    tree_items[cat_id] = iid
                    to_process.remove(cat_id)
                    items_added_in_pass += 1

        # Konfigurace červené barvy pro custom kategorie
        for tree in [self.tree_prijmy, self.tree_vydaje]:
            tree.tag_configure('custom', foreground='red')

        # Není třeba dopočítávat sumy v Pythonu – vše spočítala databáze.
        
        # --- AKTUALIZACE FOOTER SOUČTŮ ---
        self._update_footer_totals()
        
        return

    def _on_double_click_budget(self, event: tk.Event, tree: ttk.Treeview) -> None:
        """Zahájí editaci ve sloupci Rozpočet, pokud jde o listovou kategorii."""
        # Identifikace sloupce – '#2' odpovídá 'rozpoctu' (('plan','rozpocet','plneni'))
        col = tree.identify_column(event.x)
        if col != '#2':
            return
        iid = tree.identify_row(event.y)
        if not iid:
            return
        # vyber správnou mapu podle stromu
        if tree is self.tree_prijmy:
            if iid not in self._iid_to_catid_income:
                return
            cat_id = self._iid_to_catid_income[iid]
        else:
            if iid not in self._iid_to_catid_expense:
                return
            cat_id = self._iid_to_catid_expense[iid]
            
        # VALIDACE: Custom kategorie nelze editovat - rozpočet se počítá automaticky
        if db.is_custom_category(self.app.profile_path, cat_id):
            messagebox.showinfo(
                "Nelze editovat", 
                "Rozpočet custom kategorie se počítá automaticky jako součet podkategorií.\n\n"
                "Pro změnu rozpočtu upravte rozpočty jednotlivých podkategorií."
            )
            return

        # Souřadnice buňky pro overlay Entry
        bbox = tree.bbox(iid, col)
        if not bbox:
            return
        x, y, w, h = bbox
        editor = ttk.Entry(tree)
        editor.place(x=x, y=y, width=w, height=h)

        # Předvyplnit vlastní plán, ne agregát
        try:
            current_own = db.get_own_budget(self.app.profile_path, cat_id)
        except Exception:
            current_own = 0.0
        # Editor předvyplníme kladnou hodnotou, 2 desetinná místa dle _format_number_for_edit
        editor.insert(0, self._format_number_for_edit(abs(current_own)))
        editor.select_range(0, 'end')
        editor.focus_set()

        self._active_editor = (editor, tree, iid)


        def commit() -> None:
            # detekce prvního rozpočtu (před uložením)
            had_any_before = db.has_any_budget(self.app.profile_path)

            text = editor.get()
            value = parse_money(text)
            editor.destroy()
            self._active_editor = None
            if value is None:
                return
            # Rozpočet ukládáme se správným znaménkem dle stromu, ale velikost bereme jako kladnou (2 desetinná místa)
            value = round(abs(value), 2)
            if tree is self.tree_vydaje:
                value = -value
            # Pokud se fakticky nic nezměnilo oproti uložené hodnotě, neukládej
            if abs(value - float(current_own)) < 1e-9:
                return
            db.update_or_insert_budget(self.app.profile_path, cat_id, float(value))
            
            # NOVÉ: Přepočítej custom kategorie po změně podkategorie
            db.update_custom_category_budgets(self.app.profile_path)
            
            self.load_data()

            # po uložení: pokud předtím žádný rozpočet nebyl, právě vznikl první
            has_any_now = db.has_any_budget(self.app.profile_path)
            # uložení prvního rozpočtu odemkne záložku analýzy + nabídne import aktuálních dat
            if not had_any_before and has_any_now:
                # přepočet viditelnosti záložek (odemkne Analýzu dle logiky v controlleru)
                self.app.update_tabs_visibility()
                if messagebox.askyesno(
                    "Rozpočet vytvořen",
                    "První rozpočet byl vytvořen.\nChcete nyní importovat aktuální data pro Analýzu a Plnění?"
                ):
                    self.app.import_excel(is_current=1)

        def cancel() -> None:
            editor.destroy()
            self._active_editor = None

        editor.bind('<Return>', lambda e: commit())
        editor.bind('<KP_Enter>', lambda e: commit())
        editor.bind('<Escape>', lambda e: cancel())
        editor.bind('<FocusOut>', lambda e: commit())

    def _format_number_for_edit(self, val: float) -> str:
        # Pro editor bez měny a bez oddělovačů tisíců
        if abs(val - int(val)) < 1e-9:
            return str(int(val))
        return f"{val:.2f}"

    def _update_footer_totals(self) -> None:
        """Vypočítá a zobrazí celkové součty pro oba stromy (příjmy/výdaje)."""
        
        def calculate_totals(tree: ttk.Treeview) -> Tuple[float, float, float]:
            """Sečte hodnoty všech root kategorií v daném stromu."""
            total_past = 0.0
            total_budget = 0.0
            total_current = 0.0
            
            # Projdeme všechny root items (parent='')
            for iid in tree.get_children(''):
                values = tree.item(iid, 'values')
                if values:
                    # Formát: ('909 101,39 Kč', '570 000,00 Kč', '446 250,35 Kč')
                    past = parse_money(values[0]) or 0.0
                    budget = parse_money(values[1]) or 0.0
                    current = parse_money(values[2]) or 0.0
                    
                    total_past += past
                    total_budget += budget
                    total_current += current
            
            return total_past, total_budget, total_current
        
        def get_color(current: float, budget: float) -> str:
            """Vrací barvu podle % plnění."""
            if budget == 0:
                return 'black'
            pct = abs(current) / abs(budget) * 100
            if pct < 50:
                return 'green'
            elif pct < 99:
                return '#DAA520'  # Dark goldenrod (žlutá)
            else:
                return 'red'
        
        # Aktualizace příjmů
        past_in, budget_in, current_in = calculate_totals(self.tree_prijmy)
        self.tree_prijmy.footer_labels['past'].config(text=format_money(past_in))
        self.tree_prijmy.footer_labels['budget'].config(text=format_money(budget_in))
        self.tree_prijmy.footer_labels['current'].config(
            text=format_money(current_in),
            foreground=get_color(current_in, budget_in)
        )
        
        # Aktualizace výdajů
        past_out, budget_out, current_out = calculate_totals(self.tree_vydaje)
        self.tree_vydaje.footer_labels['past'].config(text=format_money(past_out))
        self.tree_vydaje.footer_labels['budget'].config(text=format_money(budget_out))
        self.tree_vydaje.footer_labels['current'].config(
            text=format_money(current_out),
            foreground=get_color(current_out, budget_out)
        )