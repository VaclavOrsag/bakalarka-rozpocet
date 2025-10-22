import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import simpledialog

from app import database as db

class AccountingStructureTab:
    def __init__(self, tab_frame, app_controller):
        """
        Inicializuje obsah záložky 'Účetní Osnova' jako nástroj pro třídění.
        """
        self.app = app_controller
        self.tab_frame = tab_frame

        # --- Hlavní rozdělení na tři panely ---
        main_pane = ttk.PanedWindow(self.tab_frame, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 1. LEVÝ PANEL: Nalezené položky
        left_frame = ttk.LabelFrame(main_pane, text="Nalezené položky z 'Co'")
        main_pane.add(left_frame, weight=2)

        self.unassigned_list = tk.Listbox(left_frame)
        self.unassigned_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 2. STŘEDNÍ PANEL: Ovládací tlačítka
        controls_frame = ttk.Frame(main_pane)
        main_pane.add(controls_frame, weight=1)

        ttk.Button(controls_frame, text="Přidat jako hlavní >>", command=self.add_as_main_category).pack(pady=15, padx=5)
        ttk.Button(controls_frame, text="Přidat jako podkategorii >>", command=self.add_as_subcategory).pack(pady=5, padx=5)
        ttk.Separator(controls_frame, orient='horizontal').pack(fill='x', pady=10)
        ttk.Button(controls_frame, text="Přejmenovat", command=self.rename_category).pack(pady=5, padx=5)
        ttk.Button(controls_frame, text="Smazat", command=self.delete_category).pack(pady=5, padx=5)

        # 3. PRAVÝ PANEL: Moje účetní osnova
        right_frame = ttk.LabelFrame(main_pane, text="Moje účetní osnova")
        main_pane.add(right_frame, weight=3)

        self.tree = ttk.Treeview(right_frame, columns=('id', 'typ'), show='tree headings')
        self.tree.heading('#0', text='Název kategorie')
        self.tree.heading('id', text='ID')
        self.tree.heading('typ', text='Typ')
        self.tree.column('id', width=40, stretch=tk.NO)
        self.tree.column('typ', width=80, stretch=tk.NO)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Načteme data do obou panelů
        self.refresh_data()

    def refresh_data(self):
        """Obnoví data v obou panelech."""
        self.load_unassigned_list()
        self.load_categories_tree()

    def load_unassigned_list(self):
        """Načte nezařazené položky do levého seznamu."""
        self.unassigned_list.delete(0, tk.END)
        unassigned_items = db.get_unassigned_categories(self.app.profile_path)
        for item in unassigned_items:
            self.unassigned_list.insert(tk.END, item)

    def load_categories_tree(self):
        """Načte existující účetní osnovu do pravého stromu."""
        for i in self.tree.get_children():
            self.tree.delete(i)
        
        all_categories = db.get_all_categories(self.app.profile_path)
        category_map = {cat[0]: cat for cat in all_categories}
        tree_items = {}

        for cat_id, cat_data in category_map.items():
            parent_id = cat_data[3]
            if parent_id is None:
                iid = self.tree.insert('', 'end', text=cat_data[1], values=(cat_id, cat_data[2]), open=True)
                tree_items[cat_id] = iid
        
        for cat_id, cat_data in category_map.items():
            parent_id = cat_data[3]
            if parent_id in tree_items:
                parent_iid = tree_items[parent_id]
                iid = self.tree.insert(parent_iid, 'end', text=cat_data[1], values=(cat_id, cat_data[2]), open=True)
                tree_items[cat_id] = iid


    def add_as_main_category(self):
        """
        Vezme vybranou položku, automaticky určí její typ (nebo se zeptá),
        vytvoří novou hlavní kategorii a hromadně přiřadí všechny
        související transakce k této nové kategorii.
        """
        # Krok 1: Zjistíme, co je vybráno v levém seznamu
        selected_indices = self.unassigned_list.curselection()
        if not selected_indices:
            messagebox.showwarning("Chyba", "Nejprve vyberte položku v levém seznamu 'Nalezené položky'.")
            return
        
        name = self.unassigned_list.get(selected_indices[0])
        
        # Krok 2: Pokusíme se typ určit automaticky
        typ = db.determine_category_type(self.app.profile_path, name)
        
        # Krok 3: Pokud se to nepodaří, zeptáme se uživatele
        if typ is None:
            typ = simpledialog.askstring(
                "Nelze určit typ", 
                f"Pro položku '{name}' nebyly nalezeny žádné transakce s nenulovou částkou.\n\nZadejte prosím její typ ručně ('příjem' nebo 'výdej'):"
            )
            if typ not in ['příjem', 'výdej']:
                messagebox.showerror("Chyba", "Neplatný typ. Operace byla zrušena.")
                return

        # Krok 4: Vložíme kategorii do databáze a získáme její nové ID
        new_category_id = db.add_category(self.app.profile_path, name, typ, None)
        
        # Krok 5: Hromadně přiřadíme ID všem souvisejícím transakcím
        db.assign_category_to_items(self.app.profile_path, name, new_category_id)
        
        # Krok 6: Obnovíme oba panely, aby se změna okamžitě projevila
        self.refresh_data()

    def add_as_subcategory(self):
        print("Logika pro přidání podkategorie bude zde.")
        # 1. Zjistit, co je vybráno vlevo (název).
        # 2. Zjistit, co je vybráno vpravo (rodič).
        # 3. Vložit do DB s parent_id rodiče.
        # 4. Obnovit oba panely.

    def rename_category(self):
        print("Logika pro přejmenování bude zde (v pravém panelu).")

    def delete_category(self):
        print("Logika pro smazání bude zde (v pravém panelu).")