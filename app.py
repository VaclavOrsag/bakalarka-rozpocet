import tkinter as tk
import database as db  # Importujeme náš nový soubor

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Nástroj pro tvorbu rozpočtu")
        self.root.geometry("800x600")

        # Inicializujeme databázi hned na startu
        db.init_db()

        # --- Formulář pro zadávání dat ---
        # (zůstává stejný)
        self.label_description = tk.Label(self.root, text="Popis:", font=("Arial", 12))
        self.label_description.grid(row=0, column=0, padx=10, pady=5, sticky='w')
        self.entry_description = tk.Entry(self.root, font=("Arial", 12))
        self.entry_description.grid(row=0, column=1, padx=10, pady=5, sticky='we')

        self.label_amount = tk.Label(self.root, text="Částka:", font=("Arial", 12))
        self.label_amount.grid(row=1, column=0, padx=10, pady=5, sticky='w')
        # U pole pro částku nastavíme validaci
        vcmd = (self.root.register(self.validate_amount), '%P')
        self.entry_amount = tk.Entry(self.root, font=("Arial", 12),
                                     validate="key", validatecommand=vcmd)
        self.entry_amount.grid(row=1, column=1, padx=10, pady=5, sticky='we')

        self.add_button = tk.Button(self.root, text="Přidat položku", command=self.add_item)
        self.add_button.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky='we')

        self.delete_button = tk.Button(self.root, text="Smazat vybranou položku", command=self.delete_item)
        self.delete_button.grid(row=3, column=0, columnspan=2, padx=10, pady=5, sticky='we')

        self.items_listbox = tk.Listbox(self.root, font=("Arial", 12))
        self.items_listbox.grid(row=4, column=0, columnspan=2, padx=10, pady=10, sticky='nsew')
        
        # NOVÝ popisek pro zobrazení součtu
        self.total_label = tk.Label(self.root, text="Celkem: 0.00 Kč", font=("Arial", 14, "bold"))
        self.total_label.grid(row=5, column=0, columnspan=2, padx=10, pady=10, sticky='e')

        self.load_items()
        self.update_total() # Zavoláme aktualizaci součtu při startu

        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(4, weight=1)


    # NOVÁ METODA pro validaci
    def validate_amount(self, P):
        """Povolí změnu, jen pokud je nový text prázdný nebo platné číslo."""
        if P == "" or P == "-":
            return True
        try:
            float(P)
            return True
        except ValueError:
            return False
        
    def load_items(self):
        """Načte všechny položky z databáze a zobrazí je v Listboxu."""
        self.items_listbox.delete(0, tk.END)  # Vyčistíme listbox
        self.all_items = db.get_all_items() # Uložíme si aktuální data pro mazání
        for item in self.all_items:
            # item je teď (id, description, amount)
            self.items_listbox.insert(tk.END, f"{item[1]} - {item[2]} Kč")

    def add_item(self):
        description = self.entry_description.get()
        amount = self.entry_amount.get()

        if description and amount:
            # Převádíme částku na float před uložením
            db.add_item(description, float(amount))
            self.load_items()
            self.update_total() # Aktualizujeme součet
            self.entry_description.delete(0, tk.END)
            self.entry_amount.delete(0, tk.END)

    def delete_item(self):
        selected_indices = self.items_listbox.curselection()
        if not selected_indices:
            return
        
        index = selected_indices[0]
        # Z našeho seznamu všech položek získáme ID té, kterou chceme smazat
        item_to_delete = self.all_items[index]
        item_id = item_to_delete[0]

        db.delete_item(item_id) # Smažeme z DB
        self.load_items() # Znovu načteme a zobrazíme data
        self.update_total() # Aktualizujeme součet

    def update_total(self):
        """Získá celkovou sumu z DB a aktualizuje popisek."""
        total = db.get_total_amount()
        self.total_label.config(text=f"Celkem: {total:.2f} Kč")