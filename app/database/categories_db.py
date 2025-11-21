import sqlite3

def create_categories_table(cursor):
    """Vytvoří tabulku 'kategorie', pokud neexistuje."""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS kategorie (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nazev TEXT NOT NULL,
            typ TEXT NOT NULL,
            parent_id INTEGER,
            is_custom INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (parent_id) REFERENCES kategorie (id),
            UNIQUE(nazev, typ)
        )
    ''')

def get_all_categories(db_path):
    """Získá všechny kategorie z databáze."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, nazev, typ, parent_id, is_custom FROM kategorie ORDER BY typ, nazev")
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

def add_category(db_path, nazev, typ, parent_id, is_custom=0):
    """Přidá novou kategorii do databáze. Kontroluje duplicity a hierarchická pravidla."""
    
    # VALIDACE HIERARCHIE: Pokud má rodiče, zkontroluj pravidla
    if parent_id is not None:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Získej informace o rodičovské kategorii
        cursor.execute("SELECT is_custom FROM kategorie WHERE id = ?", (parent_id,))
        parent_result = cursor.fetchone()
        
        if not parent_result:
            conn.close()
            raise ValueError(f"Rodičovská kategorie s ID {parent_id} neexistuje.")
        
        parent_is_custom = parent_result[0]
        
        # PRAVIDLO 1: Transakční kategorie (is_custom=0) nemohou mít žádné podkategorie
        if parent_is_custom == 0:
            conn.close()
            raise ValueError(
                "Podkategorie lze přidávat pouze k custom kategoriím (červené s ikonou 📁).\n\n"
                "Transakční kategorie slouží pouze pro přiřazování transakcí."
            )
        
        conn.close()
    
    # Vložení kategorie (duplicita se ošetří přes IntegrityError)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO kategorie (nazev, typ, parent_id, is_custom) VALUES (?, ?, ?, ?)", (nazev, typ, parent_id, is_custom))
        new_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return new_id # Vrátíme ID pro další použití
    except sqlite3.IntegrityError:
        conn.close()
        raise ValueError(f"Kategorie '{nazev}' typu '{typ}' již existuje.")

def get_custom_category_names(db_path):
    """Vrátí seznam názvů custom kategorií (is_custom = 1)."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT nazev FROM kategorie WHERE is_custom = 1")
        result = cursor.fetchall()
        
        conn.close()
        return [row[0] for row in result]
    except Exception as e:
        print(f"Chyba při získávání custom kategorií: {e}")
        return []

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