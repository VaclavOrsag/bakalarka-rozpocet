import os

def get_profiles_directory() -> str:
    """
    Vrátí absolutní cestu k adresáři pro ukládání profilů.
    Pokud adresář neexistuje, automaticky ho vytvoří.

    Returns:
        str: Cesta k adresáři s profily (např. C:/Users/User/.rozpocet_app_data).
    """
    # os.path.expanduser('~') vrátí cestu k domovskému adresáři uživatele (např. C:/Users/vacla)
    home_dir = os.path.expanduser('~')

    # Název naší složky (tečka na začátku ji na Linuxu/macOS skryje)
    app_data_folder = ".rozpocet_app_data"

    # Spojíme cestu k domovskému adresáři a názvu naší složky
    profiles_dir_path = os.path.join(home_dir, app_data_folder)

    # Vytvoříme adresář, pokud ještě neexistuje
    os.makedirs(profiles_dir_path, exist_ok=True)

    return profiles_dir_path