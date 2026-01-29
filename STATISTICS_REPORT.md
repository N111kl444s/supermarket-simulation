# Statistikbericht – Auswertung, Inhalte & Berechnung

Diese Datei beschreibt, **welche Statistiken wo angezeigt werden** und **wie sie berechnet werden**.

---

## 1) Sidebar → Tab „Statistiken“ (Live‑Übersicht)

**Live‑Metriken (während der Simulation):**

- **Kunden im Laden**
  - *Definition:* Aktuell aktive Kunden im Shop.
  - *Berechnung:* `len(customers_model)`.

- **Kunden in Schlange**
  - *Definition:* Summe aller wartenden Kunden an allen Kassen.
  - *Berechnung:* `sum(len(queue) for queue in checkout_queues)`.

- **Längste Queue**
  - *Definition:* Maximale Queue‑Länge, die bisher am Tag erreicht wurde, inkl. Kassen‑IDs.
  - *Berechnung:* `max(len(queue))` über die Zeit; Kassen‑IDs werden mitgeführt.

- **Ø Wartezeit**
  - *Definition:* Durchschnittliche Wartezeit bis Servicebeginn.
  - *Berechnung:* Mittelwert aus `queue_wait_times` (Sek.) → angezeigt in Minuten.

- **Durchsatz (Kunden/h)**
  - *Definition:* Bediente Kunden pro Stunde.
  - *Berechnung:* `served / (elapsed_open_seconds / 3600)`.

- **Kassen verfügbar**
  - *Definition:* Offene Kassen ohne Störung/Konflikt.
  - *Berechnung:* `available / open`.

- **Zufriedenheit (0–100)**
  - *Definition:* Score basierend auf Ø‑Verweildauer und Ø‑Wartezeit.
  - *Berechnung:* lineare Abwertung gegenüber Zielwerten (20 min Shop / 5 min Queue).

- **Geöffnet (bisher)**
  - *Definition:* Reale Öffnungszeit seit Start.
  - *Berechnung:* `elapsed_open_seconds` → Format `H:MM`.

- **Geplant geöffnet**
  - *Definition:* Geplante Öffnungsdauer aus Öffnen/Schließen.
  - *Berechnung:* `scheduled_open_seconds` → Format `H:MM`.

- **Überzeit**
  - *Definition:* Zusätzliche Öffnungszeit nach Ladenschluss.
  - *Berechnung:* `max(0, elapsed - scheduled)`.

---

## 2) Statistik‑Report (Dialog, End‑of‑Day oder Live)

### 2.1 Übersicht‑Tab

**Globale Kennzahlen:**
- Kunden gesamt (spawned), Kunden bedient, Artikel gesamt, Ø Artikel/Kunde.

**Durchschnittswerte:**
- Ø Verweildauer, Ø Wartezeit, Ø Servicezeit (in Minuten).

**Zufriedenheitsbalken:**
- Score 0–100, basierend auf Ø‑Verweildauer und Ø‑Wartezeit.

### 2.2 Kundenfluss‑Tab

**Tabelle Min/Ø/Max (Minuten):**
- Verweildauer (Store Stay)
- Wartezeit (Queue Wait)
- Servicezeit (Checkout Service)

### 2.3 Bezahlung‑Tab

**Tabelle je Zahlungsart:**
- Anzahl
- Ø Zeit (s)
- Min/Max (s)

### 2.4 Betrieb‑Tab

**Öffnungszeiten & Peak:**
- Öffnet / Schließt (Uhrzeit)
- Geplant geöffnet (Sek.)
- Tatsächlich geöffnet (Sek.)
- Überzeit (Sek.)
- Max. Queue + Kassen‑IDs
- Spitzenstunde (Busiest Hour)

**Stundentabelle:**
- Ø Kunden im Laden je Stunde (aus Zeitreihen‑Samples)

### 2.5 Kassen‑Tab (Übersicht)

**Tabelle je Kasse:**
- Skill
- Kunden, Artikel
- Ø Queue, Ø Service, Ø Scan, Ø Bezahlen (min)
- Bar/Karte‑Anzahl

**Diagramm:**
- Balken: Ø Servicezeit je Kasse

### 2.6 Kassen‑Details‑Tab

**Verfügbarkeit & Queue:**
- Queue Min/Ø/Max
- Uptime %
- Downtime (min)
- Störung (min)
- Konflikt (min)
- Störungen/ Konflikte (Anzahl)
- Handscanner‑Kunden

### 2.7 Erweitert‑Tab

**Skill‑Vergleich:**
- Azubi vs. Pro: Ø Scan (s), Ø Bezahlen (s)
- Effizienz‑Ratio: `newbie_scan_avg / pro_scan_avg`

### 2.8 Diagramme‑Tab

- **Boxplot:** Verteilung der Aufenthalts‑, Queue‑ und Servicezeiten
- **Pie:** Zahlungsmethoden (Bar/Karte)
- **Pie:** Kundentypen (Normal/Eingeschränkt)
- **Histogramm:** Verteilung der Queue‑Zeiten

### 2.9 Export‑Tab

- JSON‑Export (vollständiger Stats‑Dump)
- CSV‑Export (Tabellen/Key‑Value‑Struktur)

---

## 3) Berechnungsdetails (Backend‑Quelle)

### 3.1 Zeitmetriken pro Kunde

- **Verweildauer:** `exit_time_sec - entry_time_sec`
- **Wartezeit:** `service_start_time_sec - queue_join_time_sec`
- **Servicezeit:** `service_end_time_sec - service_start_time_sec`
- **Bezahlzeit:** `service_end_time_sec - payment_start_time_sec`
- **Scanzeit (abgeleitet):** `service_time - payment_time`

### 3.2 Uptime / Downtime je Kasse

- **Open/Closed‑Zeit:** per Tick anhand `checkout.open`
- **Downtime:** Zeit mit `malfunction=True` oder `conflict=True`
- **Uptime %:** `(open_time - downtime) / open_time * 100`

### 3.3 Peak‑Analyse

- **Zeitreihe:** 1‑Min‑Samples (`customers_in_store`, `total_queue`)
- **Busiest Hour:** höchste Ø‑Kundenzahl je Stunde

### 3.4 Zahlung & Kundentypen

- **Cash/Card‑Counts:** je Kunde nach Zahlungsart
- **Handscanner:** `uses_handheld == True`
- **Normal/Disabled:** `is_disabled == True/False`

---

## 4) Hinweis

- Alle Zeiten sind intern in **Sekunden** erfasst und im UI je nach Kontext in **Sekunden** oder **Minuten** angezeigt.
- Live‑Report nutzt Momentaufnahme (Snapshot) und aktualisiert sich automatisch.
