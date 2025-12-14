import sqlite3
from typing import List, Tuple, Optional, Dict, Any

def create_categories_table(cursor: sqlite3.Cursor) -> None:
    """
    Vytvoří tabulku 'kategorie', pokud neexistuje.
    
    Tabulka definuje hierarchickou strukturu účetní osnovy.
    - is_custom=0: LEAF kategorie (obsahuje transakce)
    - is_custom=1: CUSTOM kategorie (obsahuje podkategorie, ne transakce)
    
    Args:
        cursor (sqlite3.Cursor): Databázový kurzor.
    """
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS kategorie (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nazev TEXT NOT NULL,
            typ TEXT NOT NULL,
            parent_id INTEGER,
            is_custom INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (parent_id) REFERENCES kategorie (id),
            UNIQUE(nazev, typ)
        )
    ''')

def get_all_categories(db_path: str) -> List[Tuple]:
    """
    Získá všechny kategorie z databáze seřazené podle typu a názvu.
    
    Args:
        db_path (str): Cesta k databázi.
        
    Returns:
        List[Tuple]: Seznam kategorií (id, nazev, typ, parent_id, is_custom).
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, nazev, typ, parent_id, is_custom FROM kategorie ORDER BY typ, nazev")
    categories = cursor.fetchall()
    conn.close()
    return categories

def add_category(
    db_path: str, 
    nazev: str, 
    typ: str, 
    parent_id: Optional[int], 
    is_custom: int = 0
) -> int:
    """
    Přidá novou kategorii do databáze. Kontroluje duplicity a hierarchická pravidla.
    
    LOW-LEVEL funkce - pro běžné použití preferujte add_category_with_workflow().
    
    Validace:
    1. Duplicita (nazev + typ) - řešeno přes UNIQUE constraint.
    2. Hierarchie - rodič musí být CUSTOM kategorie (is_custom=1).
    3. Konzistence typu - potomek musí mít stejný typ (příjem/výdej) jako rodič.
    
    Args:
        db_path (str): Cesta k databázi.
        nazev (str): Název kategorie.
        typ (str): Typ ('příjem' nebo 'výdej').
        parent_id (Optional[int]): ID rodičovské kategorie (nebo None pro root).
        is_custom (int): 0 pro LEAF (transakční), 1 pro CUSTOM (složku).
        
    Returns:
        int: ID nově vytvořené kategorie.
        
    Raises:
        ValueError: Pokud jsou porušena validační pravidla.
    """
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # VALIDACE 1: Pokud má rodiče, zkontroluj hierarchická pravidla
    if parent_id is not None:
        # Získej informace o rodičovské kategorii
        cursor.execute("SELECT is_custom, typ FROM kategorie WHERE id = ?", (parent_id,))
        parent_result = cursor.fetchone()
        
        if not parent_result:
            conn.close()
            raise ValueError(f"Rodičovská kategorie s ID {parent_id} neexistuje.")
        
        parent_is_custom, parent_typ = parent_result
        
        # PRAVIDLO 1: Transakční kategorie nemohou mít žádné podkategorie
        if parent_is_custom == 0:
            conn.close()
            raise ValueError(
                "Transakční kategorie nemohou mít podkategorie.\n\n"
                "Pouze custom kategorie (červené s 📁) mohou obsahovat podkategorie."
            )
        
        # PRAVIDLO 2: Typ child musí být stejný jako typ parent
        if typ != parent_typ:
            conn.close()
            raise ValueError(
                f"Nelze zařadit položku typu '{typ.capitalize()}' pod '{parent_typ.capitalize()}'."
            )
    
    # VALIDACE 2: Vložení kategorie (duplicita se ošetří přes UNIQUE constraint)
    try:
        cursor.execute("INSERT INTO kategorie (nazev, typ, parent_id, is_custom) VALUES (?, ?, ?, ?)", (nazev, typ, parent_id, is_custom))
        new_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return new_id
    except sqlite3.IntegrityError:
        conn.close()
        raise ValueError(f"Kategorie '{nazev}' typu '{typ}' již existuje.")


def add_category_with_workflow(
    db_path: str, 
    nazev: str, 
    typ: str, 
    parent_id: Optional[int] = None, 
    is_custom: int = 0, 
    assign_transactions: bool = False
) -> int:
    """
    Kompletní workflow pro přidání kategorie s automatickou aktualizací metrik.
    
    Tato HIGH-LEVEL funkce zajišťuje:
    1. Vytvoření kategorie v DB (deleguje validaci na add_category).
    2. Přiřazení existujících transakcí (pokud assign_transactions=True).
    3. Přepočet pre-computed metrik (jen pro LEAF kategorie).
    
    Args:
        db_path (str): Cesta k databázi.
        nazev (str): Název kategorie.
        typ (str): 'příjem' nebo 'výdej'.
        parent_id (Optional[int]): ID rodiče (None = root kategorie).
        is_custom (int): 0 = LEAF (transakční), 1 = CUSTOM (agregační).
        assign_transactions (bool): True = přiřadí transakce podle názvu+typu.
        
    Returns:
        int: ID nově vytvořené kategorie.
    """
    # Import zde, aby fungoval i když categorization_manager importuje categories_db
    from . import categorization_manager
    
    # KROK 1: Vytvoř kategorii v DB (validace se děje zde)
    new_category_id = add_category(db_path, nazev, typ, parent_id, is_custom)
    
    # KROK 2: Přiřaď transakce (pouze pokud požadováno)
    if assign_transactions:
        categorization_manager.assign_category_to_items_by_type(db_path, nazev, new_category_id, typ)
        
        # KROK 3: Přepočítej pre-computed metriky (update_category_metrics skippuje CUSTOM)
        update_category_metrics(db_path, new_category_id)
    
    return new_category_id

def get_custom_category_names(db_path: str) -> List[str]:
    """
    Vrátí seznam názvů všech custom kategorií (is_custom = 1).
    
    Args:
        db_path (str): Cesta k databázi.
        
    Returns:
        List[str]: Seznam názvů custom kategorií.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT nazev FROM kategorie WHERE is_custom = 1")
        result = cursor.fetchall()
        
        conn.close()
        return [row[0] for row in result]
    except Exception as e:
        print(f"Chyba při získávání custom kategorií: {e}")
        return []

def is_custom_category(db_path: str, category_id: int) -> bool:
    """
    Ověří, zda je daná kategorie typu CUSTOM (složka).
    
    Args:
        db_path (str): Cesta k databázi.
        category_id (int): ID kategorie.
        
    Returns:
        bool: True pokud je custom, jinak False.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT is_custom FROM kategorie WHERE id = ?", (category_id,))
        result = cursor.fetchone()
        
        conn.close()
        return result is not None and result[0] == 1
    except Exception as e:
        print(f"Chyba při kontrole custom kategorie: {e}")
        return False

def delete_category(db_path: str, category_id: int) -> None:
    """
    Smaže kategorii z databáze.
    
    Díky ON DELETE CASCADE v databázi se automaticky smažou i závislosti
    (např. záznamy v tabulce rozpočtů).
    
    Args:
        db_path (str): Cesta k databázi.
        category_id (int): ID kategorie ke smazání.
    """
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")  # Nutné pro Cascade delete
    cursor = conn.cursor()
    cursor.execute("DELETE FROM kategorie WHERE id = ?", (category_id,))
    conn.commit()
    conn.close()

def has_categories(db_path: str) -> bool:
    """
    Ověří, zda v databázi existuje alespoň jedna kategorie.
    
    Args:
        db_path (str): Cesta k databázi.
        
    Returns:
        bool: True pokud existují kategorie, jinak False.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # LIMIT 1 je optimalizace - databáze přestane hledat hned po prvním nálezu.
    cursor.execute("SELECT 1 FROM kategorie LIMIT 1")
    result = cursor.fetchone()
    conn.close()
    return result is not None


def update_category_metrics(db_path: str, category_id: int) -> None:
    """
    Přepočítá pre-computed metriky pro jednu LEAF kategorii.
    
    Automaticky se volá po:
    - Přidání transakce (items_db.py)
    - Úpravě transakce (items_db.py)
    - Smazání transakce (items_db.py)
    
    Args:
        db_path (str): Cesta k databázi.
        category_id (int): ID kategorie (MUSÍ být is_custom=0, jinak se skip).
        
    DŮLEŽITÉ:
    - Počítá JEN pro LEAF kategorie (is_custom=0).
    - Custom kategorie se počítají za běhu v calculate_custom_values().
    - Historical = všechny transakce s is_current=0.
    - YTD = všechny transakce s is_current=1.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Kontrola: je to LEAF kategorie?
    cursor.execute("SELECT is_custom FROM kategorie WHERE id = ?", (category_id,))
    result = cursor.fetchone()
    if not result or result[0] == 1:
        conn.close()
        return  # Skip - custom kategorie se nepočítají zde
    
    # 1. HISTORICAL ROZPOČET = všechny historical transakce (is_current=0)
    cursor.execute("""
        SELECT COALESCE(SUM(ABS(castka)), 0)
        FROM items
        WHERE kategorie_id = ? 
          AND is_current = 0
          AND castka != 0
    """, (category_id,))
    historical_sum = cursor.fetchone()[0]
    
    # 2. YTD PLNĚNÍ = všechny current transakce (is_current=1)
    cursor.execute("""
        SELECT COALESCE(SUM(ABS(castka)), 0)
        FROM items
        WHERE kategorie_id = ?
          AND is_current = 1
          AND castka != 0
    """, (category_id,))
    ytd = cursor.fetchone()[0]
    
    # 3. UPSERT do rozpocty (kategorie_id je PRIMARY KEY)
    cursor.execute("""
        INSERT INTO rozpocty (kategorie_id, budget_plan, sum_past, sum_current)
        VALUES (?, 0, ?, ?)
        ON CONFLICT(kategorie_id) DO UPDATE SET
            sum_past = excluded.sum_past,
            sum_current = excluded.sum_current
    """, (category_id, historical_sum, ytd))
    
    conn.commit()
    conn.close()


def calculate_custom_values(data: Dict[int, Any], cat_id: int) -> Dict[str, float]:
    """
    Vypočítá hodnoty pro kategorii (LEAF nebo CUSTOM) rekurzivně.
    
    LEAF kategorie (is_custom=0):
    - Vrátí pre-computed hodnoty z tabulky rozpocty.
    
    CUSTOM kategorie (is_custom=1):
    - Rekurzivně sečte hodnoty všech přímých dětí.
    - Rozpoznání: má children (data[cat_id]['children'] != []).
    
    Podporuje N-level hierarchii (custom může mít custom dítě).
    
    Args:
        data (Dict): Dict s kategoriemi obsahující klíče: sum_past, sum_current, budget_plan.
        cat_id (int): ID kategorie k výpočtu.
        
    Returns:
        Dict[str, float]: {
            'sum_past': float,      # Součet historical transakcí
            'sum_current': float,   # Součet current transakcí
            'budget_plan': float    # Roční rozpočet
        }
    """
    if cat_id not in data:
        return {'sum_past': 0.0, 'sum_current': 0.0, 'budget_plan': 0.0}
    
    cat = data[cat_id]
    
    # LEAF kategorie (nemá děti) - vrat pre-computed hodnoty
    if not cat['children']:
        return {
            'sum_past': float(cat['sum_past']),
            'sum_current': float(cat['sum_current']),
            'budget_plan': float(cat['budget_plan'])
        }
    
    # CUSTOM kategorie (má děti) - sečti všechny přímé děti REKURZIVNĚ
    totals = {
        'sum_past': 0.0,
        'sum_current': 0.0,
        'budget_plan': 0.0
    }
    
    for child_id in cat['children']:
        # Rekurzivní volání (pokud je dítě taky custom, zavolá se znovu)
        child_values = calculate_custom_values(data, child_id)
        totals['sum_past'] += child_values['sum_past']
        totals['sum_current'] += child_values['sum_current']
        totals['budget_plan'] += child_values['budget_plan']
    
    return totals