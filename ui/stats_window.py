import tkinter as tk
from tkinter import ttk
from app.database import dashboard_db

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
        self.window.geometry("650x500")
        
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

        # Definice sloupců
        columns = ("Kategorie", "Minulé období", "Plnění")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=18)
        
        # Nastavení hlaviček a šířek sloupců
        for col in columns:
            self.tree.heading(col, text=col)
        
        self.tree.column("Kategorie", width=260, anchor="w")
        self.tree.column("Minulé období", width=140, anchor="e")
        self.tree.column("Plnění", width=140, anchor="e")

        # Scrollbar
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        # Footer s tlačítkem Zavřít
        footer = ttk.Frame(self.window, padding=(12, 0, 12, 12))
        footer.pack(fill="x")
        
        ttk.Button(footer, text="Zavřít", command=self.window.destroy).pack(side="right")

    def _load_data(self):
        """Načte data z databáze a zobrazí v tabulce."""
        
        # Vyčistí existující data
        self.tree.delete(*self.tree.get_children())
        
        try:
            # Načte data z databáze
            data = dashboard_db.get_month_category_comparison(
                self.app.profile_path, 
                self.month, 
                self.transaction_type
            )
            
            if not data:
                self.tree.insert("", "end", values=("Žádná data k zobrazení", "—", "—"))
                return
            
            # Zobrazí data v tabulce
            for row in data:
                historical_text = f"{row['historical']:,.0f} Kč" if row['historical'] > 0 else "—"
                current_text = f"{row['current']:,.0f} Kč" if row['current'] > 0 else "—"
                
                self.tree.insert("", "end", values=(
                    row['kategorie'],
                    historical_text,
                    current_text
                ))
        
        except Exception as e:
            print(f"Chyba při načítání dat: {e}")
            self.tree.insert("", "end", values=("Chyba při načítání", str(e), "—"))
