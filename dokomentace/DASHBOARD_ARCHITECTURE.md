# 📊 Dashboard & Stats Window - Architektura a Funkčnost

## 🎯 Přehled
Dashboard poskytuje vizuální přehled rozpočtového plnění po měsících. Stats Window zobrazuje detailní hierarchický rozpis kategorií s porovnáním historických dat a rozpočtu.

---

## 🏗️ Architektura - Tok dat

```
┌─────────────────────────────────────────────────────────────────────┐
│                         UŽIVATELSKÉ AKCE                             │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
                    ▼                               ▼
        ┌─────────────────────┐         ┌─────────────────────┐
        │   Budget Tab        │         │   Home Tab          │
        │   (budget_tab.py)   │         │   (home_tab.py)     │
        └─────────────────────┘         └─────────────────────┘
                    │                               │
                    │ set_budget()                  │ add/edit/delete
                    │                               │ transaction()
                    ▼                               ▼
        ┌─────────────────────────────────────────────────────┐
        │            budgets_db.py / items_db.py              │
        │  - update_or_insert_budget()                        │
        │  - update_custom_category_budgets()                 │
        │  - check_budget_completeness()                      │
        └─────────────────────────────────────────────────────┘
                                    │
                                    │ invalidate_cache()
                                    ▼
        ┌─────────────────────────────────────────────────────┐
        │              Dashboard Tab (dashboard_tab.py)        │
        │  - _refresh_dashboard()                             │
        │  - check completeness → locked/unlocked             │
        └─────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
                    ▼                               ▼
        ┌─────────────────────┐         ┌─────────────────────┐
        │   Locked View       │         │   Months View       │
        │   🔒 Dashboard      │         │   📅 12 tlačítek    │
        │   zamčen            │         │   (barevně)         │
        └─────────────────────┘         └─────────────────────┘
                                                    │
                                                    │ click
                                                    ▼
                                        ┌─────────────────────┐
                                        │   Stats Window      │
                                        │   (stats_window.py) │
                                        │   📊 Detail měsíce  │
                                        └─────────────────────┘
```

---

## 🔄 Invalidace Cache - CO TO JE A PROČ?

### Problém: Stará data v UI
Když uživatel přidá/upraví/smaže transakci nebo změní rozpočet, **Dashboard má staré (cached) hodnoty**. Bez invalidace by se nezobrazily aktuální částky a barvy tlačítek.

### Jak Dashboard vzniká?
```python
# home_tab.py řádek ~120
def _show_dashboard(self):
    """Dashboard se vytváří DYNAMICKY až když jsou splněny podmínky."""
    from ui.tabs.dashboard_tab import DashboardTab
    
    # Vytvoříme instanci dashboardu
    self.dashboard_instance = DashboardTab(self.tab_frame, self.app)
    
    # ⚠️ DŮLEŽITÉ: Uložíme referenci do app pro pozdější invalidaci
    self.app.dashboard_ui = self.dashboard_instance  # <-- Tady!
```

**PROČ ukládáme referenci?**  
Dashboard se vytváří až na koncu (když jsou data + rozpočet), ale později potřebujeme říct dashboardu "aktualizuj se!" když uživatel přidá transakci.

### Tok invalidace:
```
1. User přidá transakci "Nákup 500 Kč" → sources_tab nebo jiný import
   ↓
2. Data se uloží do DB (items tabulka)
   ↓
3. main_app.import_excel() zavolá:
   if hasattr(self, 'dashboard_ui'):
       self.dashboard_ui.invalidate_cache()  # <-- Používá uloženou referenci!
   ↓
4. dashboard_tab.invalidate_cache() zavolá _refresh_dashboard()
   ↓
5. _refresh_dashboard() znovu načte data z DB a překreslí tlačítka
   ↓
6. Uživatel vidí aktualizované hodnoty a barvy! ✅
```

### Co je "invalidate_cache()"?
```python
# dashboard_tab.py
def invalidate_cache(self):
    """
    Vymaže cache (staré hodnoty) a znovu načte data z databáze.
    
    V našem případě cache = stav tlačítek (barvy, texty).
    Po změně dat v DB musíme tlačítka překreslit s novými hodnotami.
    """
    self._refresh_dashboard()  # Znovu načte a překreslí
```

### PROČ ukládáme referenci na `app`?
```python
# home_tab.py - konstruktor
def __init__(self, tab_frame, app_controller):
    self.app = app_controller  # <-- Reference na hlavní aplikaci
```

**Důvod:** Home Tab vytváří Dashboard, ale později nemá přímou referenci na něj (Dashboard je v proměnné `dashboard_instance`). Proto komunikujeme přes **centrální app controller**:

```
┌─────────────┐
│  Main App   │  ← Centrální controller
│  (app)      │     Má referenci na všechny komponenty
└─────────────┘
       │
       ├─→ home_tab (vytváří dashboard)
       ├─→ sources_tab (importuje data)
       ├─→ budget_tab (mění rozpočet)
       └─→ dashboard_ui (potřebuje se aktualizovat)

Tok:
sources_tab → app.import_excel() → app.dashboard_ui.invalidate_cache()
```

**Alternativní řešení (bez app reference):**
- ❌ Event bus / Observer pattern (složitější, overkill pro malou aplikaci)
- ❌ Polling (neefektivní - kontrolovat DB každou vteřinu)
- ❌ Manual refresh button (špatný UX - uživatel musí klikat)
- ✅ **Centrální controller (náš přístup)** - jednoduché a funkční!

---

## 🔒 Dashboard Lock Logic

### PROČ zamykat Dashboard?
Pokud uživatel má nastavený rozpočet jen pro ČÁST kategorií, Dashboard by zobrazoval **zavádějící data**:
- YTD 5000 Kč / Rozpočet 10000 Kč = 50% ✅ (zelená)
- Ale chybí rozpočet pro další 3 kategorie!
- Ve skutečnosti už může být překročeno!

### Řešení: Kompletní rozpočet nebo nic
```python
# dashboard_tab._refresh_dashboard()
completeness = budgets_db.check_budget_completeness(...)

if not completeness['is_complete']:
    # 🔒 Zobraz locked screen + seznam chybějících kategorií
    self._show_locked_view(completeness['missing_categories'])
else:
    # ✅ Zobraz měsíční tlačítka
    self._show_months_view()
```

### Co kontroluje `check_budget_completeness()`?
```sql
-- Najde všechny transakční kategorie (non-custom)
SELECT k.id, k.nazev
FROM kategorie k
WHERE k.typ = 'výdej'  -- nebo 'příjem'
  AND k.is_custom = 0   -- jen transakční

-- Zkontroluje které MAJÍ rozpočet
SELECT k.id
FROM kategorie k
JOIN rozpocty r ON r.kategorie_id = k.id
WHERE r.rok = 2025
```

**Pokud chybí alespoň 1 kategorie → Dashboard LOCKED** 🔒

---

## 📊 Stats Window - Hierarchická agregace

### 7 sloupců
| Sloupec | Co zobrazuje | Zdroj |
|---------|--------------|-------|
| Kategorie | Hierarchický strom | `kategorie.nazev` + rekurzivní CTE |
| Min.transakce | Historické data (is_current=0) | `SUM(items WHERE is_current=0)` |
| Akt.transakce | Aktuální YTD (is_current=1) | `SUM(items WHERE is_current=1)` |
| %(M→M) | Month-to-month comparison | `(current / historical) * 100` |
| Rozpočet | Celý rok | `rozpocty.planovana_castka` |
| Plnění R. | YTD proti rozpočtu | `SUM(items YTD)` |
| %(R) | Rozpočtové plnění | `(ytd / budget) * 100` |

### Barevné kódování
```python
# %(M→M) - světlé barvy (informativní)
≤ 80%   → Světle zelená  #e8f5e9  (výborně!)
≤ 100%  → Světle žlutá   #fffde7  (ok)
> 100%  → Světle červená #ffebee  (varování)
NOVÉ    → Světle modrá   #e3f2fd  (nová položka bez historie)

# %(R) - sytější barvy (akční - rozpočet!)
≤ 80%   → Zelená         #c8e6c9  (máš rezervu)
≤ 100%  → Žlutá          #fff9c4  (blíží se limit)
> 100%  → Červená        #ffcdd2  (PŘEKROČENO!)
```

**Priorita barvy řádku:** Pokud %(R) != šedá, použij %(R) barvu. Jinak %(M→M).

---

## 🎨 Dashboard Tlačítka - Barevná logika

### Proporcionální YTD logic
```python
ytd_percentage = (ytd_spending / total_budget) * 100
expected_percentage = (month / 12) * 100

# Příklad: Červen (měsíc 6)
# Očekáváme: 6/12 = 50% rozpočtu
# Skutečnost: 45% → ZELENÁ (v limitu)
# Skutečnost: 52% → ŽLUTÁ (warning, ale OK)
# Skutečnost: 58% → ČERVENÁ (přečerpání!)
```

### Barvy
```python
if ytd_percentage <= expected_percentage:
    color = "#c8e6c9"  # ✅ Zelená - v limitu
elif ytd_percentage <= expected_percentage + 5:
    color = "#fff9c4"  # ⚠️ Žlutá - mírné překročení
else:
    color = "#ffcdd2"  # 🚨 Červená - výrazné překročení
```

**PROČ +5% tolerance?** Drobné odchylky jsou normální, nechceme "false alarms".

---

## 🔍 SQL Optimalizace - Rekurzivní CTE

### Problém: Hierarchie kategorií
```
Bydlení (custom)
  ├─ Nájem (transakční)
  ├─ Energie (transakční)
  └─ Internet (transakční)
```

**Chceme:** Součet Bydlení = Nájem + Energie + Internet

### Naivní řešení (POMALÉ ❌)
```python
# Pro každou kategorii samostatný SQL dotaz
for category in categories:
    for child in get_children(category):
        sum += get_transactions(child)
        for grandchild in get_children(child):
            sum += get_transactions(grandchild)
            # atd...
```
**Problém:** O(n²) dotazů! Pro 50 kategorií = 2500+ dotazů!

### Rekurzivní CTE (RYCHLÉ ✅)
```sql
WITH RECURSIVE tree(ancestor_id, descendant_id) AS (
    -- Základní případy: každá kategorie je sama sobě potomek
    SELECT id, id FROM kategorie WHERE typ = 'výdej'
    
    UNION ALL
    
    -- Rekurze: přidej všechny potomky
    SELECT t.ancestor_id, k.id
    FROM tree t
    JOIN kategorie k ON k.parent_id = t.descendant_id
)
-- Nyní máme kompletní mapu: (předek → potomek)
-- Bydlení → Bydlení
-- Bydlení → Nájem
-- Bydlení → Energie
-- Bydlení → Internet
```

**Výsledek:** **1 SQL dotaz** pro všechny kategorie! 🚀

### Použití
```sql
SELECT 
    a.nazev,
    COALESCE(SUM(i.castka), 0) AS total
FROM kategorie a
LEFT JOIN tree t ON t.ancestor_id = a.id
LEFT JOIN items i ON i.kategorie_id = t.descendant_id
GROUP BY a.id
```

---

## 💰 ABS() hodnoty - PROČ?

### Problém: Výdaje jsou záporné
```
DB: castka = -500  (výdej)
DB: castka = +1000 (příjem)
```

### UI očekává kladné hodnoty
```
Dashboard: "5000 Kč" (ne "-5000 Kč")
Stats: "Rozpočet: 50000 Kč" (ne "-50000 Kč")
```

### Řešení: ABS() všude
```sql
SUM(ABS(i.castka))  -- -500 → 500
ABS(r.planovana_castka)  -- -50000 → 50000
```

```python
budget = abs(row['budget'])  # UI zobrazí kladně
ytd_current = abs(row['ytd_current'])  # UI zobrazí kladně
```

**DŮLEŽITÉ:** ABS() voláme až při zobrazení, ne při ukládání! V DB zůstávají výdaje záporné (pro budoucí analýzy).

---

## 🎯 Custom kategorie - Automatický přepočet

### Co jsou custom kategorie?
```
Bydlení (custom, is_custom=1)  ← TOTO
  ├─ Nájem (transakční, is_custom=0)
  ├─ Energie (transakční, is_custom=0)
  └─ Internet (transakční, is_custom=0)
```

**Custom kategorie = agregát podkategorií** (nemůže mít vlastní transakce)

### PROČ je nelze editovat přímo?
```python
# budget_tab.py - validace při dvojkliku
if db.is_custom_category(cat_id):
    messagebox.showinfo(
        "Nelze editovat",
        "Rozpočet custom kategorie se počítá automaticky..."
    )
    return
```

**Důvod:** Předejít duplicitnímu počítání!

```
Příklad špatně:
Bydlení rozpočet = 15000 Kč (ručně nastaveno)
  Nájem = 8000
  Energie = 4000
  Internet = 1000
Celkem = 15000 + 8000 + 4000 + 1000 = 28000 Kč ❌ DUPLICITA!

Správně:
Bydlení rozpočet = auto (8000 + 4000 + 1000 = 13000 Kč)
  Nájem = 8000
  Energie = 4000
  Internet = 1000
Celkem = 13000 Kč ✅ CORRECT!
```

### Automatický přepočet
```python
# budget_tab._on_double_click_budget() po uložení
db.update_or_insert_budget(...)  # Ulož podkategorii
db.update_custom_category_budgets(...)  # ← Auto přepočet!
```

```python
# budgets_db.update_custom_category_budgets()
for custom_category in custom_categories:
    total = SUM(rozpocty WHERE parent_id = custom_category)
    UPDATE rozpocty SET planovana_castka = total
```

---

## 🔄 Filtrace kategorií - JEN S ROZPOČTEM

### PROČ?
Dashboard a Stats Window ukazují **plnění rozpočtu**. Pokud kategorie nemá rozpočet, nemůžeme počítat plnění!

```
Kategorie "Dárky": Žádný rozpočet
YTD: 2000 Kč
Plnění: 2000 / ??? = ??? %  ❌ NEMÁ SMYSL!
```

### Implementace
```sql
-- dashboard_db.get_month_total_budget_summary()
SELECT SUM(ABS(i.castka))
FROM items i
WHERE ...
  AND EXISTS (
      SELECT 1 FROM rozpocty r
      WHERE r.kategorie_id = k.id
      AND r.rok = ?
  )  -- ← JEN kategorie S rozpočtem!
```

```python
# stats_window._load_data()
for row in performance_data:
    if row['id'] in budgets:  # ← JEN kategorie S rozpočtem!
        month_data.append(row)
```

---

## 🎭 Edge Cases - Okrajové případy

### 1. Žádný rozpočet
```python
if total_budget == 0:
    return None  # Dashboard locked
```

### 2. Nulové hodnoty
```python
# calculate_performance_percentage()
if historical == 0:
    if current > 0:
        return -1.0  # Speciální: NOVÁ položka
    else:
        return 0.0  # Žádná data
```

### 3. Záporný rozpočet (výdaje)
```python
budget = abs(row['budget'])  # Vždy zobrazíme kladně
```

### 4. Custom kategorie bez podkategorií
```python
# update_custom_category_budgets()
total_budget = 0  # Pokud žádné podkategorie
```

---

## 📱 API Reference

### `budgets_db.py`
```python
check_budget_completeness(db_path, transaction_type, year) → dict
    """Zkontroluje jestli všechny kategorie mají rozpočet."""
    Returns: {
        'is_complete': bool,
        'total_categories': int,
        'categories_with_budget': int,
        'missing_categories': list
    }

get_total_budget_for_type(db_path, transaction_type, year) → float
    """Celkový roční rozpočet (jen non-custom)."""

update_custom_category_budgets(db_path, year) → None
    """Automaticky přepočítá rozpočty custom kategorií."""
```

### `dashboard_db.py`
```python
get_year_performance_summary(db_path, transaction_type, year) → list[dict]
    """Kompletní roční přehled pro stats_window (12 měsíců × všechny kategorie)."""
    Returns: [{
        'id', 'nazev', 'typ', 'parent_id', 'is_custom', 'month',
        'historical', 'current', 'own_historical', 'own_current',
        'own_percentage', 'total_percentage', 'worst_percentage'
    }, ...]

calculate_category_worst_case(performance_data) → dict
    """Vypočítá worst_percentage rekurzivně (propagace z dětí na rodiče)."""

get_month_total_budget_summary(db_path, transaction_type, month, year) → dict
    """Celkový rozpočet a YTD pro Dashboard tlačítko."""
    Returns: {
        'total_budget': float,
        'ytd_spending': float,
        'ytd_percentage': float
    }
```

### `dashboard_tab.py`
```python
invalidate_cache() → None
    """Znovu načte dashboard data (volá _refresh_dashboard)."""

_refresh_dashboard() → None
    """Zkontroluje kompletnost rozpočtu → locked/unlocked view."""

_update_month_buttons() → None
    """Aktualizuje barvy a texty měsíčních tlačítek."""
```

### `stats_window.py`
```python
invalidate_cache() → None
    """Znovu načte stats window data (volá _load_data)."""

_load_data() → None
    """Načte performance data, rozpočty, YTD → zobrazí hierarchii."""
```

---

## 🐛 Debugging Tips

### Dashboard neukazuje aktuální data
```python
# Zkontroluj jestli se volá invalidace
# home_tab._save_item() → self.app.invalidate_dashboard_cache()
print(f"Invalidating dashboard cache after save")
```

### Stats window má jiná čísla než Dashboard
```python
# Zkontroluj filtraci kategorií s rozpočtem
# stats_window._load_data()
print(f"Categories with budget: {len(budgets)}")
print(f"Filtered data: {len(month_data)}")
```

### Custom kategorie má špatný rozpočet
```python
# Zkontroluj jestli se volá auto přepočet
# budget_tab._on_double_click_budget() po uložení
db.update_custom_category_budgets(self.app.profile_path, year)
```

### Dashboard locked i když jsou všechny rozpočty
```python
# Debug check_budget_completeness()
completeness = budgets_db.check_budget_completeness(...)
print(f"Missing: {completeness['missing_categories']}")
```

---

## 🚀 Performance

### Optimalizace
- ✅ **1 SQL query** pro celý rok (ne 12× samostatně)
- ✅ **Rekurzivní CTE** pro hierarchii (ne N dotazů)
- ✅ **Pre-agregace** pomocí `items_agg` a `budgets_agg`
- ✅ **COALESCE** místo NULL kontroly v Pythonu
- ✅ **EXISTS** místo JOIN pro kontrolu rozpočtu

### Měření
```python
import time
start = time.time()
data = dashboard_db.get_year_performance_summary(...)
print(f"Loaded in {time.time() - start:.2f}s")
# Typicky: 0.05s pro 50 kategorií × 12 měsíců = 600 řádků
```

---

## ✅ Checklist pro commit

- [x] Smazány duplicitní funkce (`get_month_category_comparison`, `debug_month_data`)
- [x] Smazána duplicitní sekce v `dashboard_tab.py`
- [x] Konzistentní YTD logika (jen kategorie s rozpočtem)
- [x] Konzistentní rozpočet agregace (jen non-custom)
- [x] Dashboard lock implementován
- [x] Invalidace cache funguje
- [x] Barevné kódování jednotné
- [x] Dokumentace vytvořena

**Ready for commit!** 🎉
