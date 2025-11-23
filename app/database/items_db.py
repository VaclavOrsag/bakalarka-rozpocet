import sqlite3
from . import categories_db

def create_items_table(cursor):
    """Vytvoří tabulku 'items', pokud neexistuje, s novým sloupcem 'is_current'."""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY,
            datum TEXT, doklad TEXT, zdroj TEXT, firma TEXT, text TEXT,
            madati REAL, dal REAL, castka REAL,
            cin INTEGER, cislo INTEGER, co TEXT, kdo TEXT, stredisko TEXT,
            kategorie_id INTEGER,
            is_current INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (kategorie_id) REFERENCES kategorie (id)
        )
    ''')
    
    # ✅ NOVÉ: Indexy pro rychlejší aggregace v update_category_metrics()
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_items_kategorie_current 
        ON items(kategorie_id, is_current)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_items_datum 
        ON items(datum)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_items_kategorie_datum 
        ON items(kategorie_id, datum)
    ''')

def add_item(db_path, datum, doklad, zdroj, firma, text, madati, dal, castka, cin, cislo, co, kdo, stredisko, is_current, skip_metrics_update=False):
    """
    Přidá novou položku do databáze a pokusí se ji automaticky přiřadit k existující kategorii.
    
    Args:
        skip_metrics_update: Pokud True, nepřepočítá metriky (užitečné při hromadném importu).
                            Po dokončení hromadného importu je nutné zavolat update_all_metrics().
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Pokusíme se najít existující kategorii pro automatické přiřazení
    # DŮLEŽITÉ: Pouze LEAF kategorie (is_custom=0) mohou mít transakce!
    kategorie_id = None
    if co and co.strip() and castka != 0:
        # Určíme typ podle znaménka částky
        if castka > 0:
            transaction_type = 'příjem'
        elif castka < 0:
            transaction_type = 'výdej'
        else:
            transaction_type = None
        
        # Pokud dokážeme určit typ, pokusíme se najít existující LEAF kategorii
        if transaction_type:
            cursor.execute(
                "SELECT id FROM kategorie WHERE nazev = ? AND typ = ? AND is_custom = 0", 
                (co, transaction_type)
            )
            existing_category = cursor.fetchone()
            if existing_category:
                kategorie_id = existing_category[0]
    
    # Vložíme transakci s příslušnou kategorie_id (může být None nebo nalezená)
    cursor.execute('''
        INSERT INTO items (datum, doklad, zdroj, firma, text, madati, dal, castka, cin, cislo, co, kdo, stredisko, is_current, kategorie_id) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (datum, doklad, zdroj, firma, text, madati, dal, castka, cin, cislo, co, kdo, stredisko, is_current, kategorie_id))
    
    conn.commit()
    conn.close()
    
    # Přepočítej pre-computed metriky pro kategorii (pokud byla přiřazena a není skip)
    if kategorie_id and not skip_metrics_update:
        categories_db.update_category_metrics(db_path, kategorie_id)

def get_items(db_path, is_current):
    """Získá všechny položky z databáze pro daný stav (historické/aktuální)."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items WHERE is_current = ? ORDER BY datum DESC", (is_current,))
    items = cursor.fetchall()
    conn.close()
    return items

def delete_item(db_path, item_id):
    """Smaže položku z databáze podle jejího ID."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Před smazáním uložíme kategorie_id pro přepočet metrik
    cursor.execute("SELECT kategorie_id FROM items WHERE id = ?", (item_id,))
    result = cursor.fetchone()
    kategorie_id = result[0] if result else None
    
    # Smažeme transakci
    cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    
    # Přepočítej pre-computed metriky pro kategorii (pokud byla přiřazena)
    if kategorie_id:
        categories_db.update_category_metrics(db_path, kategorie_id)

def delete_all_items(db_path, is_current):
    """
    Smaže VŠECHNY položky pro daný stav z tabulky items.
    Po smazání přepočítá metriky všech kategorií.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM items WHERE is_current = ?", (is_current,))
    conn.commit()
    conn.close()
    
    # Přepočítej metriky všech kategorií po smazání
    update_all_metrics(db_path)

def get_total_amount(db_path, is_current):
    """Vrátí součet všech částek pro daný stav."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(castka) FROM items WHERE is_current = ?", (is_current,))
    total = cursor.fetchone()[0]
    conn.close()
    return total if total is not None else 0

def has_transactions(db_path, is_current):
    """Vrátí True, pokud v databázi existuje alespoň jedna transakce pro daný stav."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM items WHERE is_current = ? LIMIT 1", (is_current,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def get_item_by_id(db_path, item_id):
    """
    Získá kompletní data jedné transakce podle jejího ID.
    
    Tato funkce je užitečná pro načtení všech údajů transakce při editaci,
    kde potřebujeme předvyplnit formulář s existujícími hodnotami.
    
    Args:
        db_path (str): Cesta k SQLite databázi
        item_id (int): Jedinečný identifikátor transakce
        
    Returns:
        tuple nebo None: Kompletní záznam transakce jako tuple 
                        (id, datum, doklad, zdroj, firma, text, madati, dal, 
                         castka, cin, cislo, co, kdo, stredisko, kategorie_id, is_current)
                        nebo None pokud transakce s daným ID neexistuje
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items WHERE id = ?", (item_id,))
    result = cursor.fetchone()
    conn.close()
    return result

def update_item(db_path, item_id, datum, doklad, zdroj, firma, text, madati, dal, castka, cin, cislo, co, kdo, stredisko):
    """
    Aktualizuje existující transakci v databázi s automatickým přiřazením kategorie.
    
    Funkce provede úplnou aktualizaci všech polí transakce a zároveň se pokusí
    automaticky přiřadit kategorii na základě pole "co" a typu transakce (příjem/výdej).
    Typ je určen podle znaménka částky - kladná = příjem, záporná = výdej.
    
    Pokud existuje kategorie se jménem shodným s polem "co" a správným typem,
    transakce bude automaticky k této kategorii přiřazena. Pokud ne, zůstane
    nepřiřazená (kategorie_id = None).
    
    Args:
        db_path (str): Cesta k SQLite databázi
        item_id (int): ID transakce, která má být aktualizována
        datum (str): Datum ve formátu YYYY-MM-DD (může být prázdné)
        doklad (str): Číslo nebo označení dokladu
        zdroj (str): Zdroj transakce (např. banka, hotovost)
        firma (str): Název firmy nebo protistrany
        text (str): Popis transakce
        madati (float): Částka v koloně "Má dáti" (obvykle pro příjmy)
        dal (float): Částka v koloně "Dal" (obvykle pro výdaje)
        castka (float): Výsledná částka (+ pro příjem, - pro výdaj)
        cin (int nebo None): Číslo činnosti (může být prázdné)
        cislo (int nebo None): Pořadové číslo (může být prázdné)
        co (str): Kategorie nebo účel transakce
        kdo (str): Osoba zodpovědná za transakci
        stredisko (str): Středisko nebo oddělení
        
    Note:
        Funkce automaticky zachová původní is_current hodnotu transakce.
        Pokud kategorie s názvem z pole "co" neexistuje, transakce zůstane
        nepřiřazená a bude k dispozici v levých seznamech účetní osnovy.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Uložíme starou kategorie_id před updatem (pro přepočet)
    cursor.execute("SELECT kategorie_id FROM items WHERE id = ?", (item_id,))
    old_result = cursor.fetchone()
    old_kategorie_id = old_result[0] if old_result else None
    
    # Najdeme kategorii podle 'co' a typu (určeného ze znaménka částky)
    # DŮLEŽITÉ: Pouze LEAF kategorie (is_custom=0) mohou mít transakce!
    kategorie_id = None
    if co and co.strip() and castka != 0:
        if castka > 0:
            transaction_type = 'příjem'
        elif castka < 0:
            transaction_type = 'výdej'
        else:
            transaction_type = None
        
        if transaction_type:
            cursor.execute(
                "SELECT id FROM kategorie WHERE nazev = ? AND typ = ? AND is_custom = 0", 
                (co, transaction_type)
            )
            existing_category = cursor.fetchone()
            if existing_category:
                kategorie_id = existing_category[0]
    
    # Update transakce s automaticky přiřazenou nebo None kategorie_id
    cursor.execute("""
        UPDATE items SET 
        datum = ?, doklad = ?, zdroj = ?, firma = ?, text = ?,
        madati = ?, dal = ?, castka = ?, cin = ?, cislo = ?,
        co = ?, kdo = ?, stredisko = ?, kategorie_id = ?
        WHERE id = ?
    """, (datum, doklad, zdroj, firma, text, madati, dal, castka, 
          cin, cislo, co, kdo, stredisko, kategorie_id, item_id))
    
    conn.commit()
    conn.close()
    
    # Přepočítej pre-computed metriky pro obě kategorie (starou i novou, pokud existují)
    if old_kategorie_id:
        categories_db.update_category_metrics(db_path, old_kategorie_id)
    
    if kategorie_id and kategorie_id != old_kategorie_id:
        categories_db.update_category_metrics(db_path, kategorie_id)
def update_all_metrics(db_path):
    """
    Přepočítá pre-computed metriky pro VŠECHNY kategorie v databázi.
    Užitečné po hromadném importu nebo migracích.
    """
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Získej všechny kategorie
    cursor.execute("SELECT id FROM kategorie")
    all_categories = cursor.fetchall()
    conn.close()
    
    # Přepočítej metriky pro každou kategorii
    for (cat_id,) in all_categories:
        categories_db.update_category_metrics(db_path, cat_id)
