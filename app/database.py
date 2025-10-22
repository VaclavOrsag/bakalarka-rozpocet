import sqlite3

def init_db(db_path):
    """Vytvoří databázový soubor a tabulku s rozšířenou strukturou."""
    conn = sqlite3.connect(db_path)
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
            stredisko TEXT,
            kategorie_id INTEGER,
            FOREIGN KEY (kategorie_id) REFERENCES kategorie (id)         
        )
    ''')
    # NOVÁ TABULKA pro účetní osnovu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS kategorie (
            id INTEGER PRIMARY KEY,
            nazev TEXT NOT NULL,
            typ TEXT NOT NULL, -- Bude 'příjem' nebo 'výdej'
            parent_id INTEGER, -- Odkaz na ID nadřazené kategorie
            FOREIGN KEY (parent_id) REFERENCES kategorie (id)
        )
    ''')
    conn.commit()
    conn.close()

def add_item(db_path, datum, doklad, zdroj, firma, text, madati, dal, castka, cin, cislo, co, kdo, stredisko):
    """Přidá novou položku se všemi sloupci do databáze."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO items (datum, doklad, zdroj, firma, text, madati, dal, castka, cin, cislo, co, kdo, stredisko) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (datum, doklad, zdroj, firma, text, madati, dal, castka, cin, cislo, co, kdo, stredisko))
    conn.commit()
    conn.close()

def get_all_items(db_path):
    """Získá všechny položky z databáze."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items ORDER BY datum DESC") # Seřadíme od nejnovějšího
    items = cursor.fetchall()
    conn.close()
    return items

def delete_item(db_path, item_id):
    """Smaže položku z databáze podle jejího ID."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()

def delete_all_items(db_path):
    """Smaže VŠECHNY položky z tabulky items."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM items")
    conn.commit()
    conn.close()
    
def update_item(db_path, item_id, datum, doklad, zdroj, firma, text, madati, dal, castka, cin, cislo, co, kdo, stredisko):
    """Aktualizuje položku v databázi podle jejího ID."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE items 
        SET datum=?, doklad=?, zdroj=?, firma=?, text=?, madati=?, dal=?, castka=?, cin=?, cislo=?, co=?, kdo=?, stredisko=? 
        WHERE id = ?
    ''', (datum, doklad, zdroj, firma, text, madati, dal, castka, cin, cislo, co, kdo, stredisko, item_id))
    conn.commit()
    conn.close()

def get_total_amount(db_path):
    """Vrátí součet všech částek."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(castka) FROM items")
    total = cursor.fetchone()[0]
    conn.close()
    return total if total is not None else 0

def get_all_categories(db_path):
    """Získá všechny kategorie z databáze."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, nazev, typ, parent_id FROM kategorie ORDER BY nazev")
    categories = cursor.fetchall()
    conn.close()
    return categories

def add_category(db_path, nazev, typ, parent_id):
    """Přidá novou kategorii do databáze."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO kategorie (nazev, typ, parent_id) VALUES (?, ?, ?)", (nazev, typ, parent_id))
    conn.commit()
    conn.close()

def update_category(db_path, category_id, new_name):
    """Aktualizuje název existující kategorie."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("UPDATE kategorie SET nazev = ? WHERE id = ?", (new_name, category_id))
    conn.commit()
    conn.close()

def delete_category(db_path, category_id):
    """Smaže kategorii z databáze."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM kategorie WHERE id = ?", (category_id,))
    conn.commit()
    conn.close()