# ...existing code...
import tkinter as tk
from tkinter import ttk, messagebox
from app import database as db

from ui.hierarchy_dialog import open_hierarchy_dialog


class AnalysisTab:
    """Analysis tab UI scaffold.

    Provides filter controls and a Treeview for hierarchical pivot-like output.
    Data loading is left as a placeholder; later we'll hook it to a DB helper.
    """
    def __init__(self, tab_frame, app_controller):
        self.app = app_controller
        self.parent = tab_frame

        container = ttk.Frame(tab_frame, padding=8)
        container.pack(fill='both', expand=True)

        # --- Controls (top) ---
        ctrl = ttk.Frame(container)
        ctrl.pack(fill='x', pady=(0,6))

        ttk.Label(ctrl, text="Preset:").pack(side='left')
        self.preset_var = tk.StringVar(value='Analýza středisek')
        self.preset_cb = ttk.Combobox(
            ctrl,
            textvariable=self.preset_var,
            values=['Analýza středisek', 'Analýza rozpočtu','Analýza rozpočtu 2', 'Vlastní'],
            state='readonly',
            width=20
        )
        self.preset_cb.pack(side='left', padx=6)
        # bind to handler that sets defaults and enables/disables hierarchy editing
        self.preset_cb.bind('<<ComboboxSelected>>', self._on_preset_change)

        ttk.Label(ctrl, text="Řádky:").pack(side='left', padx=(12,0))
        # hierarchy selection via dialog (UI labels). 'kategorie' je uživatelský název pro kategorie_id
        self.available_dims = ['kategorie','stredisko','text','kdo','firma']
        self.row_dims = ['stredisko']  # default selection
        self.hierarchy_btn = ttk.Button(ctrl, text="Upravit hierarchii...", command=self._open_hierarchy_dialog)
        self.hierarchy_btn.pack(side='left', padx=6)

        ttk.Label(ctrl, text="Zobrazení:").pack(side='left', padx=(12,0))
        self.current_var = tk.StringVar(value='Aktuální')
        # only two options: Aktuální / Historické
        self.current_cb = ttk.Combobox(
            ctrl,
            textvariable=self.current_var,
            values=['Aktuální','Historické'],
            state='readonly',
            width=12
        )
        self.current_cb.pack(side='left', padx=6)
        self.current_cb.bind('<<ComboboxSelected>>', lambda e: self.load())

        # Filtr typu (Příjmy/Výdaje) dvěma checkboxy
        types_frame = ttk.Frame(ctrl)
        types_frame.pack(side='left', padx=(18,0))
        ttk.Label(types_frame, text="Typ:").pack(side='left')
        self.include_income_var = tk.BooleanVar(value=True)
        self.include_expense_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(types_frame, text='Příjmy', variable=self.include_income_var, command=self.load).pack(side='left', padx=4)
        ttk.Checkbutton(types_frame, text='Výdaje', variable=self.include_expense_var, command=self.load).pack(side='left', padx=4)

        # Note: search/export/drilldown are postponed; UI simplified for MVP.

        # --- Main area: Treeview for results ---
        body = ttk.Frame(container)
        body.pack(fill='both', expand=True)

        self.tree = ttk.Treeview(body, columns=('total',), show='tree headings')
        self.tree.heading('#0', text='Řádek')
        self.tree.heading('total', text='Celkem')
        self.tree.column('total', width=120, anchor='e')
        self.tree.pack(side='left', fill='both', expand=True)

        vsb = ttk.Scrollbar(body, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side='left', fill='y')

        # Drill-down is postponed; do not bind double-click yet.

        # Initial placeholder
        self._on_preset_change()  # set initial state and load
        # Načtení aktuálních změn (učetní osnova...) při zviditelnění tabu
        self.parent.bind("<Visibility>", lambda e: self.load())

    def _show_placeholder(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        self.tree.insert('', 'end', text='Nejsou načtena data', values=('',))

    def _format_money(self, val: float) -> str:
        # Jednoduché česko-like formátování: mezery jako tisícové oddělovače, čárka jako desetinná
        s = f"{val:,.2f}".replace(",", " ").replace(".", ",")
        return s + " Kč"

    def load(self):
        """Načte agregovaná data dle self.row_dims a zobrazení a vykreslí strom."""
        # Vyčistit strom
        for i in self.tree.get_children():
            self.tree.delete(i)

        is_current = 1 if self.current_var.get() == 'Aktuální' else 0
        # Mapování UI labelů na DB sloupce
        dims = [self._map_dim_to_column(d) for d in self.row_dims]

        # Odvození allowed_types z checkboxů
        inc = getattr(self, 'include_income_var', None)
        exp = getattr(self, 'include_expense_var', None)
        allowed_types = None
        if inc is not None and exp is not None:
            inc_val = self.include_income_var.get()
            exp_val = self.include_expense_var.get()
            if not inc_val and not exp_val:
                self._show_placeholder()
                return
            if inc_val and exp_val:
                allowed_types = ['příjem', 'výdej']
            elif inc_val:
                allowed_types = ['příjem']
            elif exp_val:
                allowed_types = ['výdej']

        try:
            rows = db.get_pivot_rows(self.app.profile_path, dims, is_current, allowed_types)
        except Exception:
            # Pokud by se něco pokazilo, zobrazíme placeholder (tiché selhání v UI)
            self._show_placeholder()
            return

        # Bez dimenzí – jen jeden řádek s celkem
        if not dims:
            total = rows[0]['total'] if rows else 0.0
            self.tree.insert('', 'end', text='Celkem', values=(self._format_money(total),))
            return

        if not rows:
            self._show_placeholder()
            return

        # 1) Spočítat sumy pro všechny prefixy cest (aby měly hodnotu i rodiče)
        from collections import defaultdict
        sums = defaultdict(float)
        max_depth = 0
        # Předzpracujeme také sekvence klíčů s náhradou prázdných řetězců
        processed = []
        for r in rows:
            keys = [k if (k is not None and k != "") else "—" for k in r['keys']]
            total = float(r['total'] or 0.0)
            processed.append((keys, total))
            max_depth = max(max_depth, len(keys))
            for d in range(1, len(keys) + 1):
                sums[tuple(keys[:d])] += total

        # 2) Vykreslit uzly po vrstvách, aby rodiče vznikli dřív
        nodes = {}  # path tuple -> iid
        for depth in range(1, max_depth + 1):
            added = set()
            for keys, _ in processed:
                if len(keys) < depth:
                    continue
                path = tuple(keys[:depth])
                if path in added:
                    continue
                parent_path = path[:-1]
                parent_iid = nodes[parent_path] if parent_path in nodes else ''
                iid = self.tree.insert(
                    parent_iid, 'end',
                    text=path[-1],
                    values=(self._format_money(sums[path]),),
                    open=False
                )
                nodes[path] = iid
                added.add(path)

    def _on_preset_change(self, event=None):
        """Apply preset defaults and enable hierarchy editing only for 'Vlastní'."""
        preset = self.preset_var.get()
        if preset == 'Analýza středisek':
            # fixed preset: rows = stredisko
            self.row_dims = ['stredisko', 'kdo', 'kategorie', 'text']
            self.hierarchy_btn.state(['disabled'])
        elif preset == 'Analýza rozpočtu':
            # fixed preset: rows = kategorie, stredisko
            self.row_dims = ['kategorie', 'stredisko', 'text']
            self.hierarchy_btn.state(['disabled'])
        elif preset == 'Analýza rozpočtu 2':
            # co - text - kdo
            self.row_dims = ['kategorie', 'text', 'kdo']
            self.hierarchy_btn.state(['disabled'])
        else:  # 'Vlastní'
            # allow user to edit hierarchy
            self.hierarchy_btn.state(['!disabled'])
            # keep existing self.row_dims (user may have set earlier)
            if not self.row_dims:
                self.row_dims = ['stredisko']
        # Sanitize na aktuální dostupné dimenze (odstraníme legacy 'co' apod.)
        self.row_dims = [d for d in self.row_dims if d in self.available_dims]
        # load view for new preset
        self.load()

    def _open_hierarchy_dialog(self):
        def _apply(new_dims):
            self.row_dims = [d for d in new_dims if d in self.available_dims]
            self.load()
        open_hierarchy_dialog(self.parent, self.available_dims, self.row_dims, _apply)

    def _map_dim_to_column(self, dim_label: str) -> str:
        """Mapuje UI label na název sloupce v DB."""
        return 'kategorie_id' if dim_label == 'kategorie' else dim_label
