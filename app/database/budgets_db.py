import sqlite3

def create_budgets_table(cursor):
    """
    Vytvoří tabulku 'rozpocty' s pre-computed metrikami.
    
    SLOUPCE:
    - budget_plan: roční rozpočet (zadává uživatel pro LEAF kategorie)
    - sum_past: SUM všech historical transakcí (AUTO-UPDATE při změně transakce)
    - sum_current: SUM všech current transakcí (AUTO-UPDATE při změně transakce)
    
    Pre-computed hodnoty se ukládají JEN pro LEAF kategorie (is_custom=0).
    Custom kategorie (is_custom=1) se počítají za běhu jako SUM dětí.
    
    DŮLEŽITÉ: Každá kategorie má JEN JEDEN rozpočet (není potřeba rok).
    YTD (Year-To-Date) se počítá dynamicky podle měsíce pomocí get_ytd_for_category().
    """
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rozpocty (
            kategorie_id INTEGER PRIMARY KEY,
            budget_plan REAL NOT NULL DEFAULT 0,
            sum_past REAL NOT NULL DEFAULT 0,
            sum_current REAL NOT NULL DEFAULT 0,
            FOREIGN KEY (kategorie_id) REFERENCES kategorie (id) ON DELETE CASCADE
        )
    ''')
    
    # Index pro rychlé dotazy (kategorie_id je už PRIMARY KEY, tak nepotřebujeme extra index)


def update_or_insert_budget(db_path, category_id: int, budget_value: float) -> None:
    """
    Uloží (nebo aktualizuje) plánovanou částku rozpočtu pro danou kategorii.
    Používá UPSERT na unikátní kategorie_id.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO rozpocty (kategorie_id, budget_plan)
        VALUES (?, ?)
        ON CONFLICT(kategorie_id) DO UPDATE SET
            budget_plan = excluded.budget_plan
        ;
        """,
        (category_id, budget_value),
    )
    conn.commit()
    conn.close()


def check_budget_completeness(db_path: str, transaction_type: str) -> dict:
    """
    Zkontroluje jestli všechny transakční kategorie mají přiřazený rozpočet.
    
    Args:
        db_path: Cesta k databázi
        transaction_type: 'výdej' nebo 'příjem'
        
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
    
    # Zjisti které kategorie MAJÍ rozpočet (budget_plan != 0)
    cursor.execute("""
        SELECT k.id, k.nazev
        FROM kategorie k
        JOIN rozpocty r ON r.kategorie_id = k.id
        WHERE k.typ = ?
          AND k.is_custom = 0
          AND r.budget_plan != 0
    """, (transaction_type,))
    
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


def get_total_budget_for_type(db_path: str, transaction_type: str) -> float:
    """
    Vypočítá celkový roční rozpočet pro daný typ transakce.
    
    Sčítá JEN kategorie které NEJSOU custom (is_custom=0) aby nedošlo k duplicitnímu počítání.
    Custom kategorie jsou agregáty svých dětí, takže jejich rozpočet se nepočítá samostatně.
    
    Používá ABS() protože výdaje jsou uloženy jako záporné hodnoty.
    
    Args:
        db_path: Cesta k databázi
        transaction_type: 'výdej' nebo 'příjem'
        
    Returns:
        Celkový roční rozpočet (suma absolutních hodnot planovanych_castek pro non-custom kategorie)
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT COALESCE(SUM(ABS(r.budget_plan)), 0) as total_budget
        FROM rozpocty r
        JOIN kategorie k ON r.kategorie_id = k.id
        WHERE k.typ = ?
          AND k.is_custom = 0
    """, (transaction_type,))
    
    total_budget = cursor.fetchone()[0]
    conn.close()
    
    return float(total_budget)

def get_budget_overview(db_path: str):
    """
    Vrátí kompletní přehled pro záložku Rozpočet pomocí pre-computed metrik.
    
    Pro LEAF kategorie (is_custom=0):
      - Načte přímo z tabulky rozpocty: sum_past, sum_current, budget_plan
      
    Pro CUSTOM kategorie (is_custom=1):
      - Prázdné hodnoty se nahradí runtime součtem dětí pomocí rekurzivní agregace
      
    Výsledek: list dictů se sloupci: id, nazev, typ, parent_id, is_custom, sum_past, sum_current, budget_plan
    """
    from . import categories_db
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Jednoduchý SELECT s JOIN na rozpocty (pre-computed metriky)
    sql = """
    SELECT 
        k.id,
        k.nazev,
        k.typ,
        k.parent_id,
        k.is_custom,
        COALESCE(r.sum_past, 0) AS sum_past,
        COALESCE(r.sum_current, 0) AS sum_current,
        COALESCE(r.budget_plan, 0) AS budget_plan
    FROM kategorie k
    LEFT JOIN rozpocty r ON r.kategorie_id = k.id
    ORDER BY k.typ, k.nazev
    """

    cursor.execute(sql)
    rows = cursor.fetchall()
    conn.close()
    
    # Vytvoř dict s children pro calculate_custom_values()
    data_dict = {}
    for row in rows:
        cat_id = row['id']
        data_dict[cat_id] = dict(row)
        data_dict[cat_id]['children'] = []
    
    # Přiřaď děti k parentům
    for row in rows:
        parent_id = row['parent_id']
        if parent_id and parent_id in data_dict:
            data_dict[parent_id]['children'].append(row['id'])
    
    # Přepočítej custom kategorie runtime
    result = []
    for row in rows:
        row_dict = dict(row)
        if row_dict['is_custom'] == 1:
            # Vypočítej hodnoty custom kategorie rekurzivně
            custom_values = categories_db.calculate_custom_values(data_dict, row_dict['id'])
            row_dict['sum_past'] = custom_values['sum_past']
            row_dict['sum_current'] = custom_values['sum_current']
            row_dict['budget_plan'] = custom_values['budget_plan']
        result.append(row_dict)
    
    return result

def has_any_budget(db_path) -> bool:
    """
    Vrátí True pokud tabulka 'rozpocty' obsahuje alespoň jeden záznam s budget_plan != 0.
    Záznamy s budget_plan = 0 se NEPOČÍTAJÍ (automaticky vytvořené, ale nevyplněné).
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM rozpocty WHERE budget_plan != 0 LIMIT 1")
    result = cursor.fetchone()
    conn.close()
    return result is not None

def get_own_budget(db_path: str, category_id: int) -> float:
    """Vrátí vlastní plánovanou částku pro danou kategorii (bez potomků)."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT budget_plan FROM rozpocty WHERE kategorie_id = ? LIMIT 1",
        (category_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return float(row[0]) if row is not None else 0.0

def update_custom_category_budgets(db_path):
    """Automaticky aktualizuje rozpočty custom kategorií jako součet jejich podkategorií."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Najdi všechny custom kategorie
    cursor.execute("SELECT id FROM kategorie WHERE is_custom = 1")
    custom_categories = cursor.fetchall()
    
    for (custom_id,) in custom_categories:
        # Spočítej součet rozpočtů podkategorií
        cursor.execute("""
            SELECT COALESCE(SUM(r.budget_plan), 0)
            FROM kategorie k
            LEFT JOIN rozpocty r ON k.id = r.kategorie_id
            WHERE k.parent_id = ?
        """, (custom_id,))
        
        total_budget = cursor.fetchone()[0]
        
        # Aktualizuj nebo vlož rozpočet custom kategorie
        cursor.execute("""
            INSERT OR REPLACE INTO rozpocty (kategorie_id, budget_plan)
            VALUES (?, ?)
        """, (custom_id, total_budget))
    
    conn.commit()
    conn.close()