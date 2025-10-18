import tkinter as tk
import tkinter.messagebox as messagebox
import database as db

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Nástroj pro tvorbu rozpočtu")
        self.root.geometry("800x600")

        # --- Vytvoření horního menu ---
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Vytvoříme hlavní položku "Soubor"
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Soubor", menu=file_menu)

        # Přidáme do "Soubor" podpoložku "Konec", která zavře aplikaci
        file_menu.add_command(label="Konec", command=self.root.quit)

        # --- Vytvoření a rozmístění hlavních rámů ---
        # Horní rám pro formulář
        top_frame = tk.Frame(self.root, padx=10, pady=10, bg="lightblue")
        top_frame.grid(row=0, column=0, sticky='ew')

        # Dolní rám pro seznam a součet
        bottom_frame = tk.Frame(self.root, padx=10, pady=10, bg="lightgrey")
        bottom_frame.grid(row=1, column=0, sticky='nsew')

        # Konfigurace mřížky hlavního okna
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)

        # --- Formulář v horním rámu (top_frame) ---
        self.label_description = tk.Label(top_frame, text="Popis:", font=("Arial", 12))
        self.label_description.grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.entry_description = tk.Entry(top_frame, font=("Arial", 12))
        self.entry_description.grid(row=0, column=1, padx=5, pady=5, sticky='we')

        self.label_amount = tk.Label(top_frame, text="Částka:", font=("Arial", 12))
        self.label_amount.grid(row=1, column=0, padx=5, pady=5, sticky='w')
        vcmd = (self.root.register(self.validate_amount), '%P')
        self.entry_amount = tk.Entry(top_frame, font=("Arial", 12), validate="key", validatecommand=vcmd)
        self.entry_amount.grid(row=1, column=1, padx=5, pady=5, sticky='we')

        self.add_button = tk.Button(top_frame, text="Přidat položku", command=self.add_item)
        self.add_button.grid(row=2, column=0, columnspan=2, padx=5, pady=10, sticky='we')
        self.delete_button = tk.Button(top_frame, text="Smazat vybranou položku", command=self.delete_item)
        self.delete_button.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky='we')
        
        # Konfigurace sloupce v horním rámu
        top_frame.grid_columnconfigure(1, weight=1)

        # --- Seznam v dolním rámu (bottom_frame) ---
        # Rám pro Listbox a Scrollbar
        list_frame = tk.Frame(bottom_frame)
        list_frame.grid(row=0, column=0, sticky='nsew')

        self.items_listbox = tk.Listbox(list_frame, font=("Arial", 12))
        # NOVÁ ŘÁDKA: Navázání události dvojkliku na novou metodu
        self.items_listbox.bind("<Double-1>", self.open_edit_window)
        self.scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=self.items_listbox.yview)
        self.items_listbox.config(yscrollcommand=self.scrollbar.set)
        
        self.scrollbar.pack(side="right", fill="y")
        self.items_listbox.pack(side="left", fill="both", expand=True)

        self.total_label = tk.Label(bottom_frame, text="Celkem: 0.00 Kč", font=("Arial", 14, "bold"))
        self.total_label.grid(row=1, column=0, padx=5, pady=10, sticky='e')
        
        # Konfigurace mřížky v dolním rámu
        bottom_frame.grid_columnconfigure(0, weight=1)
        bottom_frame.grid_rowconfigure(0, weight=1)

        # Načtení dat
        db.init_db()
        self.load_items()
        self.update_total()

    def validate_amount(self, P):
        if P == "" or P == "-": return True
        try:
            float(P)
            return True
        except ValueError:
            return False

    def load_items(self):
        self.items_listbox.delete(0, tk.END)
        self.all_items = db.get_all_items()
        for item in self.all_items:
            self.items_listbox.insert(tk.END, f"{item[1]} - {item[2]:.2f} Kč")

    def add_item(self):
        description = self.entry_description.get()
        amount = self.entry_amount.get()
        if description and amount:
            db.add_item(description, float(amount))
            self.load_items()
            self.update_total()
            self.entry_description.delete(0, tk.END)
            self.entry_amount.delete(0, tk.END)

    def delete_item(self):
        selected_indices = self.items_listbox.curselection()
        if not selected_indices: 
            return
        is_sure = messagebox.askyesno("Potvrdit smazání", "Opravdu chcete smazat vybranou položku?")
        if not is_sure:
            return
        index = selected_indices[0]
        item_to_delete = self.all_items[index]
        item_id = item_to_delete[0]
        db.delete_item(item_id)
        self.load_items()
        self.update_total()

    def update_total(self):
        total = db.get_total_amount()
        self.total_label.config(text=f"Celkem: {total:.2f} Kč")

    # NOVÁ METODA pro otevření editačního okna
    def open_edit_window(self, event):
        selected_indices = self.items_listbox.curselection()
        if not selected_indices:
            return
        
        index = selected_indices[0]
        selected_item = self.all_items[index]
        item_id, description, amount = selected_item

        # Vytvoření nového "Toplevel" okna
        edit_win = tk.Toplevel(self.root)
        edit_win.title("Upravit položku")

        # Formulář v novém okně (podobný jako v hlavním)
        tk.Label(edit_win, text="Popis:", font=("Arial", 12)).grid(row=0, column=0, padx=10, pady=5)
        edit_description_entry = tk.Entry(edit_win, font=("Arial", 12))
        edit_description_entry.grid(row=0, column=1, padx=10, pady=5)
        edit_description_entry.insert(0, description) # Vložíme stávající popis

        tk.Label(edit_win, text="Částka:", font=("Arial", 12)).grid(row=1, column=0, padx=10, pady=5)
        edit_amount_entry = tk.Entry(edit_win, font=("Arial", 12))
        edit_amount_entry.grid(row=1, column=1, padx=10, pady=5)
        edit_amount_entry.insert(0, amount) # Vložíme stávající částku

        # Funkce pro uložení změn
        def save_changes():
            new_description = edit_description_entry.get()
            new_amount = edit_amount_entry.get()
            if new_description and new_amount:
                try:
                    db.update_item(item_id, new_description, float(new_amount))
                    self.load_items()
                    self.update_total()
                    edit_win.destroy() # Zavřeme editační okno
                except ValueError:
                    messagebox.showerror("Chyba", "Částka musí být platné číslo.")

        # Tlačítko pro uložení
        save_button = tk.Button(edit_win, text="Uložit změny", command=save_changes)
        save_button.grid(row=2, column=0, columnspan=2, pady=10)