import tkinter as tk
import tkinter.messagebox as messagebox
from tkinter import filedialog
import database as db
import file_exporter
import file_importer

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Nástroj pro tvorbu rozpočtu")
        self.root.geometry("1024x768") # Zvětšíme okno

        # --- Menu ---
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Soubor", menu=file_menu)
        file_menu.add_command(label="Exportovat do CSV...", command=self.export_csv)
        file_menu.add_command(label="Importovat z Excelu...", command=self.import_excel)
        file_menu.add_separator()
        file_menu.add_command(label="Konec", command=self.root.quit)

        # --- Hlavní rám pro seznam a součet ---
        main_frame = tk.Frame(self.root, padx=10, pady=10)
        main_frame.grid(row=0, column=0, sticky='nsew')
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        
        # --- Seznam v hlavním rámu ---
        list_frame = tk.Frame(main_frame)
        list_frame.grid(row=0, column=0, sticky='nsew')
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)

        # Použijeme font s pevnou šířkou pro zarovnání sloupců
        list_font = ("Courier", 10)
        self.items_listbox = tk.Listbox(list_frame, font=list_font)
        self.items_listbox.bind("<Double-1>", self.open_edit_window)

        self.scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=self.items_listbox.yview)
        self.items_listbox.config(yscrollcommand=self.scrollbar.set)
        
        self.scrollbar.pack(side="right", fill="y")
        self.items_listbox.pack(side="left", fill="both", expand=True)

        self.delete_button = tk.Button(main_frame, text="Smazat vybranou položku", command=self.delete_item)
        self.delete_button.grid(row=1, column=0, padx=5, pady=10, sticky='w')

        self.total_label = tk.Label(main_frame, text="Celkem: 0.00 Kč", font=("Arial", 14, "bold"))
        self.total_label.grid(row=1, column=0, padx=5, pady=10, sticky='e')

        # Načtení dat
        db.init_db()
        self.load_items()
        self.update_total()

    def _center_window(self, win):
        # ... (tato metoda zůstává stejná)
        win.update_idletasks()
        root_x, root_y = self.root.winfo_x(), self.root.winfo_y()
        root_w, root_h = self.root.winfo_width(), self.root.winfo_height()
        win_w, win_h = win.winfo_width(), win.winfo_height()
        x = root_x + (root_w - win_w) // 2
        y = root_y + (root_h - win_h) // 2
        win.geometry(f"+{x}+{y}")

    def load_items(self):
        self.items_listbox.delete(0, tk.END)
        self.all_items = db.get_all_items()

        # Hlavička pro seznam
        header = f"{'Datum':<12}{'Text':<50}{'Částka':>15}"
        self.items_listbox.insert(tk.END, header)
        self.items_listbox.insert(tk.END, "-"*80)

        for item in self.all_items:
            # item[1] = datum, item[5] = text, item[8] = castka
            datum_str = str(item[1]).split(" ")[0] # Zobrazíme jen datum bez času
            list_item_text = f"{datum_str:<12}{str(item[5]):<50}{float(item[8]):>15.2f} Kč"
            self.items_listbox.insert(tk.END, list_item_text)

    def delete_item(self):
        selected_indices = self.items_listbox.curselection()
        if not selected_indices: return
        
        # Odečteme 2 kvůli hlavičce a oddělovači
        index = selected_indices[0] - 2
        if index < 0: return # Nemažeme hlavičku

        if not messagebox.askyesno("Potvrdit smazání", "Opravdu chcete smazat vybranou položku?"):
            return
        
        item_to_delete = self.all_items[index]
        item_id = item_to_delete[0]
        db.delete_item(item_id)
        self.load_items()
        self.update_total()

    def open_edit_window(self, event):
        selected_indices = self.items_listbox.curselection()
        if not selected_indices: return
        
        index = selected_indices[0] - 2
        if index < 0: return # Needitujeme hlavičku

        selected_item = self.all_items[index]
        
        # Editační okno pro teď necháme velmi jednoduché, zaměřené na klíčové položky
        edit_win = tk.Toplevel(self.root)
        edit_win.title("Upravit položku")

        tk.Label(edit_win, text="Text:", font=("Arial", 12)).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        edit_text_entry = tk.Entry(edit_win, font=("Arial", 12), width=50)
        edit_text_entry.grid(row=0, column=1, padx=10, pady=5)
        edit_text_entry.insert(0, selected_item[5]) # text

        tk.Label(edit_win, text="Částka:", font=("Arial", 12)).grid(row=1, column=0, padx=10, pady=5, sticky="w")
        edit_amount_entry = tk.Entry(edit_win, font=("Arial", 12), width=50)
        edit_amount_entry.grid(row=1, column=1, padx=10, pady=5)
        edit_amount_entry.insert(0, selected_item[8]) # castka

        def save_changes():
            try:
                # Získáme staré hodnoty a přepíšeme jen ty změněné
                updated_item = list(selected_item)
                updated_item[5] = edit_text_entry.get()
                updated_item[8] = float(edit_amount_entry.get())
                
                # Voláme update se všemi parametry (id je první, proto updated_item[1:])
                db.update_item(updated_item[0], *updated_item[1:])
                
                self.load_items()
                self.update_total()
                edit_win.destroy()
            except ValueError:
                messagebox.showerror("Chyba", "Částka musí být platné číslo.")
        
        save_button = tk.Button(edit_win, text="Uložit změny", command=save_changes)
        save_button.grid(row=2, column=0, columnspan=2, pady=10)
        self._center_window(edit_win)

    def update_total(self):
        total = db.get_total_amount()
        self.total_label.config(text=f"Celkem: {total:.2f} Kč")
    
    def export_csv(self):
        # ... (tato metoda zůstává stejná)
        filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV soubory", "*.csv")])
        if filepath:
            if file_exporter.export_to_csv(filepath):
                messagebox.showinfo("Export úspěšný", f"Data byla úspěšně exportována do souboru:\n{filepath}")
            else:
                messagebox.showerror("Chyba exportu", "Při exportu dat nastala chyba.")
    
    def import_excel(self):
        # ... (tato metoda zůstává stejná)
        filepath = filedialog.askopenfilename(filetypes=[("Excel soubory", "*.xlsx *.xlsm")])
        if filepath:
            choice = messagebox.askyesnocancel("Možnosti importu", "Chcete nová data PŘIDAT k existujícím (Ano),\nnebo chcete PŘEPSAT všechna stávající data (Ne)?")
            if choice is None: return
            if choice is False: db.delete_all_items()
            if file_importer.import_from_excel(filepath):
                self.load_items()
                self.update_total()
                messagebox.showinfo("Import úspěšný", "Data byla úspěšně naimportována.")
            else:
                messagebox.showerror("Chyba importu", "Při importu dat nastala chyba.")