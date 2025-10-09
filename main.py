import tkinter as tk
# Z našeho souboru app.py importujeme třídu App.
from app import App

# Tento blok zajistí, že se kód spustí jen tehdy, když spouštíme tento soubor přímo.
if __name__ == "__main__":
    root = tk.Tk()  # Vytvoříme základní okno
    app = App(root) # Vytvoříme naši aplikaci a předáme jí okno
    root.mainloop() # Spustíme ji