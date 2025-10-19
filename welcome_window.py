import tkinter as tk
from tkinter import filedialog
import os

class WelcomeWindow:
    def __init__(self, root):
        # Vytvoříme Toplevel okno, které se zobrazí nad hlavním (skrytým) oknem
        self.top = tk.Toplevel(root)
        self.top.title("Výběr profilu")
        
        self.selected_profile = None # Zde si uložíme cestu k vybranému profilu

        # Vytvoříme rám pro lepší vzhled
        frame = tk.Frame(self.top, padx=20, pady=20)
        frame.pack()

        tk.Label(frame, text="Vyberte existující profil nebo vytvořte nový:", font=("Arial", 12)).pack(pady=10)

        # Listbox pro zobrazení existujících profilů
        self.profile_listbox = tk.Listbox(frame, width=50, height=10)
        self.profile_listbox.pack(pady=5)

        # Načteme existující profily
        self.load_profiles()

        # Rám pro tlačítka
        button_frame = tk.Frame(frame)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Otevřít vybraný", command=self.open_profile).pack(side="left", padx=10)
        tk.Button(button_frame, text="Vytvořit nový...", command=self.create_profile).pack(side="left", padx=10)

    def load_profiles(self):
        """Prohledá aktuální adresář a najde všechny soubory s koncovkou .db"""
        self.profile_listbox.delete(0, tk.END)
        try:
            # os.listdir('.') vrátí seznam všech souborů v aktuálním adresáři
            files = [f for f in os.listdir('.') if f.endswith('.db')]
            for file in files:
                self.profile_listbox.insert(tk.END, file)
        except Exception as e:
            print(f"Chyba při načítání profilů: {e}")

    def open_profile(self):
        """Získá vybraný profil a zavře okno."""
        selection = self.profile_listbox.curselection()
        if not selection:
            return
        self.selected_profile = self.profile_listbox.get(selection[0])
        self.top.destroy() # Zavřeme jen toto okno, ne celou aplikaci

    def create_profile(self):
        """Otevře dialog pro uložení nového profilu."""
        filepath = filedialog.asksaveasfilename(
            title="Vytvořit nový profil",
            defaultextension=".db",
            filetypes=[("Databázové soubory", "*.db")]
        )
        if filepath:
            self.selected_profile = filepath
            self.top.destroy()