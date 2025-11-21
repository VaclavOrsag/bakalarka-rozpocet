import tkinter as tk
from tkinter import ttk
from datetime import datetime
from ..stats_window import StatsWindow


class DashboardTab:
    def __init__(self, tab_frame, app_controller):
        self.tab_frame = tab_frame
        self.app = app_controller
        
        # Aktuální zobrazovaný rok
        self.current_year = datetime.now().year
        
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
                  text="📊 Dashboard - Přehled výdajů", 
                  font=("Arial", 18, "bold")).pack()
        
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
        pass
    
    def _open_month_detail(self, month: int):
        StatsWindow(self.tab_frame, self.app, month)