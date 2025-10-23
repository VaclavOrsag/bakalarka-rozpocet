import sqlite3

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

def reapply_all_categories(db_path):
    """
    Projde všechny existující kategorie a pokusí se znovu přiřadit
    kategorii ke všem transakcím v 'items' na základě shody jména a 'co'.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Získáme seznam všech existujících kategorií (název, id)
    cursor.execute("SELECT nazev, id FROM kategorie")
    all_categories = cursor.fetchall()

    # Pro každou kategorii provedeme hromadný update
    for category_name, category_id in all_categories:
        cursor.execute("UPDATE items SET kategorie_id = ? WHERE co = ?", (category_id, category_name))
    
    conn.commit()
    conn.close()