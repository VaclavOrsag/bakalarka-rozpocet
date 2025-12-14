"""
Modul pro dialogové okno přidání nebo editace transakce.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Tuple, Any
import re
import datetime
from app import database as db

class ItemDialog:
    """
    Dialogové okno pro přidání nebo úpravu transakce.
    """

    def __init__(self, parent_tab: Any, mode: str = "add", item_data: Optional[Tuple] = None) -> None:
        """
        Inicializuje dialog.

        Args:
            parent_tab: Instance záložky (SourcesTab), která dialog volá.
            mode: Režim dialogu ("add" nebo "edit").
            item_data: Data transakce pro editaci (tuple z databáze).
        """
        self.parent_tab = parent_tab
        self.mode = mode
        self.item_data = item_data
        
        # Vytvoření okna
        self.window = tk.Toplevel(parent_tab.tab_frame)
        if mode == "edit":
            self.window.title("Upravit transakci")
        else:
            self.window.title("Přidat transakci")
        self.window.transient(parent_tab.tab_frame)
        self.window.grab_set()

        self._create_layout()
        
        # Předvyplnění dat
        if mode == "edit" and item_data:
            self._fill_data(item_data)

    def _create_layout(self) -> None:
        """Vytvoří rozložení formuláře."""
        # Vytvoření polí
        self.v_datum = self._add_row("Datum (YYYY-MM-DD)", required=True)
        self.v_doklad = self._add_row("Doklad")
        self.v_zdroj = self._add_row("Zdroj")
        self.v_firma = self._add_row("Firma")
        self.v_text = self._add_row("Text", width=40)
        self.v_castka = self._add_row("Částka (+/-)", required=True)
        self.v_cin = self._add_row("Čin")
        self.v_cislo = self._add_row("Číslo")
        self.v_co = self._add_row("Co", required=True)
        self.v_kdo = self._add_row("Kdo")
        self.v_stred = self._add_row("Středisko")

        # Info labely
        info_req = ttk.Label(self.window, text="Položky označené * jsou povinné.", foreground="#555", font=("Arial", 8, "italic"))
        info_req.pack(fill='x', padx=10, pady=(2,0))

        info = ttk.Label(self.window, text="Má dáti / Dal se nastaví automaticky podle znaménka částky.", foreground="#555")
        info.pack(fill='x', padx=10, pady=(2,6))

        # Tlačítka
        btns = ttk.Frame(self.window)
        btns.pack(fill='x', padx=10, pady=(0,10))

        ttk.Button(btns, text="Uložit", command=self._save).pack(side='right')
        ttk.Button(btns, text="Zrušit", command=self._cancel).pack(side='right', padx=(6,0))
        
        # Focus na první pole
        self.v_datum.focus_set()

    def _add_row(self, label: str, width: int = 16, required: bool = False) -> ttk.Entry:
        """
        Přidá řádek s popiskem a vstupním polem.
        
        Args:
            label: Text popisku.
            width: Šířka vstupního pole.
            required: Zda je pole povinné (přidá hvězdičku).
            
        Returns:
            Vytvořený widget Entry.
        """
        frm = ttk.Frame(self.window)
        frm.pack(fill='x', padx=10, pady=4)
        
        text = label + (" *" if required else "")
        # Zvětšíme width labelu z 18 na 22, aby se vešlo i nejdelší datum s hvězdičkou a zarovnání zůstalo
        ttk.Label(frm, text=text, width=22, anchor='w').pack(side='left')
        
        var = tk.StringVar()
        ent = ttk.Entry(frm, textvariable=var, width=width)
        ent.pack(side='left', fill='x', expand=True)
        return ent

    def _fill_data(self, item_data: Tuple) -> None:
        """
        Vyplní formulář daty pro editaci.
        
        Args:
            item_data: Tuple s daty transakce.
        """
        # item_data je tuple: (id, datum, doklad, zdroj, firma, text, madati, dal, castka, cin, cislo, co, kdo, stredisko, kategorie_id, is_current)
        self.v_datum.insert(0, str(item_data[1]) if item_data[1] else "")
        self.v_doklad.insert(0, str(item_data[2]) if item_data[2] else "")
        self.v_zdroj.insert(0, str(item_data[3]) if item_data[3] else "")
        self.v_firma.insert(0, str(item_data[4]) if item_data[4] else "")
        self.v_text.insert(0, str(item_data[5]) if item_data[5] else "")
        self.v_castka.insert(0, str(item_data[8]) if item_data[8] else "")  # castka
        self.v_cin.insert(0, str(item_data[9]) if item_data[9] else "")    # cin
        self.v_cislo.insert(0, str(item_data[10]) if item_data[10] else "") # cislo
        self.v_co.insert(0, str(item_data[11]) if item_data[11] else "")   # co
        self.v_kdo.insert(0, str(item_data[12]) if item_data[12] else "")  # kdo
        self.v_stred.insert(0, str(item_data[13]) if item_data[13] else "") # stredisko

    def _valid_date(self, s: str) -> bool:
        """Ověří formát data YYYY-MM-DD."""
        if not s.strip():
            return True  # Prázdné datum je OK
        
        # Validace formátu: přesně YYYY-MM-DD (s nulovými paddingem)
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s.strip()):
            try:
                datetime.datetime.strptime(s.strip(), "%Y-%m-%d")
                return True
            except ValueError:
                return False
        return False

    def _parse_float(self, s: str) -> Optional[float]:
        """Převede řetězec na float."""
        if s is None: return None
        s = s.strip().replace('Kč','').replace(' ','').replace(',','.')
        if not s: return None
        try:
            return float(s)
        except ValueError:
            return None

    def _parse_int(self, s: str) -> Optional[int]:
        """Převede řetězec na int."""
        if s is None: return None
        s = s.strip()
        if not s: return None
        try:
            return int(s)
        except ValueError:
            return None

    def _save(self) -> None:
        """Uloží transakci do databáze."""
        # Validace datumu
        raw_datum = self.v_datum.get().strip()
        if raw_datum and not self._valid_date(raw_datum):
            messagebox.showerror("Chybný formát", "Datum musí být ve formátu YYYY-MM-DD (např. 2024-03-15).")
            return
        
        datum = raw_datum
        
        # Validace částky
        amt = self._parse_float(self.v_castka.get())
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
        cin = self._parse_int(self.v_cin.get())
        cislo = self._parse_int(self.v_cislo.get())
        doklad = self.v_doklad.get().strip()
        zdroj = self.v_zdroj.get().strip()
        firma = self.v_firma.get().strip()
        text = self.v_text.get().strip()
        co = self.v_co.get().strip()
        kdo = self.v_kdo.get().strip()
        stredisko = self.v_stred.get().strip()
        
        # Validace Co
        if co:
            custom_categories = db.get_custom_category_names(self.parent_tab.app.profile_path)
            if co in custom_categories:
                messagebox.showerror("Chybné pole Co", f"'{co}' je název custom kategorie (kontejneru). Použijte prosím jinou hodnotu.")
                return
        
        try:
            if self.mode == "add":
                # Přidání nové transakce
                db.add_item(
                    self.parent_tab.app.profile_path,
                    datum, doklad, zdroj, firma, text,
                    madati, dal, amt, cin, cislo, co, kdo, stredisko,
                    self.parent_tab.current_view
                )
            else:
                # Editace existující transakce
                if self.item_data:
                    item_id = self.item_data[0]  # První prvek je ID
                    db.update_item(
                        self.parent_tab.app.profile_path,
                        item_id, datum, doklad, zdroj, firma, text,
                        madati, dal, amt, cin, cislo, co, kdo, stredisko
                    )
                
        except Exception as e:
            messagebox.showerror("Chyba", f"Transakci se nepodařilo uložit:\n{e}")
            return
            
        # Zavření a refresh
        self.window.destroy()
        self.parent_tab.load_items()

        # Po operaci refresh
        self.parent_tab.app.update_tabs_visibility()
        if hasattr(self.parent_tab.app, 'accounting_ui'):
            self.parent_tab.app.accounting_ui.refresh_data()
        if hasattr(self.parent_tab.app, 'budget_ui'):
            self.parent_tab.app.budget_ui.load_data()
        if hasattr(self.parent_tab.app, 'analysis_tab'):
            self.parent_tab.app.analysis_tab.load()
        
        # Invalidace cache pro dashboard a stats_window
        if hasattr(self.parent_tab.app, 'dashboard_ui'):
            self.parent_tab.app.dashboard_ui.invalidate_cache()

    def _cancel(self) -> None:
        """Zruší akci a zavře okno."""
        self.window.destroy()

def open_item_dialog(parent_tab: Any, mode: str = "add", item_data: Optional[Tuple] = None) -> None:
    """
    Otevře unified dialog pro transakce.
    
    Args:
        parent_tab: Instance záložky (SourcesTab).
        mode: "add" nebo "edit".
        item_data: Pro edit - tuple z databáze (id, datum, doklad, ...).
    """
    dialog = ItemDialog(parent_tab, mode, item_data)
    dialog.window.wait_window()
