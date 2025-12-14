"""
Modul pro dialogové okno úpravy hierarchie.

Umožňuje uživateli vybrat a seřadit dimenze pro kontingenční tabulku.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Callable

MAX_LEVELS = 5

class HierarchyDialog:
    """
    Dialogové okno pro výběr a řazení hierarchie (dimenzí).
    """

    def __init__(self, parent: tk.Widget, available_dims: List[str], current_dims: List[str], on_result: Callable[[List[str]], None]) -> None:
        """
        Inicializuje dialog.

        Args:
            parent: Rodičovské okno.
            available_dims: Seznam všech dostupných dimenzí.
            current_dims: Seznam aktuálně vybraných dimenzí (v daném pořadí).
            on_result: Callback funkce, která se zavolá s novým seznamem dimenzí při potvrzení.
        """
        self.parent = parent
        self.available_dims = available_dims
        self.current_dims = list(current_dims)  # Kopie pro lokální úpravy
        self.on_result = on_result

        self.window = tk.Toplevel(parent)
        self.window.title("Upravit hierarchii řádků")
        self.window.transient(parent)
        self.window.grab_set()
        
        self._create_layout()

    def _create_layout(self) -> None:
        """Vytvoří rozložení dialogu."""
        # Levý panel - Dostupné
        left = ttk.Frame(self.window, padding=6)
        left.pack(side='left', fill='both', expand=True)
        ttk.Label(left, text="Dostupné pole").pack()
        
        self.avail_lb = tk.Listbox(left, height=8, exportselection=False)
        self.avail_lb.pack(fill='both', expand=True, padx=4, pady=4)
        
        # Naplnění dostupných (jen ty, co nejsou vybrané)
        for item in self.available_dims:
            if item not in self.current_dims:
                self.avail_lb.insert('end', item)

        # Střední panel - Tlačítka
        mid = ttk.Frame(self.window, padding=6)
        mid.pack(side='left', fill='y')

        # Pravý panel - Vybrané
        right = ttk.Frame(self.window, padding=6)
        right.pack(side='left', fill='both', expand=True)
        ttk.Label(right, text="Vybraná hierarchie (pořadí)").pack()
        
        self.selected_lb = tk.Listbox(right, height=8, exportselection=False)
        self.selected_lb.pack(fill='both', expand=True, padx=4, pady=4)
        
        # Naplnění vybraných
        for item in self.current_dims:
            self.selected_lb.insert('end', item)

        # Tlačítka akcí
        ttk.Button(mid, text="→", width=4, command=self._add_one).pack(pady=4)
        ttk.Button(mid, text="←", width=4, command=self._remove_one).pack(pady=4)
        ttk.Button(mid, text="▲", width=4, command=lambda: self._move(True)).pack(pady=4)
        ttk.Button(mid, text="▼", width=4, command=lambda: self._move(False)).pack(pady=4)

        # Spodní panel - OK/Zrušit
        btns = ttk.Frame(self.window, padding=6)
        btns.pack(side='bottom', fill='x')

        ttk.Button(btns, text="OK", command=self._on_ok).pack(side='right', padx=6)
        ttk.Button(btns, text="Zrušit", command=self._on_cancel).pack(side='right')

    def _add_one(self) -> None:
        """Přesune vybranou položku z dostupných do vybraných."""
        sel = self.avail_lb.curselection()
        if not sel:
            return
        idx = sel[0]
        val = self.avail_lb.get(idx)
        
        self.selected_lb.insert('end', val)
        self.avail_lb.delete(idx)

    def _remove_one(self) -> None:
        """Přesune vybranou položku z vybraných zpět do dostupných."""
        sel = self.selected_lb.curselection()
        if not sel:
            return
        idx = sel[0]
        val = self.selected_lb.get(idx)
        
        self.selected_lb.delete(idx)
        
        # Vrátit do levého seznamu a seřadit podle původního pořadí
        items = list(self.avail_lb.get(0, 'end'))
        items.append(val)
        # Seřadit podle indexu v self.available_dims
        items.sort(key=lambda x: self.available_dims.index(x) if x in self.available_dims else 999)
        
        self.avail_lb.delete(0, 'end')
        for item in items:
            self.avail_lb.insert('end', item)

    def _move(self, up: bool) -> None:
        """
        Posune vybranou položku v seznamu vybraných nahoru nebo dolů.
        
        Args:
            up: True pro posun nahoru, False pro posun dolů.
        """
        sel = self.selected_lb.curselection()
        if not sel:
            return
        i = sel[0]
        
        if up and i == 0:
            return
        if not up and i >= self.selected_lb.size() - 1:
            return
            
        val = self.selected_lb.get(i)
        new_index = i - 1 if up else i + 1
        
        self.selected_lb.delete(i)
        self.selected_lb.insert(new_index, val)
        self.selected_lb.selection_set(new_index)

    def _on_ok(self) -> None:
        """Potvrdí výběr a zavolá callback."""
        vals = list(self.selected_lb.get(0, 'end'))
        
        if len(vals) > MAX_LEVELS:
            messagebox.showwarning("Omezení", f"Maximálně {MAX_LEVELS} úrovní povoleno.")
            return
        if not vals:
            messagebox.showwarning("Vyberte pole", "Musíte vybrat alespoň jedno pole pro řádky.")
            return
            
        self.window.destroy()
        self.on_result(vals)

    def _on_cancel(self) -> None:
        """Zavře dialog bez uložení."""
        self.window.destroy()

def open_hierarchy_dialog(parent: tk.Widget, available_dims: List[str], current_dims: List[str], on_result: Callable[[List[str]], None]) -> None:
    """
    Otevře dialog pro úpravu hierarchie.
    
    Args:
        parent: Rodičovské okno.
        available_dims: Seznam dostupných dimenzí.
        current_dims: Seznam aktuálních dimenzí.
        on_result: Callback funkce volaná při potvrzení (přebírá list[str]).
    """
    dialog = HierarchyDialog(parent, available_dims, current_dims, on_result)
    dialog.window.wait_window()