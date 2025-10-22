import tkinter as tk
from app.main_app import App
from ui.welcome_window import WelcomeWindow
import app.database as db

if __name__ == "__main__":
    # Vytvoříme hlavní, ale zatím skryté okno
    root = tk.Tk()
    root.withdraw() # Skryjeme hlavní okno

    # Zobrazíme uvítací okno a počkáme, až ho uživatel zavře
    welcome = WelcomeWindow(root)
    root.wait_window(welcome.top) # Tento příkaz pozastaví kód, dokud se okno 'welcome.top' nezavře

    # Získáme cestu k profilu, kterou si uživatel vybral
    profile_path = welcome.selected_profile_path

    # Pokud si uživatel vybral profil, spustíme hlavní aplikaci
    if profile_path:
        # Inicializujeme databázi pro nově vytvořený profil
        db.init_db(profile_path)
        
        # Zobrazíme hlavní okno aplikace
        root.deiconify() 
        app = App(root, profile_path) # Předáme cestu k profilu hlavní aplikaci
        root.mainloop()
    else:
        # Pokud si uživatel nevybral žádný profil (zavřel okno), ukončíme aplikaci
        root.destroy()