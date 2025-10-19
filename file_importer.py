import pandas as pd
import database as db

def import_from_excel(filepath, db_path):
    """
    Načte data, nahradí prázdné hodnoty a bezpečně je převede na správné
    datové typy před vložením do databáze.
    """
    try:
        df = pd.read_excel(filepath, sheet_name='Zdroj')
        df = df.fillna('')  # Nahradíme NaN za prázdný řetězec

        for _, row in df.iterrows():
            # Helper funkce pro bezpečnou konverzi na int
            def to_int(value):
                if value == '': return None
                try:
                    return int(value)
                except (ValueError, TypeError):
                    return None

            # Nová helper funkce pro bezpečnou konverzi na float
            def to_float(value):
                if value == '': return 0.0 # Prázdnou hodnotu považujeme za 0.0
                try:
                    return float(value)
                except (ValueError, TypeError):
                    return 0.0 # Pokud konverze selže, vrátíme 0.0

            # Získáme všechny hodnoty s použitím nových funkcí
            datum = row.get('Datum', '')
            doklad = row.get('Doklad', '')
            zdroj = row.get('Zdroj', '')
            firma = row.get('Firma', '')
            text = row.get('Text', '')
            madati = to_float(row.get('MD', 0.0)) # Použijeme novou funkci
            dal = to_float(row.get('D', 0.0))     # Použijeme novou funkci
            castka = to_float(row.get('Částka', 0.0)) # Použijeme novou funkci
            cin = to_int(row.get('Cin', ''))
            cislo = to_int(row.get('Číslo', ''))
            co = row.get('Co', '')
            kdo = row.get('Kdo', '')
            stredisko = row.get('Středisko', '')

            # Přidáme položku, jen pokud má vyplněný text
            if str(text).strip():
                db.add_item(
                    db_path,
                    str(datum), str(doklad), str(zdroj), str(firma), str(text),
                    madati, dal, castka, # Už posíláme bezpečně převedené floaty
                    cin, cislo,
                    str(co), str(kdo), str(stredisko)
                )
        return True
    except FileNotFoundError:
        print("Chyba: Soubor nebyl nalezen.")
        return False
    except KeyError as e:
        print(f"Chyba: V Excel souboru chybí očekávaný sloupec: {e}")
        return False
    except Exception as e:
        print(f"Při importu nastala neočekávaná chyba: {e}")
        return False