import csv
from . import database as db

def export_to_csv(filepath, db_path):
    """
    Exportuje přehled rozpočtu (tak jak je vidět v záložce Rozpočet) do CSV.
    Data obsahují agregované hodnoty pro kategorie.
    """
    try:
        # Získáme kompletní přehled rozpočtu (včetně agregací)
        overview = db.get_budget_overview(db_path)

        # Otevřeme soubor pro zápis
        # newline='' zabraňuje vkládání prázdných řádků mezi záznamy
        with open(filepath, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file, delimiter=';') # Excel v CZ často preferuje středník

            # Zapíšeme hlavičku
            writer.writerow([
                'Kategorie', 
                'Typ', 
                'Minulé období', 
                'Rozpočet', 
                'Plnění'
            ])

            # Zapíšeme data
            for row in overview:
                writer.writerow([
                    row['nazev'],
                    row['typ'],
                    str(row['sum_past']).replace('.', ','), # Formátování pro český Excel
                    str(row['budget_plan']).replace('.', ','),
                    str(row['sum_current']).replace('.', ',')
                ])
        
        return True
    except Exception as e:
        print(f"Chyba při exportu do CSV: {e}")
        return False