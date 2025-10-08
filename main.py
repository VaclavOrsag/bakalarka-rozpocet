# Importujeme knihovnu Tkinter, která nám umožní vytvářet grafické uživatelské rozhraní (okna, tlačítka atd.).
# Zkracujeme její název na 'tk' pro pohodlnější psaní.
import tkinter as tk

# Vytvoříme hlavní okno naší aplikace.
# Proměnná 'root' je běžně používaný název pro toto hlavní okno.
root = tk.Tk()

# Nastavíme titulek okna, který se zobrazí v jeho horní liště.
root.title("Nástroj pro tvorbu rozpočtu")

# Nastavíme počáteční rozměry okna v pixelech (šířka x výška).
root.geometry("800x600")

# Toto je klíčový příkaz, který aplikaci "spustí".
# Udržuje okno otevřené, čeká na akce od uživatele (kliknutí, psaní) a stará se o překreslování.
# Bez tohoto řádku by program jen problikl a hned se ukončil.
root.mainloop()