import tkinter as tk
from tkinter import ttk, messagebox, filedialog

class AnalysisTab:
    """Analysis tab UI scaffold.

    This provides filter controls, a Refresh button, a Treeview for
    hierarchical pivot-like output and Export/Drilldown stubs. Data
    loading is left as a simple placeholder; later we'll hook it
    to a DB helper (get_pivot_rows) to populate the Treeview.
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
        self.preset_cb = ttk.Combobox(ctrl, textvariable=self.preset_var, values=['Analýza středisek', 'Analýza rozpočtu', 'Vlastní'], state='readonly', width=20)
        self.preset_cb.pack(side='left', padx=6)

        ttk.Label(ctrl, text="Řádky:").pack(side='left', padx=(12,0))
        self.rows_var = tk.StringVar(value='stredisko')
        # limited set of dims; MVP will support single or multi-level through comma
        dims = ['co','stredisko','text','kdo','firma','kategorie_id']
        self.rows_cb = ttk.Combobox(ctrl, textvariable=self.rows_var, values=dims, width=20)
        self.rows_cb.pack(side='left', padx=6)

        ttk.Label(ctrl, text="is_current:").pack(side='left', padx=(12,0))
        self.current_var = tk.StringVar(value='Obě')
        self.current_cb = ttk.Combobox(ctrl, textvariable=self.current_var, values=['Obě','Aktuální','Historické'], state='readonly', width=12)
        self.current_cb.pack(side='left', padx=6)

        ttk.Label(ctrl, text="Hledat:").pack(side='left', padx=(12,0))
        self.search_var = tk.StringVar()
        ttk.Entry(ctrl, textvariable=self.search_var, width=20).pack(side='left', padx=6)

        ttk.Button(ctrl, text='Obnovit', command=self.refresh).pack(side='right')
        ttk.Button(ctrl, text='Export CSV', command=self.export_csv).pack(side='right', padx=6)

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

        # Bind double-click for drilldown
        self.tree.bind('<Double-1>', self._on_double_click)

        # Initial placeholder
        self._show_placeholder()

    def _show_placeholder(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        self.tree.insert('', 'end', text='Nejsou načtena data', values=('',''))

    def refresh(self):
        """Refresh view: currently placeholder. Later will call DB helper to load pivot rows."""
        # For now show a message and placeholder.
        # Later: call e.g. app.database.items_db.get_pivot_rows(...) and render.
        messagebox.showinfo('Analýza', 'Funkce obnovit ještě není napojena na DB helper. Toto je stub UI.')
        self._show_placeholder()

    def export_csv(self):
        filepath = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV','*.csv')])
        if not filepath:
            return
        # Placeholder export: export current Treeview rows
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                # header
                f.write('row;total\n')
                for item in self.tree.get_children():
                    row = self.tree.item(item)['text']
                    total = self.tree.item(item)['values'][0] if self.tree.item(item)['values'] else ''
                    f.write(f'"{row}";{total}\n')
            messagebox.showinfo('Export', 'Export dokončen')
        except Exception as e:
            messagebox.showerror('Export', f'Chyba při exportu: {e}')

    def _on_double_click(self, event):
        item = self.tree.focus()
        if not item:
            return
        row_text = self.tree.item(item)['text']
        messagebox.showinfo('Drill-down', f'Drill-down pro: {row_text}\n(Tato funkce bude později otevřít seznam transakcí.)')
