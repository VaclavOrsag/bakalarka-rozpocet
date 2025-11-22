import sqlite3

def create_budgets_table(cursor):
    """Vytvoří tabulku 'rozpocty' pro ukládání plánovaných částek."""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rozpocty (
            id INTEGER PRIMARY KEY,
            rok INTEGER NOT NULL,
            kategorie_id INTEGER NOT NULL,
            planovana_castka REAL NOT NULL,
            UNIQUE(rok, kategorie_id),
            FOREIGN KEY (kategorie_id) REFERENCES kategorie (id) ON DELETE CASCADE
        )
    ''')

def update_or_insert_budget(db_path, category_id: int, year: int, budget_value: float) -> None:
    """
    Uloží (nebo aktualizuje) plánovanou částku rozpočtu pro danou kategorii a rok.
    Používá UPSERT na unikátní kombinaci (rok, kategorie_id).
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO rozpocty (rok, kategorie_id, planovana_castka)
        VALUES (?, ?, ?)
        ON CONFLICT(rok, kategorie_id) DO UPDATE SET
            planovana_castka = excluded.planovana_castka
        ;
        """,
        (year, category_id, budget_value),
    )
    conn.commit()
    conn.close()


def check_budget_completeness(db_path: str, transaction_type: str, year: int) -> dict:
    """
    Zkontroluje jestli všechny transakční kategorie mají přiřazený rozpočet.
    
    Args:
        db_path: Cesta k databázi
        transaction_type: 'výdej' nebo 'příjem'
        year: Rok pro kontrolu rozpočtu
        
    Returns:
        {
            'is_complete': bool,           # True = všechny kategorie mají rozpočet
            'total_categories': int,       # Počet transakčních kategorií
            'categories_with_budget': int, # Kolik má rozpočet
            'missing_categories': list     # Seznam názvů kategorií bez rozpočtu
        }
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Najdi všechny transakční kategorie (non-custom) daného typu
    cursor.execute("""
        SELECT k.id, k.nazev
        FROM kategorie k
        WHERE k.typ = ?
          AND k.is_custom = 0
        ORDER BY k.nazev
    """, (transaction_type,))
    
    all_categories = cursor.fetchall()
    total_categories = len(all_categories)
    
    # Zjisti které kategorie MAJÍ rozpočet
    cursor.execute("""
        SELECT k.id, k.nazev
        FROM kategorie k
        JOIN rozpocty r ON r.kategorie_id = k.id
        WHERE k.typ = ?
          AND k.is_custom = 0
          AND r.rok = ?
    """, (transaction_type, year))
    
    categories_with_budget = cursor.fetchall()
    categories_with_budget_ids = {cat[0] for cat in categories_with_budget}
    
    # Zjisti které kategorie NEMAJÍ rozpočet
    missing_categories = [
        cat[1] for cat in all_categories 
        if cat[0] not in categories_with_budget_ids
    ]
    
    conn.close()
    
    return {
        'is_complete': len(missing_categories) == 0,
        'total_categories': total_categories,
        'categories_with_budget': len(categories_with_budget),
        'missing_categories': missing_categories
    }


def get_total_budget_for_type(db_path: str, transaction_type: str, year: int) -> float:
    """
    Vypočítá celkový roční rozpočet pro daný typ transakce.
    
    Sčítá JEN kategorie které NEJSOU custom (is_custom=0) aby nedošlo k duplicitnímu počítání.
    Custom kategorie jsou agregáty svých dětí, takže jejich rozpočet se nepočítá samostatně.
    
    Používá ABS() protože výdaje jsou uloženy jako záporné hodnoty.
    
    Args:
        db_path: Cesta k databázi
        transaction_type: 'výdej' nebo 'příjem'
        year: Rok pro filtrování rozpočtu
        
    Returns:
        Celkový roční rozpočet (suma absolutních hodnot planovanych_castek pro non-custom kategorie)
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT COALESCE(SUM(ABS(r.planovana_castka)), 0) as total_budget
        FROM rozpocty r
        JOIN kategorie k ON r.kategorie_id = k.id
        WHERE k.typ = ?
          AND k.is_custom = 0
          AND r.rok = ?
    """, (transaction_type, year))
    
    total_budget = cursor.fetchone()[0]
    conn.close()
    
    return float(total_budget)

def get_budget_overview(db_path: str, year: int):
    """
    Vrátí kompletní přehled pro záložku Rozpočet.

    Pro KAŽDOU kategorii spočítá (včetně všech jejích podkategorií):
      - sum_past: součet historických transakcí (is_current=0)
      - sum_current: součet aktuálních transakcí (is_current=1)
      - budget_plan: součet plánovaných částek z tabulky rozpocty pro daný rok

    Výsledek: list dictů se sloupci: id, nazev, typ, parent_id, sum_past, sum_current, budget_plan
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Rekurzivní CTE (předek, potomek) + před-aggregace položek i rozpočtů, aby nedocházelo k násobení řádků
    sql = """
    WITH RECURSIVE tree(ancestor_id, descendant_id) AS (
        SELECT id, id FROM kategorie
        UNION ALL
        SELECT t.ancestor_id, k.id
        FROM tree t
        JOIN kategorie k ON k.parent_id = t.descendant_id
    ),
    items_agg AS (
        SELECT 
            i.kategorie_id AS descendant_id,
            SUM(CASE WHEN i.is_current = 0 THEN i.castka ELSE 0 END) AS sum_past,
            SUM(CASE WHEN i.is_current = 1 THEN i.castka ELSE 0 END) AS sum_current
        FROM items i
        GROUP BY i.kategorie_id
    ),
    budgets_agg AS (
        SELECT 
            r.kategorie_id AS descendant_id,
            SUM(r.planovana_castka) AS budget_plan
        FROM rozpocty r
        WHERE r.rok = ?
        GROUP BY r.kategorie_id
    )
    SELECT 
        a.id,
        a.nazev,
        a.typ,
        a.parent_id,
        a.is_custom,
        COALESCE(SUM(ia.sum_past), 0) AS sum_past,
        COALESCE(SUM(ia.sum_current), 0) AS sum_current,
        -- Všechny kategorie: jen vlastní rozpočet
        -- (custom = automatický součet, transakční = vlastní hodnota)
        COALESCE(ba_own.budget_plan, 0) AS budget_plan
    FROM kategorie a
    LEFT JOIN tree t ON t.ancestor_id = a.id
    LEFT JOIN items_agg ia ON ia.descendant_id = t.descendant_id
    LEFT JOIN budgets_agg ba_own ON ba_own.descendant_id = a.id
    GROUP BY a.id, a.nazev, a.typ, a.parent_id, a.is_custom, ba_own.budget_plan
    ORDER BY a.typ, a.nazev
    ;
    """

    cursor.execute(sql, (year,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def has_budget_for_year(db_path, year):
    """Vrátí True, pokud pro daný rok existuje alespoň jeden záznam v rozpočtu."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # LIMIT 1 je optimalizace - databáze přestane hledat hned po prvním nálezu.
    cursor.execute("SELECT 1 FROM rozpocty WHERE rok = ? LIMIT 1", (year,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def has_any_budget(db_path) -> bool:
    """Vrátí True pokud tabulka 'rozpocty' obsahuje alespoň jeden záznam (bez nutnosti zadat rok)."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM rozpocty LIMIT 1")
    result = cursor.fetchone()
    conn.close()
    return result is not None

def get_own_budget(db_path: str, category_id: int, year: int) -> float:
    """Vrátí vlastní plánovanou částku pro danou kategorii a rok (bez potomků)."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT planovana_castka FROM rozpocty WHERE rok = ? AND kategorie_id = ? LIMIT 1",
        (year, category_id),
    )
    row = cursor.fetchone()
    conn.close()
    return float(row[0]) if row is not None else 0.0

def update_custom_category_budgets(db_path, year):
    """Automaticky aktualizuje rozpočty custom kategorií jako součet jejich podkategorií."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Najdi všechny custom kategorie
    cursor.execute("SELECT id FROM kategorie WHERE is_custom = 1")
    custom_categories = cursor.fetchall()
    
    for (custom_id,) in custom_categories:
        # Spočítej součet rozpočtů podkategorií
        cursor.execute("""
            SELECT COALESCE(SUM(r.planovana_castka), 0)
            FROM kategorie k
            LEFT JOIN rozpocty r ON k.id = r.kategorie_id AND r.rok = ?
            WHERE k.parent_id = ?
        """, (year, custom_id))
        
        total_budget = cursor.fetchone()[0]
        
        # Aktualizuj nebo vlož rozpočet custom kategorie
        cursor.execute("""
            INSERT OR REPLACE INTO rozpocty (kategorie_id, rok, planovana_castka)
            VALUES (?, ?, ?)
        """, (custom_id, year, total_budget))
    
    conn.commit()
    conn.close()