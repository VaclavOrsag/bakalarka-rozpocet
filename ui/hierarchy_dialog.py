import tkinter as tk
from tkinter import ttk, messagebox

MAX_LEVELS = 5

def open_hierarchy_dialog(parent, available_dims, current_dims, on_result):
    """Otevře dialog pro úpravu hierarchie. on_result(list[str]) zavolá po OK."""
    dlg = tk.Toplevel(parent)
    dlg.title("Upravit hierarchii řádků")
    dlg.transient(parent)
    dlg.grab_set()

    left = ttk.Frame(dlg, padding=6)
    left.pack(side='left', fill='both', expand=True)
    ttk.Label(left, text="Dostupné pole").pack()
    avail_lb = tk.Listbox(left, height=8, exportselection=False)
    for it in available_dims:
        avail_lb.insert('end', it)
    avail_lb.pack(fill='both', expand=True, padx=4, pady=4)

    mid = ttk.Frame(dlg, padding=6)
    mid.pack(side='left', fill='y')

    right = ttk.Frame(dlg, padding=6)
    right.pack(side='left', fill='both', expand=True)
    ttk.Label(right, text="Vybraná hierarchie (pořadí)").pack()
    selected_lb = tk.Listbox(right, height=8, exportselection=False)
    for it in current_dims:
        selected_lb.insert('end', it)
    selected_lb.pack(fill='both', expand=True, padx=4, pady=4)

    def add_one():
        sel = avail_lb.curselection()
        if not sel:
            return
        val = avail_lb.get(sel[0])
        if val in selected_lb.get(0, 'end'):
            return
        selected_lb.insert('end', val)

    def remove_one():
        sel = selected_lb.curselection()
        if not sel:
            return
        selected_lb.delete(sel[0])

    def move(up):
        sel = selected_lb.curselection()
        if not sel:
            return
        i = sel[0]
        if up and i == 0:
            return
        if not up and i >= selected_lb.size() - 1:
            return
        v = selected_lb.get(i)
        ni = i - 1 if up else i + 1
        selected_lb.delete(i)
        selected_lb.insert(ni, v)
        selected_lb.selection_set(ni)

    ttk.Button(mid, text="→", width=4, command=add_one).pack(pady=4)
    ttk.Button(mid, text="←", width=4, command=remove_one).pack(pady=4)
    ttk.Button(mid, text="▲", width=4, command=lambda: move(True)).pack(pady=4)
    ttk.Button(mid, text="▼", width=4, command=lambda: move(False)).pack(pady=4)

    btns = ttk.Frame(dlg, padding=6)
    btns.pack(side='bottom', fill='x')

    def on_ok():
        vals = list(selected_lb.get(0, 'end'))
        if len(vals) > MAX_LEVELS:
            messagebox.showwarning("Omezení", f"Maximálně {MAX_LEVELS} úrovní povoleno.")
            return
        if not vals:
            messagebox.showwarning("Vyberte pole", "Musíte vybrat alespoň jedno pole pro řádky.")
            return
        dlg.destroy()
        on_result(vals)

    def on_cancel():
        dlg.destroy()

    ttk.Button(btns, text="OK", command=on_ok).pack(side='right', padx=6)
    ttk.Button(btns, text="Zrušit", command=on_cancel).pack(side='right')

    dlg.wait_window()