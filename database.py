import sqlite3

def init_db():
    """Vytvoří databázový soubor a tabulku, pokud neexistují."""
    conn = sqlite3.connect('budget.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY,
            description TEXT NOT NULL,
            amount REAL NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def add_item(description, amount):
    """Přidá novou položku do databáze."""
    conn = sqlite3.connect('budget.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO items (description, amount) VALUES (?, ?)", (description, amount))
    conn.commit()
    conn.close()

def get_all_items():
    """Získá všechny položky z databáze."""
    conn = sqlite3.connect('budget.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items")
    items = cursor.fetchall()
    conn.close()
    return items

def delete_item(item_id):
    """Smaže položku z databáze podle jejího ID."""
    conn = sqlite3.connect('budget.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()

def get_total_amount():
    """Vrátí součet všech částek."""
    conn = sqlite3.connect('budget.db')
    cursor = conn.cursor()
    # SQL funkce SUM() sečte hodnoty v daném sloupci
    cursor.execute("SELECT SUM(amount) FROM items")
    total = cursor.fetchone()[0]
    conn.close()
    # Pokud je tabulka prázdná, total bude None, tak vrátíme 0
    return total if total is not None else 0