# 📊 Statistik-Redesign Plan - Professionelle Filialleiter-Auswertung

## 🎯 Zielsetzung

Eine **benutzerfreundliche, professionelle und aussagekräftige** Statistikauswertung schaffen, die einem Filialleiter echten Mehrwert bietet und auf einen Blick die wichtigsten Kennzahlen liefert.

---

## 🚨 Aktuelle Probleme

### Dialog (StatisticsReportDialog)
- ❌ **Zu viele Tabs** (7 Tabs) → Informationen sind zu fragmentiert
- ❌ **Schlechte Informationshierarchie** → Wichtige KPIs gehen unter
- ❌ **Fehlende Erklärungen** → Metriken ohne Kontext
- ❌ **Ineffiziente Raumnutzung** → Große Boxen mit wenig Inhalt
- ❌ **Inkonsistente Visualisierung** → Mix aus Tabellen, Charts ohne klare Struktur
- ❌ **Keine Handlungsempfehlungen** → Nur Daten, keine Insights
- ❌ **Fehlende Priorisierung** → Alles gleich wichtig

### Sidebar (Live-Statistiken)
- ❌ **Unübersichtlich** → Zu viele einzelne Labels
- ❌ **Fehlende visuelle Hierarchie** → Alles sieht gleich aus
- ❌ **Keine Farbcodierung** → Gut/Schlecht nicht erkennbar
- ❌ **Schlechte Gruppierung** → Zusammengehörige Metriken getrennt

---

## ✨ Redesign-Konzept

### 1️⃣ Dashboard-Philosophie

**Denke wie ein Business Dashboard:**
- **Top KPIs zuerst** → Die wichtigsten 3-5 Kennzahlen prominent
- **Drill-Down möglich** → Von Overview zu Details
- **Visuell schnell erfassbar** → Farben, Icons, Gauges
- **Actionable Insights** → Was bedeutet das? Was tun?

---

## 📋 TEIL 1: Sidebar Live-Statistiken Redesign

### Aktuelles Layout (❌ Probleme)
```
Globale Kennzahlen
├─ Kunden in Warteschlange: 12
├─ Kunden im Laden: 8
├─ Kunden Gesamt: 45
├─ Längste Warteschlange: 5
├─ Ø Wartezeit: 3.2 min
├─ Durchsatz: 18 Kunden/h
├─ Verfügbare Kassen: 4
├─ Zufriedenheit: 78%
├─ Verstrichene Zeit: 02:15:30
├─ Geplante Öffnungszeit: 12:00:00
└─ Überzeit: 00:15:30
```

### ✅ NEUES DESIGN: **Live-Dashboard (Kompakt & Visuell)**

#### **Karten-basiertes Layout (Cards)**

```
┌─────────────── LIVE-DASHBOARD ──────────────┐
│                                              │
│  ┌─────────────────────────────────────┐    │
│  │  🏪 LADEN-STATUS          [●LIVE]   │    │
│  │                                     │    │
│  │  Im Laden:      █████░░ 8/15       │    │
│  │  Warteschlange: ██████░ 12 Kunden  │    │
│  │  Längste Queue: Kasse #2 (5)       │    │
│  └─────────────────────────────────────┘    │
│                                              │
│  ┌─────────────────────────────────────┐    │
│  │  ⏱️ WARTEZEIT & EFFIZIENZ           │    │
│  │                                     │    │
│  │  Ø Wartezeit:   ████░░ 3.2 min     │    │
│  │  Durchsatz:     18 Kunden/h         │    │
│  │  Ziel:          ≤ 5 min ✅          │    │
│  └─────────────────────────────────────┘    │
│                                              │
│  ┌─────────────────────────────────────┐    │
│  │  💰 KASSEN-STATUS                   │    │
│  │                                     │    │
│  │  🟢 Offen:     4 Kassen             │    │
│  │  🔴 Störung:   1 Kasse              │    │
│  │  ⚪ Geschl.:   2 Kassen              │    │
│  └─────────────────────────────────────┘    │
│                                              │
│  ┌─────────────────────────────────────┐    │
│  │  😊 ZUFRIEDENHEIT                   │    │
│  │                                     │    │
│  │      78%     ████████░░             │    │
│  │                                     │    │
│  │  Status: GUT ✅                     │    │
│  └─────────────────────────────────────┘    │
│                                              │
│  ┌─────────────────────────────────────┐    │
│  │  🕐 ÖFFNUNGSZEITEN                  │    │
│  │                                     │    │
│  │  Verstrichen:  02:15:30             │    │
│  │  Geplant:      12:00:00             │    │
│  │  ⚠️ Überzeit:  +00:15:30            │    │
│  └─────────────────────────────────────┘    │
│                                              │
│  ┌─────────────────────────────────────┐    │
│  │  📈 HEUTE BEDIENT                   │    │
│  │                                     │    │
│  │       45 Kunden                     │    │
│  │                                     │    │
│  └─────────────────────────────────────┘    │
└──────────────────────────────────────────────┘
```

#### **Design-Prinzipien für Sidebar:**

1. **Gruppierte Karten (QGroupBox mit Schatten/Rand)**
   - Jede Karte = eine Metrik-Kategorie
   - Visuell getrennt, klar strukturiert

2. **Farbcodierung**
   - 🟢 Grün = Gut (≤ Zielwert)
   - 🟡 Gelb = Akzeptabel (nahe Zielwert)
   - 🔴 Rot = Kritisch (> Zielwert)

3. **Icons für schnelle Orientierung**
   - 🏪 Laden-Status
   - ⏱️ Zeiten
   - 💰 Kassen
   - 😊 Zufriedenheit
   - 🕐 Öffnungszeiten
   - 📈 Tagesstatistik

4. **Fortschrittsbalken (QProgressBar)**
   - Visuell schneller erfassbar als Zahlen
   - Mit Farbcodierung

5. **Live-Indikator**
   - Blinkender "●LIVE" Punkt oben rechts
   - Zeigt, dass Updates in Echtzeit kommen

6. **Kompakter Plot**
   - Kleines Liniendiagramm für "Kunden im Laden über Zeit"
   - Zeigt Trend auf einen Blick

---

## 📊 TEIL 2: Statistik-Dialog Redesign

### Aktuelles Tab-System (❌ Zu fragmentiert)
1. Übersicht
2. Kunden
3. Bezahlung
4. Betrieb
5. Kassen
6. Erweitert
7. Export

### ✅ NEUES TAB-SYSTEM (4 Tabs statt 7)

```
┌─────────────── STATISTIKBERICHT ───────────────┐
│                                                 │
│  ┌───┬───────┬─────────┬──────────┬──────┐    │
│  │ 📊│ 👥   │ 💳      │ 🏪      │ ⚙️  │    │
│  │KPIs│Kunden│Kassen   │Betrieb  │Export│    │
│  └───┴───────┴─────────┴──────────┴──────┘    │
│                                                 │
│  [Hier: Tab-Inhalt]                            │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

### 🏆 TAB 1: **KPIs & ÜBERSICHT** (Dashboard-Style)

**Ziel:** Wichtigste Kennzahlen auf einen Blick

#### **Layout (3-Spalten-Grid)**

```
┌─────────────────────────────────────────────────────────┐
│                     KPI DASHBOARD                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌───────────────┐  ┌───────────────┐  ┌────────────┐ │
│  │  📊 KUNDEN    │  │  ⏱️ WARTEZEIT  │  │ 😊 ZUFRIED.│ │
│  │               │  │                │  │            │ │
│  │      145      │  │    3.2 min    │  │    78%     │ │
│  │   bedient     │  │   Ø Warten    │  │            │ │
│  │               │  │                │  │  ████████░ │ │
│  │  ✅ +12%      │  │  ✅ ≤ 5 min   │  │  GUT ✅    │ │
│  │   vs. Ziel    │  │    Ziel       │  │            │ │
│  └───────────────┘  └───────────────┘  └────────────┘ │
│                                                         │
│  ┌───────────────┐  ┌───────────────┐  ┌────────────┐ │
│  │  💰 UMSATZ    │  │  🏃 DURCHSATZ │  │ 🕐 ÜBERZEIT│ │
│  │               │  │                │  │            │ │
│  │   1.890 €     │  │  18 Kunden/h  │  │  +15 min   │ │
│  │  (geschätzt)  │  │               │  │            │ │
│  │               │  │                │  │            │ │
│  │  ✅ +8%       │  │  ✅ Normal    │  │  ⚠️ Hoch   │ │
│  │   vs. Ø       │  │               │  │            │ │
│  └───────────────┘  └───────────────┘  └────────────┘ │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                   TRENDANALYSE                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Kunden im Laden über Zeit                      │   │
│  │                                                 │   │
│  │  15 ┤     ╭─╮                                  │   │
│  │  12 ┤    ╭╯ ╰╮  ╭╮                             │   │
│  │   9 ┤   ╭╯   ╰╮╭╯╰─╮                           │   │
│  │   6 ┤  ╭╯     ╰╯   ╰╮                          │   │
│  │   3 ┤ ╭╯           ╰─╮                         │   │
│  │   0 ┴──────────────────────                    │   │
│  │     8:00  10:00  12:00  14:00  16:00  18:00   │   │
│  │                                                 │   │
│  │  🔴 Peak: 14:30 (15 Kunden)                    │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                HANDLUNGSEMPFEHLUNGEN                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ✅ Zufriedenheit im grünen Bereich (78%)              │
│  ⚠️  Überzeit: 15 Minuten - Kassenöffnung prüfen      │
│  💡 Peak um 14:30 - mehr Kassen zur Mittagszeit?      │
│  📊 18 Kunden/h - Durchsatz normal                     │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

#### **Komponenten:**

1. **6 KPI-Karten** (2 Reihen × 3 Spalten)
   - Große Zahl in der Mitte
   - Kontextuelle Information (Ziel, Vergleich)
   - Status-Icon (✅ Gut, ⚠️ Warnung, 🔴 Kritisch)
   - Farbcodierter Rand

2. **Trendanalyse-Chart**
   - Zeigt Kundenaufkommen über den Tag
   - Markiert Peak-Zeiten
   - Gut für visuelles Verständnis

3. **Handlungsempfehlungen** (NEU!)
   - Automatisch generierte Insights
   - Konkrete Vorschläge basierend auf Daten
   - Leicht verständliche Sprache

---

### 👥 TAB 2: **KUNDEN** (Detaillierte Kundenanalyse)

#### **Layout (2-Spalten)**

```
┌──────────────────────────────────────────────────────┐
│                   KUNDENANALYSE                      │
├──────────────────────────────────────────────────────┤
│                                                      │
│  KUNDENVERTEILUNG          │  ZEITMETRIKEN          │
│                            │                        │
│  ┌───────────────────┐    │  ┌──────────────────┐  │
│  │ Kundentypen       │    │  │ Durchlaufzeiten  │  │
│  │                   │    │  │                  │  │
│  │     ╭──────╮      │    │  │ Min  │ Ø │ Max │  │
│  │  78%│Normal│22%   │    │  ├──────┼───┼─────┤  │
│  │     ╰──────╯      │    │  │ 8.2  │15 │ 28  │  │
│  │    Beeinträchtigt │    │  │      │min│     │  │
│  │                   │    │  └──────────────────┘  │
│  └───────────────────┘    │                        │
│                            │  Verweildauer im Laden│
│  ┌───────────────────┐    │                        │
│  │ Handscanner       │    │  ┌──────────────────┐  │
│  │                   │    │  │ Wartezeit Queue  │  │
│  │     32 Kunden     │    │  │                  │  │
│  │      (22%)        │    │  │ Min  │ Ø │ Max │  │
│  │                   │    │  ├──────┼───┼─────┤  │
│  └───────────────────┘    │  │ 0.5  │3.2│ 12  │  │
│                            │  │      │min│     │  │
│                            │  └──────────────────┘  │
│  ┌───────────────────┐    │                        │
│  │ Bezahlmethoden    │    │  Wartezeit an der Kasse│
│  │                   │    │                        │
│  │     ╭──────╮      │    │  ┌──────────────────┐  │
│  │  43%│ Bar  │57%   │    │  │ Servicezeit      │  │
│  │     ╰──────╯      │    │  │                  │  │
│  │       Karte       │    │  │ Min  │ Ø │ Max │  │
│  │                   │    │  ├──────┼───┼─────┤  │
│  └───────────────────┘    │  │ 1.2  │2.8│ 8.5 │  │
│                            │  │      │min│     │  │
│                            │  └──────────────────┘  │
│                            │                        │
│                            │  Scan & Bezahlung     │
│                            │                        │
├────────────────────────────┴────────────────────────┤
│                   KUNDENLISTE                        │
├──────────────────────────────────────────────────────┤
│                                                      │
│  [Tabelle: Alle Kunden mit Details]                │
│                                                      │
│  ID │Typ│Handscanner│Zahlung│Artikel│Kasse│Zeiten  │
│  ──────────────────────────────────────────────────│
│  001│ N │    ✓     │  Bar  │  12   │  2  │15.2min │
│  002│ B │    ✗     │ Karte │   8   │  1  │18.5min │
│  ...                                                │
│                                                      │
│  [Sortierbar nach allen Spalten]                   │
│  [Filterbar nach Typ, Zahlung, Kasse]              │
│                                                      │
└──────────────────────────────────────────────────────┘
```

#### **Verbesserungen:**

1. **Visuelle Verteilung** (Pie Charts)
   - Kundentypen
   - Bezahlmethoden
   - Handscanner-Nutzung

2. **Kompakte Zeitmetriken-Boxen**
   - Min/Ø/Max in Tabellenform
   - Getrennt nach Metrik-Typ
   - Farbcodierung bei Überschreitung

3. **Erweiterte Kundenliste**
   - Sortierbar
   - Filterbar
   - Exportierbar

---

### 💳 TAB 3: **KASSEN** (Kassenanalyse & Performance)

#### **Layout**

```
┌──────────────────────────────────────────────────────┐
│                  KASSEN-ÜBERSICHT                    │
├──────────────────────────────────────────────────────┤
│                                                      │
│  KASSEN-STATUS             │  TOP/FLOP KASSEN       │
│                            │                        │
│  🟢 Offen:        4        │  🏆 TOP PERFORMER      │
│  🔴 Störung:      1        │  Kasse #3 (Pro)       │
│  ⚪ Geschlossen:  2        │  • 45 Kunden          │
│                            │  • Ø Queue: 1.8 min   │
│  Gesamt:          7        │  • Zufriedenheit: 95% │
│                            │                        │
│                            │  ⚠️ FLOP PERFORMER    │
│                            │  Kasse #5 (Azubi)     │
│                            │  • 28 Kunden          │
│                            │  • Ø Queue: 7.2 min   │
│                            │  • 2 Störungen        │
│                            │                        │
├────────────────────────────┴────────────────────────┤
│              KASSEN-PERFORMANCE-TABELLE              │
├──────────────────────────────────────────────────────┤
│                                                      │
│ ID│Skill│👥│📦│⏱️Queue│⏱️Scan│💳│🟢Uptime│🔴Störung│
│ ──────────────────────────────────────────────────  │
│ 1 │ Pro │45│540│ 2.1  │ 0.8 │Bar│  98%  │   0    │
│ 2 │Azubi│38│380│ 3.5  │ 1.2 │Mix│  95%  │   1    │
│ 3 │ Pro │52│624│ 1.8  │ 0.7 │Card│ 99%  │   0    │
│ 4 │  SB │25│250│ 4.2  │  -  │Mix│  92%  │   2    │
│ 5 │Azubi│28│336│ 7.2  │ 1.5 │Bar│  85%  │   2    │
│ 6 │ Pro │41│492│ 2.3  │ 0.9 │Card│ 97%  │   0    │
│ 7 │ - - │ -│ - │  -   │  -  │ - │   -   │   -    │
│                                                      │
│  [Farbcodierung: Grün=Gut, Gelb=OK, Rot=Problem]   │
│                                                      │
├──────────────────────────────────────────────────────┤
│                SKILL-VERGLEICH                       │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌────────────────────────────────────────┐         │
│  │ Durchschnittliche Scanzeit nach Skill  │         │
│  │                                        │         │
│  │  Pro:   ████ 0.8 min                  │         │
│  │  Azubi: ███████ 1.35 min              │         │
│  │  SB:    ──────── (selbst scannen)     │         │
│  │                                        │         │
│  │  📊 Effizienz-Ratio: Azubi 1.69x langsamer│     │
│  └────────────────────────────────────────┘         │
│                                                      │
│  💡 Erkenntnis: Pro-Kassierer 69% schneller!       │
│  💡 Empfehlung: Mehr Schulungen für Azubis         │
│                                                      │
└──────────────────────────────────────────────────────┘
```

#### **Verbesserungen:**

1. **Status-Übersicht mit Icons**
   - Schneller Überblick über Kassenzustand
   - Farbcodierung

2. **Top/Flop-Kassen**
   - Hebt beste und schlechteste Kasse hervor
   - Gibt direkte Hinweise

3. **Performance-Tabelle mit Icons**
   - Icons statt langer Texte
   - Farbcodierung für Quick-Scan
   - Sortierbar nach jeder Spalte

4. **Skill-Vergleich**
   - Zeigt Effizienz-Unterschied zwischen Skill-Levels
   - Balkendiagramm für Vergleich
   - Konkrete Handlungsempfehlung

---

### 🏪 TAB 4: **BETRIEB** (Betriebszeiten & Peak-Analyse)

#### **Layout**

```
┌──────────────────────────────────────────────────────┐
│                   BETRIEBSANALYSE                    │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ÖFFNUNGSZEITEN            │  PEAK-ZEITEN           │
│                            │                        │
│  Öffnet:      08:00        │  Spitzenstunde:        │
│  Schließt:    20:00        │  14:00 - 15:00         │
│  Geplant:     12h 00min    │                        │
│  Tatsächlich: 12h 15min    │  Ø Kunden: 15          │
│  ⚠️ Überzeit:  +15min      │  Max Queue: 8          │
│                            │                        │
│  ⏱️ +2.1% über Zielzeit   │  💡 Mehr Kassen?       │
│                            │                        │
├────────────────────────────┴────────────────────────┤
│            AUSLASTUNG ÜBER DEN TAG                   │
├──────────────────────────────────────────────────────┤
│                                                      │
│  Kunden im Laden (stündlich)                        │
│                                                      │
│  15┤           ╭──╮                                 │
│  12┤         ╭─╯  ╰─╮                              │
│   9┤       ╭─╯      ╰─╮                            │
│   6┤     ╭─╯          ╰──╮                         │
│   3┤   ╭─╯               ╰─╮                       │
│   0┴───────────────────────────                    │
│    8  9 10 11 12 13 14 15 16 17 18 19 20 Uhr     │
│                                                      │
│  🔴 Peak: 14:30 (15 Kunden gleichzeitig)           │
│  🟢 Ruhig: 10:00 (3 Kunden)                        │
│                                                      │
├──────────────────────────────────────────────────────┤
│               WARTESCHLANGEN-ANALYSE                 │
├──────────────────────────────────────────────────────┤
│                                                      │
│  Maximale Queue:     8 Kunden (Kasse #2, 14:45)    │
│  Ø Queue (gesamt):   2.8 Kunden                     │
│                                                      │
│  ┌────────────────────────────────────────┐         │
│  │ Queue-Länge über Zeit                  │         │
│  │                                        │         │
│  │  8┤           ╭╮                       │         │
│  │  6┤         ╭─╯╰─╮                    │         │
│  │  4┤       ╭─╯    ╰──╮                 │         │
│  │  2┤   ╭───╯         ╰───╮             │         │
│  │  0┴────────────────────────           │         │
│  │   8  10  12  14  16  18  20 Uhr     │         │
│  └────────────────────────────────────────┘         │
│                                                      │
│  💡 Kritischer Zeitraum: 14:00-15:30               │
│  💡 Empfehlung: +1 Kasse in dieser Zeit öffnen     │
│                                                      │
└──────────────────────────────────────────────────────┘
```

#### **Verbesserungen:**

1. **Übersichtliche Zeiterfassung**
   - Geplant vs. Tatsächlich
   - Überzeit farblich hervorgehoben

2. **Peak-Zeiten prominent**
   - Zeigt kritische Zeitfenster
   - Konkrete Empfehlungen

3. **Zwei Trend-Charts**
   - Kunden im Laden
   - Queue-Länge
   - Beide mit Peak-Markierungen

4. **Handlungsempfehlungen**
   - Basierend auf Peak-Zeiten
   - Konkrete Vorschläge für Optimierung

---

### ⚙️ TAB 5: **EXPORT** (Vereinfacht)

```
┌──────────────────────────────────────────────────────┐
│                  DATEN EXPORTIEREN                   │
├──────────────────────────────────────────────────────┤
│                                                      │
│  Exportiere die Statistiken für weitere Analysen.   │
│                                                      │
│  ┌────────────────────────────────────────┐         │
│  │  📊 Als JSON speichern                │         │
│  │  Für Entwickler und API-Integration   │         │
│  └────────────────────────────────────────┘         │
│                                                      │
│  ┌────────────────────────────────────────┐         │
│  │  📄 Als CSV speichern                 │         │
│  │  Für Excel, Pivot-Tabellen, etc.      │         │
│  └────────────────────────────────────────┘         │
│                                                      │
│  ┌────────────────────────────────────────┐         │
│  │  📋 Als PDF-Report exportieren (NEU!)  │         │
│  │  Druckfertiger professioneller Report  │         │
│  └────────────────────────────────────────┘         │
│                                                      │
└──────────────────────────────────────────────────────┘
```

---

## 🎨 Design-System

### Farbpalette

```python
# Erfolg/Ziel erreicht
COLOR_SUCCESS = "#10B981"  # Grün
COLOR_SUCCESS_BG = "#D1FAE5"  # Helles Grün

# Warnung/Nahe am Limit
COLOR_WARNING = "#F59E0B"  # Orange
COLOR_WARNING_BG = "#FEF3C7"  # Helles Orange

# Kritisch/Über Limit
COLOR_ERROR = "#EF4444"  # Rot
COLOR_ERROR_BG = "#FEE2E2"  # Helles Rot

# Neutral/Information
COLOR_INFO = "#3B82F6"  # Blau
COLOR_INFO_BG = "#DBEAFE"  # Helles Blau

# Akzent
COLOR_ACCENT = "#8B5CF6"  # Lila

# Text
COLOR_TEXT_PRIMARY = "#111827"
COLOR_TEXT_SECONDARY = "#6B7280"

# Hintergrund
COLOR_BG_CARD = "#FFFFFF"
COLOR_BG_PANEL = "#F9FAFB"
```

### Typografie

```python
# KPI-Zahlen (groß und prominent)
FONT_KPI_NUMBER = "font-size: 36px; font-weight: 700; color: #111827;"

# KPI-Label (klein unter Zahl)
FONT_KPI_LABEL = "font-size: 12px; font-weight: 500; color: #6B7280; text-transform: uppercase;"

# Überschriften
FONT_H1 = "font-size: 24px; font-weight: 700; color: #111827;"
FONT_H2 = "font-size: 18px; font-weight: 600; color: #374151;"
FONT_H3 = "font-size: 14px; font-weight: 600; color: #4B5563;"

# Body Text
FONT_BODY = "font-size: 14px; color: #374151;"
FONT_SMALL = "font-size: 12px; color: #6B7280;"
```

### Widget-Komponenten

#### 1. **KPI-Karte (QGroupBox)**

```python
class KPICard(QGroupBox):
    def __init__(self, title, value, unit="", status="neutral", parent=None):
        super().__init__(parent)
        self.setTitle("")
        layout = QVBoxLayout(self)
        
        # Icon + Title
        title_layout = QHBoxLayout()
        icon_label = QLabel(self._get_icon_for_status(status))
        icon_label.setStyleSheet("font-size: 24px;")
        title_label = QLabel(title)
        title_label.setStyleSheet(FONT_KPI_LABEL)
        title_layout.addWidget(icon_label)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        # Value
        value_label = QLabel(f"{value} {unit}")
        value_label.setStyleSheet(FONT_KPI_NUMBER)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(value_label)
        
        # Status Text
        status_label = QLabel(self._get_status_text(status))
        status_label.setStyleSheet(f"color: {self._get_status_color(status)}; font-size: 12px; font-weight: 600;")
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(status_label)
        
        # Style
        self.setStyleSheet(f"""
            QGroupBox {{
                background-color: {COLOR_BG_CARD};
                border: 2px solid {self._get_status_color(status)};
                border-radius: 12px;
                padding: 15px;
            }}
        """)
```

#### 2. **Metric-Box (Kompakt)**

```python
class MetricBox(QWidget):
    """Kleine Box für Min/Ø/Max Werte"""
    def __init__(self, label, min_val, avg_val, max_val, unit="", parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        
        # Label
        lbl = QLabel(label)
        lbl.setStyleSheet(FONT_H3)
        layout.addWidget(lbl)
        
        # Table
        table = QTableWidget(1, 3)
        table.setHorizontalHeaderLabels(["Min", "Ø", "Max"])
        table.setItem(0, 0, QTableWidgetItem(f"{min_val:.1f}{unit}"))
        table.setItem(0, 1, QTableWidgetItem(f"{avg_val:.1f}{unit}"))
        table.setItem(0, 2, QTableWidgetItem(f"{max_val:.1f}{unit}"))
        table.setStyleSheet(TABLE_COMPACT_STYLE)
        layout.addWidget(table)
```

---

## 🚀 Implementierungs-Reihenfolge

### Phase 1: Sidebar-Redesign (Priorität: HOCH)
1. ✅ Neue Card-basierte Komponenten erstellen
2. ✅ Farbcodierung implementieren
3. ✅ Icons hinzufügen
4. ✅ Fortschrittsbalken für visuelle Metriken
5. ✅ Live-Indikator

### Phase 2: Dialog Tab 1 - KPI Dashboard (Priorität: HOCH)
1. ✅ KPI-Karten erstellen
2. ✅ 3-Spalten-Grid-Layout
3. ✅ Trend-Chart integrieren
4. ✅ Handlungsempfehlungen generieren

### Phase 3: Dialog Tab 2 - Kunden (Priorität: MITTEL)
1. ✅ 2-Spalten-Layout
2. ✅ Pie-Charts für Verteilung
3. ✅ Kompakte Metrik-Boxen
4. ✅ Erweiterte Kundenliste

### Phase 4: Dialog Tab 3 - Kassen (Priorität: MITTEL)
1. ✅ Status-Übersicht
2. ✅ Top/Flop-Kassen
3. ✅ Performance-Tabelle mit Icons
4. ✅ Skill-Vergleich

### Phase 5: Dialog Tab 4 - Betrieb (Priorität: MITTEL)
1. ✅ Zeiterfassung
2. ✅ Peak-Analyse
3. ✅ Trend-Charts
4. ✅ Handlungsempfehlungen

### Phase 6: Export-Funktionen (Priorität: NIEDRIG)
1. ✅ PDF-Export hinzufügen
2. ✅ Verbessertes CSV-Format
3. ✅ JSON-Export beibehalten

---

## 🎯 Erwartete Verbesserungen

### Usability
- ⬆️ **80% schnellere Erfassung** wichtiger KPIs (durch Dashboard)
- ⬆️ **Reduzierte Klicks** von 7 auf 4 Tabs
- ⬆️ **Besseres Verständnis** durch Visualisierung
- ⬆️ **Actionable Insights** statt nur Rohdaten

### Design
- ✨ **Moderne, professionelle Optik**
- ✨ **Konsistente Farbcodierung**
- ✨ **Intuitive Icons**
- ✨ **Bessere Informationshierarchie**

### Funktionalität
- 🆕 **Handlungsempfehlungen**
- 🆕 **Top/Flop-Analyse**
- 🆕 **PDF-Export**
- 🆕 **Live-Dashboard in Sidebar**

---

## 📝 Technische Umsetzungs-Hinweise

### Neue Komponenten erstellen

```
supermarkt-simulator/src/views/
├── components/
│   ├── kpi_card.py          # KPI-Karte Komponente
│   ├── metric_box.py        # Metrik-Box für Min/Ø/Max
│   ├── status_badge.py      # Status-Badge (Grün/Gelb/Rot)
│   └── trend_chart.py       # Wrapper für matplotlib Charts
├── statistics_dialogs.py    # Refactored
└── components/
    └── sidebar.py           # Stats-Sektion refactored
```

### Datenstruktur erweitern

```python
# In simulation_manager.py
def _build_statistics_dict(self):
    # ... existing code ...
    
    # NEU: Handlungsempfehlungen
    stats["recommendations"] = self._generate_recommendations()
    
    # NEU: Top/Flop Kassen
    stats["top_checkouts"] = self._get_top_checkouts(3)
    stats["flop_checkouts"] = self._get_flop_checkouts(2)
    
    return stats

def _generate_recommendations(self):
    """Generiert automatische Handlungsempfehlungen"""
    recommendations = []
    
    # Zufriedenheit
    if satisfaction < 70:
        recommendations.append({
            "icon": "⚠️",
            "text": f"Zufriedenheit bei {satisfaction}% - Wartezeiten reduzieren!",
            "severity": "high"
        })
    
    # Überzeit
    if overtime > 0:
        recommendations.append({
            "icon": "⏰",
            "text": f"Überzeit: {overtime} Min - Kassenöffnung optimieren",
            "severity": "medium"
        })
    
    # Peak-Zeiten
    peak_hour = self._get_peak_hour()
    recommendations.append({
        "icon": "💡",
        "text": f"Peak um {peak_hour} - mehr Kassen zu dieser Zeit?",
        "severity": "info"
    })
    
    return recommendations
```

---

## ✅ Zusammenfassung

Dieses Redesign transformiert die Statistik-Ansicht von einer **datenorientierten Übersicht** zu einem **businessorientierten Dashboard**, das:

1. ✅ **Schnell** wichtige Kennzahlen zeigt
2. ✅ **Visuell** ansprechend und modern ist
3. ✅ **Actionable** Empfehlungen gibt
4. ✅ **Intuitiv** zu bedienen ist
5. ✅ **Professionell** aussieht

Ein Filialleiter kann nun:
- Auf einen Blick sehen, wie der Tag lief
- Probleme sofort erkennen (Farbcodierung)
- Konkrete Maßnahmen ableiten
- Schnell Drill-Downs in Details machen
- Reports für das Management exportieren

**Das ist ein echter Mehrwert! 🚀**
