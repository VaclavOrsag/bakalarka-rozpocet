import sqlite3


def get_month_category_comparison(db_path: str, month: int, transaction_type: str):
    """
    Vrátí porovnání kategorií pro daný měsíc a typ transakce.
    
    Args:
        db_path: Cesta k databázi
        month: Číslo měsíce (1-12)
        transaction_type: "výdej" nebo "příjem"
    
    Returns:
        List[dict] s klíči:
        - kategorie: název kategorie
        - historical: suma za historické období (is_current=0)  
        - current: suma za aktuální období (is_current=1)
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    month_str = f"{month:02d}"
    
    cursor.execute("""
        SELECT 
            k.nazev as kategorie,
            SUM(CASE WHEN i.is_current = 0 THEN ABS(i.castka) ELSE 0 END) as historical,
            SUM(CASE WHEN i.is_current = 1 THEN ABS(i.castka) ELSE 0 END) as current
        FROM items i
        JOIN kategorie k ON i.kategorie_id = k.id
        WHERE k.typ = ?
        AND i.kategorie_id IS NOT NULL
        AND i.castka != 0
        AND i.co IS NOT NULL 
        AND i.co != ''
        AND (
            -- ISO formát YYYY-MM-DD
            (instr(i.datum, '-') > 0 AND substr(i.datum, 6, 2) = ?)
            OR
            -- CZ formát DD.MM.YYYY  
            (instr(i.datum, '.') > 0 AND substr(i.datum, 4, 2) = ?)
        )
        GROUP BY k.id, k.nazev
        HAVING historical > 0 OR current > 0
        ORDER BY current DESC, historical DESC
    """, (transaction_type, month_str, month_str))
    
    results = []
    for row in cursor.fetchall():
        results.append({
            'kategorie': row[0],
            'historical': float(row[1] or 0),
            'current': float(row[2] or 0)
        })
    
    conn.close()
    return results


def debug_month_data(db_path: str, month: int):
    """Debug funkce - ukáže všechna data pro měsíc."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    month_str = f"{month:02d}"
    cursor.execute("""
        SELECT i.datum, i.castka, i.co, i.is_current, k.nazev, k.typ
        FROM items i
        LEFT JOIN kategorie k ON i.kategorie_id = k.id
        WHERE (
            (instr(i.datum, '-') > 0 AND substr(i.datum, 6, 2) = ?)
            OR
            (instr(i.datum, '.') > 0 AND substr(i.datum, 4, 2) = ?)
        )
        ORDER BY i.datum
    """, (month_str, month_str))
    
    print(f"\n=== Data pro měsíc {month} ===")
    for row in cursor.fetchall():
        print(f"Datum: {row[0]}, Částka: {row[1]}, Co: {row[2]}, Current: {row[3]}, Kategorie: {row[4]} ({row[5]})")
    
    conn.close()
