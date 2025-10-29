# Průvodce aplikací pro tvorbu rozpočtu (verze prvni-ukazka)

## 1. Správa profilů

*   Aplikace funguje na bázi **profilů**. Každý profil je samostatný soubor (`.db`), který obsahuje veškerá data (transakce, kategorie, rozpočty).
*   Při spuštění si uživatel může vytvořit nový profil nebo otevřít existující. Název profilu se zobrazuje v titulku okna.

## 2. Průvodce prvním spuštěním

*   Po vytvoření nového profilu provede záložka **"Home"** uživatele třemi základními kroky:
    1.  **Import historických dat:** Uživatel je vyzván k importu transakcí z minulého období z Excel souboru. Tato data slouží jako základ pro plánování.
    2.  **Tvorba účetní osnovy:** Po importu je uživatel naveden na záložku "Účetní osnova", kde si může z naimportovaných položek sestavit vlastní strom kategorií (příjmů a výdajů).
    3.  **Tvorba rozpočtu:** Jakmile je vytvořena první kategorie, zpřístupní se záložka "Rozpočet".

## 3. Záložka "Transakce"

*   Tato záložka nahradila původní "Zdroje" a slouží k práci se všemi finančními transakcemi.
*   **Oddělení dat:** Transakce jsou rozděleny na dva typy:
    *   **Historické:** Data z minulých období, sloužící pro analýzu a plánování.
    *   **Aktuální:** Nové transakce z aktuálního období, které slouží ke sledování plnění rozpočtu.
*   **Přepínání pohledů:** Uživatel může pomocí tlačítka snadno přepínat mezi zobrazením historických a aktuálních transakcí.
*   **Kontextový import:** Funkce importu z Excelu je nyní zde. Aplikace automaticky importuje data jako "aktuální" nebo "historická" podle toho, který pohled je zrovna aktivní.

## 4. Záložka "Účetní osnova"

*   Umožňuje uživateli interaktivně budovat stromovou strukturu příjmových a výdajových kategorií.
*   V levé části jsou zobrazeny všechny dosud nezařazené položky z importu.
*   Uživatel může tyto položky zařadit pomocí tlačítek a vytvořit z nich hlavní kategorie nebo je zařadit pod již existující.
*   Je možné také vytvářet zcela vlastní kategorie a podkategorie a mazat.

## 5. Záložka "Rozpočet" - Plánování a sledování

*   Tato záložka poskytuje přehled o rozpočtu ve struktuře vytvořené účetní osnovy.
*   Obsahuje klíčové sloupce:
    *   **Kategorie:** Stromová struktura kategorií.
    *   **Minulé období:** Agregované součty z **historických** transakcí. Slouží jako vodítko pro plánování.
    *   **Rozpočet:** Plánované částky pro jednotlivé kategorie (v této verzi zatím není editovatelné).
    *   **Plnění:** Agregované součty z **aktuálních** transakcí. Uživatel zde v reálném čase vidí, jak plní svůj rozpočet.

## 6. Export dat

*   V menu "Soubor" je možnost **"Exportovat do CSV"**, v této verzi je funkce zastaralá.

---

## 7. Plány do budoucna

1.  **Dokončení Funkčnosti Rozpočtu:**
    *   **Editovatelný rozpočet:** Implementovat možnost ručně zadávat a ukládat plánované částky ve sloupci "Rozpočet".
    *   **Navedení na plnění:** Po vytvoření rozpočtu aktivně vyzvat uživatele (např. pomocí dialogového okna) k importu aktuálních transakcí, aby se začal naplňovat sloupec "Plnění". (Aktuálně je funkční, ale aktuální transakce musíme přidat --> Transakce --> Přepnout na Aktuální transakce --> Importovat z excelu)

2.  **Záložka "Analýza" a Pokročilé Metriky:**
    *   **Vývoj záložky:** Vytvořit novou záložku "Analýza" pro detailní pohled na data.
    *   **Analýza dle středisek:** Umožnit filtrování a agregaci dat podle nákladových středisek.
    *   **Pokročilé plnění:** Přidání metriky, která by porovnávala aktuální plnění s plněním za stejné období v minulosti (např. "Plnění v květnu 2024 vs. Plnění v květnu 2023").

3.  **Dashboard a Vizuální Vylepšení:**
    *   **Přeměna "Home" na Dashboard:** Po dokončení úvodního nastavení transformovat záložku "Home" na hlavní panel zobrazující klíčové ukazatele (KPIs) a souhrnné grafy.
    *   **Integrace grafů:** Přidat grafy pro vizualizaci vývoje nákladů, porovnání kategorií atd.
    *   **Vizuální upozornění:** Zvýraznit v tabulkách klíčové stavy – například červeně, pokud plnění překračuje rozpočet, nebo označit transakce, které se nepodařilo automaticky zařadit.
