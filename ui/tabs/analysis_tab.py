# ...existing code...
import tkinter as tk
from tkinter import ttk, messagebox

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
            values=['Analýza středisek', 'Analýza rozpočtu', 'Vlastní'],
            state='readonly',
            width=20
        )
        self.preset_cb.pack(side='left', padx=6)
        # bind to handler that sets defaults and enables/disables hierarchy editing
        self.preset_cb.bind('<<ComboboxSelected>>', self._on_preset_change)

        ttk.Label(ctrl, text="Řádky:").pack(side='left', padx=(12,0))
        # hierarchy selection via dialog (prevents typos)
        self.available_dims = ['co','stredisko','text','kdo','firma','kategorie_id']
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
        self.current_cb.bind('<<ComboboxSelected>>', lambda e: self.refresh())

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
        self._on_preset_change()  # set initial state and refresh

    def _show_placeholder(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        self.tree.insert('', 'end', text='Nejsou načtena data', values=('',))

    def refresh(self):
        """Refresh view: placeholder for DB hook.

        Called automatically on control changes. Currently shows placeholder.
        Later: call analysis_db.get_pivot_rows(...) and render nested hierarchy.
        """
        # We intentionally avoid message boxes on auto-refresh; show placeholder silently.
        # (Later: call DB helper with self.row_dims and current selection and render results)
        self._show_placeholder()

    def _on_preset_change(self, event=None):
        """Apply preset defaults and enable hierarchy editing only for 'Vlastní'."""
        preset = self.preset_var.get()
        if preset == 'Analýza středisek':
            # fixed preset: rows = stredisko
            self.row_dims = ['stredisko']
            self.hierarchy_btn.state(['disabled'])
        elif preset == 'Analýza rozpočtu':
            # fixed preset: rows = co, stredisko (example)
            self.row_dims = ['co', 'stredisko']
            self.hierarchy_btn.state(['disabled'])
        else:  # 'Vlastní'
            # allow user to edit hierarchy
            self.hierarchy_btn.state(['!disabled'])
            # keep existing self.row_dims (user may have set earlier)
            if not self.row_dims:
                self.row_dims = ['stredisko']
        # refresh view for new preset
        self.refresh()

    def _open_hierarchy_dialog(self):
        """Open modal to edit ordered list of row dimensions (available -> selected)."""
        # only allow editing when preset == 'Vlastní' (extra safety)
        if self.preset_var.get() != 'Vlastní':
            messagebox.showinfo("Upozornění", "Hierarchii lze upravovat pouze v režimu 'Vlastní'.")
            return

        dlg = tk.Toplevel(self.parent)
        dlg.title("Upravit hierarchii řádků")
        dlg.transient(self.parent)
        dlg.grab_set()

        left = ttk.Frame(dlg, padding=6)
        left.pack(side='left', fill='both', expand=True)
        ttk.Label(left, text="Dostupné pole").pack()
        avail_lb = tk.Listbox(left, height=8, exportselection=False)
        for it in self.available_dims:
            avail_lb.insert('end', it)
        avail_lb.pack(fill='both', expand=True, padx=4, pady=4)

        mid = ttk.Frame(dlg, padding=6)
        mid.pack(side='left', fill='y')

        def add_one():
            sel = avail_lb.curselection()
            if not sel: return
            val = avail_lb.get(sel[0])
            if val in selected_lb.get(0, 'end'): return
            selected_lb.insert('end', val)

        def remove_one():
            sel = selected_lb.curselection()
            if not sel: return
            selected_lb.delete(sel[0])

        def move_up():
            sel = selected_lb.curselection()
            if not sel: return
            i = sel[0]
            if i == 0: return
            v = selected_lb.get(i)
            selected_lb.delete(i)
            selected_lb.insert(i-1, v)
            selected_lb.selection_set(i-1)

        def move_down():
            sel = selected_lb.curselection()
            if not sel: return
            i = sel[0]
            if i >= selected_lb.size()-1: return
            v = selected_lb.get(i)
            selected_lb.delete(i)
            selected_lb.insert(i+1, v)
            selected_lb.selection_set(i+1)

        ttk.Button(mid, text="→", width=4, command=add_one).pack(pady=4)
        ttk.Button(mid, text="←", width=4, command=remove_one).pack(pady=4)
        ttk.Button(mid, text="▲", width=4, command=move_up).pack(pady=4)
        ttk.Button(mid, text="▼", width=4, command=move_down).pack(pady=4)

        right = ttk.Frame(dlg, padding=6)
        right.pack(side='left', fill='both', expand=True)
        ttk.Label(right, text="Vybraná hierarchie (pořadí)").pack()
        selected_lb = tk.Listbox(right, height=8, exportselection=False)
        for it in self.row_dims:
            selected_lb.insert('end', it)
        selected_lb.pack(fill='both', expand=True, padx=4, pady=4)

        btns = ttk.Frame(dlg, padding=6)
        btns.pack(side='bottom', fill='x')

        def on_ok():
            vals = list(selected_lb.get(0, 'end'))
            MAX_LEVELS = 5
            if len(vals) > MAX_LEVELS:
                messagebox.showwarning("Omezení", f"Maximálně {MAX_LEVELS} úrovní povoleno.")
                return
            if not vals:
                messagebox.showwarning("Vyberte pole", "Musíte vybrat alespoň jedno pole pro řádky.")
                return
            self.row_dims = vals
            dlg.destroy()
            self.refresh()

        def on_cancel():
            dlg.destroy()

        ttk.Button(btns, text="OK", command=on_ok).pack(side='right', padx=6)
        ttk.Button(btns, text="Zrušit", command=on_cancel).pack(side='right')

        dlg.wait_window()

    def _on_double_click(self, event):
        # placeholder kept but not bound; drill-down will be implemented later
        pass
