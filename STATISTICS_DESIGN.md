# Statistik-Design für Kassensimulator

## 1. KUNDENFLUSS (Globale Kundensicht)

### 1.1 Zeitmetriken – Kunden im Laden

**Fokus:** Wie lange Kunden insgesamt im Laden verbringen (vom Betreten bis Verlassen)

- **Minimale Zeit** (Min): Schnellster Kunde
- **Maximale Zeit** (Max): Langsamster Kunde
- **Durchschnittliche Zeit** (Ø): Typischer Aufenthalt
- **Stichwörter:** Verweildauer, Ladendurchsatz, Shopper-Effizienz

**Darstellung:**

- **Tabelle:** Min / Max / Ø Werte nebeneinander
- **Box-Plot:** Verteilung mit Quartilen visualisieren
- **Histogramm:** Häufigkeitsverteilung der Verweilzeiten

### 1.2 Zeitmetriken – Kunden in der Warteschlange

**Fokus:** Wie lange Kunden durchschnittlich vor der Kasse warten

- **Minimale Zeit** (Min): Schnellster Zugang
- **Maximale Zeit** (Max): Längste Wartezeit
- **Durchschnittliche Zeit** (Ø): Typische Wartezeit
- **Stichwörter:** Queue-Dauer, Warteschlangen-Performance, Customer Satisfaction

**Darstellung:**

- **Tabelle:** Min / Max / Ø Werte
- **Gauge/Speedometer:** Ø-Wartezeit gegen Zielwert (z.B. max. 5 Min)
- **Zeitreihen-Diagramm:** Wartezeit über Tagesverlauf

### 1.3 Zeitmetriken – Kunden an der Kasse (Service)

**Fokus:** Wie lange Kunden bei der Bezahlung an der Kasse stehen

- **Minimale Zeit** (Min): Schnellster Service
- **Maximale Zeit** (Max): Längster Service
- **Durchschnittliche Zeit** (Ø): Typische Kassenzeit
- **Stichwörter:** Gesamtservicezeit, Checkout-Effizienz, Kundenzufriedenheit

**Darstellung:**

- **Tabelle:** Min / Max / Ø Werte
- **Balkendiagramm:** Vergleich Min/Ø/Max nebeneinander
- **Box-Plot:** Verteilung mit Ausreißern

---

## 2. GESAMTSTATISTIKEN (Globale Aggregates)

### 2.1 Kundenanzahl

**Fokus:** Wie viele Kunden wurden bedient, klassifiziert nach Typ

- **Anzahl Normal-Kunden:** Reguläre Kunden (zu Fuß)
- **Anzahl Eingeschränkt-Kunden:** Kunden mit Behinderungen (z.B. Rollstuhl, langsamere Bewegung)
- **Gesamte Kundenanzahl:** Sum (Normal + Eingeschränkt)
- **Stichwörter:** Customer Count, Accessibility, Traffic Volume

**Darstellung:**

- **Tabelle:** Alle drei Zahlen übersichtlich
- **Kreisdiagramm (Pie Chart):** Anteil Normal vs. Eingeschränkt
- **Balkendiagramm:** Absolute Werte

### 2.2 Artikel-Verarbeitung

**Fokus:** Gesamtumsatz (in Stückzahl)

- **Gesamte gescannte Artikel:** Summe aller Items über alle Kunden
- **Durchschnitt Items pro Kunde:** Ø (Total Items / Total Customers)
- **Stichwörter:** Throughput, Average Basket Size, Item Count

**Darstellung:**

- **Tabelle:** Total Items + Ø Items/Kunde
- **Kennzahl-Anzeige:** Große Zahlen prominent angezeigt

---

## 3. BEZAHLMETHODEN (Globale Verteilung)

### 3.1 Zahlungsart-Verteilung

**Fokus:** Wie Kunden bezahlen und deren Effizienz

- **Anteil Barverkäufe:** % (Cash / Total)
- **Anteil Kartenzahlungen:** % (Card / Total)
- **Stichwörter:** Payment Method Distribution, Cash vs. Digital

**Darstellung:**

- **Kreisdiagramm (Pie Chart):** Anteil Bar vs. Karte
- **Balkendiagramm:** Prozentuale Verteilung
- **Tabelle:** Absolute Anzahl + Prozent

### 3.2 Zahlungszeiten nach Methode

**Fokus:** Durchschnittliche Bezahldauer pro Zahlungsart

- **Durchschnitt Barzahlung:** Ø Dauer (Bargeld)
- **Durchschnitt Kartenzahlung:** Ø Dauer (Karte / Kontaktlos)
- **Min/Max pro Zahlungsart:** Range per method
- **Stichwörter:** Payment Speed, Processing Time, Method Efficiency

**Darstellung:**

- **Balkendiagramm (Grouped):** Bar vs. Karte mit Min/Ø/Max
- **Tabelle:** Detaillierte Werte für beide Methoden
- **Komparativ-Anzeige:** "Kartenzahlung ist X% schneller"

---

## 4. JE KASSE (Kassierer/Checkout-Perspektive)

### 4.1 Service-Zeiten pro Kasse

**Fokus:** Wie schnell Kassierer scannen und Kunden bezahlen lassen (Kassen-spezifisch)

#### Scanning-Dauer (nur das Artikel-Scannen)

- **Durchschnitt (Ø):** Mittlere Scan-Zeit pro Artikel
- **Minimum (Min):** Schnellster Scan
- **Maximum (Max):** Langsamster Scan
- **Stichwörter:** Artikel-Verarbeitung, Kassierer-Skill (Azubi vs. Pro)

**Darstellung:**

- **Tabelle:** Min / Ø / Max pro Kasse
- **Balkendiagramm:** Vergleich zwischen Kassen

#### Bezahl-Dauer (nur Bezahlung an der Kasse)

- **Durchschnitt (Ø):** Mittlere Bezahl-Zeit
- **Minimum (Min):** Schnellste Bezahlung
- **Maximum (Max):** Längste Bezahlung
- **Stichwörter:** Payment Processing, Finalisierung, Checkout-Abschluss

**Darstellung:**

- **Tabelle:** Min / Ø / Max pro Kasse
- **Balkendiagramm:** Vergleich zwischen Kassen

### 4.2 Warteschlange pro Kasse

**Fokus:** Queue-Längen und Staus an dieser Kasse

- **Durchschnittliche Länge (Ø):** Typische Queue-Länge
- **Minimum (Min):** Kürzeste Queue
- **Maximum (Max):** Längste Queue
- **Stichwörter:** Queue Depth, Waiting Customers, Congestion

**Darstellung:**

- **Tabelle:** Min / Ø / Max pro Kasse
- **Zeitreihen-Diagramm:** Queue-Länge über Tagesverlauf pro Kasse
- **Balkendiagramm:** Queue-Vergleich zwischen Kassen

### 4.3 Konflikte pro Kasse (Kreisdiagramm / Kategorien)

**Fokus:** Typen von Problemen, die an dieser Kasse auftraten

- **Normal (keine Probleme):** % Zeit, dass alles glatt lief
- **Kassenstörung (Malfunction):** % Zeit, dass Kasse Fehler hatte
- **Verärgerte Kunden (Conflict):** % Zeit, dass Kunden ungeduldig wurden
- **Stichwörter:** Problem Distribution, Conflict Types, Downtime Cause

**Darstellung:**

- **Kreisdiagramm (Pie Chart):** Dreiteilung Normal / Störung / Konflikt pro Kasse
- **Stacked Balkendiagramm:** Alle Kassen nebeneinander mit Anteilen
- **Tabelle:** Absolute Zeiten + Prozentanteile

### 4.4 Verfügbarkeit pro Kasse

**Fokus:** Wie lange war die Kasse betriebsbereit

- **Uptime (%):** Prozentsatz der Zeit, dass Kasse offen/verfügbar war
- **Downtime (%):** Prozentsatz der Zeit, dass Kasse nicht verfügbar war
  - **Störungs-Downtime:** Wie lange Kasse wegen technischer Probleme ausfiel
  - **Konflikt-Downtime:** Wie lange Kasse wegen Kundenproblemen blockiert war
- **Reparaturdauer (Total):** Gesamte Zeit, die Reparaturen benötigten
- **Konflikt-Lösungs-Dauer (Total):** Gesamte Zeit für Deeskalation
- **Stichwörter:** Availability, MTTR (Mean Time To Repair), System Reliability

**Darstellung:**

- **Gauge/Speedometer:** Uptime % pro Kasse
- **Stacked Balkendiagramm:** Uptime vs. Störungs-Downtime vs. Konflikt-Downtime
- **Tabelle:** Uptime %, Fehler-Zeiten, Konflikt-Zeiten
- **Zeitreihen:** Verfügbarkeit über Tagesverlauf

### 4.5 Kundentypen pro Kasse

**Fokus:** Wer hat an dieser Kasse bezahlt

- **Anzahl Normal-Kunden:** Reguläre Kunden an dieser Kasse
- **Anzahl Eingeschränkt-Kunden:** Behinderte/langsame Kunden an dieser Kasse
- **Anzahl mit Handscanner:** Kunden, die Handheld-Scanner nutzten
- **Stichwörter:** Customer Mix, Accessibility Handling, Scanner Usage

**Darstellung:**

- **Kreisdiagramm:** Anteil der Kundentypen pro Kasse
- **Gestapeltes Balkendiagramm:** Alle Kassen mit Typ-Mix nebeneinander
- **Tabelle:** Absolute Zahlen pro Kasse

### 4.6 Artikel-Verarbeitung pro Kasse

**Fokus:** Workload dieser Kasse

- **Gesamte gescannte Artikel:** Summe Items an dieser Kasse
- **Durchschnitt Items pro Kunde:** Ø Basket Size für diese Kasse
- **Stichwörter:** Workload, Throughput per Checkout, Item Volume

**Darstellung:**

- **Balkendiagramm:** Total Items pro Kasse
- **Tabelle:** Total Items + Ø Items/Kunde

### 4.7 Zahlungsmethoden pro Kasse

**Fokus:** Wie wurde an dieser Kasse bezahlt

- **Anzahl Barzahlungen:** Häufigkeit Cash
- **Anzahl Kartenzahlungen:** Häufigkeit Card
- **Durchschnitt Barzahlung (Zeit):** Ø Duration Cash
- **Durchschnitt Kartenzahlung (Zeit):** Ø Duration Card
- **Stichwörter:** Payment Mix, Method-Specific Performance

**Darstellung:**

- **Kreisdiagramm:** Bar vs. Karte Anteil pro Kasse
- **Balkendiagramm (Grouped):** Bar und Karte mit deren Zeiten nebeneinander
- **Tabelle:** Absolute Anzahl + Ø-Zeiten

---

## 5. ZUSÄTZLICHE STATISTIKEN (Empfehlungen & Verbesserungen)

### 5.1 Kassierer-Skill Impact (Fokus: Kassier-Effizienz)

**Neu:** Unterscheidung nach Kassierer-Qualifikation

- **"Azubi"-Kassen:** Durchschnittliche Scan-/Bezahl-Zeiten für unerfahrene Kassierer
- **"Pro"-Kassen:** Durchschnittliche Scan-/Bezahl-Zeiten für erfahrene Kassierer
- **Skill-Efficiency-Ratio:** Wie viel schneller ist "Pro" vs. "Azubi" (z.B. 1.3x schneller)
- **Stichwörter:** Staff Performance, Training Impact, Expertise Effect

**Warum:** Die Simulation unterscheidet bereits Skill-Level; diese Metrik zeigt direkten ROI von besserer Schulung.

**Darstellung:**

- **Vergleich-Balkendiagramm:** Azubi vs. Pro Scan-Zeit und Bezahl-Zeit nebeneinander
- **KPI-Anzeige:** Efficiency Ratio als Kennzahl (z.B. "1.35x schneller")
- **Tabelle:** Detaillierte Min/Ø/Max für beide Skill-Level

### 5.2 Kundenzufriedenheits-Index (Indirekt aus Wartezeiten berechnen)

**Neu:** Synthethischer Score für Kundenerlebnis

- **Durchschnittliche Gesamt-Verweildauer:** Idealerweise < 20 Min
- **Durchschnittliche Wartezeit an Kasse:** Idealerweise < 5 Min
- **Satisfaction Score:** Z.B. 100 wenn alle < Zielzeiten, sonst graduated falloff
- **Stichwörter:** Customer Experience, SLA Compliance, Quality Metric

**Warum:** Hilft Betreibern zu verstehen, wie glücklich Kunden wahrscheinlich sind.

**Darstellung:**

- **Gauge/Speedometer:** Satisfaction Score von 0–100
- **Fortschrittsbalken:** Visuelle Bewertung (grün = gut, gelb = ok, rot = schlecht)
- **Tabelle:** Score mit Erklärung (z.B. "Verweildauer 18 Min (Ziel: < 20)")

### 5.3 Peak-Load-Analyse (Zeitbasiert)

**Neu:** Spitzenlast-Momente verstehen

- **Höchste Queue-Länge (Global):** Wann entstand größter Stau
- **Durchschnittliche Kundenzahl im Laden (Zeitfenster):** Z.B. 9-10 Uhr vs. 15-16 Uhr
- **Busiest Hour:** Welche Stunde hatte meisten Kunden
- **Stichwörter:** Peak Management, Staffing Needs, Rush Hour

**Warum:** Kassensimulation ist szenariobasiert; Peak-Analyse hilft bei Personalplanung.

**Darstellung:**

- **Zeitreihen-Diagramm (Line Chart):** Kundenzahl im Laden über Tagesverlauf
- **Balkendiagramm:** Queue-Längen stündlich
- **Tabelle:** Peak-Hour mit max. Queue-Länge und Kundenzahl
- **Heatmap (optional):** Auslastung je Kasse über Zeit

### 5.4 Checkout-Effektivitäts-Ratio (je Kasse)

**Neu:** Normalisierer für Vergleich zwischen Kassen

- **Kasse X Effizienz Score:** (Items Processed) / (Total Time including Downtime)
- **Relative Ranking:** Kasse A war 10% effizienter als Kasse B
- **Stichwörter:** KPI, Comparative Performance, Benchmark

**Darstellung:**

- **Ranking-Tabelle:** Kassen sortiert nach Effizienz-Score
- **Balkendiagramm:** Effizienz-Score pro Kasse mit Benchmark-Linie
- **Farbcodierung:** Grün (gut) bis Rot (schlecht)

### 5.5 Fehlerrate & Reparaturmuster

**Neu:** Predictive Maintenance Input

- **Fehlerrate pro Kasse:** % (Störungen / Betriebsstunden)
- **Durchschnittliche Reparaturdauer:** Wie lange dauert Reparatur typischerweise
- **Häufigste Fehler-Uhrzeit:** Neigt sich zu bestimmten Zeiten zu Fehlern?
- **Stichwörter:** Maintenance Prediction, System Reliability, Preventive Care

**Warum:** Supermarkt-Betreiber können so Wartungspläne optimieren.

**Darstellung:**

- **Tabelle:** Fehlerrate % + durchschnittliche Reparaturdauer pro Kasse
- **Zeitreihen:** Fehler über Tagesverlauf (um Muster zu erkennen)
- **Balkendiagramm:** Fehlerrate im Vergleich zwischen Kassen

---

## 6. IMPLEMENTIERUNGS-KONZEPT (Integration in bestehende Anwendung)

### 6.1 Architektur-Übersicht

Die Statistik-Erfassung und -Anzeige wird in drei Schichten implementiert:

1. **Daten-Erfassungs-Schicht** (Backend, in `SimulationManager`)
   - Tracking von Kundenereignissen (Spawn, Queue, Checkout, Leave)
   - Sampling von Kassen-States (Uptime, Downtime, Queue-Länge)
   - Persistierung in datenstrukturen (`stats_dict`)

2. **Aggregations-Schicht** (In `SimulationManager`, nach `day_finished` Signal)
   - Berechnung von Aggregates (Min/Max/Ø, Percentiles, etc.)
   - Pro-Checkout und globale Metriken zusammenführen
   - JSON/CSV Export generieren

3. **Präsentations-Schicht** (UI in `src/views`)
   - **Live-Dashboard in Sidebar** (während laufender Simulation)
   - **End-of-Day-Dialog** (nach Tagesabschluss)
   - **Checkout-Details-Dialog** (per Klick auf Kasse)

---

### 6.2 Live-Statistiken in der Sidebar (während Simulation)

**Wo:** Neue Sektion in der Sidebar (`src/views/components/sidebar.py` erweitern oder neue Component `sidebar_stats.py`)

**Inhalt (Minimale Echtzeit-Metriken):**

- **Aktive Kunden im Laden:** Live-Zähler
- **Warteschlange (Global):** Durchschnitt + aktuell längste Queue
- **Ø Wartezeit (bis jetzt):** Running Average
- **Durchsatz:** Kunden/Stunde (live berechnet)
- **Verfügbare Kassen:** Anzahl offener vs. gestörter Kassen (Ampel: grün/gelb/rot)
- **Top KPI:** Satisfaction Score (0–100, Gauge-ähnlich)

**Tech-Umsetzung:**

```
SimulationManager emittiert neues Signal: stats_updated(live_stats_dict)
  - Alle 1 Sekunde oder bei Meilenstein-Ereignissen
  - live_stats_dict enthält: aktive_kunden, ø_wartezeit, durchsatz, verfügbare_kassen, satisfaction_score

Sidebar verbindet sich mit diesem Signal und updated die Anzeige real-time
```

**Mock-Example:**

```
┌─── ECHTZEIT-STATISTIKEN ─────────────┐
│                                      │
│  Kunden im Laden: 12                 │
│  Längste Queue: 5 (an Kasse 2)      │
│  Ø Wartezeit: 3.2 Min               │
│  Durchsatz: 18 Kunden/h             │
│                                      │
│  Kassen:  🟢 4 offen | 🔴 1 Störung │
│                                      │
│  Zufriedenheit: ████░ 78%           │
└──────────────────────────────────────┘
```

---

### 6.3 End-of-Day Statistiken Dialog (nach `day_finished`)

**Trigger:** Wenn `SimulationManager` das Signal `day_finished` emittiert, öffnet sich automatisch ein neuer Dialog `StatisticsReportDialog` (in `src/views/dialogs.py` oder neu `src/views/screens/statistics_screen.py`)

**Inhalt (Umfassender Bericht):**

- **Reiter / Tabs:**
  1. **Kundenfluss** (Abschnitt 1)
     - Box-Plots für Laden/Queue/Service-Zeiten
     - Min/Max/Ø Werte
  2. **Gesamtstatistiken** (Abschnitt 2)
     - Kundenanzahl (Pie Chart: Normal vs. Eingeschränkt)
     - Total Items (Kennzahl)
  3. **Bezahlmethoden** (Abschnitt 3)
     - Pie Chart: Bar vs. Karte
     - Grouped Bar: Zeiten vergleich
  4. **Je Kasse (Detailansicht)** (Abschnitt 4)
     - Tabelle: Alle Kassen mit ihren Metriken
     - Oder: Dropdown um einzelne Kasse zu wählen und Deep-Dive zu machen
     - Pie Chart: Konflikte (Normal / Störung / Verärgerung) für ausgewählte Kasse
     - Gauge: Uptime % für Kasse
     - Stacked Bar: Störungs-Downtime vs. Konflikt-Downtime
  5. **Erweiterte Analysen** (Abschnitt 5)
     - Skill-Vergleich (Azubi vs. Pro)
     - Satisfaction Score mit Explanation
     - Peak-Hours (Line Chart + Tabelle)
     - Fehlerrate (Bar Chart)
  6. **Export**
     - Button: "Als JSON speichern" → `stats_YYYYMMDD_HHMM.json`
     - Button: "Als CSV speichern" → `stats_YYYYMMDD_HHMM.csv` (für Pivot in Excel)

**Tech-Umsetzung:**

```
1. SimulationManager speichert während der Simulation alle Events:
   - CustomerModel.entry_time, queue_join_time, service_start, service_end
   - CheckoutData: malfunction_events, conflict_events, timestamps

2. Bei day_finished emittiert SimulationManager: stats_ready(detailed_stats_dict)
   - detailed_stats_dict ist vollständig vorkalibriert (Min/Max/Ø bereits berechnet)

3. MainController / MainWindow verbindet sich mit day_finished
   → Öffnet StatisticsReportDialog(detailed_stats_dict)

4. Dialog nutzt matplotlib/plotly (oder simple PyQt Graphics) um Diagramme zu rendern
   → Tabellen via QTableWidget
   → Export via json.dump() / csv.writer()
```

---

### 6.4 Live-Checkout-Statistiken (Klick auf Kasse während Simulation)

**Feature:** Wenn die Simulation läuft und man auf eine Kasse in der Szene klickt, erscheint ein kleines Pop-Up oder Dialog mit **Live-Statistiken dieser Kasse**

**Inhalt:**

- **Kasse ID / Kassierer Skill:** z.B. "Kasse #3 (Azubi)"
- **Aktuelle Queue-Länge:** Kunden in der Schlange (mit Namen/ID)
- **Status:** "Offen", "Störung", "Konflikt", "Reparieren", etc.
- **Kunden an dieser Kasse (heute):**
  - Anzahl bedient
  - Ø Scan-Zeit
  - Ø Bezahl-Zeit
  - Total Items gescannt
- **Zeiten (laufend):**
  - Uptime % (bisherig)
  - Störungs-Downtime (bisherig)
  - Konflikt-Downtime (bisherig)
- **Bezahlmethoden:** % Bar vs. Karte an dieser Kasse

**Tech-Umsetzung:**

```
1. VisualController / InteractionController verbindet Checkout-Click mit Slot:
   on_checkout_clicked(checkout_id)

2. Slot fragt SimulationManager nach live_stats_for_checkout(checkout_id)
   → Gibt aktuellen dict mit Echtzeit-Daten zurück

3. Zeigt CheckoutStatsDialog(checkout_id, live_stats) an
   - Dialog updates alle 0.5 sec die Werte
   - Werte sind out-of-the-box verfügbar (nicht neu berechnet)
```

**Mock-Example Dialog:**

```
┌────────── KASSE #3 (Azubi) ──────────┐
│                                      │
│  Status: Offen                       │
│  Queue-Länge: 2                      │
│                                      │
│  ─────── KUNDEN HEUTE ───────        │
│  Bedient: 14 Kunden                  │
│  Ø Scan-Zeit: 0.8 sec               │
│  Ø Bezahl-Zeit: 2.1 sec             │
│  Total Items: 167                    │
│                                      │
│  ─────── VERFÜGBARKEIT ──────        │
│  Uptime: 94%                         │
│  Störung: 4% (5 Min)                │
│  Konflikt: 2% (2 Min)               │
│                                      │
│  ─────── BEZAHLUNG ──────            │
│  Bar: 57% | Karte: 43%              │
└──────────────────────────────────────┘
```

---

### 6.5 Technische Implementierungs-Checklist

**Phase 1: Backend (Stats-Erfassung in `SimulationManager`)**

- [ ] Erweitere `SimulationManager.__init__()` mit Stats-Datenstrukturen:
  - `self.stats = { "global": {...}, "checkouts": {...}, "events": [...] }`
  - `self.live_stats_cache = {...}` (für Sidebar/Dialog Updates)
- [ ] Modifiziere `_tick()` um Events zu tracken:
  - Wenn Kunde spawnt: `model.entry_time_sec = current_sim_seconds`
  - Wenn Kunde Queue jointet: `model.queue_join_time = current_sim_seconds`
  - Wenn Service startet: `model.service_start_time = current_sim_seconds`
  - Wenn Service endet: `model.service_end_time = current_sim_seconds`
  - Wenn Störung/Konflikt: `checkout_data["events"].append({"type": "malfunction", "start": t, "end": t2})`
- [ ] Implementiere Aggregations-Methode `_finalize_statistics()`:
  - Ruft auf bei `day_finished`
  - Berechnet Min/Max/Ø/Percentiles
  - Exportiert JSON/CSV
- [ ] Emittiere neue Signals:
  - `live_stats_updated(stats_dict)` — 1x pro Sekunde für Sidebar
  - `stats_ready(detailed_stats_dict)` — bei `day_finished` für End-of-Day Dialog

**Phase 2: UI (Präsentation)**

- [ ] Sidebar erweitern:
  - Neue Componente `StatisticsPanel` in `sidebar.py`
  - Connect zu `live_stats_updated` Signal
- [ ] End-of-Day Dialog:
  - Neue Klasse `StatisticsReportDialog` in `dialogs.py`
  - Mit Tabs für: Kundenfluss, Gesamtstats, Bezahlung, Je-Kasse, Erweitert, Export
  - Nutze QTabWidget
- [ ] Checkout-Klick-Statistiken:
  - Hook in `InteractionController` oder `VisualController`
  - Neue Klasse `CheckoutStatsDialog` in `dialogs.py`
  - Auto-refresh via Timer

**Phase 3: Graphiken & Export**

- [ ] Wähle Graphik-Library:
  - Option A: `matplotlib` (einfach, robust)
  - Option B: `plotly` (interaktiv, aber schwerer)
  - Option C: PyQt `QChart` (native, aber limitiert)
- [ ] Implementiere Render-Funktionen für:
  - Box-Plots (Wartezeiten)
  - Pie Charts (Kundentypen, Zahlungsart, Konflikte)
  - Bar Charts (Vergleiche zwischen Kassen)
  - Stacked Bar (Downtime-Kategorien)
  - Line Charts (Peak-Hours, Verfügbarkeit über Zeit)
- [ ] Export-Features:
  - JSON: `json.dump(stats_dict, file)`
  - CSV: Konvertiere Tabellen zu CSV

---

### 6.6 Daten-Struktur Beispiel (SimulationManager.stats)

```python
stats = {
    "global": {
        "total_customers_spawned": 50,
        "total_customers_served": 48,
        "total_normal_customers": 45,
        "total_disabled_customers": 5,
        "total_items_processed": 623,
        "avg_items_per_customer": 12.98,

        "times": {
            "store_stay_min": 5.2,
            "store_stay_max": 42.1,
            "store_stay_avg": 18.5,
            "queue_wait_min": 0.1,
            "queue_wait_max": 12.3,
            "queue_wait_avg": 3.2,
            "service_time_min": 1.5,
            "service_time_max": 8.9,
            "service_time_avg": 4.1,
        },

        "payment": {
            "cash_count": 28,
            "card_count": 20,
            "cash_percent": 58.3,
            "card_percent": 41.7,
            "cash_time_avg": 3.5,
            "card_time_avg": 2.1,
        },

        "satisfaction_score": 78,  # 0–100
    },

    "checkouts": {
        1: {
            "id": 1,
            "skill": "Azubi",
            "customers_served": 12,
            "normal_customers": 11,
            "disabled_customers": 1,
            "handheld_users": 3,
            "total_items": 156,

            "scan_time": {"min": 0.4, "max": 1.2, "avg": 0.75},
            "pay_time": {"min": 1.0, "max": 5.5, "avg": 2.2},
            "queue": {"min": 0, "max": 4, "avg": 1.5},

            "payment": {
                "cash_count": 7,
                "card_count": 5,
                "cash_time_avg": 3.6,
                "card_time_avg": 2.0,
            },

            "uptime_percent": 92.5,
            "malfunction_downtime_sec": 450,  # 7.5 Min
            "conflict_downtime_sec": 30,
            "total_malfunction_events": 2,
            "total_conflict_events": 1,

            "conflicts": {
                "normal": 0.925,       # 92.5%
                "malfunction": 0.060,  # 6%
                "conflict": 0.015,     # 1.5%
            },
        },
        # ... mehr Kassen
    },

    "events": [
        # Optional: Array aller relevanten Events für Zeitreihen
        {"type": "customer_entered", "time": 120, "customer_id": 1},
        {"type": "customer_queued", "time": 180, "customer_id": 1, "checkout_id": 1},
        {"type": "customer_served", "time": 420, "customer_id": 1, "checkout_id": 1},
        # ...
    ],
}
```

---

### 6.7 Signal-Flow

```
SimulationManager
├─ (jede Sekunde) stats_updated(live_stats)
│  ├─> Sidebar.update_live_stats()
│  └─> CheckoutStatsDialog.refresh() (falls offen)
│
└─ (bei day_finished) day_finished()
   ├─> Berechne final statistics
   ├─> Emittiere: stats_ready(detailed_stats_dict)
   └─> MainWindow öffnet StatisticsReportDialog(detailed_stats)
       └─> Dialog zeigt alle Tabs + Export-Buttons
```

---

## 7. ZUSAMMENFASSUNG FÜR SIMULATOR-FOKUS
