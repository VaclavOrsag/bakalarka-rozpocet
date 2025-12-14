import sqlite3
from . import items_db
from . import categories_db
from . import budgets_db

def init_db(db_path: str) -> None:
    """
    Inicializuje kompletní databázové schéma.
    
    Tato funkce slouží jako centrální bod pro vytvoření všech tabulek.
    Deleguje vytváření na jednotlivé moduly (items_db, categories_db, budgets_db),
    čímž dodržuje princip Single Responsibility.
    
    Args:
        db_path (str): Cesta k souboru databáze.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Postupně zavoláme funkce pro vytvoření jednotlivých tabulek
    categories_db.create_categories_table(cursor)
    items_db.create_items_table(cursor)
    budgets_db.create_budgets_table(cursor)
    
    conn.commit()
    conn.close()