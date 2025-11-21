import tkinter as tk
from tkinter import ttk


class StatsWindow:
    def __init__(self, parent, app, month: int):
        self.parent = parent
        self.app = app
        self.month = month
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
        return f"Detail měsíce – {month_names[self.month-1]}"

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
        """Načte data do tabulky. Zatím jen placeholder."""
        # Vyčistí existující data
        self.tree.delete(*self.tree.get_children())
        
        # TODO: Zde bude logika pro načtení dat z databáze
        # Prozatím jen placeholder data
        placeholder_data = [
            ("Žádná data k zobrazení", "—", "—"),
        ]
        
        for row in placeholder_data:
            self.tree.insert("", "end", values=row)
            