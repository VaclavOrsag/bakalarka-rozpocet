import tkinter as tk
from tkinter import ttk
from app.database import dashboard_db
from app.utils import format_money

class StatsWindow:
    def __init__(self, parent, app, month: int, transaction_type: str):
        self.parent = parent
        self.app = app
        self.month = month
        self.transaction_type = transaction_type  # "výdej" nebo "příjem"
        
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
        columns = ("Min.transakce", "Akt.transakce", "%(M→M)", "Rozpočet", "Plnění R.", "%(R)")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="tree headings", height=18)
        
        # Nastavení hlaviček a šířek sloupců
        self.tree.heading("#0", text="Kategorie")  # Stromová část (s +/- boxíky)
        self.tree.heading("Min.transakce", text="Min.transakce")
        self.tree.heading("Akt.transakce", text="Akt.transakce")
        self.tree.heading("%(M→M)", text="%(M→M)")
        self.tree.heading("Rozpočet", text="Rozpočet")
        self.tree.heading("Plnění R.", text="Plnění R.")
        self.tree.heading("%(R)", text="%(R)")
        
        self.tree.column("#0", width=250, anchor="w")  # Stromová část
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
            # NOVÝ SYSTÉM: Načti pre-computed data
            self.stats_data = dashboard_db.get_stats_data(
                self.app.profile_path,
                self.transaction_type
            )
            
            if not self.stats_data:
                self.tree.insert("", "end", text="Žádné kategorie", values=("—", "—", "—", "—", "—", "—"), tags=('gray',))
                self._update_footer(0, 0, 0)
                return
            
            # Vypočítej hodnoty pro všechny kategorie (LEAF i CUSTOM)
            # a připrav data pro zobrazení
            display_data = {}
            for cat_id, cat_info in self.stats_data.items():
                # Spočítej hodnoty rekurzivně (CUSTOM nebo LEAF)
                values = dashboard_db.calculate_custom_values(self.stats_data, cat_id)
                
                display_data[cat_id] = {
                    'id': cat_id,
                    'nazev': cat_info['nazev'],
                    'parent_id': cat_info['parent_id'],
                    'is_custom': cat_info['is_custom'],
                    'children': cat_info['children'],
                    'sum_past': values['sum_past'],
                    'sum_current': values['sum_current'],
                    'budget_plan': values['budget_plan']
                }
            
            # Filtruj jen kategorie s rozpočtem (použij ABS pro výdaje se záporným rozpočtem)
            filtered_data = {
                cat_id: data for cat_id, data in display_data.items()
                if abs(data['budget_plan']) > 0
            }
            
            if not filtered_data:
                self.tree.insert("", "end", text="Žádný rozpočet nastaven", values=("—", "—", "—", "—", "—", "—"), tags=('gray',))
                self._update_footer(0, 0, 0)
                return
            
            # Zobrazí data v hierarchické struktuře
            self._display_hierarchy(filtered_data, parent_item="")
            
            # Aktualizuj footer s celkovými hodnotami (jen top-level kategorie, použij YTD do měsíce)
            total_budget = sum(abs(data['budget_plan']) for data in filtered_data.values() 
                             if data['parent_id'] is None)
            
            # Spočítej YTD pro top-level kategorie
            total_ytd = 0.0
            for cat_id, data in filtered_data.items():
                if data['parent_id'] is None:
                    ytd = dashboard_db.get_ytd_for_category(
                        self.app.profile_path, cat_id, self.month, data=self.stats_data
                    )
                    total_ytd += ytd
            
            total_percentage = (total_ytd / total_budget * 100) if total_budget > 0 else 0
            self._update_footer(total_budget, total_ytd, total_percentage)
        
        except Exception as e:
            print(f"Chyba při načítání dat: {e}")
            import traceback
            traceback.print_exc()
            self.tree.insert("", "end", text="Chyba při načítání", values=(str(e), "—", "—", "—", "—", "—"), tags=('gray',))
            self._update_footer(0, 0, 0)
    
    def _display_hierarchy(self, data: dict, parent_item: str, parent_cat_id=None):
        """
        Rekurzivně zobrazí hierarchii kategorií v Treeview.
        
        NOVÝ SYSTÉM: Používá pre-computed data z get_stats_data().
        
        Args:
            data: Dict z _load_data() - {cat_id: {'nazev', 'parent_id', 'children', 'sum_past', 'sum_current', 'budget_plan'}}
            parent_item: ID rodiče v Treeview (prázdný string pro top-level)
            parent_cat_id: ID rodičovské kategorie (None pro top-level)
        """
        # Najdi kategorie na aktuální úrovni
        categories = [
            cat_id for cat_id, info in data.items()
            if info['parent_id'] == parent_cat_id
        ]
        
        # Seřaď podle názvu
        categories.sort(key=lambda cid: data[cid]['nazev'])
        
        for cat_id in categories:
            cat_info = data[cat_id]
            
            # Název kategorie
            category_name = cat_info['nazev']
            
            # Hodnoty z pre-computed metrik (použij ABS pro výdaje)
            historicky = abs(cat_info['sum_past'])
            budget = abs(cat_info['budget_plan'])
            
            # Načti měsíční data pro Min.transakce (is_current=0) a Akt.transakce (is_current=1)
            historical_month = dashboard_db.get_month_data_for_category(
                self.app.profile_path, cat_id, self.month, is_current=False, data=self.stats_data
            )
            current_month = dashboard_db.get_month_data_for_category(
                self.app.profile_path, cat_id, self.month, is_current=True, data=self.stats_data
            )
            
            # Načti YTD (Year-To-Date) = součet od ledna do aktuálního měsíce
            ytd = dashboard_db.get_ytd_for_category(
                self.app.profile_path, cat_id, self.month, data=self.stats_data
            )
            
            # Formátování částek (s 2 desetinnými místy)
            historical_text = format_money(historical_month) if historical_month > 0 else "—"
            current_text = format_money(current_month) if current_month > 0 else "—"
            budget_text = format_money(budget)
            ytd_text = format_money(ytd) if ytd > 0 else "—"
            
            # Výpočet %(M→M) - month-to-month comparison
            if historical_month > 0:
                mm_percentage = (current_month / historical_month) * 100
                mm_text = f"{mm_percentage:.1f}%"
                mm_color = self._get_mm_color_tag(mm_percentage)
            else:
                mm_text = "—"
                mm_color = 'gray'
            
            # Výpočet %(R) - YTD plnění ročního rozpočtu
            if budget > 0:
                r_percentage = (ytd / budget) * 100
                r_text = f"{r_percentage:.1f}%"
                r_color = self._get_r_color_tag(r_percentage)
            else:
                r_text = "—"
                r_color = 'gray'
            
            # Určení hlavní barvy řádku
            row_color = r_color if r_color != 'gray' else mm_color
            
            # Vložení řádku do Treeview
            item_id = self.tree.insert(
                parent_item, 
                "end",
                text=category_name,
                values=(historical_text, current_text, mm_text, budget_text, ytd_text, r_text),
                tags=(row_color,),
                open=True  # Rozbal custom kategorie automaticky
            )
            
            # Rekurzivně zobraz děti (pokud existují a jsou ve filtered data)
            if cat_info['children']:
                # Zobraz jen děti které prošly filtrem (mají rozpočet)
                filtered_children = [child_id for child_id in cat_info['children'] if child_id in data]
                if filtered_children:
                    self._display_hierarchy(data, item_id, cat_id)

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
        
        # Formátování textu (s 2 desetinnými místy)
        text = f"Celkem: {format_money(total_ytd)} / {format_money(total_budget)} ({total_percentage:.1f}%)"
        
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
