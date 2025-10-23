import sqlite3
from . import items_db
from . import categories_db

def init_db(db_path):
    """
    Inicializuje kompletní databázi a vytvoří všechny potřebné tabulky.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Postupně zavoláme funkce pro vytvoření jednotlivých tabulek
    categories_db.create_categories_table(cursor)
    items_db.create_items_table(cursor)
    
    conn.commit()
    conn.close()