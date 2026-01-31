# Vollständiger Übersetzungsplan

## Status: Button-Fix ✅ 
- Report-Button hat jetzt das richtige Styling (weiß, hellblau bei Hover, blau bei Click)
- Button ist am unteren Ende der Sidebar positioniert

## Noch zu übersetzen (MASSIVE Aufgabe):

### 1. PRIORITÄT HOCH: Sidebar Statistik-Tab
**Datei: `src/views/components/sidebar.py`** (Zeilen 1088-1340)

Hardcodierte deutsche Texte:
- "KUNDEN" → `sidebar.stats.customers_header`
- "Im Laden:" → `sidebar.stats.in_store`
- "Kunden" (Unit) → `sidebar.stats.customers_unit`
- "Gesamt bedient:" → `sidebar.stats.total_served`
- "Durchsatz:" → `sidebar.stats.throughput`
- "KUNDENZUFRIEDENHEIT" → `sidebar.stats.satisfaction_header`
- "Ø Wartezeit:" → `sidebar.stats.avg_wait_time`
- "In Warteschlange:" → `sidebar.stats.in_queue`
- "Längste Queue:" → `sidebar.stats.longest_queue`
- "Kasse #0 (0)" → Format: `sidebar.stats.checkout_queue_format`
- "⚡ KASSEN-STATUS" → `sidebar.stats.checkouts_status_header`
- "Offen:" → `sidebar.stats.open`
- "Störung:" → `sidebar.stats.malfunction`
- "Geschlossen:" → `sidebar.stats.closed`
- "Kassen" (Unit) → `sidebar.stats.checkouts_unit`
- "ZUFRIEDENHEITSSCORE" → `sidebar.stats.satisfaction_score_header`
- "Status: GUT/AKZEPTABEL/KRITISCH" → `sidebar.stats.status_good/acceptable/critical`

### 2. PRIORITÄT HOCH: stats_live_tab.py
**Datei: `src/views/components/stats_live_tab.py`**

Alle Labels übersetzen (identisch zu sidebar.py Zeilen 1088-1340)

### 3. PRIORITÄT HOCH: stats_details_tab.py
**Datei: `src/views/components/stats_details_tab.py`**

Hardcodierte deutsche Texte:
- "ARTIKEL-STATISTIKEN" → `sidebar.stats.details.items_header`
- "Gesamt gescannt:" → `sidebar.stats.details.items_scanned`
- "Ø pro Kunde:" → `sidebar.stats.details.avg_per_customer`
- "Artikel" (Unit) → `sidebar.stats.details.items_unit`
- "HEUTE BEDIENT" → `sidebar.stats.details.served_today`
- "ZAHLUNGSMETHODEN" → `sidebar.stats.details.payment_methods`
- "Bargeld:" → `sidebar.stats.details.cash`
- "Karte:" → `sidebar.stats.details.card`
- "KASSEN-PROBLEME" → `sidebar.stats.details.checkout_problems`
- "Störungen:" → `sidebar.stats.details.malfunctions`
- "Verärgerungen:" → `sidebar.stats.details.annoyances`
- "Konflikte:" → `sidebar.stats.details.conflicts`
- "ÖFFNUNGSZEITEN" → `sidebar.stats.details.opening_hours`
- "Verstrichen:" → `sidebar.stats.details.elapsed`
- "Geplant:" → `sidebar.stats.details.scheduled`
- "Überzeit:" → `sidebar.stats.details.overtime`

### 4. PRIORITÄT HOCH: stats_log_tab.py (Protokoll)
**Datei: `src/views/components/stats_log_tab.py`**

- "Ereignis-Protokoll" → `sidebar.stats.log.header`
- Alle Event-Messages (wird komplex, da dynamisch generiert)

### 5. PRIORITÄT MITTEL: Export-Funktionalität
**Datei: `src/views/statistics_dialogs.py`**

- CSV Header-Texte übersetzen
- Export-Button-Tooltips
- "Vollständiger Datensatz für Entwickler und API-Integration" → Tooltip-Text
- "Tabellarische Daten für Excel, Pivot-Tabellen, etc." → Tooltip-Text
- "Druckfertiger professioneller Report (in Entwicklung)" → Tooltip-Text

### 6. PRIORITÄT NIEDRIG: Checkout-Dialog
**Datei: `src/views/statistics_dialogs.py`** (CheckoutStatsDialog)

- Alle Status-Texte
- Form-Labels

### 7. PRIORITÄT NIEDRIG: Controller-Meldungen
**Dateien: `src/controllers/*.py`**

- Print-Statements
- Error-Messages
- Debug-Ausgaben

## Geschätzte Anzahl der Änderungen:
- **~200+ Übersetzungsschlüssel** müssen zu de.json/en.json hinzugefügt werden
- **~150+ Code-Zeilen** müssen geändert werden (Labels durch translator.get() ersetzen)

## Empfohlenes Vorgehen:
1. ✅ Button-Fix (ERLEDIGT)
2. ⏳ Sidebar Stats-Tab komplett übersetzen (NÄCHSTER SCHRITT)
3. ⏳ stats_live_tab.py übersetzen
4. ⏳ stats_details_tab.py übersetzen
5. ⏳ stats_log_tab.py übersetzen
6. Export-Texte übersetzen
7. Controller-Meldungen übersetzen

Möchten Sie, dass ich jetzt mit Schritt 2-5 fortfahre?
