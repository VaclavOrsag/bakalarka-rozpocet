import sqlite3

def get_unassigned_categories_by_type(db_path):
    """
    Najde všechny nezařazené položky 'co' a roztřídí je na příjmy, výdej a neurčené.
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
        # Pro každou položku zkontrolujeme, jestli má NEZAŘAZENÉ příjmy a/nebo výdej
        cursor.execute("SELECT COUNT(*) FROM items WHERE co = ? AND castka > 0 AND kategorie_id IS NULL", (item_name,))
        has_income = cursor.fetchone()[0] > 0
        
        cursor.execute("SELECT COUNT(*) FROM items WHERE co = ? AND castka < 0 AND kategorie_id IS NULL", (item_name,))
        has_expense = cursor.fetchone()[0] > 0
        
        cursor.execute("SELECT COUNT(*) FROM items WHERE co = ? AND castka = 0 AND kategorie_id IS NULL", (item_name,))
        has_zero = cursor.fetchone()[0] > 0
        
        # Položka se může objevit v obou seznamech, pokud má obojí
        if has_income:
            result['příjem'].append(item_name)
        if has_expense:
            result['výdej'].append(item_name)
        if not has_income and not has_expense and has_zero:
            result['neurčeno'].append(item_name)
    
    conn.close()
    # Seřadíme seznamy pro přehlednost
    for key in result:
        result[key].sort()
        
    return result


def assign_category_to_items_by_type(db_path, co_name, category_id, transaction_type):
    """
    Přiřadí kategorii pouze transakcím určitého typu (příjem/výdej).
    transaction_type: 'příjem' nebo 'výdej'
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    if transaction_type == 'příjem':
        cursor.execute("UPDATE items SET kategorie_id = ? WHERE co = ? AND castka > 0 AND kategorie_id IS NULL", (category_id, co_name))
    elif transaction_type == 'výdej':
        cursor.execute("UPDATE items SET kategorie_id = ? WHERE co = ? AND castka < 0 AND kategorie_id IS NULL", (category_id, co_name))
    
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
