import tkinter as tk
from tkinter import ttk, messagebox
from app import database as db


def add_new_item(self):
        """Otevře dialog pro přidání nové transakce (items)."""
        win = tk.Toplevel(self.tab_frame)
        win.title("Přidat transakci")
        win.transient(self.tab_frame)
        win.grab_set()

        def add_row(label, width=16):
            frm = ttk.Frame(win)
            frm.pack(fill='x', padx=10, pady=4)
            ttk.Label(frm, text=label, width=18, anchor='w').pack(side='left')
            var = tk.StringVar()
            ent = ttk.Entry(frm, textvariable=var, width=width)
            ent.pack(side='left', fill='x', expand=True)
            return ent

        v_datum = add_row("Datum (DD.MM.YYYY)")
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

        info = ttk.Label(win, text="Má dáti / Dal se nastaví automaticky podle znaménka částky.", foreground="#555")
        info.pack(fill='x', padx=10, pady=(2,6))

        btns = ttk.Frame(win)
        btns.pack(fill='x', padx=10, pady=(0,10))

        def _valid_date(s: str) -> bool:
            import re
            return bool(re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", s))

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

        def save():
            datum = v_datum.get().strip()
            if datum and not _valid_date(datum):
                messagebox.showerror("Chybný formát", "Datum musí být ve formátu DD.MM.YYYY.")
                return
            amt = _parse_float(v_castka.get())
            if amt is None:
                messagebox.showerror("Chybná částka", "Zadejte platnou číselnou hodnotu.")
                return
            amt = round(amt, 2)
            # Odvození madati/dal podle znaménka
            if amt < 0:
                madati = round(abs(amt), 2); dal = 0.0
            elif amt > 0:
                dal = round(abs(amt), 2); madati = 0.0
            else:
                madati = dal = 0.0
            cin = _parse_int(v_cin.get())
            cislo = _parse_int(v_cislo.get())
            doklad = v_doklad.get().strip()
            zdroj = v_zdroj.get().strip()
            firma = v_firma.get().strip()
            text = v_text.get().strip()
            co = v_co.get().strip()
            kdo = v_kdo.get().strip()
            stredisko = v_stred.get().strip()
            try:
                db.add_item(
                    self.app.profile_path,
                    datum,
                    doklad,
                    zdroj,
                    firma,
                    text,
                    madati,
                    dal,
                    amt,
                    cin,
                    cislo,
                    co,
                    kdo,
                    stredisko,
                    self.current_view
                )
            except Exception as e:
                messagebox.showerror("Chyba", f"Transakci se nepodařilo uložit:\n{e}")
                return
            win.destroy()
            self.load_items()
            self.update_total()

            # Po importu musíme zkontrolovat, zda se mají zobrazit nové záložky
            self.app.update_tabs_visibility()
            if hasattr(self.app, 'accounting_ui'):
                self.app.accounting_ui.refresh_data()
            if hasattr(self.app, 'budget_ui'):
                self.app.budget_ui.load_data()
            if hasattr(self.app, 'analysis_tab'):
                self.app.analysis_tab.load()  # pokud chceš ihned promítnout do analýzy

        def cancel():
            win.destroy()

        ttk.Button(btns, text="Uložit", command=save).pack(side='right')
        ttk.Button(btns, text="Zrušit", command=cancel).pack(side='right', padx=(6,0))

        v_datum.focus_set()