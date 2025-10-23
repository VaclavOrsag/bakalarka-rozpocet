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

        # 1. LEVÝ PANEL: Nalezené položky roztříděné
        left_frame = ttk.LabelFrame(main_pane, text="Nalezené položky z 'Co'")
        main_pane.add(left_frame, weight=2)

        ttk.Label(left_frame, text="Příjmy", font=("Arial", 10, "bold")).pack(anchor='w', padx=5, pady=(5,0))
        self.list_prijmy = tk.Listbox(left_frame, height=6)
        self.list_prijmy.pack(fill='x', padx=5)
        
        ttk.Label(left_frame, text="Výdaje", font=("Arial", 10, "bold")).pack(anchor='w', padx=5, pady=(10,0))
        self.list_vydaje = tk.Listbox(left_frame, height=10)
        self.list_vydaje.pack(fill='both', expand=True, padx=5)
        
        ttk.Label(left_frame, text="Nelze určit / Nutná kontrola", font=("Arial", 10, "bold")).pack(anchor='w', padx=5, pady=(10,0))
        self.list_neurceno = tk.Listbox(left_frame, height=4)
        self.list_neurceno.pack(fill='x', padx=5, pady=(0,5))

        # 2. STŘEDNÍ PANEL: Ovládací tlačítka
        controls_frame = ttk.Frame(main_pane)
        main_pane.add(controls_frame, weight=1)

        ttk.Button(controls_frame, text="Přidat jako hlavní >>", command=self.add_as_main_category).pack(pady=15, padx=5)
        ttk.Button(controls_frame, text="Přidat jako podkategorii >>", command=self.add_as_subcategory).pack(pady=5, padx=5)
        ttk.Separator(controls_frame, orient='horizontal').pack(fill='x', pady=10)
        #ttk.Button(controls_frame, text="Přejmenovat", command=self.rename_category).pack(pady=5, padx=5)
        ttk.Button(controls_frame, text="Smazat", command=self.delete_category).pack(pady=5, padx=5)

        # 3. PRAVÝ PANEL: Moje účetní osnova
        right_frame = ttk.LabelFrame(main_pane, text="Moje účetní osnova")
        main_pane.add(right_frame, weight=3)

        self.active_tree = None

        # 4. Dělící panel pro pravou stranu
        right_pane = ttk.PanedWindow(right_frame, orient=tk.HORIZONTAL)
        right_pane.pack(fill=tk.BOTH, expand=True)

        # 5. Rám a strom pro Příjmy
        income_frame = ttk.Frame(right_pane)
        ttk.Label(income_frame, text="Příjmy", font=("Arial", 12, "bold")).pack(pady=5)
        self.tree_prijmy = self.create_treeview(income_frame)
        self.tree_prijmy.bind("<Button-1>", self._clear_other_tree_selection)
        right_pane.add(income_frame, weight=1)

        # 6. Rám a strom pro Výdaje
        expense_frame = ttk.Frame(right_pane)
        ttk.Label(expense_frame, text="Výdaje", font=("Arial", 12, "bold")).pack(pady=5)
        self.tree_vydaje = self.create_treeview(expense_frame)
        self.tree_vydaje.bind("<Button-1>", self._clear_other_tree_selection)
        right_pane.add(expense_frame, weight=1)
        
        # Načteme data do obou panelů
        self.refresh_data()

    def create_treeview(self, parent_frame):
        """Pomocná metoda, která vytvoří a nakonfiguruje jeden Treeview widget."""
        # Nepotřebujeme sloupec 'typ', protože ten je dán tím, ve kterém stromu se kategorie nachází.
        tree = ttk.Treeview(parent_frame, columns=('id',), displaycolumns=(), show='tree headings')
        tree.heading('#0', text='Název kategorie')
        
        # Když uživatel klikne do stromu, zavolá se metoda _on_tree_focus
        tree.bind("<FocusIn>", self._on_tree_focus)
        
        tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        return tree
        
    def _on_tree_focus(self, event):
        """Zapamatuje si, který strom byl naposledy aktivní."""
        # event.widget je přímý odkaz на widget, který událost spustil (náš strom)
        self.active_tree = event.widget

    def refresh_data(self):
        """Obnoví data v obou panelech."""
        self.load_unassigned_list()
        self.load_categories_tree()

    def load_unassigned_list(self):
        """Načte nezařazené položky a roztřídí je do tří seznamů."""
        # Smažeme obsah všech tří seznamů
        self.list_prijmy.delete(0, tk.END)
        self.list_vydaje.delete(0, tk.END)
        self.list_neurceno.delete(0, tk.END)
        
        # Získáme roztříděná data z databáze
        sorted_items = db.get_unassigned_categories_by_type(self.app.profile_path)
        
        # Naplníme seznamy
        for item in sorted_items['příjem']:
            self.list_prijmy.insert(tk.END, item)
        for item in sorted_items['výdej']:
            self.list_vydaje.insert(tk.END, item)
        for item in sorted_items['neurčeno']:
            self.list_neurceno.insert(tk.END, item)

    def load_categories_tree(self):
        """Načte existující účetní osnovu a rozdělí ji do dvou stromů."""
        # Smažeme obsah obou stromů
        for tree in [self.tree_prijmy, self.tree_vydaje]:
            for i in tree.get_children():
                tree.delete(i)
        
        all_categories = db.get_all_categories(self.app.profile_path)
        category_map = {cat[0]: cat for cat in all_categories}
        tree_items = {} # Slovník pro uložení iid (ID v Treeview)

        # Rozdělíme vkládání hlavních kategorií podle typu
        for cat_id, cat_data in category_map.items():
            parent_id = cat_data[3]
            if parent_id is None:
                # Rozhodneme, do kterého stromu patří
                tree = self.tree_prijmy if cat_data[2] == 'příjem' else self.tree_vydaje
                # Vložíme a uložíme si iid
                iid = tree.insert('', 'end', text=cat_data[1], values=(cat_id,), open=True)
                tree_items[cat_id] = iid
        
        # Vložíme podkategorie (zde je logika skoro stejná)
        for cat_id, cat_data in category_map.items():
            parent_id = cat_data[3]
            if parent_id in tree_items:
                # Znovu určíme správný strom podle typu kategorie
                tree = self.tree_prijmy if cat_data[2] == 'příjem' else self.tree_vydaje
                parent_iid = tree_items[parent_id]
                iid = tree.insert(parent_iid, 'end', text=cat_data[1], values=(cat_id,), open=True)
                tree_items[cat_id] = iid


    def get_selected_unassigned_with_type(self):
        """
        Pomocná metoda, která zjistí, co je vybráno v levých seznamech,
        a vrátí název položky i její typ ('příjem', 'výdej', 'neurčeno').
        """
        # Vytvoříme si mapu pro snadné určení typu
        listbox_map = {
            'příjem': self.list_prijmy,
            'výdej': self.list_vydaje,
            'neurčeno': self.list_neurceno
        }

        for typ, listbox in listbox_map.items():
            selected_indices = listbox.curselection()
            if selected_indices:
                name = listbox.get(selected_indices[0])
                return name, typ # Vrátíme název i typ
        
        return None, None # Pokud není nic vybráno
    
    def add_as_main_category(self):
        """
        Vezme vybranou položku, využije její před-analyzovaný typ (nebo se zeptá),
        vytvoří novou hlavní kategorii a hromadně přiřadí všechny
        související transakce k této nové kategorii.
        """
        # Krok 1: Zjistíme, co je vybráno a jaký to má typ, pomocí naší nové metody
        name, typ = self.get_selected_unassigned_with_type()
        if not name:
            messagebox.showwarning("Chyba", "Nejprve vyberte položku v jednom z levých seznamů.")
            return
        
        # Krok 2: typ známe, při neurčeno nastává chyba -- nutné doplnit od uživatele
        if typ not in ['příjem', 'výdej']:
            messagebox.showerror("Chyba", "Neplatný typ. Operace byla zrušena.")
            return

        # Krok 3: Vložíme kategorii do databáze a získáme její nové ID
        new_category_id = db.add_category(self.app.profile_path, name, typ, None)
        
        # Krok 4: Hromadně přiřadíme ID všem souvisejícím transakcím
        db.assign_category_to_items(self.app.profile_path, name, new_category_id)
        
        # Krok 5: Obnovíme oba panely, aby se změna okamžitě projevila
        self.refresh_data()

    def add_as_subcategory(self):
        """
        Vezme vybranou položku z levého seznamu a přidá ji jako 
        podkategorii k vybrané položce v pravém stromu.
        """
        # 1. Zjistíme, co je vybráno vlevo (název i skutečný typ)
        name, actual_type = self.get_selected_unassigned_with_type()
        if not name:
            messagebox.showwarning("Chyba", "Nejprve vyberte položku v jednom z levých seznamů.")
            return
        # 2. Zjistíme, co je vybráno vpravo (rodič)
        if not self.active_tree:
            messagebox.showwarning("Chyba", "Nejprve v pravém panelu klikněte do stromu (Příjmy nebo Výdaje), kam chcete přidat.")
            return
        selected_iid_right = self.active_tree.focus()
        if not selected_iid_right:
            messagebox.showwarning("Chyba", "Nejprve v pravém stromu vyberte nadřazenou kategorii.")
            return

        # 3. Získáme potřebné údaje o rodiči 
        parent_id = self.active_tree.item(selected_iid_right)['values'][0]
        # Zjistíme typ tak, že se podíváme, který strom je aktivní
        parent_type = 'příjem' if self.active_tree == self.tree_prijmy else 'výdej'

        # Pokud se snažíme zařadit položku typu nerovnému tomu rodiče
        if actual_type != parent_type:
            messagebox.showerror(
                "Chyba zařazení", 
                f"Nelze zařadit položku typu '{actual_type.capitalize()}' pod '{parent_type.capitalize()}'."
            )
            return
        # --- KONEC KONTROLY ---

        # 4. Vložíme kategorii a získáme její nové ID
        new_category_id = db.add_category(self.app.profile_path, name, parent_type, parent_id)
        
        # 5. Hromadně aktualizujeme všechny související transakce
        db.assign_category_to_items(self.app.profile_path, name, new_category_id)
        
        # 6. Obnovíme zobrazení
        self.refresh_data()

    def delete_category(self):
        """
        Smaže kategorii vybranou v pravém stromu a všechny související
        transakce vrátí mezi nezařazené.
        """
        if not self.active_tree:
            messagebox.showwarning("Chyba", "Nejprve v pravém panelu vyberte kategorii ke smazání.")
            return
        
        selected_iid = self.active_tree.focus()
        if not selected_iid:
            messagebox.showwarning("Chyba", "Nejprve v pravém stromu vyberte kategorii ke smazání.")
            return
            
        if self.active_tree.get_children(selected_iid):
            messagebox.showerror("Chyba", "Nelze smazat kategorii, která obsahuje podkategorie.")
            return

        category_id = self.active_tree.item(selected_iid)['values'][0]
        category_name = self.active_tree.item(selected_iid)['text']

        if messagebox.askyesno("Potvrdit smazání", f"Opravdu chcete smazat kategorii '{category_name}'?\n\nVšechny přiřazené transakce se vrátí mezi nezařazené."):
            
            # Krok 1: "Vysypeme" všechny transakce z této kategorie
            db.unassign_items_from_category(self.app.profile_path, category_id)
            
            # Krok 2: Teprve teď smažeme samotnou kategorii
            db.delete_category(self.app.profile_path, category_id)
            
            # Krok 3: Obnovíme zobrazení
            self.refresh_data()

    def _clear_other_tree_selection(self, event):
        """
        Zjistí, který strom spustil událost, a zruší výběr v tom druhém.
        """
        active_widget = event.widget
        
        # Určíme, který je ten "druhý" strom
        other_tree = self.tree_vydaje if active_widget == self.tree_prijmy else self.tree_prijmy
        
        # Zrušíme výběr ve druhém stromu
        for item in other_tree.selection():
            other_tree.selection_remove(item)