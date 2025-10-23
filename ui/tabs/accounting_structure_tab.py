import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import simpledialog

from app import database as db

class AccountingStructureTab:
    def __init__(self, tab_frame, app_controller):
        """
        Inicializuje obsah záložky 'Účetní Osnova' a deleguje tvorbu UI
        na specializované metody.
        """
        self.app = app_controller
        self.tab_frame = tab_frame
        self.active_tree = None

        self._setup_layout()
        self._setup_left_panel()
        self._setup_controls_panel()
        self._setup_right_panel()
        
        self.refresh_data()

    # --- METODY PRO SESTAVENÍ UI ---

    def _setup_layout(self):
        """Vytvoří hlavní třípanelový layout."""
        main_pane = ttk.PanedWindow(self.tab_frame, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.left_pane = ttk.PanedWindow(main_pane, orient=tk.VERTICAL)
        main_pane.add(self.left_pane, weight=2)

        self.controls_frame = ttk.Frame(main_pane)
        main_pane.add(self.controls_frame, weight=1)

        self.right_frame = ttk.LabelFrame(main_pane, text="Moje účetní osnova")
        main_pane.add(self.right_frame, weight=3)

    def _setup_left_panel(self):
        """Vytvoří obsah levého panelu (3 seznamy)."""
        income_lf = ttk.LabelFrame(self.left_pane, text="Příjmy")
        self.left_pane.add(income_lf, weight=2)
        self.list_prijmy = self._create_scrolled_listbox(income_lf)

        expense_lf = ttk.LabelFrame(self.left_pane, text="Výdaje")
        self.left_pane.add(expense_lf, weight=3)
        self.list_vydaje = self._create_scrolled_listbox(expense_lf)
        
        unknown_lf = ttk.LabelFrame(self.left_pane, text="Nelze určit / Nutná kontrola")
        self.left_pane.add(unknown_lf, weight=1)
        self.list_neurceno = self._create_scrolled_listbox(unknown_lf, height=3)

    def _setup_controls_panel(self):
        """Vytvoří obsah středního panelu (tlačítka)."""
        ttk.Button(self.controls_frame, text="Přidat jako hlavní >>", command=self.add_as_main_category).pack(pady=15, padx=5)
        ttk.Button(self.controls_frame, text="Přidat jako podkategorii >>", command=self.add_as_subcategory).pack(pady=5, padx=5)
        ttk.Separator(self.controls_frame, orient='horizontal').pack(fill='x', pady=10)
        ttk.Button(self.controls_frame, text="Smazat", command=self.delete_category).pack(pady=5, padx=5)

    def _setup_right_panel(self):
        """Vytvoří obsah pravého panelu (2 stromy)."""
        right_pane = ttk.PanedWindow(self.right_frame, orient=tk.HORIZONTAL)
        right_pane.pack(fill=tk.BOTH, expand=True)
        
        income_frame = ttk.Frame(right_pane)
        ttk.Label(income_frame, text="Příjmy", font=("Arial", 12, "bold")).pack(pady=5)
        self.tree_prijmy = self.create_treeview(income_frame)
        self.tree_prijmy.bind("<Button-1>", self._clear_other_tree_selection)
        right_pane.add(income_frame, weight=1)

        expense_frame = ttk.Frame(right_pane)
        ttk.Label(expense_frame, text="Výdaje", font=("Arial", 12, "bold")).pack(pady=5)
        self.tree_vydaje = self.create_treeview(expense_frame)
        self.tree_vydaje.bind("<Button-1>", self._clear_other_tree_selection)
        right_pane.add(expense_frame, weight=1)

    # --- POMOCNÉ METODY PRO UI ---
    
    def create_treeview(self, parent_frame):   
        tree = ttk.Treeview(parent_frame, columns=('id',), displaycolumns=(), show='tree headings')
        tree.heading('#0', text='Název kategorie')
        tree.bind("<FocusIn>", self._on_tree_focus)
        tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        return tree
        
    def _create_scrolled_listbox(self, parent_frame, height=None):
        list_frame = ttk.Frame(parent_frame)
        list_frame.pack(fill='both', expand=True, padx=5, pady=5)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical")
        if height:
            listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, height=height)
        else:
            listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        scrollbar.config(command=listbox.yview)
        scrollbar.pack(side="right", fill="y")
        listbox.pack(side="left", fill="both", expand=True)
        return listbox

    # --- METODY PRO UDÁLOSTI A NAČÍTÁNÍ DAT ---

    def _on_tree_focus(self, event):
        self.active_tree = event.widget

    def _clear_other_tree_selection(self, event):
        active_widget = event.widget
        other_tree = self.tree_vydaje if active_widget == self.tree_prijmy else self.tree_prijmy
        for item in other_tree.selection():
            other_tree.selection_remove(item)

    def refresh_data(self): 
        self.load_unassigned_list()
        self.load_categories_tree()

    def load_unassigned_list(self):   
        for lst in [self.list_prijmy, self.list_vydaje, self.list_neurceno]:
            lst.delete(0, tk.END)
        sorted_items = db.get_unassigned_categories_by_type(self.app.profile_path)
        for item in sorted_items['příjem']: self.list_prijmy.insert(tk.END, item)
        for item in sorted_items['výdej']: self.list_vydaje.insert(tk.END, item)
        for item in sorted_items['neurčeno']: self.list_neurceno.insert(tk.END, item)

    def load_categories_tree(self):    
        for tree in [self.tree_prijmy, self.tree_vydaje]:
            for i in tree.get_children(): tree.delete(i)
        all_categories = db.get_all_categories(self.app.profile_path)
        category_map = {cat[0]: cat for cat in all_categories}
        tree_items = {}
        for cat_id, cat_data in category_map.items():
            parent_id = cat_data[3]
            if parent_id is None:
                tree = self.tree_prijmy if cat_data[2] == 'příjem' else self.tree_vydaje
                iid = tree.insert('', 'end', text=cat_data[1], values=(cat_id,), open=True)
                tree_items[cat_id] = iid
        for cat_id, cat_data in category_map.items():
            parent_id = cat_data[3]
            if parent_id in tree_items:
                tree = self.tree_prijmy if cat_data[2] == 'příjem' else self.tree_vydaje
                parent_iid = tree_items[parent_id]
                iid = tree.insert(parent_iid, 'end', text=cat_data[1], values=(cat_id,), open=True)
                tree_items[cat_id] = iid

    # --- METODY PRO AKCE (BUSINESS LOGIKA) ---

    def get_selected_unassigned_with_type(self):        
        listbox_map = {'příjem': self.list_prijmy, 'výdej': self.list_vydaje, 'neurčeno': self.list_neurceno}
        for typ, listbox in listbox_map.items():
            selected_indices = listbox.curselection()
            if selected_indices:
                name = listbox.get(selected_indices[0])
                return name, typ
        return None, None
    
    def add_as_main_category(self):        
        name, typ = self.get_selected_unassigned_with_type()
        if not name:
            messagebox.showwarning("Chyba", "Nejprve vyberte položku v jednom z levých seznamů.")
            return
        if typ not in ['příjem', 'výdej']:
            messagebox.showerror("Chyba zařazení", f"Položku '{name}' nelze automaticky zařadit.")
            return
        new_category_id = db.add_category(self.app.profile_path, name, typ, None)
        db.assign_category_to_items(self.app.profile_path, name, new_category_id)
        self.refresh_data()

    def add_as_subcategory(self):
        name, actual_type = self.get_selected_unassigned_with_type()
        if not name:
            messagebox.showwarning("Chyba", "Nejprve vyberte položku v jednom z levých seznamů.")
            return
        if not self.active_tree:
            messagebox.showwarning("Chyba", "Nejprve v pravém panelu klikněte do stromu.")
            return
        selected_iid_right = self.active_tree.focus()
        if not selected_iid_right:
            messagebox.showwarning("Chyba", "Nejprve v pravém stromu vyberte nadřazenou kategorii.")
            return
        parent_id = self.active_tree.item(selected_iid_right)['values'][0]
        parent_type = 'příjem' if self.active_tree == self.tree_prijmy else 'výdej'
        if actual_type != parent_type:
            messagebox.showerror("Chyba zařazení", f"Nelze zařadit položku typu '{actual_type.capitalize()}' pod '{parent_type.capitalize()}'.")
            return
        new_category_id = db.add_category(self.app.profile_path, name, parent_type, parent_id)
        db.assign_category_to_items(self.app.profile_path, name, new_category_id)
        self.refresh_data()

    def delete_category(self):       
        if not self.active_tree:
            messagebox.showwarning("Chyba", "Nejprve vyberte kategorii ke smazání.")
            return
        selected_iid = self.active_tree.focus()
        if not selected_iid:
            messagebox.showwarning("Chyba", "Nejprve vyberte kategorii ke smazání.")
            return
        if self.active_tree.get_children(selected_iid):
            messagebox.showerror("Chyba", "Nelze smazat kategorii, která obsahuje podkategorie.")
            return
        category_id = self.active_tree.item(selected_iid)['values'][0]
        category_name = self.active_tree.item(selected_iid)['text']
        if messagebox.askyesno("Potvrdit smazání", f"Opravdu chcete smazat '{category_name}'?"):
            db.unassign_items_from_category(self.app.profile_path, category_id)
            db.delete_category(self.app.profile_path, category_id)
            self.refresh_data()