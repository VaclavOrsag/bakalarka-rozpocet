import tkinter as tk
from tkinter import ttk  # Nový import pro Treeview
import tkinter.messagebox as messagebox
from tkinter import filedialog
import database as db
import file_exporter
import file_importer
import os

class App:
    def __init__(self, root, profile_path):
        self.root = root
        self.profile_path = profile_path
        self.root.title(f"Nástroj pro tvorbu rozpočtu - {os.path.basename(profile_path)}")
        self.root.geometry("1280x800")  # Zvětšíme okno pro více sloupců

        # --- Menu (zůstává stejné) ---
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Soubor", menu=file_menu)
        file_menu.add_command(label="Exportovat do CSV...", command=self.export_csv)
        file_menu.add_command(label="Importovat z Excelu...", command=self.import_excel)
        file_menu.add_separator()
        file_menu.add_command(label="Konec", command=self.root.quit)

        # --- KROK 1: Vytvoření Notebooku (záložek) ---
        notebook = ttk.Notebook(self.root)
        notebook.pack(expand=True, fill='both', padx=10, pady=10)

        # --- KROK 2: Vytvoření rámů pro jednotlivé záložky ---
        self.tab_home = ttk.Frame(notebook)
        self.tab_sources = ttk.Frame(notebook)
        self.tab_budget = ttk.Frame(notebook)
        self.tab_analysis = ttk.Frame(notebook)
        notebook.add(self.tab_home, text='Home')
        notebook.add(self.tab_sources, text='Zdroje')
        notebook.add(self.tab_budget, text='Rozpočet')
        notebook.add(self.tab_analysis, text='Analýza')
        
        # --- KROK 3: Naplnění záložek obsahem ---
        self.create_sources_tab() # Vytvoříme obsah pro záložku "Zdroje"
        
        # Ostatní záložky zatím necháme prázdné s uvítacím textem
        ttk.Label(self.tab_home, text="Vítejte! Zde bude váš hlavní přehled.", font=("Arial", 16)).pack(pady=50)
        ttk.Label(self.tab_budget, text="Tato sekce je ve vývoji.\nZde budete vytvářet a spravovat rozpočty.", justify=tk.CENTER).pack(pady=50)
        ttk.Label(self.tab_analysis, text="Tato sekce je ve vývoji.\nZde budou grafy a analýzy plnění rozpočtu.", justify=tk.CENTER).pack(pady=50)
        
    def create_sources_tab(self):
        """Vytvoří veškerý obsah pro záložku 'Zdroje'."""
        
        # Definujeme sloupce podle databáze
        self.columns = ('id', 'datum', 'doklad', 'zdroj', 'firma', 'text', 'madati', 'dal', 'castka', 'cin', 'cislo', 'co', 'kdo', 'stredisko')
        
        tree_frame = ttk.Frame(self.tab_sources)
        tree_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Nastavení Treeview
        display_cols = [col for col in self.columns if col != 'id']
        self.tree = ttk.Treeview(tree_frame, columns=self.columns, displaycolumns=display_cols, show='headings')
        
        # Nastavení hlaviček a šířky sloupců...
        column_widths = {'id': 40, 'datum': 90, 'doklad': 80, 'zdroj': 80, 'firma': 150, 'text': 300, 'madati': 80, 'dal': 80, 'castka': 100, 'cin': 80, 'cislo': 80, 'co': 100, 'kdo': 120, 'stredisko': 120}
        right_aligned_cols = ['madati', 'dal', 'castka']
        for col in self.columns:
            self.tree.heading(col, text=col.capitalize())
            width = column_widths.get(col, 100)
            anchor = 'e' if col in right_aligned_cols else 'w'
            stretch = tk.NO if col == 'id' else tk.YES
            self.tree.column(col, width=width, anchor=anchor, stretch=stretch)

        self.tree.bind("<Double-1>", self.open_edit_window)

        # Scrollbary
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        vsb.pack(side='right', fill='y')
        hsb.pack(side='bottom', fill='x')
        self.tree.pack(side='left', fill='both', expand=True)
        
        # Ovládací prvky pod tabulkou
        bottom_controls = ttk.Frame(self.tab_sources)
        bottom_controls.pack(fill='x', pady=5)

        self.delete_button = ttk.Button(bottom_controls, text="Smazat vybranou položku", command=self.delete_item)
        self.delete_button.pack(side='left')
        
        self.total_label = ttk.Label(bottom_controls, text="Celkem: 0.00 Kč", font=("Arial", 14, "bold"))
        self.total_label.pack(side='right')

        # Načtení dat po vytvoření widgetů
        self.load_items()
        self.update_total()

    def _center_window(self, win):
        # ... (metoda zůstává stejná)
        win.update_idletasks()
        root_x, root_y, root_w, root_h = self.root.winfo_x(), self.root.winfo_y(), self.root.winfo_width(), self.root.winfo_height()
        win_w, win_h = win.winfo_width(), win.winfo_height()
        x = root_x + (root_w - win_w) // 2
        y = root_y + (root_h - win_h) // 2
        win.geometry(f"+{x}+{y}")

    def load_items(self):
        # Vyčistíme stará data v Treeview
        for i in self.tree.get_children():
            self.tree.delete(i)
            
        self.all_items = db.get_all_items(self.profile_path)
        for item in self.all_items:
            # Převedeme všechny None hodnoty na prázdný řetězec pro zobrazení
            display_values = ["" if v is None else v for v in item]
            self.tree.insert('', tk.END, values=display_values)

    def delete_item(self):
        selected_item_id = self.tree.focus() # Získá ID vybraného řádku
        if not selected_item_id:
            return
            
        if not messagebox.askyesno("Potvrdit smazání", "Opravdu chcete smazat vybranou položku?"):
            return
        
        # Z ID řádku získáme databázové ID (je to první hodnota)
        item_values = self.tree.item(selected_item_id, 'values')
        db_id = item_values[0]
        
        db.delete_item(self.profile_path, db_id)
        self.load_items()
        self.update_total()

    def open_edit_window(self, event):
        selected_item_id = self.tree.focus()
        if not selected_item_id:
            return

        item_values = self.tree.item(selected_item_id, 'values')
        
        edit_win = tk.Toplevel(self.root)
        edit_win.title("Upravit položku")

        entries = {}
        # Vytvoříme formulář pro VŠECHNY sloupce (kromě ID)
        for i, col_name in enumerate(self.columns[1:], 1): # Začínáme od 1, abychom přeskočili ID
            tk.Label(edit_win, text=f"{col_name.capitalize()}:").grid(row=i-1, column=0, padx=10, pady=5, sticky="w")
            entry = tk.Entry(edit_win, width=50)
            entry.grid(row=i-1, column=1, padx=10, pady=5, sticky="ew")
            entry.insert(0, item_values[i])
            entries[col_name] = entry
        
        def save_changes():
            try:
                # Shromáždíme nové hodnoty ze všech polí
                new_values = [entries[col].get() for col in self.columns[1:]]
                db_id = item_values[0]

                db.update_item(self.profile_path, db_id, *new_values)
                
                self.load_items()
                self.update_total()
                edit_win.destroy()
            except Exception as e:
                messagebox.showerror("Chyba", f"Při ukládání nastala chyba: {e}")

        save_button = tk.Button(edit_win, text="Uložit změny", command=save_changes)
        save_button.grid(row=len(self.columns), column=0, columnspan=2, pady=10)
        
        self._center_window(edit_win)

    def update_total(self):
        total = db.get_total_amount(self.profile_path)
        self.total_label.config(text=f"Celkem: {total:.2f} Kč")

    def export_csv(self):
        # ... (metoda zůstává stejná)
        filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV soubory", "*.csv")])
        if filepath:
            if file_exporter.export_to_csv(filepath):
                messagebox.showinfo("Export úspěšný", f"Data byla úspěšně exportována.")
            else:
                messagebox.showerror("Chyba exportu", "Při exportu dat nastala chyba.")

    def import_excel(self):
        # ... (metoda zůstává stejná)
        filepath = filedialog.askopenfilename(filetypes=[("Excel soubory", "*.xlsx *.xlsm")])
        if filepath:
            choice = messagebox.askyesnocancel("Možnosti importu", "Přidat data k existujícím (Ano),\nnebo přepsat všechna data (Ne)?")
            if choice is None: return
            if choice is False: db.delete_all_items(self.profile_path)
            if file_importer.import_from_excel(filepath, self.profile_path):
                self.load_items()
                self.update_total()
                messagebox.showinfo("Import úspěšný", "Data byla úspěšně naimportována.")
            else:
                messagebox.showerror("Chyba importu", "Při importu dat nastala chyba.")