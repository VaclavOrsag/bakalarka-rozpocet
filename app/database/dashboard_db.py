import sqlite3
from . import budgets_db


# ============================================================================
# DASHBOARD & STATS WINDOW - VÝKONNOSTNÍ METRIKY
# ============================================================================

def calculate_performance_percentage(current: float, historical: float) -> float:
    """
    Vypočítá procentuální performance: (current / historical * 100).
    
    Args:
        current: Aktuální částka
        historical: Historická částka
        
    Returns:
        Procentuální hodnota (např. 85.5 znamená 85.5% historického průměru).
        Speciální hodnoty:
        - Pokud historical = 0 a current > 0: vrací -1.0 (indikátor "nová položka")
        - Pokud historical = 0 a current = 0: vrací 0.0 (žádná data)
        - Pokud historical > 0 a current = 0: vrací 0.0 (nic se neutratilo)
    """
    if historical == 0:
        if current > 0:
            return -1.0  # Speciální hodnota pro "nová položka bez historie"
        else:
            return 0.0  # Žádná data
    return abs(current / historical * 100)


def get_year_performance_summary(db_path: str, transaction_type: str, year: int = None):
    """
    Vrátí kompletní roční přehled pro stats_window s hierarchickou agregací.
    
    Pro KAŽDOU kategorii (včetně custom) spočítá pro VŠECH 12 měsíců:
      - historical: součet historických transakcí (is_current=0) včetně všech potomků
      - current: součet aktuálních transakcí (is_current=1) včetně všech potomků
      - own_percentage: performance pouze vlastních transakcí (bez potomků)
      - total_percentage: performance včetně všech potomků
      - worst_percentage: MAX(total_percentage, max(children_worst_percentage))
    
    Používá JEDNU SQL query pro celý rok - optimalizováno pro výkon.
    
    Args:
        db_path: Cesta k databázi
        transaction_type: 'výdej' nebo 'příjem'
        year: Rok pro filtrování (IGNOROVÁNO - ponecháno pro kompatibilitu API)
        
    Returns:
        List dictů se sloupci: id, nazev, typ, parent_id, is_custom, month,
                               historical, current, own_historical, own_current,
                               own_percentage, total_percentage, worst_percentage
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Rekurzivní CTE pro hierarchii + pre-agregace položek pro každý měsíc
    # Filtrujeme POUZE podle is_current, ne podle roku!
    sql = """
    WITH RECURSIVE tree(ancestor_id, descendant_id) AS (
        SELECT id, id FROM kategorie WHERE typ = ?
        UNION ALL
        SELECT t.ancestor_id, k.id
        FROM tree t
        JOIN kategorie k ON k.parent_id = t.descendant_id
    ),
    items_agg AS (
        SELECT 
            i.kategorie_id AS descendant_id,
            CAST(strftime('%m', i.datum) AS INTEGER) AS month,
            SUM(CASE WHEN i.is_current = 0 THEN ABS(i.castka) ELSE 0 END) AS historical,
            SUM(CASE WHEN i.is_current = 1 THEN ABS(i.castka) ELSE 0 END) AS current
        FROM items i
        JOIN kategorie k ON i.kategorie_id = k.id
        WHERE k.typ = ?
          AND i.kategorie_id IS NOT NULL
          AND i.castka != 0
          AND i.co IS NOT NULL 
          AND i.co != ''
        GROUP BY i.kategorie_id, month
    ),
    own_items AS (
        SELECT 
            descendant_id,
            month,
            historical AS own_historical,
            current AS own_current
        FROM items_agg
    )
    SELECT 
        a.id,
        a.nazev,
        a.typ,
        a.parent_id,
        a.is_custom,
        m.month,
        COALESCE(SUM(ia.historical), 0) AS historical,
        COALESCE(SUM(ia.current), 0) AS current,
        COALESCE(own.own_historical, 0) AS own_historical,
        COALESCE(own.own_current, 0) AS own_current
    FROM kategorie a
    CROSS JOIN (
        SELECT 1 AS month UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 
        UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 
        UNION SELECT 9 UNION SELECT 10 UNION SELECT 11 UNION SELECT 12
    ) m
    LEFT JOIN tree t ON t.ancestor_id = a.id
    LEFT JOIN items_agg ia ON ia.descendant_id = t.descendant_id AND ia.month = m.month
    LEFT JOIN own_items own ON own.descendant_id = a.id AND own.month = m.month
    WHERE a.typ = ?
    GROUP BY a.id, a.nazev, a.typ, a.parent_id, a.is_custom, m.month, own.own_historical, own.own_current
    ORDER BY m.month, a.nazev
    ;
    """

    cursor.execute(sql, (transaction_type, transaction_type, transaction_type))
    rows = cursor.fetchall()
    conn.close()
    
    # Konverze na list dictů a přidání procentuálních výpočtů
    result = []
    for r in rows:
        row_dict = dict(r)
        
        # Vypočítáme percentages
        row_dict['own_percentage'] = calculate_performance_percentage(
            row_dict['own_current'], 
            row_dict['own_historical']
        )
        row_dict['total_percentage'] = calculate_performance_percentage(
            row_dict['current'], 
            row_dict['historical']
        )
        
        # worst_percentage se počítá v samostatné funkci (KROK 1.3)
        row_dict['worst_percentage'] = row_dict['total_percentage']  # Placeholder
        
        result.append(row_dict)
    
    return result


def calculate_category_worst_case(performance_data: list) -> dict:
    """
    Vypočítá worst_percentage pro každou kategorii rekurzivně shora dolů.
    
    worst_percentage = MAX(total_percentage, max(všechny children worst_percentage))
    
    Kombinatorní logika: Pokud má kategorie total_percentage 50% (zelená), ale jedno dítě
    má worst_percentage 120% (červená), pak rodič dostane také 120% (červená).
    
    Args:
        performance_data: Výstup z get_year_performance_summary()
        
    Returns:
        Dict[Tuple[category_id, month], worst_percentage]
        
    Příklad:
        result[(123, 5)] = 95.5  # kategorie ID=123, měsíc 5, worst_percentage=95.5%
    """
    # Index dat pro rychlé vyhledávání
    by_id_month = {}
    children_map = {}  # parent_id -> list of child_ids
    
    for row in performance_data:
        key = (row['id'], row['month'])
        by_id_month[key] = row
        
        parent_id = row['parent_id']
        if parent_id:
            if parent_id not in children_map:
                children_map[parent_id] = []
            if row['id'] not in children_map[parent_id]:
                children_map[parent_id].append(row['id'])
    
    worst_cache = {}
    
    def compute_worst(cat_id: int, month: int) -> float:
        """Rekurzivní výpočet worst_percentage."""
        key = (cat_id, month)
        
        if key in worst_cache:
            return worst_cache[key]
        
        if key not in by_id_month:
            return 0.0
        
        row = by_id_month[key]
        total_perc = row['total_percentage']
        
        # Najdi nejhorší hodnotu mezi dětmi
        children_ids = children_map.get(cat_id, [])
        children_worst = [compute_worst(child_id, month) for child_id in children_ids]
        max_child_worst = max(children_worst) if children_worst else 0.0
        
        # Speciální zpracování pro -1.0 (nová položka bez historie)
        # -1.0 má vždy přednost (je nejhorší)
        if total_perc == -1.0 or max_child_worst == -1.0:
            worst = -1.0
        else:
            # worst = MAX(vlastní total_percentage, nejhorší dítě)
            worst = max(total_perc, max_child_worst)
        
        worst_cache[key] = worst
        
        return worst
    
    # Spočítej worst pro všechny kategorie
    result = {}
    for row in performance_data:
        key = (row['id'], row['month'])
        result[key] = compute_worst(row['id'], row['month'])
    
    return result


# ============================================================================
# NOVÉ FUNKCE PRO ROZPOČTOVÉ PLNĚNÍ (ROZŠÍŘENÍ)
# ============================================================================

def get_month_total_budget_summary(db_path: str, transaction_type: str, month: int, year: int) -> dict:
    """
    Vypočítá celkový rozpočet a YTD plnění pro Dashboard tlačítko.
    
    DŮLEŽITÉ: YTD počítá JEN z kategorií které mají rozpočet v daném roce,
    aby odpovídalo tomu co uživatel vidí ve stats_window.
    
    Args:
        db_path: Cesta k databázi
        transaction_type: 'výdej' nebo 'příjem'
        month: Číslo měsíce (1-12) - pro výpočet YTD do tohoto měsíce
        year: Rok pro filtrování rozpočtu
        
    Returns:
        {
            'total_budget': float,      # Celkový roční rozpočet (non-custom kategorie)
            'ytd_spending': float,      # YTD utrácení (jen z kategorií s rozpočtem)
            'ytd_percentage': float     # (ytd_spending / total_budget) * 100
        }
        nebo None pokud žádný rozpočet neexistuje
    """
    # Použij funkci z budgets_db která správně počítá jen non-custom kategorie
    total_budget = budgets_db.get_total_budget_for_type(db_path, transaction_type, year)
    
    if total_budget == 0:
        return None  # Žádný rozpočet nastaven
    
    # YTD spending - JEN z kategorií které mají rozpočet v daném roce
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT COALESCE(SUM(ABS(i.castka)), 0) as ytd_spending
        FROM items i
        JOIN kategorie k ON i.kategorie_id = k.id
        WHERE k.typ = ?
          AND i.is_current = 1
          AND CAST(strftime('%m', i.datum) AS INTEGER) <= ?
          AND i.kategorie_id IS NOT NULL
          AND i.castka != 0
          AND i.co IS NOT NULL 
          AND i.co != ''
          AND EXISTS (
              SELECT 1 FROM rozpocty r 
              WHERE r.kategorie_id = k.id 
              AND r.rok = ?
          )
    """, (transaction_type, month, year))
    
    ytd_spending = cursor.fetchone()[0]
    
    conn.close()
    
    # Výpočet %
    ytd_percentage = (ytd_spending / total_budget) * 100
    
    return {
        'total_budget': total_budget,
        'ytd_spending': ytd_spending,
        'ytd_percentage': ytd_percentage
    }
