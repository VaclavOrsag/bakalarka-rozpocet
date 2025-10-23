import sqlite3

def create_categories_table(cursor):
    """Vytvoří tabulku 'kategorie', pokud neexistuje."""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS kategorie (
            id INTEGER PRIMARY KEY,
            nazev TEXT NOT NULL,
            typ TEXT NOT NULL,
            parent_id INTEGER,
            FOREIGN KEY (parent_id) REFERENCES kategorie (id)
        )
    ''')
    
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
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id # Vrátíme ID pro další použití

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
    cursor = conn.cursor()
    cursor.execute("DELETE FROM kategorie WHERE id = ?", (category_id,))
    conn.commit()
    conn.close()

def get_unassigned_categories(db_path):
    """
    Najde všechny unikátní hodnoty ze sloupce 'co', které ještě nemají
    přiřazenou kategorii v tabulce 'items'.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # DISTINCT zajistí, že se každá hodnota vrátí jen jednou
    # IS NULL hledá řádky, které ještě nemají kategorii
    cursor.execute("SELECT DISTINCT co FROM items WHERE kategorie_id IS NULL AND co IS NOT NULL AND co != ''")
    unassigned = [item[0] for item in cursor.fetchall()]
    conn.close()
    return sorted(unassigned)

def determine_category_type(db_path, co_name):
    """
    Analyzuje PRVNÍ NALEZENOU transakci pro danou položku 'co' a určí,
    zda se jedná o příjem nebo výdej.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # LIMIT 1 zajistí, že databáze vrátí maximálně jeden záznam, což je velmi rychlé.
    cursor.execute("SELECT castka FROM items WHERE co = ? AND castka != 0 LIMIT 1", (co_name,))
    result = cursor.fetchone() # Získáme ten jeden řádek
    conn.close()

    if not result:
        # Nenalezli jsme žádnou transakci s nenulovou částkou. Nevíme.
        return None
    
    # Pokud jsme zde, 'result' obsahuje nenulovou částku.
    amount = result[0]
    return 'příjem' if amount > 0 else 'výdej'

def assign_category_to_items(db_path, co_name, category_id):
    """
    Najde všechny transakce s daným 'co' a přiřadí jim ID kategorie.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("UPDATE items SET kategorie_id = ? WHERE co = ?", (category_id, co_name))
    conn.commit()
    conn.close()

def unassign_items_from_category(db_path, category_id):
    """
    Najde všechny transakce přiřazené ke smazané kategorii a nastaví
    jejich 'kategorie_id' zpět na NULL.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("UPDATE items SET kategorie_id = NULL WHERE kategorie_id = ?", (category_id,))
    conn.commit()
    conn.close()