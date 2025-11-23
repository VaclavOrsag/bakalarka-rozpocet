"""
Unified dialog pro přidání/editaci transakcí.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from app import database as db


def open_item_dialog(parent_tab, mode="add", item_data=None):
    """
    Otevře unified dialog pro transakce.
    
    Args:
        parent_tab: Sources tab instance
        mode: "add" nebo "edit" 
        item_data: Pro edit - tuple z databáze (id, datum, doklad, ...)
    """
    
    # Vytvoření okna
    win = tk.Toplevel(parent_tab.tab_frame)
    if mode == "edit":
        win.title("Upravit transakci")
    else:
        win.title("Přidat transakci")
    win.transient(parent_tab.tab_frame)
    win.grab_set()

    # Helper funkce pro řádky
    def add_row(label, width=16):
        frm = ttk.Frame(win)
        frm.pack(fill='x', padx=10, pady=4)
        ttk.Label(frm, text=label, width=18, anchor='w').pack(side='left')
        var = tk.StringVar()
        ent = ttk.Entry(frm, textvariable=var, width=width)
        ent.pack(side='left', fill='x', expand=True)
        return ent

    # Vytvoření polí
    v_datum = add_row("Datum (YYYY-MM-DD)")
    v_doklad = add_row("Doklad")
    v_zdroj = add_row("Zdroj")
    v_firma = add_row("Firma")
    v_text = add_row("Text", width=40)
    v_castka = add_row("Částka (+/-)")
    v_cin = add_row("Čin")
    v_cislo = add_row("Číslo")
    v_co = add_row("Co")
    v_kdo = add_row("Kdo")
    v_stred = add_row("Středisko")

    # Info label
    info = ttk.Label(win, text="Má dáti / Dal se nastaví automaticky podle znaménka částky.", foreground="#555")
    info.pack(fill='x', padx=10, pady=(2,6))

    # NOVÉ: Předvyplnění pro edit mode
    if mode == "edit" and item_data:
        # item_data je tuple: (id, datum, doklad, zdroj, firma, text, madati, dal, castka, cin, cislo, co, kdo, stredisko, kategorie_id, is_current)
        v_datum.insert(0, str(item_data[1]) if item_data[1] else "")
        v_doklad.insert(0, str(item_data[2]) if item_data[2] else "")
        v_zdroj.insert(0, str(item_data[3]) if item_data[3] else "")
        v_firma.insert(0, str(item_data[4]) if item_data[4] else "")
        v_text.insert(0, str(item_data[5]) if item_data[5] else "")
        v_castka.insert(0, str(item_data[8]) if item_data[8] else "")  # castka
        v_cin.insert(0, str(item_data[9]) if item_data[9] else "")    # cin
        v_cislo.insert(0, str(item_data[10]) if item_data[10] else "") # cislo
        v_co.insert(0, str(item_data[11]) if item_data[11] else "")   # co
        v_kdo.insert(0, str(item_data[12]) if item_data[12] else "")  # kdo
        v_stred.insert(0, str(item_data[13]) if item_data[13] else "") # stredisko

    # Tlačítka
    btns = ttk.Frame(win)
    btns.pack(fill='x', padx=10, pady=(0,10))

    # Helper funkce
    def _valid_date(s: str) -> bool:
        import re
        import datetime
        
        if not s.strip():
            return True  # Prázdné datum je OK
        
        if re.fullmatch(r"\d{4}-\d{1,2}-\d{1,2}", s.strip()):
            try:
                datetime.datetime.strptime(s.strip(), "%Y-%m-%d")
                return True
            except ValueError:
                return False
        return False

    def _parse_float(s: str):
        if s is None: return None
        s = s.strip().replace('Kč','').replace(' ','').replace(',','.')
        if not s: return None
        try:
            return float(s)
        except ValueError:
            return None

    def _parse_int(s: str):
        if s is None: return None
        s = s.strip()
        if not s: return None
        try:
            return int(s)
        except ValueError:
            return None

    # Hlavní save funkce
    def save():
        # Validace datumu
        raw_datum = v_datum.get().strip()
        if raw_datum and not _valid_date(raw_datum):
            messagebox.showerror("Chybný formát", "Datum musí být ve formátu YYYY-MM-DD (např. 2024-03-15).")
            return
        
        datum = raw_datum
        
        # Validace částky
        amt = _parse_float(v_castka.get())
        if amt is None:
            messagebox.showerror("Chybná částka", "Zadejte platnou číselnou hodnotu.")
            return
        amt = round(amt, 2)
        
        # Odvození madati/dal
        if amt < 0:
            madati = round(abs(amt), 2); dal = 0.0
        elif amt > 0:
            dal = round(abs(amt), 2); madati = 0.0
        else:
            madati = dal = 0.0
            
        # Parsování polí
        cin = _parse_int(v_cin.get())
        cislo = _parse_int(v_cislo.get())
        doklad = v_doklad.get().strip()
        zdroj = v_zdroj.get().strip()
        firma = v_firma.get().strip()
        text = v_text.get().strip()
        co = v_co.get().strip()
        kdo = v_kdo.get().strip()
        stredisko = v_stred.get().strip()
        
        # Validace Co
        if co:
            custom_categories = db.get_custom_category_names(parent_tab.app.profile_path)
            if co in custom_categories:
                messagebox.showerror("Chybné pole Co", f"'{co}' je název custom kategorie (kontejneru). Použijte prosím jinou hodnotu.")
                return
        
        try:
            if mode == "add":
                # Přidání nové transakce
                db.add_item(
                    parent_tab.app.profile_path,
                    datum, doklad, zdroj, firma, text,
                    madati, dal, amt, cin, cislo, co, kdo, stredisko,
                    parent_tab.current_view
                )
            else:
                # NOVÉ: Editace existující transakce
                item_id = item_data[0]  # První prvek je ID
                db.update_item(
                    parent_tab.app.profile_path,
                    item_id, datum, doklad, zdroj, firma, text,
                    madati, dal, amt, cin, cislo, co, kdo, stredisko
                )
                
        except Exception as e:
            messagebox.showerror("Chyba", f"Transakci se nepodařilo uložit:\n{e}")
            return
            
        # Zavření a refresh
        win.destroy()
        parent_tab.load_items()

        # Po operaci refresh
        parent_tab.app.update_tabs_visibility()
        if hasattr(parent_tab.app, 'accounting_ui'):
            parent_tab.app.accounting_ui.refresh_data()
        if hasattr(parent_tab.app, 'budget_ui'):
            parent_tab.app.budget_ui.load_data()
        if hasattr(parent_tab.app, 'analysis_tab'):
            parent_tab.app.analysis_tab.load()
        
        # Invalidace cache pro dashboard a stats_window
        if hasattr(parent_tab.app, 'dashboard_ui'):
            parent_tab.app.dashboard_ui.invalidate_cache()

    def cancel():
        win.destroy()

    # Tlačítka
    ttk.Button(btns, text="Uložit", command=save).pack(side='right')
    ttk.Button(btns, text="Zrušit", command=cancel).pack(side='right', padx=(6,0))

    v_datum.focus_set()
