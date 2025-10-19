import pandas as pd
import database as db

def import_from_excel(filepath):
    """
    Načte data z určeného listu v Excel souboru a vloží je do databáze.
    """
    try:
        df = pd.read_excel(filepath, sheet_name='Zdroj')

        for index, row in df.iterrows():
            # Získáme všechny potřebné hodnoty
            datum = row.get('Datum', '')
            doklad = row.get('Doklad', '')
            zdroj = row.get('Zdroj', '')
            firma = row.get('Firma', '')
            text = row.get('Text', '')
            madati = row.get('MD', 0.0)
            dal = row.get('D', 0.0)
            castka = row.get('Částka', 0.0)
            cin = row.get('Cin', '')
            cislo = row.get('Číslo', '')
            co = row.get('Co', '')
            kdo = row.get('Kdo', '')
            stredisko = row.get('Středisko', '')

            # Přidáme položku, jen pokud má vyplněný text a částku
            if pd.notna(text) and pd.notna(castka) and castka != 0:
                db.add_item(
                    str(datum), str(doklad), str(zdroj), str(firma), str(text),
                    float(madati), float(dal), float(castka),
                    str(cin), str(cislo), str(co), str(kdo), str(stredisko)
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