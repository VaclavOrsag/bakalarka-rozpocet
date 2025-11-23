import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as messagebox

from ui.item_dialog import open_item_dialog

from app import database as db
from app.utils import format_money

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

        self.add_button = ttk.Button(top_frame, text="Přidat záznam...", command=self.open_add_dialog)
        self.add_button.pack(side='left', padx=(0, 10))

        # UI prvky pro editaci a odstranění 
        self.edit_button = ttk.Button(top_frame, text="Upravit…", command=self.open_edit_dialog)
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
        # Přidáváme 'id' jako skrytý sloupec a 'co' sloupec
        columns = ('id', 'datum', 'doklad', 'firma', 'text', 'co', 'castka')
        tree = ttk.Treeview(parent, columns=columns, show='headings', displaycolumns=('datum', 'doklad', 'firma', 'text', 'co', 'castka'))
        
        # ID sloupec je skrytý, nastavíme ale jeho heading pro lepší kód
        tree.heading('id', text='ID')
        tree.column('id', width=0, stretch=False)  # Skrytý sloupec
        
        tree.heading('datum', text='Datum')
        tree.heading('doklad', text='Doklad')
        tree.heading('firma', text='Firma')
        tree.heading('text', text='Text')
        tree.heading('co', text='Co')
        tree.heading('castka', text='Částka')

        tree.column('castka', anchor='e')
        
        # Konfigurace tagu pro neúplné řádky (červené pozadí)
        tree.tag_configure("incomplete", background="#ffcccc", foreground="#cc0000")

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
            # Struktura: (id, datum, doklad, zdroj, firma, text, madati, dal, castka, cin, cislo, co, kdo, stredisko, is_current, kategorie_id)
            
            # Formátování částky - zobrazujeme se znaménkem (výdaje záporné, příjmy kladné)
            castka_formatted = format_money(item[8], use_abs=False) if item[8] != 0 else "0,00 Kč"
            
            # Data pro zobrazení včetně sloupce "Co"
            display_values = (
                item[0],           # ID (skryté)
                item[1],           # Datum
                item[2],           # Doklad  
                item[4],           # Firma
                item[5],           # Text
                item[11] or "",    # Co
                castka_formatted   # Částka
            )
            
            # Detekce neúplných dat
            is_incomplete = (
                not item[11] or               # Chybí "Co"
                str(item[11]).strip() == "" or  # "Co" je prázdné
                item[8] == 0                  # Částka je nula
            )
            
            # Vložení řádku s příslušným tagem
            tag = "incomplete" if is_incomplete else ""
            self.tree.insert('', 'end', values=display_values, tags=(tag,) if tag else ())

    def update_total(self):
        """Aktualizuje zobrazenou celkovou částku."""
        total = db.get_total_amount(self.app.profile_path, self.current_view)
        self.total_label.config(text=f"Celková částka: {format_money(total, use_abs=False)}")

    def delete_selected_item(self):
        """Smaže vybranou transakci po potvrzení."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Upozornění", "Nejprve vyberte transakci, kterou chcete smazat.")
            return
        
        # Získáme ID z prvního sloupce (skrytého)
        item_data = self.tree.item(selection[0], 'values')
        item_id = int(item_data[0])  # ID je první hodnota
        
        # Zobrazíme detaily pro potvrzení - upraveno pro nový sloupec "Co"
        item_text = f"Datum: {item_data[1]}\nDoklad: {item_data[2]}\nFirma: {item_data[3]}\nText: {item_data[4]}\nCo: {item_data[5]}\nČástka: {item_data[6]}"
        
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
                
                # Invalidace cache pro dashboard
                if hasattr(self.app, 'dashboard_ui'):
                    self.app.dashboard_ui.invalidate_cache()
                
                messagebox.showinfo("Úspěch", "Transakce byla úspěšně smazána.")
            except Exception as e:
                messagebox.showerror("Chyba", f"Při mazání transakce došlo k chybě:\n{str(e)}")

    def start_import(self):
        """Zahájí proces importu na základě aktuálního zobrazení."""
        self.app.import_excel(is_current=self.current_view)


    def open_add_dialog(self):
        """Otevře dialog pro přidání nové transakce."""
        open_item_dialog(self, mode="add")
        
    def open_edit_dialog(self):
        """Otevře dialog pro editaci vybrané transakce."""
        # Zkontroluj výběr
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Výběr transakce", 
                                 "Nejprve vyberte transakci, kterou chcete upravit.")
            return
        
        # Získej ID z treeview (první sloupec je skrytý ID)
        selected_item = selection[0]
        values = self.tree.item(selected_item)['values']
        item_id = values[0]  # ID je první hodnota
        
        # Načti data z databáze
        item_data = db.get_item_by_id(self.app.profile_path, item_id)
        if not item_data:
            messagebox.showerror("Chyba", "Nepodařilo se načíst data transakce.")
            return
            
        # Otevři edit dialog
        open_item_dialog(self, mode="edit", item_data=item_data)