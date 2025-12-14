import sqlite3
from typing import List, Dict, Any, Optional, Set

# Povolené dimenze (sloupce) – bezpečnost proti SQL injection
# Sloupce tabulky 'items', se kterými má smysl dělat pivot
_WHITELIST = {"co", "stredisko", "text", "kdo", "firma", "kategorie_id"}

# Normalizované platné typy kategorií pro filtrování
VALID_TYPES = {"příjem", "výdej"}


def get_pivot_rows(
    db_path: str,
    dims: List[str],
    is_current: int,
    allowed_types: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Vrátí agregované řádky pro hierarchický pohled (Pivot Table) dle zadaných dimenzí.
    
    Tato funkce dynamicky sestavuje SQL dotaz pro GROUP BY operace nad tabulkou items.
    Umožňuje seskupovat data podle libovolné kombinace povolených sloupců (např. Středisko -> Kategorie).
    
    Args:
        db_path (str): Cesta k SQLite databázi.
        dims (List[str]): Seznam dimenzí pro seskupení (např. ['stredisko', 'kategorie_id']).
                          Pořadí v seznamu určuje hierarchii seskupení.
        is_current (int): 1 pro aktuální data, 0 pro historická.
        allowed_types (Optional[List[str]]): Filtr typů transakcí (např. ['příjem']).
                                            Pokud je zadán, provede se JOIN na tabulku kategorií.

    Returns:
        List[Dict[str, Any]]: Seznam výsledků, kde každý prvek obsahuje:
                              - 'keys': List[str] (hodnoty dimenzí pro daný řádek)
                              - 'total': float (součet částek pro danou skupinu)
    """

    # Filtrace dimenzí proti whitelistu (prevence SQL injection)
    dims = [d for d in dims if d in _WHITELIST]
    
    # Rozhodnutí, zda je nutný JOIN na tabulku kategorií
    # JOIN je nutný, pokud seskupujeme podle kategorie NEBO pokud filtrujeme podle typu kategorie
    join_kat = ("kategorie_id" in dims) or (allowed_types is not None and len(allowed_types) > 0)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        # Sestavení WHERE klauzule
        where_clauses = ["i.is_current = ?"]
        params = [is_current]
        
        if allowed_types:
            filtered = [t for t in allowed_types if t in VALID_TYPES]
            if filtered:
                # Dynamické vytvoření placeholderů (?, ?, ...)
                placeholders = ", ".join(["?"] * len(filtered))
                where_clauses.append(f"k.typ IN ({placeholders})")
                params.extend(filtered)

        # Pokud nejsou zadány žádné dimenze, vrátíme celkový součet (Grand Total)
        if not dims:
            sql_total = f"""
                SELECT COALESCE(SUM(i.castka), 0)
                FROM items i
                {"LEFT JOIN kategorie k ON k.id = i.kategorie_id" if join_kat else ""}
                WHERE {' AND '.join(where_clauses)}
            """
            cursor.execute(sql_total, tuple(params))
            total = float(cursor.fetchone()[0] or 0.0)
            return [{"keys": [], "total": total}]

        # Sestavení dynamických částí SQL dotazu
        select_parts = []
        order_parts = []
        group_parts = []
        
        for d in dims:
            if d == "kategorie_id":
                # Pro kategorii chceme zobrazit její název, ne ID
                select_parts.append('COALESCE(k.nazev, "") AS kategorie')
                order_parts.append('k.nazev COLLATE NOCASE')
                group_parts.append('i.kategorie_id')
            else:
                # Pro ostatní sloupce bereme hodnotu přímo
                select_parts.append(f'COALESCE(i.{d}, "") AS {d}')
                order_parts.append(f'i.{d} COLLATE NOCASE')
                group_parts.append(f'i.{d}')

        # Finální sestavení SQL dotazu
        sql = f"""
            SELECT {", ".join(select_parts)}, COALESCE(SUM(i.castka), 0) AS total
            FROM items i
            {"LEFT JOIN kategorie k ON k.id = i.kategorie_id" if join_kat else ""}
            WHERE {' AND '.join(where_clauses)}
            GROUP BY {", ".join(group_parts)}
            ORDER BY {", ".join(order_parts)}
        """
        
        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall()

        # Formátování výstupu do slovníků
        out = []
        for r in rows:
            # Všechny sloupce kromě posledního jsou klíče (dimenze)
            key_vals = [("" if v is None else str(v)) for v in r[:-1]]
            # Poslední sloupec je součet (total)
            total = float(r[-1] or 0.0)
            out.append({"keys": key_vals, "total": total})
        return out
    finally:
        conn.close()

