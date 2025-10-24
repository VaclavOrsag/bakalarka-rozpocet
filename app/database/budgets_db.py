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

def has_budget_for_year(db_path, year):
    """Vrátí True, pokud pro daný rok existuje alespoň jeden záznam v rozpočtu."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # LIMIT 1 je optimalizace - databáze přestane hledat hned po prvním nálezu.
    cursor.execute("SELECT 1 FROM rozpocty WHERE rok = ? LIMIT 1", (year,))
    result = cursor.fetchone()
    conn.close()
    return result is not None