import sqlite3

def init_db():
    """Vytvoří databázový soubor a tabulku s rozšířenou strukturou."""
    conn = sqlite3.connect('budget.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY,
            datum TEXT,
            doklad TEXT,
            zdroj TEXT,
            firma TEXT,
            text TEXT,
            madati REAL,
            dal REAL,
            castka REAL,
            cin INTEGER,
            cislo INTEGER,
            co TEXT,
            kdo TEXT,
            stredisko TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_item(datum, doklad, zdroj, firma, text, madati, dal, castka, cin, cislo, co, kdo, stredisko):
    """Přidá novou položku se všemi sloupci do databáze."""
    conn = sqlite3.connect('budget.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO items (datum, doklad, zdroj, firma, text, madati, dal, castka, cin, cislo, co, kdo, stredisko) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (datum, doklad, zdroj, firma, text, madati, dal, castka, cin, cislo, co, kdo, stredisko))
    conn.commit()
    conn.close()

def get_all_items():
    """Získá všechny položky z databáze."""
    conn = sqlite3.connect('budget.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items ORDER BY datum DESC") # Seřadíme od nejnovějšího
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

def delete_all_items():
    """Smaže VŠECHNY položky z tabulky items."""
    conn = sqlite3.connect('budget.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM items")
    conn.commit()
    conn.close()
    
def update_item(item_id, datum, doklad, zdroj, firma, text, madati, dal, castka, cin, cislo, co, kdo, stredisko):
    """Aktualizuje položku v databázi podle jejího ID."""
    conn = sqlite3.connect('budget.db')
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE items 
        SET datum=?, doklad=?, zdroj=?, firma=?, text=?, madati=?, dal=?, castka=?, cin=?, cislo=?, co=?, kdo=?, stredisko=? 
        WHERE id = ?
    ''', (datum, doklad, zdroj, firma, text, madati, dal, castka, cin, cislo, co, kdo, stredisko, item_id))
    conn.commit()
    conn.close()

def get_total_amount():
    """Vrátí součet všech částek."""
    conn = sqlite3.connect('budget.db')
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(castka) FROM items")
    total = cursor.fetchone()[0]
    conn.close()
    return total if total is not None else 0