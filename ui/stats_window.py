import tkinter as tk
from tkinter import ttk
from app.database import dashboard_db
from datetime import datetime
import sqlite3

class StatsWindow:
    def __init__(self, parent, app, month: int, transaction_type: str):
        self.parent = parent
        self.app = app
        self.month = month
        self.transaction_type = transaction_type  # "výdej" nebo "příjem"
        self.current_year = datetime.now().year
        
        self.window = tk.Toplevel(parent)
        self.window.title(self._get_title())
        self.window.transient(parent)
        self.window.grab_set()
        self.window.geometry("1200x600")  # Širší kvůli 7 sloupcům
        
        self._create_layout()
        self._load_data()

    def _get_title(self):
        month_names = ["Leden", "Únor", "Březen", "Duben", "Květen", "Červen",
                       "Červenec", "Srpen", "Září", "Říjen", "Listopad", "Prosinec"]
        type_name = "Výdaje" if self.transaction_type == "výdej" else "Příjmy"
        return f"Detail měsíce – {month_names[self.month-1]} – {type_name}"

    def _create_layout(self):
        """Vytvoří layout okna s tabulkou kategorií."""
        # Header
        header = ttk.Frame(self.window, padding=(12, 12))
        header.pack(fill="x")
        
        ttk.Label(header, 
                  text=self._get_title(), 
                  font=("Arial", 14, "bold")).pack(side="left")

        # Tabulka s kategoriemi
        table_frame = ttk.Frame(self.window, padding=(12, 0, 12, 12))
        table_frame.pack(fill="both", expand=True)

        # Definice sloupců - 7 sloupců pro kompletní přehled
        columns = ("Kategorie", "Min.transakce", "Akt.transakce", "%(M→M)", "Rozpočet", "Plnění R.", "%(R)")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=18)
        
        # Nastavení hlaviček a šířek sloupců
        self.tree.heading("Kategorie", text="Kategorie")
        self.tree.heading("Min.transakce", text="Min.transakce")
        self.tree.heading("Akt.transakce", text="Akt.transakce")
        self.tree.heading("%(M→M)", text="%(M→M)")
        self.tree.heading("Rozpočet", text="Rozpočet")
        self.tree.heading("Plnění R.", text="Plnění R.")
        self.tree.heading("%(R)", text="%(R)")
        
        self.tree.column("Kategorie", width=250, anchor="w")
        self.tree.column("Min.transakce", width=120, anchor="e")
        self.tree.column("Akt.transakce", width=120, anchor="e")
        self.tree.column("%(M→M)", width=100, anchor="e")
        self.tree.column("Rozpočet", width=120, anchor="e")
        self.tree.column("Plnění R.", width=120, anchor="e")
        self.tree.column("%(R)", width=100, anchor="e")
        
        # Definice barevných tagů pro řádky
        # Světlé barvy pro %(M→M) - informativní
        self.tree.tag_configure('mm_green', background='#e8f5e9')    # Světle zelená
        self.tree.tag_configure('mm_yellow', background='#fffde7')   # Světle žlutá
        self.tree.tag_configure('mm_red', background='#ffebee')      # Světle červená
        self.tree.tag_configure('mm_blue', background='#e3f2fd')     # Světle modrá: NOVÉ
        
        # Sytější barvy pro %(R) - akční
        self.tree.tag_configure('r_green', background='#c8e6c9')     # Zelená rozpočtu
        self.tree.tag_configure('r_yellow', background='#fff9c4')    # Žlutá rozpočtu
        self.tree.tag_configure('r_red', background='#ffcdd2')       # Červená rozpočtu
        
        self.tree.tag_configure('gray', background='#f5f5f5')        # Šedá: žádná data

        # Scrollbar
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        # Footer s celkovým přehledem rozpočtu
        self.footer_frame = ttk.Frame(self.window, padding=(12, 0, 12, 12))
        self.footer_frame.pack(fill="x")
        
        # Label pro celkový rozpočet (bude aktualizován v _update_footer)
        self.footer_label = ttk.Label(self.footer_frame, text="", font=("Arial", 10, "bold"))
        self.footer_label.pack(side="left")
        
        ttk.Button(self.footer_frame, text="Zavřít", command=self.window.destroy).pack(side="right")

    def _load_data(self):
        """Načte data z databáze a zobrazí v hierarchické tabulce s barvami."""
        
        # Vyčistí existující data
        self.tree.delete(*self.tree.get_children())
        
        try:
            # Načti performance data (původní funkce)
            performance_data = dashboard_db.get_year_performance_summary(
                self.app.profile_path,
                self.transaction_type,
                self.current_year
            )
            
            # Načti rozpočty pro tento rok
            budgets = self._load_budgets()
            
            # Načti YTD (year-to-date) plnění
            ytd_data = self._load_ytd_spending()
            
            # Filtruj data jen pro aktuální měsíc A jen kategorie s rozpočtem
            month_data = []
            for row in performance_data:
                if row['month'] == self.month and row['id'] in budgets:
                    # Přidej budget a ytd info
                    row['budget'] = budgets.get(row['id'], 0)
                    row['ytd_current'] = ytd_data.get(row['id'], 0)
                    month_data.append(row)
            
            if not month_data:
                self.tree.insert("", "end", values=("Žádný rozpočet nastaven", "—", "—", "—", "—", "—", "—"), tags=('gray',))
                self._update_footer(0, 0, 0)
                return
            
            # Seřadí data hierarchicky
            hierarchy = self._build_hierarchy(month_data)
            
            # Zobrazí data v hierarchické struktuře
            self._display_hierarchy(hierarchy, parent_item="", level=0)
            
            # Aktualizuj footer s celkovými hodnotami (jen top-level kategorie)
            total_budget = sum(abs(row['budget']) for row in month_data if row['parent_id'] is None)
            total_ytd = sum(row['ytd_current'] for row in month_data if row['parent_id'] is None)
            total_percentage = (total_ytd / total_budget * 100) if total_budget > 0 else 0
            self._update_footer(total_budget, total_ytd, total_percentage)
        
        except Exception as e:
            print(f"Chyba při načítání dat: {e}")
            import traceback
            traceback.print_exc()
            self.tree.insert("", "end", values=("Chyba při načítání", str(e), "—", "—", "—", "—", "—"), tags=('gray',))
            self._update_footer(0, 0, 0)
    
    def _load_budgets(self) -> dict:
        """Načte rozpočty pro aktuální rok. Returns: {kategorie_id: budget_amount}"""
        conn = sqlite3.connect(self.app.profile_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT kategorie_id, planovana_castka
            FROM rozpocty
            WHERE rok = ?
        """, (self.current_year,))
        budgets = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()
        return budgets
    
    def _load_ytd_spending(self) -> dict:
        """Načte YTD spending (leden až aktuální měsíc). Returns: {kategorie_id: ytd_amount}"""
        conn = sqlite3.connect(self.app.profile_path)
        cursor = conn.cursor()
        cursor.execute("""
            WITH RECURSIVE tree(ancestor_id, descendant_id) AS (
                SELECT id, id FROM kategorie WHERE typ = ?
                UNION ALL
                SELECT t.ancestor_id, k.id
                FROM tree t
                JOIN kategorie k ON k.parent_id = t.descendant_id
            )
            SELECT 
                t.ancestor_id,
                COALESCE(SUM(ABS(i.castka)), 0) as ytd_total
            FROM tree t
            LEFT JOIN items i ON i.kategorie_id = t.descendant_id
                AND i.is_current = 1
                AND CAST(strftime('%m', i.datum) AS INTEGER) <= ?
                AND i.castka != 0
                AND i.co IS NOT NULL 
                AND i.co != ''
            GROUP BY t.ancestor_id
        """, (self.transaction_type, self.month))
        ytd = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()
        return ytd

    def _build_hierarchy(self, data: list) -> dict:
        """
        Vytvoří hierarchickou strukturu z plochého listu dat.
        
        Returns:
            Dict: {category_id: {'data': row_dict, 'children': [child_ids]}}
        """
        hierarchy = {}
        
        for row in data:
            cat_id = row['id']
            if cat_id not in hierarchy:
                hierarchy[cat_id] = {'data': row, 'children': []}
        
        # Propojí rodiče s dětmi
        for row in data:
            parent_id = row['parent_id']
            if parent_id and parent_id in hierarchy:
                cat_id = row['id']
                if cat_id not in hierarchy[parent_id]['children']:
                    hierarchy[parent_id]['children'].append(cat_id)
        
        return hierarchy

    def _display_hierarchy(self, hierarchy: dict, parent_item: str, level: int, parent_cat_id=None):
        """
        Rekurzivně zobrazí hierarchii kategorií v Treeview.
        
        Args:
            hierarchy: Hierarchická struktura z _build_hierarchy()
            parent_item: ID rodiče v Treeview (prázdný string pro top-level)
            level: Úroveň odsazení (0 = top-level, 1 = podkategorie, atd.)
            parent_cat_id: ID rodičovské kategorie (None pro top-level)
        """
        # Najdi kategorie na aktuální úrovni
        categories = [
            cat_id for cat_id, info in hierarchy.items()
            if info['data']['parent_id'] == parent_cat_id
        ]
        
        # Seřaď podle názvu
        categories.sort(key=lambda cid: hierarchy[cid]['data']['nazev'])
        
        for cat_id in categories:
            info = hierarchy[cat_id]
            row = info['data']
            
            # Odsazení názvu kategorie podle úrovně
            indent = "    " * level
            category_name = f"{indent}{row['nazev']}"
            
            # Formátování částek
            historical = row['historical']
            current = row['current']
            budget = abs(row['budget'])  # ABS protože výdaje jsou záporné
            ytd_current = row['ytd_current']
            
            historical_text = f"{historical:,.0f} Kč" if historical > 0 else "—"
            current_text = f"{current:,.0f} Kč" if current > 0 else "—"
            budget_text = f"{budget:,.0f} Kč"
            ytd_text = f"{ytd_current:,.0f} Kč" if ytd_current > 0 else "—"
            
            # Výpočet %(M→M) - month-to-month comparison
            if historical > 0:
                mm_percentage = (current / historical) * 100
                mm_text = f"{mm_percentage:.1f}%"
                mm_color = self._get_mm_color_tag(mm_percentage)
            elif current > 0 and historical == 0:
                mm_text = "NOVÉ"
                mm_color = 'mm_blue'
            else:
                mm_text = "—"
                mm_color = 'gray'
            
            # Výpočet %(R) - rozpočet percentage
            if budget > 0:
                r_percentage = (ytd_current / budget) * 100
                r_text = f"{r_percentage:.1f}%"
                r_color = self._get_r_color_tag(r_percentage)
            else:
                r_text = "—"
                r_color = 'gray'
            
            # Určení hlavní barvy řádku (priorita: %(R) > %(M→M))
            if r_color != 'gray':
                row_color = r_color
            else:
                row_color = mm_color
            
            # Vložení řádku do Treeview
            item_id = self.tree.insert(
                parent_item, 
                "end", 
                values=(category_name, historical_text, current_text, mm_text, budget_text, ytd_text, r_text),
                tags=(row_color,)
            )
            
            # Rekurzivně zobraz děti
            if info['children']:
                self._display_hierarchy(hierarchy, item_id, level + 1, cat_id)

    def _get_mm_color_tag(self, percentage: float) -> str:
        """
        Určí barevný tag pro %(M→M) - světlé barvy (informativní).
        
        Args:
            percentage: Procentuální hodnota
            
        Returns:
            'mm_green', 'mm_yellow', 'mm_red', nebo 'mm_blue'
        """
        if percentage <= 80:
            return 'mm_green'
        elif percentage <= 100:
            return 'mm_yellow'
        else:
            return 'mm_red'
    
    def _get_r_color_tag(self, percentage: float) -> str:
        """
        Určí barevný tag pro %(R) - sytější barvy (akční).
        
        Args:
            percentage: Procentuální hodnota
            
        Returns:
            'r_green', 'r_yellow', nebo 'r_red'
        """
        if percentage <= 80:
            return 'r_green'
        elif percentage <= 100:
            return 'r_yellow'
        else:
            return 'r_red'
    
    def _update_footer(self, total_budget: float, total_ytd: float, total_percentage: float):
        """
        Aktualizuje footer s celkovým přehledem rozpočtu.
        
        Args:
            total_budget: Celkový roční rozpočet
            total_ytd: Celkové YTD (year-to-date) plnění
            total_percentage: Celková procentuální hodnota
        """
        if total_budget == 0:
            self.footer_label.config(text="Žádný rozpočet nastaven", foreground="gray")
            return
        
        # Formátování textu
        text = f"Celkem: {total_ytd:,.0f} Kč / {total_budget:,.0f} Kč ({total_percentage:.1f}%)"
        
        # Určení barvy podle výkonnosti
        if total_percentage <= 80:
            color = "#2e7d32"  # Tmavě zelená
        elif total_percentage <= 100:
            color = "#f57f17"  # Tmavě žlutá
        else:
            color = "#c62828"  # Tmavě červená
        
        self.footer_label.config(text=text, foreground=color)
    
    def invalidate_cache(self):
        """
        Vymaže cache pro performance data.
        Volá se když uživatel přidá/upraví/smaže transakci.
        """
        self._load_data()  # Znovu načte data (cache již není potřeba)
