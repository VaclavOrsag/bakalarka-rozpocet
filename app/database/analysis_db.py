import sqlite3
from typing import List, Dict, Any, Optional

# Povolené dimenze (sloupce) – bezpečnost proti SQL injection
_WHITELIST = {"co", "stredisko", "text", "kdo", "firma", "kategorie_id"}


def get_pivot_rows(
	db_path: str,
	dims: List[str],
	is_current: int,
	allowed_types: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
	"""
	Vrátí agregované řádky pro hierarchický pohled dle zadaných dimenzí.

	Parametry:
	- db_path: cesta k SQLite databázi (profilu)
	- dims: pořadí dimenzí pro GROUP BY, např. ['stredisko', 'co']
	- is_current: 1 = aktuální data, 0 = historická
	- allowed_types: volitelně seznam typů kategorií, např. ['příjem','výdaj'];
	  pokud je zadán, filtruje se dle k.typ (case-insensitive match), a proto se přidá JOIN
	  na tabulku kategorie bez ohledu na to, zda je kategorie v dimenzích.

	Návratová hodnota:
	- list slovníků tvaru { 'keys': [hodnota_dim_1, ..., hodnota_dim_n], 'total': float }
	  kde 'keys' jsou textové reprezentace hodnot dimenzí (u kategorie název).
	"""

	# Očistit dimenze dle whitelistu a zachovat pořadí
	dims = [d for d in dims if d in _WHITELIST]
	# JOIN na kategorie je potřeba pokud zobrazujeme kategorii nebo pokud filtrujeme allowed_types
	join_kat = ("kategorie_id" in dims) or (allowed_types is not None and len(allowed_types) > 0)

	conn = sqlite3.connect(db_path)
	cursor = conn.cursor()

	try:
		# WHERE sestavení
		where_clauses = ["i.is_current = ?"]
		params: List[Any] = [is_current]
		if allowed_types:
			# použijeme case-insensitive porovnání přes LOWER
			placeholders = ", ".join(["LOWER(?)" for _ in allowed_types])
			where_clauses.append(f"LOWER(k.typ) IN ({placeholders})")
			params.extend(allowed_types)

		if not dims:
			# Bez dimenzí: jen jeden celkový součet (s případným filtrem typů)
			sql_total = f"""
				SELECT COALESCE(SUM(i.castka), 0)
				FROM items i
				{"LEFT JOIN kategorie k ON k.id = i.kategorie_id" if join_kat else ""}
				WHERE {' AND '.join(where_clauses)}
			"""
			cursor.execute(sql_total, tuple(params))
			total = float(cursor.fetchone()[0] or 0.0)
			return [{"keys": [], "total": total}]

		select_parts = []
		order_parts = []
		group_parts = []

		for d in dims:
			if d == "kategorie_id":
				# Zobrazíme název kategorie; group-by držíme na id kvůli jednoznačnosti
				select_parts.append('COALESCE(k.nazev, "") AS kategorie')
				order_parts.append('k.nazev COLLATE NOCASE')
				group_parts.append('i.kategorie_id')
			else:
				select_parts.append(f'COALESCE(i.{d}, "") AS {d}')
				order_parts.append(f'i.{d} COLLATE NOCASE')
				group_parts.append(f'i.{d}')

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

		out: List[Dict[str, Any]] = []
		for r in rows:
			# Poslední položka je total, předchozí jsou klíče
			key_vals = [("" if v is None else str(v)) for v in r[:-1]]
			total = float(r[-1] or 0.0)
			out.append({"keys": key_vals, "total": total})
		return out
	finally:
		conn.close()

