import tkinter as tk
from tkinter import ttk
from datetime import datetime
from ..stats_window import StatsWindow


class DashboardTab:
    def __init__(self, tab_frame, app_controller):
        self.tab_frame = tab_frame
        self.app = app_controller
        
        # Aktuální zobrazovaný rok a typ
        self.current_year = datetime.now().year
        self.current_type = "výdej"  # Výchozí typ
        
        # Reference na UI komponenty
        self.monthly_buttons = {}
        
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
        
        # Mřížka měsíčních tlačítek (4x3)
        months_frame = ttk.Frame(self.tab_frame)
        months_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        month_names = ["Leden", "Únor", "Březen", "Duben", "Květen", "Červen",
                       "Červenec", "Srpen", "Září", "Říjen", "Listopad", "Prosinec"]
        
        for i, month_name in enumerate(month_names):
            row = i // 4
            col = i % 4
            
            # Frame pro každé měsíční tlačítko
            month_frame = ttk.Frame(months_frame)
            month_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            
            # Konfigurace grid pro rovnoměrné roztažení
            months_frame.grid_rowconfigure(row, weight=1)
            months_frame.grid_columnconfigure(col, weight=1)
            
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
    
    def _refresh_dashboard(self):
        """Aktualizuje všechna měsíční tlačítka s aktuálními daty."""
        month_names = ["Leden", "Únor", "Březen", "Duben", "Květen", "Červen",
                       "Červenec", "Srpen", "Září", "Říjen", "Listopad", "Prosinec"]
        
        for m in range(1, 13):
            btn = self.monthly_buttons.get(m)
            if btn:
                # Zatím jen placeholder text
                type_name = "Výdaje" if self.current_type == "výdej" else "Příjmy"
                btn.config(text=f"{month_names[m-1]}\n\n— Kč\n({type_name})")
    
    def _on_type_change(self):
        """Callback při změně typu - aktualizuje tlačítka."""
        self.current_type = self.type_var.get()
        self._refresh_dashboard()

    def _open_month_detail(self, month: int):
        """Otevře okno s detailem měsíce pro aktuální typ."""
        StatsWindow(self.tab_frame, self.app, month, self.current_type)