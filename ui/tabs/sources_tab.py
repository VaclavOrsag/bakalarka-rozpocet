import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as messagebox
from app import database as db

class SourcesTab:
    def __init__(self, tab_frame, app_controller):
        """
        Inicializuje obsah záložky 'Zdroje'.
        :param tab_frame: Rám (Frame) záložky, do kterého se má vše vykreslit.
        :param app_controller: Odkaz na hlavní třídu App pro přístup k profilu a dalším metodám.
        """
        self.app = app_controller
        
        self.columns = ('id', 'datum', 'doklad', 'zdroj', 'firma', 'text', 'madati', 'dal', 'castka', 'cin', 'cislo', 'co', 'kdo', 'stredisko')
        
        tree_frame = ttk.Frame(tab_frame)
        tree_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        display_cols = [col for col in self.columns if col != 'id']
        self.tree = ttk.Treeview(tree_frame, columns=self.columns, displaycolumns=display_cols, show='headings')
        
        column_widths = {'id': 40, 'datum': 90, 'doklad': 80, 'zdroj': 80, 'firma': 150, 'text': 300, 'madati': 80, 'dal': 80, 'castka': 100, 'cin': 80, 'cislo': 80, 'co': 100, 'kdo': 120, 'stredisko': 120}
        right_aligned_cols = ['madati', 'dal', 'castka']
        for col in self.columns:
            self.tree.heading(col, text=col.capitalize())
            width = column_widths.get(col, 100)
            anchor = 'e' if col in right_aligned_cols else 'w'
            stretch = tk.NO if col == 'id' else tk.YES
            self.tree.column(col, width=width, anchor=anchor, stretch=stretch)

        self.tree.bind("<Double-1>", self.open_edit_window)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        vsb.pack(side='right', fill='y')
        hsb.pack(side='bottom', fill='x')
        self.tree.pack(side='left', fill='both', expand=True)
        
        bottom_controls = ttk.Frame(tab_frame)
        bottom_controls.pack(fill='x', pady=5)

        self.delete_button = ttk.Button(bottom_controls, text="Smazat vybranou položku", command=self.delete_item)
        self.delete_button.pack(side='left')
        
        self.total_label = ttk.Label(bottom_controls, text="Celkem: 0.00 Kč", font=("Arial", 14, "bold"))
        self.total_label.pack(side='right')

        self.load_items()
        self.update_total()

    def load_items(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        self.all_items = db.get_all_items(self.app.profile_path)
        for item in self.all_items:
            display_values = ["" if v is None else v for v in item]
            self.tree.insert('', tk.END, values=display_values)

    def delete_item(self):
        selected_item_id = self.tree.focus()
        if not selected_item_id: return
        if not messagebox.askyesno("Potvrdit smazání", "Opravdu chcete smazat vybranou položku?"): return
        item_values = self.tree.item(selected_item_id, 'values')
        db_id = item_values[0]
        db.delete_item(self.app.profile_path, db_id)
        self.load_items()
        self.update_total()

    def open_edit_window(self, event):
        selected_item_id = self.tree.focus()
        if not selected_item_id: return
        item_values = self.tree.item(selected_item_id, 'values')
        edit_win = tk.Toplevel(self.app.root) # Rodičem je hlavní okno z 'app'
        edit_win.title("Upravit položku")
        entries = {}
        for i, col_name in enumerate(self.columns[1:], 1):
            ttk.Label(edit_win, text=f"{col_name.capitalize()}:").grid(row=i-1, column=0, padx=10, pady=5, sticky="w")
            entry = ttk.Entry(edit_win, width=50)
            entry.grid(row=i-1, column=1, padx=10, pady=5, sticky="ew")
            entry.insert(0, item_values[i])
            entries[col_name] = entry
        def save_changes():
            try:
                new_values = [entries[col].get() for col in self.columns[1:]]
                db_id = item_values[0]
                db.update_item(self.app.profile_path, db_id, *new_values)
                self.load_items()
                self.update_total()
                edit_win.destroy()
            except Exception as e:
                messagebox.showerror("Chyba", f"Při ukládání nastala chyba: {e}")
        save_button = ttk.Button(edit_win, text="Uložit změny", command=save_changes)
        save_button.grid(row=len(self.columns), column=0, columnspan=2, pady=10)
        self.app._center_window(edit_win) # Voláme centrovací metodu z 'app'

    def update_total(self):
        total = db.get_total_amount(self.app.profile_path)
        self.total_label.config(text=f"Celkem: {total:.2f} Kč")