import csv
import database as db

def export_to_csv(filepath, db_path):
    """
    Získá všechna data z databáze a zapíše je do zadaného CSV souboru.
    """
    try:
        # Získáme všechna data z databáze
        all_items = db.get_all_items(db_path)

        # Otevřeme soubor pro zápis
        # newline='' zabraňuje vkládání prázdných řádků mezi záznamy
        with open(filepath, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)

            # Zapíšeme hlavičku souboru (názvy sloupců)
            writer.writerow([
                'ID', 'Datum', 'Doklad', 'Zdroj', 'Firma', 'Text', 'MD', 'D', 
                'Částka', 'Cin', 'Číslo', 'Co', 'Kdo', 'Středisko'
            ])

            # Zapíšeme všechny datové řádky
            writer.writerows(all_items)
        
        return True # Vracíme True, pokud se export podařil
    except Exception as e:
        print(f"Chyba při exportu do CSV: {e}")
        return False # Vracíme False, pokud nastala chyba