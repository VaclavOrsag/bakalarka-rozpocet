"""
Záložka Účetní osnova - Správa kategorií a hierarchie.
"""
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import simpledialog
from typing import Any, Optional, Tuple, Dict, List

from app import database as db


class AccountingStructureTab:
    """
    Třída reprezentující záložku pro správu účetní osnovy.
    Umožňuje vytvářet kategorie (LEAF i CUSTOM), řadit je do hierarchie
    a přiřazovat k nim transakce.
    """
    
    def __init__(self, tab_frame: ttk.Frame, app_controller: Any) -> None:
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

    def _setup_layout(self) -> None:
        """Vytvoří hlavní třípanelový layout."""
        main_pane = ttk.PanedWindow(self.tab_frame, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.left_pane = ttk.PanedWindow(main_pane, orient=tk.VERTICAL)
        main_pane.add(self.left_pane, weight=2)

        self.controls_frame = ttk.Frame(main_pane)
        main_pane.add(self.controls_frame, weight=1)

        self.right_frame = ttk.LabelFrame(main_pane, text="Moje účetní osnova")
        main_pane.add(self.right_frame, weight=3)

    def _setup_left_panel(self) -> None:
        """Vytvoří obsah levého panelu (2 seznamy)."""
        income_lf = ttk.LabelFrame(self.left_pane, text="Příjmy")
        self.left_pane.add(income_lf, weight=1)
        self.list_prijmy = self._create_scrolled_listbox(income_lf)

        expense_lf = ttk.LabelFrame(self.left_pane, text="Výdaje")
        self.left_pane.add(expense_lf, weight=1)
        self.list_vydaje = self._create_scrolled_listbox(expense_lf)

    def _setup_controls_panel(self) -> None:
        """Vytvoří obsah středního panelu (tlačítka)."""
        # --- Tlačítka pro přesun z levého panelu ---
        ttk.Label(self.controls_frame, text="Zařadit položku:").pack(pady=(10, 2))
        ttk.Button(self.controls_frame, text="Přidat jako hlavní >>", command=self.add_as_main_category).pack(pady=5, padx=5, fill='x')
        ttk.Button(self.controls_frame, text="Přidat jako podkategorii >>", command=self.add_as_subcategory).pack(pady=5, padx=5, fill='x')
        
        ttk.Separator(self.controls_frame, orient='horizontal').pack(fill='x', pady=20)

        # --- Tlačítka pro správu osnovy v pravém panelu ---
        ttk.Label(self.controls_frame, text="Spravovat osnovu:").pack(pady=(10, 2))
        ttk.Button(self.controls_frame, text="Přidat custom kategorii...", command=self.add_custom_category).pack(pady=5, padx=5, fill='x')
        ttk.Button(self.controls_frame, text="Smazat vybranou", command=self.delete_category).pack(pady=5, padx=5, fill='x')

    def _setup_right_panel(self) -> None:
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
    
    def create_treeview(self, parent_frame: ttk.Frame) -> ttk.Treeview:   
        tree = ttk.Treeview(parent_frame, columns=('id',), displaycolumns=(), show='tree headings')
        tree.heading('#0', text='Název kategorie')
        tree.bind("<FocusIn>", self._on_tree_focus)
        tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        return tree
        
    def _create_scrolled_listbox(self, parent_frame: ttk.Frame, height: Optional[int] = None) -> tk.Listbox:
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

    def _on_tree_focus(self, event: tk.Event) -> None:
        self.active_tree = event.widget

    def _clear_other_tree_selection(self, event: tk.Event) -> None:
        active_widget = event.widget
        other_tree = self.tree_vydaje if active_widget == self.tree_prijmy else self.tree_prijmy
        for item in other_tree.selection():
            other_tree.selection_remove(item)

    def refresh_data(self) -> None: 
        self.load_unassigned_list()
        self.load_categories_tree()

    def load_unassigned_list(self) -> None:   
        for lst in [self.list_prijmy, self.list_vydaje]:
            lst.delete(0, tk.END)
        sorted_items = db.get_unassigned_categories_by_type(self.app.profile_path)
        for item in sorted_items['příjem']: self.list_prijmy.insert(tk.END, item)
        for item in sorted_items['výdej']: self.list_vydaje.insert(tk.END, item)

    def load_categories_tree(self) -> None:
        """
        Načte existující účetní osnovu a spolehlivě z ní sestaví
        hierarchické stromy, bez ohledu na pořadí dat.
        """
        # Smažeme obsah obou stromů
        for tree in [self.tree_prijmy, self.tree_vydaje]:
            for i in tree.get_children():
                tree.delete(i)
        
        all_categories = db.get_all_categories(self.app.profile_path)
        
        # Připravíme si data
        # 'to_process' je seznam kategorií, které ještě nemáme ve stromu
        to_process = {cat[0]: cat for cat in all_categories} 
        tree_items = {} # Slovník pro uložení iid (ID v Treeview)

        # Budeme opakovat cyklus tak dlouho, dokud se nám daří přidávat nové položky
        items_added_in_pass = -1
        while items_added_in_pass != 0:
            items_added_in_pass = 0
            
            # Projdeme všechny zbývající kategorie
            for cat_id, cat_data in list(to_process.items()):
                nazev, typ, parent_id = cat_data[1], cat_data[2], cat_data[3]
                is_custom = cat_data[4] if len(cat_data) > 4 else 0  # Přidáno čtení is_custom
                
                # Připravíme zobrazovaný text podle typu kategorie
                if is_custom == 1:
                    display_text = f"📁 {nazev}"
                else:
                    display_text = nazev
                    
                # Případ 1: Je to hlavní kategorie (nemá rodiče)
                if parent_id is None:
                    tree = self.tree_prijmy if typ == 'příjem' else self.tree_vydaje
                    iid = tree.insert('', 'end', text=display_text, values=(cat_id,), open=True)
                    
                    # Červená barva pro custom kategorie
                    if is_custom == 1:
                        tree.item(iid, tags=('custom',))
                    
                    tree_items[cat_id] = iid
                    del to_process[cat_id] # Odstraníme ze seznamu "ke zpracování"
                    items_added_in_pass += 1
                
                # Případ 2: Je to podkategorie A JEJÍ RODIČ UŽ EXISTUJE VE STROMU
                elif parent_id in tree_items:
                    tree = self.tree_prijmy if typ == 'příjem' else self.tree_vydaje
                    parent_iid = tree_items[parent_id]
                    iid = tree.insert(parent_iid, 'end', text=display_text, values=(cat_id,), open=True)
                    
                    # Červená barva pro custom kategorie
                    if is_custom == 1:
                        tree.item(iid, tags=('custom',))
                    
                    tree_items[cat_id] = iid
                    del to_process[cat_id] # Odstraníme ze seznamu "ke zpracování"
                    items_added_in_pass += 1

        # Konfigurace červené barvy pro custom kategorie
        for tree in [self.tree_prijmy, self.tree_vydaje]:
            tree.tag_configure('custom', foreground='red')

    # --- METODY PRO AKCE (BUSINESS LOGIKA) ---

    def _add_category_workflow(self, nazev: str, typ: str, parent_id: Optional[int], is_custom: int, assign_transactions: bool) -> None:
        """
        Centrální workflow pro přidání kategorie s automatickým handlingem UI notifikací.
        
        Args:
            nazev: Název kategorie
            typ: 'příjem' nebo 'výdej'
            parent_id: ID rodiče (None = root)
            is_custom: 0 = LEAF, 1 = CUSTOM
            assign_transactions: True = přiřadí transakce (jen pro LEAF)
        """
        # Zjistíme, zda se jedná o první kategorii
        is_first_category = not db.has_categories(self.app.profile_path)
        
        try:
            # Delegujeme na DB vrstvu
            db.add_category_with_workflow(
                self.app.profile_path,
                nazev,
                typ,
                parent_id,
                is_custom,
                assign_transactions
            )
            
            # Pokud to byla první přidaná kategorie, odemkneme záložku Rozpočet
            if is_first_category:
                self.app.update_tabs_visibility()
                messagebox.showinfo(
                    "Rozpočet je připraven",
                    "Byla vytvořena první kategorie a záložka 'Rozpočet' je nyní k dispozici.\n\nMůžete pokračovat v tvorbě účetní osnovy."
                )
            
            self.refresh_data()
            
        except ValueError as e:
            messagebox.showerror("Chyba", str(e))

    def get_selected_unassigned_with_type(self) -> Tuple[Optional[str], Optional[str]]:        
        listbox_map = {'příjem': self.list_prijmy, 'výdej': self.list_vydaje}
        for typ, listbox in listbox_map.items():
            selected_indices = listbox.curselection()
            if selected_indices:
                name = listbox.get(selected_indices[0])
                return name, typ
        return None, None
    
    def add_as_main_category(self) -> None:
        """Přidá LEAF kategorii na root úroveň s přiřazením transakcí."""
        name, typ = self.get_selected_unassigned_with_type()
        if not name:
            messagebox.showwarning("Chyba", "Nejprve vyberte položku v jednom z levých seznamů.")
            return
        
        self._add_category_workflow(
            nazev=name,
            typ=typ,
            parent_id=None,
            is_custom=0,
            assign_transactions=True
        )

    def add_as_subcategory(self) -> None:
        """Přidá LEAF kategorii pod vybranou CUSTOM kategorii s přiřazením transakcí."""
        name, actual_type = self.get_selected_unassigned_with_type()
        if not name:
            messagebox.showwarning("Chyba", "Nejprve vyberte položku v jednom z levých seznamů.")
            return
        
        # Zkontroluj že je vybrána nadřazená kategorie v pravém stromu
        if not self.active_tree or not self.active_tree.focus():
            messagebox.showwarning("Chyba", "Nejprve v pravém stromu vyberte nadřazenou kategorii.")
            return
        
        parent_id = self.active_tree.item(self.active_tree.focus())['values'][0]
        
        # Validace typu se děje v DB vrstvě (add_category)
        self._add_category_workflow(
            nazev=name,
            typ=actual_type,  # Použijeme actual_type (z levého panelu)
            parent_id=parent_id,
            is_custom=0,
            assign_transactions=True
        )

    def delete_category(self) -> None:       
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

    def add_custom_category(self) -> None:
        """Vytvoří CUSTOM kategorii (agregační, bez transakcí) na root nebo pod CUSTOM parent."""
        parent_id = None
        parent_type = None
        
        # Zjistíme, jestli je něco vybráno (chceme tvořit podkategorii)
        if self.active_tree and self.active_tree.focus():
            selected_iid = self.active_tree.focus()
            parent_id = self.active_tree.item(selected_iid)['values'][0]
            parent_type = 'příjem' if self.active_tree == self.tree_prijmy else 'výdej'

        # Zeptáme se na název
        name = simpledialog.askstring("Nová kategorie", "Zadejte název nové kategorie:")
        if not name or not name.strip():
            return # Uživatel nic nezadal nebo zrušil

        # Pokud jsme nezjistili typ od rodiče, musíme se zeptat
        if parent_type is None:
            typ = simpledialog.askstring("Typ kategorie", f"Zadejte typ pro '{name}' ('příjem' nebo 'výdej'):", parent=self.app.root)
            if typ not in ['příjem', 'výdej']:
                messagebox.showerror("Chyba", "Neplatný typ. Zadejte 'příjem' nebo 'výdej'.")
                return
        else:
            typ = parent_type

        # Validace duplicity se děje v DB vrstvě (add_category)
        self._add_category_workflow(
            nazev=name,
            typ=typ,
            parent_id=parent_id,
            is_custom=1,
            assign_transactions=False
        )