import sqlite3
from typing import Dict, List, Optional

def get_unassigned_categories_by_type(db_path: str) -> Dict[str, List[str]]:
    """
    Najde všechny nezařazené položky (kategorie_id IS NULL) a roztřídí je.
    
    Vrací unikátní názvy ('co') položek, které uživatel musí zařadit.
    Rozděluje je striktně na příjmy a výdaje, protože uživatel může chtít
    stejný název (např. "PayPal") zařadit jinak pro příjem a jinak pro výdej.
    
    Args:
        db_path (str): Cesta k databázi.
        
    Returns:
        Dict[str, List[str]]: Slovník {'příjem': [...], 'výdej': [...]}.
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

    # Připravíme si slovník pro výsledky
    result = {'příjem': [], 'výdej': []}

    for item_name in unassigned_items:
        # Zkontrolujeme typ transakcí pro tento název
        cursor.execute("SELECT COUNT(*) FROM items WHERE co = ? AND castka > 0 AND kategorie_id IS NULL", (item_name,))
        has_income = cursor.fetchone()[0] > 0
        
        cursor.execute("SELECT COUNT(*) FROM items WHERE co = ? AND castka < 0 AND kategorie_id IS NULL", (item_name,))
        has_expense = cursor.fetchone()[0] > 0
        
        # Přidáme do příslušných seznamů
        if has_income:
            result['příjem'].append(item_name)
        if has_expense:
            result['výdej'].append(item_name)
    
    conn.close()
    
    # Seřadíme seznamy abecedně pro lepší UX
    for key in result:
        result[key].sort()
        
    return result


def assign_category_to_items_by_type(db_path: str, co_name: str, category_id: int, transaction_type: str) -> None:
    """
    Hromadně přiřadí kategorii všem nezařazeným transakcím s daným názvem a typem.
    
    Toto je klíčová funkce pro automatizaci - uživatel jednou zařadí "Billa"
    a aplikace to aplikuje na všechny minulé i budoucí importy (pokud jsou nezařazené).
    
    Args:
        db_path (str): Cesta k databázi.
        co_name (str): Název protistrany/položky (sloupec 'co').
        category_id (int): ID vybrané kategorie.
        transaction_type (str): 'příjem' (castka > 0) nebo 'výdej' (castka < 0).
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    if transaction_type == 'příjem':
        cursor.execute(
            "UPDATE items SET kategorie_id = ? WHERE co = ? AND castka > 0 AND kategorie_id IS NULL", 
            (category_id, co_name)
        )
    elif transaction_type == 'výdej':
        cursor.execute(
            "UPDATE items SET kategorie_id = ? WHERE co = ? AND castka < 0 AND kategorie_id IS NULL", 
            (category_id, co_name)
        )
    
    conn.commit()
    conn.close()

def unassign_items_from_category(db_path: str, category_id: int) -> None:
    """
    Zruší přiřazení transakcí při smazání kategorie.
    
    Nastaví 'kategorie_id' na NULL u všech transakcí, které patřily
    do smazané kategorie. Tyto transakce se pak znovu objeví v "Nezařazené".
    
    Args:
        db_path (str): Cesta k databázi.
        category_id (int): ID mazané kategorie.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("UPDATE items SET kategorie_id = NULL WHERE kategorie_id = ?", (category_id,))
    conn.commit()
    conn.close()
