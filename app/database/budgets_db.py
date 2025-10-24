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