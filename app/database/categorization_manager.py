import sqlite3

def get_unassigned_categories_by_type(db_path):
    """
    Najde všechny nezařazené položky 'co' a roztřídí je na příjmy, výdaje a neurčené.
    Vrací slovník se třemi seznamy.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Nejdříve získáme všechny unikátní nezařazené položky
    cursor.execute("SELECT DISTINCT co FROM items WHERE kategorie_id IS NULL AND co IS NOT NULL AND co != ''")
    unassigned_items = [item[0] for item in cursor.fetchall()]

    # Připravíme si slovník pro výsledky
    result = {'příjem': [], 'výdej': [], 'neurčeno': []}

    for item_name in unassigned_items:
        # Pro každou položku zjistíme její typ
        cursor.execute("SELECT castka FROM items WHERE co = ? AND castka != 0 LIMIT 1", (item_name,))
        row = cursor.fetchone()
        
        if not row:
            result['neurčeno'].append(item_name)
        else:
            amount = row[0]
            if amount > 0:
                result['příjem'].append(item_name)
            else:
                result['výdej'].append(item_name)
    
    conn.close()
    # Seřadíme seznamy pro přehlednost
    for key in result:
        result[key].sort()
        
    return result

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
    Tato operace se provádí pro historická i aktuální data.
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