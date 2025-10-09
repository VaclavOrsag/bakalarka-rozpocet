import tkinter as tk

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Nástroj pro tvorbu rozpočtu")
        self.root.geometry("800x600")

        self.items = []

        # --- Formulář pro zadávání dat ---
        self.label_description = tk.Label(self.root, text="Popis:", font=("Arial", 12))
        self.label_description.grid(row=0, column=0, padx=10, pady=5, sticky='w')
        self.entry_description = tk.Entry(self.root, font=("Arial", 12))
        self.entry_description.grid(row=0, column=1, padx=10, pady=5, sticky='we')

        self.label_amount = tk.Label(self.root, text="Částka:", font=("Arial", 12))
        self.label_amount.grid(row=1, column=0, padx=10, pady=5, sticky='w')
        self.entry_amount = tk.Entry(self.root, font=("Arial", 12))
        self.entry_amount.grid(row=1, column=1, padx=10, pady=5, sticky='we')

        self.add_button = tk.Button(self.root, text="Přidat položku", command=self.add_item)
        self.add_button.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky='we')

        # NOVÉ TLAČÍTKO pro mazání
        self.delete_button = tk.Button(self.root, text="Smazat vybranou položku", command=self.delete_item)
        self.delete_button.grid(row=3, column=0, columnspan=2, padx=10, pady=5, sticky='we')

        self.items_listbox = tk.Listbox(self.root, font=("Arial", 12))
        self.items_listbox.grid(row=4, column=0, columnspan=2, padx=10, pady=10, sticky='nsew')

        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(4, weight=1) # Upraven řádek pro Listbox

    def add_item(self):
        description = self.entry_description.get()
        amount = self.entry_amount.get()

        if description and amount:
            item_text = f"{description} - {amount} Kč"
            self.items.append(item_text)
            self.items_listbox.insert(tk.END, item_text)
            self.entry_description.delete(0, tk.END)
            self.entry_amount.delete(0, tk.END)

    # NOVÁ METODA pro mazání
    def delete_item(self):
        # Získáme indexy označených položek (i když budeme pracovat jen s první)
        selected_indices = self.items_listbox.curselection()
        
        # Pokud není nic označeno, nic neděláme
        if not selected_indices:
            return
        
        # Vezmeme první označený index
        index = selected_indices[0]
        
        # Smažeme položku z viditelného Listboxu
        self.items_listbox.delete(index)
        
        # Smažeme položku i z našeho interního seznamu
        self.items.pop(index)