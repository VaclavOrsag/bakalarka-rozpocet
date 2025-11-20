import sqlite3

def create_categories_table(cursor):
    """Vytvoří tabulku 'kategorie', pokud neexistuje."""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS kategorie (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nazev TEXT NOT NULL,
            typ TEXT NOT NULL,
            parent_id INTEGER,
            FOREIGN KEY (parent_id) REFERENCES kategorie (id),
            UNIQUE(nazev, typ)
        )
    ''')

def get_all_categories(db_path):
    """Získá všechny kategorie z databáze."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, nazev, typ, parent_id FROM kategorie ORDER BY typ, nazev")
    categories = cursor.fetchall()
    conn.close()
    return categories

def category_exists(db_path, nazev, typ):
    """Kontroluje, zda kategorie s daným názvem a typem již existuje."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM kategorie WHERE nazev = ? AND typ = ?", (nazev, typ))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def add_category(db_path, nazev, typ, parent_id):
    """Přidá novou kategorii do databáze. Kontroluje duplicity."""
    if category_exists(db_path, nazev, typ):
        raise ValueError(f"Kategorie '{nazev}' typu '{typ}' již existuje.")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO kategorie (nazev, typ, parent_id) VALUES (?, ?, ?)", (nazev, typ, parent_id))
        new_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return new_id # Vrátíme ID pro další použití
    except sqlite3.IntegrityError:
        conn.close()
        raise ValueError(f"Kategorie '{nazev}' typu '{typ}' již existuje.")

""""
def update_category(db_path, category_id, new_name):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("UPDATE kategorie SET nazev = ? WHERE id = ?", (new_name, category_id))
    conn.commit()
    conn.close()
"""

def delete_category(db_path, category_id):
    """Smaže kategorii z databáze."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")  # Nutné pro Cascade delete (mazání kategorie = mazání rozpočtu v sql)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM kategorie WHERE id = ?", (category_id,))
    conn.commit()
    conn.close()

def has_categories(db_path):
    """Vrátí True, pokud v databázi existuje alespoň jedna kategorie."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # LIMIT 1 je optimalizace - databáze přestane hledat hned po prvním nálezu.
    cursor.execute("SELECT 1 FROM kategorie LIMIT 1")
    result = cursor.fetchone()
    conn.close()
    return result is not None