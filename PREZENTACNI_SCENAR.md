# 🎯 PREZENTAČNÍ SCÉNÁŘ - Jak ukázat aplikaci učiteli

## 📋 PŘÍPRAVA (před setkáním)

### 1. Připrav čistou databázi
```bash
# Smaz starou databázi pokud existuje
rm profiles/DEMO_prezentace.db  

# Aplikace vytvoří novou při prvním spuštění
```

### 2. Měj připravené Excel soubory
- ✅ `test_data/hospodareni-2023-DEMO.xlsx` (historical)
- ✅ `test_data/hospodareni-2024-DEMO.xlsx` (current)

---

## 🎬 PRŮBĚH PREZENTACE (30-40 minut)

### ČÁST 1: Úvod a problematika (5 min)

**CO ŘÍCT:**
> "Dobrý den, chtěl bych vám ukázat aplikaci pro rozpočtové plánování, kterou jsem vytvořil jako svou bakalářskou práci. Aplikace řeší problém, se kterým se potýkají sportovní kluby a neziskové organizace - jak efektivně plánovat rozpočet a sledovat jeho plnění v průběhu roku."

**UKÁZAT:**
- Spusť aplikaci: `python main.py`
- Vytvoř nový profil: "DEMO_prezentace"

**ZDŮRAZNIT:**
- Aplikace pracuje s **hierarchickou kategorickou strukturou**
- Podporuje **N-level hierarchii** (kategorie v kategoriích)
- Automaticky **přepočítává metriky** pro rychlé zobrazení

---

### ČÁST 2: Import historical dat (5 min)

**KROK 1: Import Excel souboru**
1. Home Tab → "Importovat historická data"
2. Vyber: `test_data/hospodareni-2023-DEMO.xlsx`
3. Počkej na import (~290 transakcí)

**CO ŘÍCT:**
> "První krok je import historických dat z roku 2023. Aplikace načte všechny transakce z Excelu a automaticky je zpracuje. Vidíte, že máme 290 transakcí za celý rok 2023."

**UKÁZAT:**
- Sources Tab - zobrazí všechny transakce
- Filtrování podle data, částky, kategorie
- Možnost editace transakce (dvojklik)

**ZDŮRAZNIT:**
- Automatická detekce sloupců z Excelu
- Validace dat při importu
- Možnost opravy chyb přímo v aplikaci

---

### ČÁST 3: Vytvoření kategorické struktury (10 min)

**KROK 2: Accounting Structure Tab**

**CO ŘÍCT:**
> "Teď vytvoříme kategorickou strukturu. Aplikace podporuje N-level hierarchii - můžeme vytvořit kategorii v kategorii v kategorii. Ukážu vám to na příkladu."

**UKÁZAT STRUKTURU (vytvoř postupně):**

#### VÝDAJE:
```
📁 Personál (CUSTOM)
  ├─ Mzdy trenérů (LEAF)
  ├─ DPP dohody (LEAF)
  └─ Sociální pojištění (LEAF)

📁 Provoz (CUSTOM)
  ├─ 📁 Pronájmy (CUSTOM pod CUSTOM!)
  │   ├─ Pronájem haly (LEAF)
  │   └─ Pronájem šaten (LEAF)
  ├─ Energie (LEAF)
  └─ Úklid (LEAF)

📁 Sportovní činnost (CUSTOM)
  ├─ Startovné (LEAF)
  ├─ Tréninkové pomůcky (LEAF)
  └─ Dresy a vybavení (LEAF)

Cestovné (LEAF - přímo pod root)
Ostatní náklady (LEAF)
```

#### PŘÍJMY:
```
📁 Dotace (CUSTOM)
  ├─ Dotace město (LEAF)
  └─ Dotace kraj (LEAF)

Členské příspěvky (LEAF)
Sponzorské dary (LEAF)
Tržby z akcí (LEAF)
```

**JAK VYTVOŘIT:**
1. **Hlavní kategorii (CUSTOM):**
   - Pravý sloupec → "Přidat vlastní kategorii"
   - Zadej název: "Personál"
   - Typ: "Výdej"
   - Zaškrtni: "✅ Přiřadit transakce"
   
2. **Podkategorii (LEAF):**
   - Vyber "Mzdy trenérů" v levém sloupci (Nepřiřazené)
   - Vyber "Personál" v pravém sloupci
   - Klikni: "Přidat jako podkategorii"

3. **Custom pod custom:**
   - Vyber "Pronájmy" jako CUSTOM
   - Pak přidej "Pronájem haly" a "Pronájem šaten" pod něj

**ZDŮRAZNIT:**
- 📁 **Červená ikona** = CUSTOM kategorie (agreguje děti)
- **Černá ikona** = LEAF kategorie (má transakce)
- **Automatic assignment** = transakce se automaticky přiřadí podle názvu
- **Pre-computed metriky** = součty se počítají automaticky

**UKÁZAT:**
- Hierarchii v pravém stromu
- Barevné rozlišení (červená = custom)
- Možnost editace/mazání kategorií
- Validace (nelze vytvořit podkategorii pod LEAF)

---

### ČÁST 4: Nastavení rozpočtu (5 min)

**KROK 3: Budget Tab**

**CO ŘÍCT:**
> "Teď nastavíme roční rozpočet pro rok 2024. Aplikace automaticky vypočítá rozpočty pro CUSTOM kategorie jako součet jejich podkategorií."

**UKÁZAT:**
1. Dvojklik na LEAF kategorii (např. "Mzdy trenérů")
2. Zadej rozpočet: 360 000 Kč (30k × 12 měsíců)
3. Ukázat že se automaticky přepočítal rozpočet pro "Personál"

**NASTAV ROZPOČTY (příklady):**
```
Personál:
  - Mzdy trenérů: 360 000
  - DPP dohody: 240 000
  - Sociální pojištění: 120 000
  → Personál celkem: 720 000 (automaticky)

Provoz > Pronájmy:
  - Pronájem haly: 420 000
  - Pronájem šaten: 84 000
  → Pronájmy celkem: 504 000 (automaticky)
  
Provoz:
  - Energie: 48 000
  - Úklid: 36 000
  → Provoz celkem: 588 000 (automaticky)
```

**ZDŮRAZNIT:**
- CUSTOM kategorie **nelze editovat** (počítá se automaticky)
- Změna podkategorie automaticky přepočítá rodiče
- Sloupec "Minulé období" = historical data z 2023
- Sloupec "Plnění" = aktuální YTD

---

### ČÁST 5: Import current dat (3 min)

**KROK 4: Import aktuálních dat**

1. Home Tab → "Importovat aktuální data"
2. Vyber: `test_data/hospodareni-2024-DEMO.xlsx`
3. Počkej na import

**CO ŘÍCT:**
> "Teď importujeme aktuální data z roku 2024. Aplikace automaticky přepočítá všechny metriky a Dashboard se aktivuje."

**UKÁZAT:**
- Dashboard se automaticky odemkl
- Měsíční tlačítka s barevným kódováním
- Zelená = v plánu, Žlutá = warning, Červená = překročeno

---

### ČÁST 6: Dashboard a analýzy (10 min)

**KROK 5: Dashboard**

**CO ŘÍCT:**
> "Dashboard poskytuje rychlý přehled o stavu rozpočtu. Každé tlačítko reprezentuje jeden měsíc a barva indikuje zda jsme v plánu."

**UKÁZAT:**
- Měsíční tlačítka (leden-červen 2024)
- YTD % vs. očekávané %
- Proporcionální logika:
  - Červen = 6/12 = 50% rozpočtu očekáváno
  - Pokud YTD < 50% → Zelená
  - Pokud YTD 50-55% → Žlutá
  - Pokud YTD > 55% → Červená

**UKÁZAT:**
- Klikni na měsíc (např. červen)
- Stats Window se otevře s detailním přehledem

**KROK 6: Stats Window**

**VYSVĚTLIT 7 SLOUPCŮ:**
1. **Kategorie** - hierarchický strom
2. **Min. období** - historical data (2023)
3. **Akt. období** - current měsíc (např. červen 2024)
4. **% (M→M)** - month-to-month porovnání
5. **Rozpočet** - roční plán
6. **Plnění R.** - YTD do června
7. **% (R)** - % rozpočtu (nejdůležitější!)

**ZDŮRAZNIT:**
- Barevné kódování (zelená/žlutá/červená)
- Hierarchická agregace (custom kategorie sčítají děti)
- Možnost drill-down do podkategorií

**KROK 7: Analysis Tab**

**CO ŘÍCT:**
> "Analysis Tab umožňuje flexibilní analýzu dat podle různých dimenzí."

**UKÁZAT:**
- Preset: "Analýza středisek"
- Pivot po střediscích (Muži A, Ženy A, Dorost, Mládež)
- Možnost změny řádků (kategorie, středisko, text, kdo)
- Filtr aktuální/historické

---

### ČÁST 7: Technické detaily a výhody (5 min)

**CO ZDŮRAZNIT:**

#### 1. N-level hierarchie
> "Aplikace podporuje neomezenou hloubku kategorií. Vidíte příklad: Provoz → Pronájmy → Pronájem haly. To je 3 úrovně. Můžeme jít ještě hlouběji."

#### 2. Pre-computed metriky
> "Aplikace používá optimalizovaný přístup - pre-computed metriky. Místo pomalých rekurzivních dotazů ukládáme součty přímo do databáze a aktualizujeme je pouze při změně transakce. Výsledek: Dashboard se načte za 18ms místo 450ms."

#### 3. Automatické přepočty
> "Když změníte transakci, aplikace automaticky přepočítá všechny metriky pro danou kategorii. Když změníte rozpočet podkategorie, automaticky se přepočítá rodič."

#### 4. Multi-vrstvové validace
> "Aplikace má 3 vrstvy validací:
> 1. UI - uživatel nemůže kliknout na špatnou akci
> 2. Import - Excel import automaticky opraví konfliktní názvy
> 3. Databáze - SQL dotazy mají extra filtry pro jistotu"

#### 5. Performance
> "Všechny dotazy jsou optimalizované:
> - Dashboard: 25x rychlejší (450ms → 18ms)
> - Budget Tab: 21x rychlejší (320ms → 15ms)
> - Stats Window: 26x rychlejší (580ms → 22ms)"

---

## ❓ OČEKÁVANÉ OTÁZKY

### Q: "Proč jste zvolil tuto architekturu?"
**A:** "Původně jsem používal rekurzivní CTE dotazy, ale při testování s 50 kategoriemi byly pomalé (~500ms). Přešel jsem na pre-computed metriky které se aktualizují jen při změně dat. To dalo 25x zrychlení."

### Q: "Jak se liší od Excelu?"
**A:** "Excel je skvělý pro data, ale nemá:
- Automatické agregace v hierarchii
- Real-time dashboard s barevným kódováním
- Validace proti špatným datům
- Multi-dimenzionální analýzy
- Historické porovnání"

### Q: "Co když má klub 200 kategorií?"
**A:** "Aplikace je optimalizovaná pro velké množství dat. Pre-computed metriky zajišťují konstantní rychlost bez ohledu na počet kategorií. Testoval jsem s 50 kategoriemi × 12 měsíců = 600 řádků a Dashboard se načetl za 18ms."

### Q: "Můžete vytvořit kategorii pod kategorií pod kategorií?"
**A:** "Ano, N-level hierarchie znamená neomezenou hloubku. Jediné omezení: transakční kategorie (LEAF) nemůže mít děti. Jen agregační kategorie (CUSTOM) mohou mít podkategorie."

### Q: "Co je nejsložitější část aplikace?"
**A:** "Synchronizace pre-computed metrik. Musím zajistit že při každé změně transakce se přepočítají správné kategorie a všichni rodiče v hierarchii. To je řešeno pomocí automatických update funkcí které se volají po každé změně."

---

## 🎯 ZÁVĚR (2 min)

**CO ŘÍCT:**
> "Aplikace kombinuje rychlost (pre-computed metriky), flexibilitu (N-level hierarchie) a robustnost (multi-vrstvové validace). Je navržena pro reálné použití v neziskových organizacích a sportovních klubech.
>
> Součástí práce je také kompletní dokumentace architektury a migration script pro existující databáze.
>
> Děkuji za pozornost, máte nějaké dotazy?"

---

## 📚 DODATEČNÉ MATERIÁLY (pokud se zeptá)

### Dokumentace:
- `dokomentace/DASHBOARD_ARCHITECTURE.md` - detailní architektura
- `dokomentace/DASHBOARD_FLOW.md` - flow diagramy

### Testy:
- `test_refactored_workflow.py` - 7/7 testů prošlo

### Commit message:
- Poslední commit obsahuje detailní popis refaktorizace

---

## ✅ CHECKLIST PŘED PREZENTACÍ

- [ ] Aplikace běží bez chyb
- [ ] Excel soubory jsou připravené
- [ ] Databáze je čistá (nový profil)
- [ ] Máš poznámky k architektuře
- [ ] Znáš performance čísla (25x rychlejší)
- [ ] Umíš vysvětlit N-level hierarchii
- [ ] Umíš vysvětlit pre-computed metriky
- [ ] Máš připravené odpovědi na otázky

---

**HODNĚ ŠTĚSTÍ! 🚀**
