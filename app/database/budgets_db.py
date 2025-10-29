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
            FOREIGN KEY (kategorie_id) REFERENCES kategorie (id)
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
        COALESCE(SUM(ia.sum_past), 0) AS sum_past,
        COALESCE(SUM(ia.sum_current), 0) AS sum_current,
        COALESCE(SUM(ba.budget_plan), 0) AS budget_plan
    FROM kategorie a
    LEFT JOIN tree t ON t.ancestor_id = a.id
    LEFT JOIN items_agg ia ON ia.descendant_id = t.descendant_id
    LEFT JOIN budgets_agg ba ON ba.descendant_id = t.descendant_id
    GROUP BY a.id, a.nazev, a.typ, a.parent_id
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