import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as messagebox

from ui.add_window import add_new_item as show_add_dialog

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

        self.add_button = ttk.Button(top_frame, text="Přidat záznam...", command=self.open_add_dialog)
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


    def open_add_dialog(self):
        """Otevře dialog pro přidání nové transakce."""
        show_add_dialog(self)