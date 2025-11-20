import sqlite3

def get_unassigned_categories_by_type(db_path):
    """
    Najde všechny nezařazené položky 'co' a roztřídí je na příjmy a výdaje.
    Vrací slovník se dvěma seznamy (neurčeno odstraněno).
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Získáme pouze položky s validním "co" A částkou != 0
    cursor.execute("""
        SELECT DISTINCT co FROM items 
        WHERE kategorie_id IS NULL 
        AND co IS NOT NULL 
        AND co != '' 
        AND castka != 0
    """)
    unassigned_items = [item[0] for item in cursor.fetchall()]

    # Připravíme si slovník pro výsledky (BEZ neurčeno)
    result = {'příjem': [], 'výdej': []}

    for item_name in unassigned_items:
        # Zkontrolujeme typ transakcí
        cursor.execute("SELECT COUNT(*) FROM items WHERE co = ? AND castka > 0 AND kategorie_id IS NULL", (item_name,))
        has_income = cursor.fetchone()[0] > 0
        
        cursor.execute("SELECT COUNT(*) FROM items WHERE co = ? AND castka < 0 AND kategorie_id IS NULL", (item_name,))
        has_expense = cursor.fetchone()[0] > 0
        
        # Přidáme do příslušných kategorií
        if has_income:
            result['příjem'].append(item_name)
        if has_expense:
            result['výdej'].append(item_name)
    
    conn.close()
    
    # Seřadíme seznamy
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
