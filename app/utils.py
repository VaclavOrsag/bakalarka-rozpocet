"""
Utility funkce pro formátování a běžné operace v aplikaci.
"""


def format_money(value: float, use_abs: bool = True) -> str:
    """
    Formátuje peněžní hodnotu v českém formátu.
    
    Args:
        value: Částka k formátování (float)
        use_abs: Pokud True, zobrazí absolutní hodnotu (bez znaménka).
                 Pokud False, zachová znaménko (výdaje záporné, příjmy kladné).
        
    Returns:
        Formátovaný řetězec ve tvaru "1 234 567,89 Kč" nebo "-1 234 567,89 Kč"
        
    Examples:
        >>> format_money(1234567.89)
        '1 234 567,89 Kč'
        >>> format_money(-1234.5, use_abs=False)
        '-1 234,50 Kč'
        >>> format_money(-1234.5, use_abs=True)
        '1 234,50 Kč'
    """
    # Použijeme absolutní hodnotu nebo zachováme znaménko
    display_value = abs(value) if use_abs else value
    
    # Formátujeme s čárkou jako oddělovačem tisíců, pak nahradíme mezerou
    # Python formát: "1,234,567.89" → "1 234 567.89"
    formatted = f"{display_value:,.2f}".replace(",", " ")
    
    return formatted + " Kč"


def parse_money(text: str) -> float:
    """
    Parsuje peněžní hodnotu z řetězce.
    
    Podporuje různé formáty:
    - "1 234,56 Kč"
    - "1234.56"
    - "1 234.56 Kč"
    - "1,234.56 Kč"
    
    Args:
        text: Řetězec s peněžní hodnotou
        
    Returns:
        Float hodnota, nebo None pokud parsování selhalo
        
    Examples:
        >>> parse_money("1 234,56 Kč")
        1234.56
        >>> parse_money("1234.56")
        1234.56
        >>> parse_money("invalid")
        None
    """
    if text is None:
        return None
    
    s = str(text).strip()
    if s == '':
        return None
    
    # Odstranit měnu
    s = s.replace('Kč', '').replace('kč', '').strip()
    
    # Odstranit mezery (tisícové oddělovače)
    s = s.replace(' ', '')
    
    # Nahradit čárku tečkou (desetinná čárka → tečka)
    s = s.replace(',', '.')
    
    try:
        return float(s)
    except ValueError:
        return None
