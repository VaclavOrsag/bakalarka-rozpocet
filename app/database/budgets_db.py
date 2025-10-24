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

def calculate_actual_sums_by_category(db_path):
    """
    Spočítá součet částek pro každou přiřazenou kategorii z tabulky 'items'.
    Vrátí slovník ve formátu {kategorie_id: skutecny_soucet}.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Seskupíme transakce podle ID kategorie a sečteme jejich částky.
    # Ignorujeme transakce, které ještě nemají kategorii (kategorie_id IS NOT NULL).
    cursor.execute("""
        SELECT kategorie_id, SUM(castka) 
        FROM items 
        WHERE kategorie_id IS NOT NULL 
        GROUP BY kategorie_id
    """)
    actual_sums = {row[0]: row[1] for row in cursor.fetchall()}
    conn.close()
    return actual_sums

def has_budget_for_year(db_path, year):
    """Vrátí True, pokud pro daný rok existuje alespoň jeden záznam v rozpočtu."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # LIMIT 1 je optimalizace - databáze přestane hledat hned po prvním nálezu.
    cursor.execute("SELECT 1 FROM rozpocty WHERE rok = ? LIMIT 1", (year,))
    result = cursor.fetchone()
    conn.close()
    return result is not None