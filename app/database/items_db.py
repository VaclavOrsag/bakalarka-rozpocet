import sqlite3

def create_items_table(cursor):
    """Vytvoří tabulku 'items', pokud neexistuje, s novým sloupcem 'is_current'."""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY,
            datum TEXT, doklad TEXT, zdroj TEXT, firma TEXT, text TEXT,
            madati REAL, dal REAL, castka REAL,
            cin INTEGER, cislo INTEGER, co TEXT, kdo TEXT, stredisko TEXT,
            kategorie_id INTEGER,
            is_current INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (kategorie_id) REFERENCES kategorie (id)
        )
    ''')

def add_item(db_path, datum, doklad, zdroj, firma, text, madati, dal, castka, cin, cislo, co, kdo, stredisko, is_current):
    """Přidá novou položku do databáze a pokusí se ji automaticky přiřadit k existující kategorii."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Pokusíme se najít existující kategorii pro automatické přiřazení
    kategorie_id = None
    if co and co.strip() and castka != 0:
        # Určíme typ podle znaménka částky
        if castka > 0:
            transaction_type = 'příjem'
        elif castka < 0:
            transaction_type = 'výdej'
        else:
            transaction_type = None
        
        # Pokud dokážeme určit typ, pokusíme se najít existující kategorii
        if transaction_type:
            cursor.execute("SELECT id FROM kategorie WHERE nazev = ? AND typ = ?", (co, transaction_type))
            existing_category = cursor.fetchone()
            if existing_category:
                kategorie_id = existing_category[0]
    
    # Vložíme transakci s příslušnou kategorie_id (může být None nebo nalezená)
    cursor.execute('''
        INSERT INTO items (datum, doklad, zdroj, firma, text, madati, dal, castka, cin, cislo, co, kdo, stredisko, is_current, kategorie_id) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (datum, doklad, zdroj, firma, text, madati, dal, castka, cin, cislo, co, kdo, stredisko, is_current, kategorie_id))
    
    conn.commit()
    conn.close()

def get_items(db_path, is_current):
    """Získá všechny položky z databáze pro daný stav (historické/aktuální)."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items WHERE is_current = ? ORDER BY datum DESC", (is_current,))
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

def delete_all_items(db_path, is_current):
    """Smaže VŠECHNY položky pro daný stav z tabulky items."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM items WHERE is_current = ?", (is_current,))
    conn.commit()
    conn.close()
    
def update_item(db_path, item_id, datum, doklad, zdroj, firma, text, madati, dal, castka, cin, cislo, co, kdo, stredisko, is_current):
    """Aktualizuje položku v databázi podle jejího ID."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE items 
        SET datum=?, doklad=?, zdroj=?, firma=?, text=?, madati=?, dal=?, castka=?, cin=?, cislo=?, co=?, kdo=?, stredisko=?, is_current=? 
        WHERE id = ?
    ''', (datum, doklad, zdroj, firma, text, madati, dal, castka, cin, cislo, co, kdo, stredisko, is_current, item_id))
    conn.commit()
    conn.close()

def get_total_amount(db_path, is_current):
    """Vrátí součet všech částek pro daný stav."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(castka) FROM items WHERE is_current = ?", (is_current,))
    total = cursor.fetchone()[0]
    conn.close()
    return total if total is not None else 0

def has_transactions(db_path, is_current):
    """Vrátí True, pokud v databázi existuje alespoň jedna transakce pro daný stav."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM items WHERE is_current = ? LIMIT 1", (is_current,))
    result = cursor.fetchone()
    conn.close()
    return result is not None