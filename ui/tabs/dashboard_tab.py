import tkinter as tk
from tkinter import ttk
from ..stats_window import StatsWindow
from app.database import dashboard_db, budgets_db


class DashboardTab:
    def __init__(self, tab_frame, app_controller):
        self.tab_frame = tab_frame
        self.app = app_controller
        
        # Aktuální zobrazovaný typ
        self.current_type = "výdej"  # Výchozí typ
        
        # Reference na UI komponenty
        self.monthly_buttons = {}
        self.months_frame = None  # Reference na frame s měsíčními tlačítky
        self.locked_frame = None  # Reference na frame se zamčeným stavem
        
        self._create_dashboard_layout()
        self._refresh_dashboard()
    
    def _create_dashboard_layout(self):
        """Vytvoří kompletní layout dashboardu s měsíčními tlačítky."""
        # Hlavní nadpis
        title_frame = ttk.Frame(self.tab_frame)
        title_frame.pack(fill=tk.X, padx=20, pady=(20, 10))
        
        ttk.Label(title_frame, 
                  text="📊 Dashboard - Přehled", 
                  font=("Arial", 18, "bold")).pack()
        
        # Přepínač typu transakce
        switch_frame = ttk.Frame(self.tab_frame)
        switch_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        ttk.Label(switch_frame, text="Zobrazit:", font=("Arial", 11)).pack(side="left")
        
        self.type_var = tk.StringVar(value="výdej")
        
        ttk.Radiobutton(switch_frame, text="Výdaje", 
                       variable=self.type_var, value="výdej",
                       command=self._on_type_change).pack(side="left", padx=(10, 5))
        
        ttk.Radiobutton(switch_frame, text="Příjmy", 
                       variable=self.type_var, value="příjem",
                       command=self._on_type_change).pack(side="left", padx=(5, 0))
        
        # Container pro obsah (bude obsahovat buď měsíční tlačítka nebo locked screen)
        self.content_container = ttk.Frame(self.tab_frame)
        self.content_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Vytvoř oba stavy (budou se přepínat)
        self._create_months_view()
        self._create_locked_view()

    def _create_months_view(self):
        """Vytvoří view s měsíčními tlačítky."""
        # Mřížka měsíčních tlačítek (4x3)
        self.months_frame = ttk.Frame(self.content_container)
        
        month_names = ["Leden", "Únor", "Březen", "Duben", "Květen", "Červen",
                       "Červenec", "Srpen", "Září", "Říjen", "Listopad", "Prosinec"]
        
        for i, month_name in enumerate(month_names):
            row = i // 4
            col = i % 4
            
            # Frame pro každé měsíční tlačítko
            month_frame = ttk.Frame(self.months_frame)
            month_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            
            # Konfigurace grid pro rovnoměrné roztažení
            self.months_frame.grid_rowconfigure(row, weight=1)
            self.months_frame.grid_columnconfigure(col, weight=1)
            
            # Tlačítko měsíce
            month_button = tk.Button(month_frame,
                                     text=f"{month_name}\n\nNačítání...",
                                     font=("Arial", 11, "bold"),
                                     width=15,
                                     height=6,
                                     relief="raised",
                                     command=lambda m=i+1: self._open_month_detail(m))
            month_button.pack(fill=tk.BOTH, expand=True)
            
            self.monthly_buttons[i + 1] = month_button
    
    def _create_locked_view(self):
        """Vytvoří view pro zamčený stav (když nejsou kompletní rozpočty)."""
        self.locked_frame = ttk.Frame(self.content_container)
        
        # Centrální box se zprávou
        center_frame = ttk.Frame(self.locked_frame)
        center_frame.pack(expand=True)
        
        # Ikona a nadpis
        ttk.Label(center_frame, 
                  text="🔒 DASHBOARD ZAMČEN", 
                  font=("Arial", 20, "bold"),
                  foreground="#d32f2f").pack(pady=(0, 20))
        
        # Zpráva
        ttk.Label(center_frame,
                  text="Pro zobrazení dashboardu musíte nastavit\nrozpočet pro VŠECHNY kategorie.",
                  font=("Arial", 12),
                  justify="center").pack(pady=(0, 20))
        
        # Frame pro seznam chybějících kategorií (bude aktualizován)
        self.missing_categories_frame = ttk.Frame(center_frame)
        self.missing_categories_frame.pack(pady=(0, 20))
        
        # Tlačítko pro přechod na záložku rozpočet
        ttk.Button(center_frame,
                   text="Otevřít záložku Rozpočet",
                   command=self._open_budget_tab).pack()

    def _open_budget_tab(self):
        """Přepne na záložku Rozpočet."""
        # Najdi index záložky Rozpočet a aktivuj ji
        # Předpokládám, že app má referenci na notebook
        if hasattr(self.app, 'notebook'):
            # Záložky jsou obvykle: Domů, Zdroje, Osnova, Rozpočet, Dashboard, Analýza
            # Index záložky Rozpočet by měl být 3 (počítáno od 0)
            self.app.notebook.select(3)

    def _show_months_view(self):
        """Zobrazí view s měsíčními tlačítky."""
        if self.locked_frame:
            self.locked_frame.pack_forget()
        if self.months_frame:
            self.months_frame.pack(fill=tk.BOTH, expand=True)
    
    def _show_locked_view(self, missing_categories: list):
        """Zobrazí locked view s informací o chybějících kategoriích."""
        if self.months_frame:
            self.months_frame.pack_forget()
        
        # Aktualizuj seznam chybějících kategorií
        for widget in self.missing_categories_frame.winfo_children():
            widget.destroy()
        
        ttk.Label(self.missing_categories_frame,
                  text="Kategorie bez rozpočtu:",
                  font=("Arial", 11, "bold")).pack(anchor="w")
        
        for cat_name in missing_categories[:10]:  # Zobraz max 10
            ttk.Label(self.missing_categories_frame,
                      text=f"  ❌ {cat_name}",
                      font=("Arial", 10),
                      foreground="#d32f2f").pack(anchor="w")
        
        if len(missing_categories) > 10:
            ttk.Label(self.missing_categories_frame,
                      text=f"  ... a {len(missing_categories) - 10} dalších",
                      font=("Arial", 10, "italic"),
                      foreground="#666").pack(anchor="w")
        
        if self.locked_frame:
            self.locked_frame.pack(fill=tk.BOTH, expand=True)

    def _refresh_dashboard(self):
        """Aktualizuje dashboard - buď zobrazí měsíční tlačítka nebo locked stav."""
        
        try:
            # Zkontroluj kompletnost rozpočtu pro aktuální typ
            completeness = budgets_db.check_budget_completeness(
                self.app.profile_path,
                self.current_type
            )
            
            if not completeness['is_complete']:
                # Rozpočet není kompletní → zobraz locked stav
                self._show_locked_view(completeness['missing_categories'])
                return
            
            # Rozpočet je kompletní → zobraz měsíční tlačítka
            self._show_months_view()
            self._update_month_buttons()
        
        except Exception as e:
            print(f"Chyba při načítání dashboard dat: {e}")
            import traceback
            traceback.print_exc()
    
    def _update_month_buttons(self):
        """Aktualizuje měsíční tlačítka s daty."""
        month_names = ["Leden", "Únor", "Březen", "Duben", "Květen", "Červen",
                       "Červenec", "Srpen", "Září", "Říjen", "Listopad", "Prosinec"]
        
        try:
            # Pro každý měsíc získej celkové rozpočtové údaje
            for month in range(1, 13):
                btn = self.monthly_buttons.get(month)
                if not btn:
                    continue
                
                # Načti celkový rozpočet pro tento měsíc
                budget_summary = dashboard_db.get_month_total_budget_summary(
                    self.app.profile_path,
                    self.current_type,
                    month
                )
                
                if not budget_summary:
                    # Žádný rozpočet nastaven
                    type_name = "Výdaje" if self.current_type == "výdej" else "Příjmy"
                    btn.config(
                        text=f"{month_names[month-1]}\n\n—\n({type_name})",
                        bg="#e0e0e0",  # Šedá
                        activebackground="#e0e0e0"
                    )
                    continue
                
                ytd_percentage = budget_summary['ytd_percentage']
                expected_percentage = (month / 12) * 100
                
                # Určení barvy podle proporcionálního porovnání
                # Zelená: ytd_percentage <= expected_percentage
                # Žlutá: ytd_percentage <= expected_percentage + 5%
                # Červená: ytd_percentage > expected_percentage + 5%
                if ytd_percentage <= expected_percentage:
                    color = "#c8e6c9"  # Zelená
                elif ytd_percentage <= expected_percentage + 5:
                    color = "#fff9c4"  # Žlutá
                else:
                    color = "#ffcdd2"  # Červená
                
                btn.config(bg=color, activebackground=color)
                
                # Text tlačítka: YTD a očekávané procento
                type_name = "Výdaje" if self.current_type == "výdej" else "Příjmy"
                btn.config(
                    text=f"{month_names[month-1]}\n\nYTD: {ytd_percentage:.1f}%\nLimit: {expected_percentage:.1f}%\n({type_name})"
                )
        
        except Exception as e:
            print(f"Chyba při načítání dashboard dat: {e}")
            import traceback
            traceback.print_exc()
            
            # Fallback: zobraz placeholder
            for month in range(1, 13):
                btn = self.monthly_buttons.get(month)
                if btn:
                    type_name = "Výdaje" if self.current_type == "výdej" else "Příjmy"
                    btn.config(text=f"{month_names[month-1]}\n\n— Kč\n({type_name})", 
                             bg="SystemButtonFace")
    
    def invalidate_cache(self):
        """
        Obnoví dashboard.
        Volá se když uživatel přidá/upraví/smaže transakci.
        """
        self._refresh_dashboard()
    
    def _on_type_change(self):
        """Callback při změně typu - aktualizuje tlačítka."""
        self.current_type = self.type_var.get()
        self._refresh_dashboard()

    def _open_month_detail(self, month: int):
        """Otevře okno s detailem měsíce pro aktuální typ."""
        StatsWindow(self.tab_frame, self.app, month, self.current_type)