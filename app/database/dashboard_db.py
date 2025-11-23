import sqlite3
from . import budgets_db, categories_db


# ============================================================================
# DASHBOARD & STATS WINDOW - ROZPOČTOVÉ PLNĚNÍ
# ============================================================================

def get_month_total_budget_summary(db_path: str, transaction_type: str, month: int) -> dict:
    """
    Vypočítá celkový rozpočet a YTD plnění pro Dashboard tlačítko.
    
    OPTIMALIZOVÁNO: Používá funkci get_ytd_for_category() pro YTD do daného měsíce.
    
    Args:
        db_path: Cesta k databázi
        transaction_type: 'výdej' nebo 'príjem'
        month: Číslo měsíce (1-12) - YTD se počítá od ledna do tohoto měsíce
        
    Returns:
        {
            'total_budget': float,      # Celkový roční rozpočet (non-custom kategorie)
            'ytd_spending': float,      # YTD utrácení od ledna do měsíce (jen z kategorií s rozpočtem)
            'ytd_percentage': float     # (ytd_spending / total_budget) * 100
        }
        nebo None pokud žádný rozpočet neexistuje
    """
    # Použij funkci z budgets_db která správně počítá jen non-custom kategorie
    total_budget = budgets_db.get_total_budget_for_type(db_path, transaction_type)
    
    if total_budget == 0:
        return None  # Žádný rozpočet nastaven
    
    # Načti stats_data pro správné zpracování CUSTOM kategorií
    stats_data = get_stats_data(db_path, transaction_type)
    
    # YTD spending - sečti YTD do měsíce pro top-level kategorie s rozpočtem
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Najdi top-level kategorie (parent_id IS NULL) s rozpočtem
    cursor.execute("""
        SELECT k.id
        FROM kategorie k
        JOIN rozpocty r ON r.kategorie_id = k.id
        WHERE k.typ = ?
          AND k.parent_id IS NULL
          AND r.budget_plan != 0
    """, (transaction_type,))
    
    top_level_cats = cursor.fetchall()
    conn.close()
    
    # Spočítaj YTD pro každou top-level kategorii (použije rekurzivní sčítání pro CUSTOM)
    ytd_spending = 0.0
    for (cat_id,) in top_level_cats:
        ytd = get_ytd_for_category(db_path, cat_id, month, stats_data)
        ytd_spending += abs(ytd)  # ABS pro výdaje
    
    # Výpočet %
    ytd_percentage = (ytd_spending / total_budget) * 100 if total_budget > 0 else 0
    
    return {
        'total_budget': total_budget,
        'ytd_spending': ytd_spending,
        'ytd_percentage': ytd_percentage
    }


# ============================================================================
# NOVÉ FUNKCE PRO PRE-COMPUTED SYSTÉM
# ============================================================================

def get_stats_data(db_path: str, transaction_type: str) -> dict:
    """
    Načte VŠECHNA data pro stats_window jedním prostým SELECTem.
    
    NAHRAZUJE: get_year_performance_summary() - už nepotřebujeme komplexní CTE!
    
    Vrací strukturu s:
    - LEAF kategorie: mají pre-computed sum_past, sum_current, budget_plan
    - CUSTOM kategorie: budou mít 0 hodnoty (počítají se za běhu v calculate_custom_values)
    
    Args:
        db_path: Cesta k databázi
        transaction_type: 'výdej' nebo 'příjem'
        
    Returns:
        Dict[category_id, {
            'id': int,
            'nazev': str,
            'parent_id': int|None,
            'is_custom': int (0 nebo 1),
            'sum_past': float,      # Součet všech historical transakcí
            'sum_current': float,   # Součet current transakcí
            'budget_plan': float,   # Roční rozpočet (user input)
            'children': List[int]   # ID přímých dětí (naplní se po načtení)
        }]
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Prostý SELECT - ŽÁDNÉ CTE!
    cursor.execute("""
        SELECT 
            k.id,
            k.nazev,
            k.parent_id,
            k.is_custom,
            COALESCE(r.sum_past, 0) as sum_past,
            COALESCE(r.sum_current, 0) as sum_current,
            COALESCE(r.budget_plan, 0) as budget_plan
        FROM kategorie k
        LEFT JOIN rozpocty r ON k.id = r.kategorie_id
        WHERE k.typ = ?
        ORDER BY k.nazev
    """, (transaction_type,))
    
    rows = cursor.fetchall()
    conn.close()
    
    # Vytvoř dict s přímými dětmi
    result = {}
    for row in rows:
        cat_id = row['id']
        result[cat_id] = dict(row)
        result[cat_id]['children'] = []
    
    # Přiřaď děti k parentům
    for row in rows:
        parent_id = row['parent_id']
        if parent_id and parent_id in result:
            result[parent_id]['children'].append(row['id'])
    
    return result


# Note: calculate_custom_values() byla přesunuta do categories_db.py
# Pro zpětnou kompatibilitu vytvořím alias:
def calculate_custom_values(data: dict, cat_id: int) -> dict:
    """
    Alias pro categories_db.calculate_custom_values().
    Funkce byla přesunuta do categories_db.py (logičtější umístění).
    """
    return categories_db.calculate_custom_values(data, cat_id)


def get_month_data_for_category(db_path: str, category_id: int, month: int, is_current: bool, data: dict = None) -> float:
    """
    Načte součet transakcí pro danou kategorii a měsíc.
    
    Pro LEAF kategorie: Načte přímo z items
    Pro CUSTOM kategorie: Rekurzivně sečte hodnoty všech dětí
    
    Args:
        db_path: Cesta k databázi
        category_id: ID kategorie
        month: Číslo měsíce (1-12)
        is_current: True = aktuální rok (is_current=1), False = historické roky (is_current=0)
        data: Dict z get_stats_data() (pro rekurzivní sčítání CUSTOM kategorií)
        
    Returns:
        Součet částek (absolutní hodnota) pro daný měsíc
    """
    # Pokud máme data dict, zkontroluj zda je to CUSTOM kategorie
    if data and category_id in data:
        cat_info = data[category_id]
        
        # CUSTOM kategorie - sečti děti rekurzivně
        if cat_info['is_custom'] == 1 and cat_info['children']:
            total = 0.0
            for child_id in cat_info['children']:
                total += get_month_data_for_category(db_path, child_id, month, is_current, data)
            return total
    
    # LEAF kategorie - načti z items
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    is_current_flag = 1 if is_current else 0
    
    cursor.execute("""
        SELECT COALESCE(SUM(ABS(castka)), 0)
        FROM items
        WHERE kategorie_id = ?
          AND is_current = ?
          AND CAST(strftime('%m', datum) AS INTEGER) = ?
          AND castka != 0
    """, (category_id, is_current_flag, month))
    
    result = cursor.fetchone()[0]
    conn.close()
    
    return result


def get_ytd_for_category(db_path: str, category_id: int, up_to_month: int, data: dict = None) -> float:
    """
    Načte YTD (Year-To-Date) součet transakcí od ledna do zadaného měsíce (včetně).
    
    Pro LEAF kategorie: Načte přímo z items
    Pro CUSTOM kategorie: Rekurzivně sečte hodnoty všech dětí
    
    Args:
        db_path: Cesta k databázi
        category_id: ID kategorie
        up_to_month: Měsíc do kterého počítat (1-12), např. 6 = leden až červen
        data: Dict z get_stats_data() (pro rekurzivní sčítání CUSTOM kategorií)
        
    Returns:
        Součet částek (absolutní hodnota) od ledna do up_to_month (včetně)
    """
    # Pokud máme data dict, zkontroluj zda je to CUSTOM kategorie
    if data and category_id in data:
        cat_info = data[category_id]
        
        # CUSTOM kategorie - sečti děti rekurzivně
        if cat_info['is_custom'] == 1 and cat_info['children']:
            total = 0.0
            for child_id in cat_info['children']:
                total += get_ytd_for_category(db_path, child_id, up_to_month, data)
            return total
    
    # LEAF kategorie - načti z items (pouze is_current=1 pro aktuální rok)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT COALESCE(SUM(ABS(castka)), 0)
        FROM items
        WHERE kategorie_id = ?
          AND is_current = 1
          AND CAST(strftime('%m', datum) AS INTEGER) <= ?
          AND castka != 0
    """, (category_id, up_to_month))
    
    result = cursor.fetchone()[0]
    conn.close()
    
    return result
