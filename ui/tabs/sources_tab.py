import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as messagebox

from app import database as db

class SourcesTab:
    def __init__(self, tab_frame, app_controller):
        self.app = app_controller
        self.tab_frame = tab_frame
        self.current_view = 0  # 0 pro historické, 1 pro aktuální

        # --- Horní panel s ovládacími prvky ---
        top_frame = ttk.Frame(self.tab_frame)
        top_frame.pack(fill='x', padx=10, pady=5)

        self.toggle_button = ttk.Button(top_frame, text="Přepnout na Aktuální transakce", command=self.toggle_view)
        self.toggle_button.pack(side='left', padx=(0, 10))

        self.import_button = ttk.Button(top_frame, text="Importovat z Excelu...", command=self.start_import)
        self.import_button.pack(side='left', padx=(0, 10))

        self.add_button = ttk.Button(top_frame, text="Přidat záznam...", command=self.add_new_item)
        self.add_button.pack(side='left', padx=(0, 10))

        # UI prvky pro editaci a odstranění (zatím bez logiky)
        self.edit_button = ttk.Button(top_frame, text="Upravit…", command=lambda: messagebox.showinfo("Info", "Editace transakce bude implementována."))
        self.edit_button.pack(side='left', padx=(0, 10))

        self.delete_button = ttk.Button(top_frame, text="Smazat", command=self.delete_selected_item)
        self.delete_button.pack(side='left')

        # --- Treeview pro zobrazení dat ---
        tree_frame = ttk.Frame(self.tab_frame)
        tree_frame.pack(expand=True, fill='both', padx=10, pady=(0, 10))
        
        self.tree = self._create_treeview(tree_frame)
        
        # --- Spodní panel se součtem ---
        bottom_frame = ttk.Frame(self.tab_frame)
        bottom_frame.pack(fill='x', padx=10, pady=5)
        self.total_label = ttk.Label(bottom_frame, text="Celková částka: 0.00 Kč", font=("Arial", 10, "bold"))
        self.total_label.pack(side='right')

        self.tab_frame.bind("<Visibility>", lambda e: self.load_items())

    def _create_treeview(self, parent):
        # Přidáváme 'id' jako skrytý sloupec
        columns = ('id', 'datum', 'doklad', 'firma', 'text', 'castka')
        tree = ttk.Treeview(parent, columns=columns, show='headings', displaycolumns=('datum', 'doklad', 'firma', 'text', 'castka'))
        
        # ID sloupec je skrytý, nastavíme ale jeho heading pro lepší kód
        tree.heading('id', text='ID')
        tree.column('id', width=0, stretch=False)  # Skrytý sloupec
        
        tree.heading('datum', text='Datum')
        tree.heading('doklad', text='Doklad')
        tree.heading('firma', text='Firma')
        tree.heading('text', text='Text')
        tree.heading('castka', text='Částka')

        tree.column('castka', anchor='e')

        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        tree.pack(side="left", fill="both", expand=True)
        
        return tree

    def toggle_view(self):
        """Přepíná mezi historickým (0) a aktuálním (1) pohledem."""
        self.current_view = 1 - self.current_view
        if self.current_view == 0:
            self.toggle_button.config(text="Přepnout na Aktuální transakce")
        else:
            self.toggle_button.config(text="Přepnout na Historické transakce")
        self.load_items()
        self.update_total()

    def load_items(self):
        """Načte položky do Treeview podle aktuálně zvoleného pohledu."""
        for i in self.tree.get_children():
            self.tree.delete(i)
        
        items = db.get_items(self.app.profile_path, self.current_view)
        for item in items:
            # ID, datum, doklad, zdroj, firma, text, madati, dal, castka, ...
            # Vložíme ID jako první hodnotu (skrytý sloupec), pak zobrazované sloupce
            self.tree.insert('', 'end', values=(item[0], item[1], item[2], item[4], item[5], f"{item[8]:,.2f} Kč"))

    def update_total(self):
        """Aktualizuje zobrazenou celkovou částku."""
        total = db.get_total_amount(self.app.profile_path, self.current_view)
        self.total_label.config(text=f"Celková částka: {total:,.2f} Kč")

    def delete_selected_item(self):
        """Smaže vybranou transakci po potvrzení."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Upozornění", "Nejprve vyberte transakci, kterou chcete smazat.")
            return
        
        # Získáme ID z prvního sloupce (skrytého)
        item_data = self.tree.item(selection[0], 'values')
        item_id = int(item_data[0])  # ID je první hodnota
        
        # Zobrazíme detaily pro potvrzení
        item_text = f"Datum: {item_data[1]}\nDoklad: {item_data[2]}\nFirma: {item_data[3]}\nText: {item_data[4]}\nČástka: {item_data[5]}"
        
        result = messagebox.askyesno(
            "Potvrzení smazání", 
            f"Opravdu chcete smazat tuto transakci?\n\n{item_text}"
        )
        
        if result:
            try:
                # Smažeme z databáze
                db.delete_item(self.app.profile_path, item_id)
                
                # Obnovíme zobrazení
                self.load_items()
                self.update_total()
                
                messagebox.showinfo("Úspěch", "Transakce byla úspěšně smazána.")
            except Exception as e:
                messagebox.showerror("Chyba", f"Při mazání transakce došlo k chybě:\n{str(e)}")

    def start_import(self):
        """Zahájí proces importu na základě aktuálního zobrazení."""
        self.app.import_excel(is_current=self.current_view)

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