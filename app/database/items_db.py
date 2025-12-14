import sqlite3
from typing import Optional, List, Tuple, Any
from . import categories_db

def create_items_table(cursor: sqlite3.Cursor) -> None:
    """
    Vytvoří tabulku 'items' a potřebné indexy, pokud neexistují.
    
    Tabulka 'items' uchovává veškeré transakce (historické i aktuální).
    Sloupec 'is_current' rozlišuje mezi historickými daty (0) a aktuálním rokem (1).
    
    Args:
        cursor (sqlite3.Cursor): Databázový kurzor.
    """
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
    
    # Indexy pro optimalizaci dotazů a agregací
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

def add_item(
    db_path: str, 
    datum: str, 
    doklad: str, 
    zdroj: str, 
    firma: str, 
    text: str, 
    madati: float, 
    dal: float, 
    castka: float, 
    cin: Optional[int], 
    cislo: Optional[int], 
    co: str, 
    kdo: str, 
    stredisko: str, 
    is_current: int, 
    skip_metrics_update: bool = False
) -> None:
    """
    Přidá novou položku (transakci) do databáze.
    
    Funkce se pokusí automaticky přiřadit transakci k existující kategorii
    na základě názvu (sloupec 'co') a typu transakce (příjem/výdej).
    
    Args:
        db_path (str): Cesta k databázovému souboru.
        datum (str): Datum transakce.
        doklad (str): Číslo dokladu.
        zdroj (str): Zdroj transakce.
        firma (str): Název firmy.
        text (str): Popis transakce.
        madati (float): Částka MD.
        dal (float): Částka D.
        castka (float): Celková částka (kladná/záporná).
        cin (int, optional): Činnost.
        cislo (int, optional): Číslo.
        co (str): Název pro kategorizaci (klíčové pro automatické přiřazení).
        kdo (str): Osoba.
        stredisko (str): Středisko.
        is_current (int): 1 pro aktuální data, 0 pro historická.
        skip_metrics_update (bool): Pokud True, nepřepočítává metriky kategorie (pro hromadné importy).
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Pokus o automatické přiřazení kategorie
    # Hledáme pouze v LEAF kategoriích (is_custom=0), protože CUSTOM kategorie nemohou mít transakce.
    kategorie_id = None
    if co and co.strip() and castka != 0:
        # Určení typu transakce podle znaménka
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
    
    # Vložení záznamu
    cursor.execute('''
        INSERT INTO items (datum, doklad, zdroj, firma, text, madati, dal, castka, cin, cislo, co, kdo, stredisko, is_current, kategorie_id) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (datum, doklad, zdroj, firma, text, madati, dal, castka, cin, cislo, co, kdo, stredisko, is_current, kategorie_id))
    
    conn.commit()
    conn.close()
    
    # Aktualizace metrik (pokud není přeskočena)
    if kategorie_id and not skip_metrics_update:
        categories_db.update_category_metrics(db_path, kategorie_id)

def get_items(db_path: str, is_current: int) -> List[Tuple]:
    """
    Získá všechny položky z databáze pro daný stav (historické/aktuální).
    
    Args:
        db_path (str): Cesta k databázi.
        is_current (int): 1 pro aktuální data, 0 pro historická.
        
    Returns:
        List[Tuple]: Seznam transakcí seřazený sestupně podle data.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items WHERE is_current = ? ORDER BY datum DESC", (is_current,))
    items = cursor.fetchall()
    conn.close()
    return items

def delete_item(db_path: str, item_id: int) -> None:
    """
    Smaže položku z databáze podle jejího ID a aktualizuje metriky.
    
    Args:
        db_path (str): Cesta k databázi.
        item_id (int): ID transakce ke smazání.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Zjištění kategorie před smazáním pro následný přepočet
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

def delete_all_items(db_path: str, is_current: int) -> None:
    """
    Smaže VŠECHNY položky pro daný stav (historické/aktuální).
    Po smazání provede kompletní přepočet metrik všech kategorií.
    
    Args:
        db_path (str): Cesta k databázi.
        is_current (int): 1 pro aktuální data, 0 pro historická.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM items WHERE is_current = ?", (is_current,))
    conn.commit()
    conn.close()
    
    # Přepočítej metriky všech kategorií po smazání
    update_all_metrics(db_path)

def has_transactions(db_path: str, is_current: int) -> bool:
    """
    Ověří, zda v databázi existují nějaké transakce pro daný stav.
    
    Args:
        db_path (str): Cesta k databázi.
        is_current (int): 1 pro aktuální data, 0 pro historická.
        
    Returns:
        bool: True pokud existují transakce, jinak False.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM items WHERE is_current = ? LIMIT 1", (is_current,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def get_item_by_id(db_path: str, item_id: int) -> Optional[Tuple]:
    """
    Získá kompletní data jedné transakce podle jejího ID.
    
    Args:
        db_path (str): Cesta k databázi.
        item_id (int): ID transakce.
        
    Returns:
        Optional[Tuple]: Záznam transakce nebo None, pokud neexistuje.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items WHERE id = ?", (item_id,))
    result = cursor.fetchone()
    conn.close()
    return result

def update_item(
    db_path: str, 
    item_id: int, 
    datum: str, 
    doklad: str, 
    zdroj: str, 
    firma: str, 
    text: str, 
    madati: float, 
    dal: float, 
    castka: float, 
    cin: Optional[int], 
    cislo: Optional[int], 
    co: str, 
    kdo: str, 
    stredisko: str
) -> None:
    """
    Aktualizuje existující transakci a znovu provede automatické zařazení.
    
    Pokud se změní klíčové údaje (částka, 'co'), může dojít k přeřazení
    transakce do jiné kategorie. Funkce zajišťuje přepočet metrik pro
    původní i novou kategorii.
    
    Args:
        db_path (str): Cesta k databázi.
        item_id (int): ID transakce.
        ... (ostatní parametry odpovídají sloupcům v DB)
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Získání původní kategorie pro přepočet
    cursor.execute("SELECT kategorie_id FROM items WHERE id = ?", (item_id,))
    old_result = cursor.fetchone()
    old_kategorie_id = old_result[0] if old_result else None
    
    # Logika pro automatické přiřazení kategorie (stejná jako v add_item)
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
    
    # Update záznamu
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
    
    # Přepočet metrik pro dotčené kategorie
    if old_kategorie_id:
        categories_db.update_category_metrics(db_path, old_kategorie_id)
    
    if kategorie_id and kategorie_id != old_kategorie_id:
        categories_db.update_category_metrics(db_path, kategorie_id)

def update_all_metrics(db_path: str) -> None:
    """
    Přepočítá metriky pro VŠECHNY kategorie v databázi.
    
    Tato operace může být náročná, používat pouze při hromadných změnách
    (např. import, smazání všech dat).
    
    Args:
        db_path (str): Cesta k databázi.
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
