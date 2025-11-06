# Piep - Der Takt der Kasse | Supermarkt-Simulation (Berufsschulprojekt FIAE 2026)

Dieses Repository enthält das Python-Projekt "Piep - Der Takt der Kasse", eine Supermarkt-Simulation, die im Rahmen der Projektarbeit für Fachinformatiker Anwendungsentwicklung an der Berufsschule Technik in Rostock entwickelt wird.

## Projektanforderungen

* [Anforderungsdokument (REQUIREMENTS.md)](docs/REQUIREMENTS.md) (Basierend auf dem Projektauftrag)
* [Clean-Code-Kriterien (CLEAN_CODE.md)](docs/CLEAN_CODE.md) (Unsere Definition nach LF 11)
* [IHK-Standards (Externer Link)](https://www.ihk.de/rostock/aus-und-weiterbildung/pruefungen/abschlusspruefung/dokumentation-projektarbeit-2646884)

## 📝 Projektbeschreibung

Die Anwendung ist eine **zeitabhängige, diskrete Ereignissimulation** eines komplexen Supermarkt-Kassenbereichs. Der Benutzer kann die Rahmenbedingungen (Parameter) für den Supermarktbetrieb konfigurieren, um die Auswirkungen auf Warteschlangen, Kassenauslastung und Kundenzufriedenheit zu analysieren. Die Anwendung dient dazu, die Auswirkungen verschiedener Eingabeparameter und Zufallsfaktoren auf ein Warteschlangensystem visuell darzustellen und auszuwerten.

Das Projekt wird entwickelt, um alle funktionalen und nicht-funktionalen Anforderungen des Projektauftrags zu erfüllen.

## ✨ Kernfeatures

Das Projekt implementiert die folgenden, im Projektauftrag geforderten Features:

* **Diskrete Ereignissimulation:** Eine logische, zeitabhängige Simulation (mittels **`SimPy`**), die Kundenankünfte, intelligente Kassenwahl, Wartezeiten und Abfertigungsprozesse (basierend auf Kassentyp und Personalrolle) modelliert.
* **Simulationsmodi:** Die Dauer kann flexibel gesteuert werden über:
    * Einen "Endlos-Modus" (läuft bis Abbruch).
    * Eine definierte Zeitspanne (z.B. "Laden öffnet um 08:00" / "schließt um 20:00").
* **Variable Simulationsgeschwindigkeit:** Die Abspielgeschwindigkeit der Simulation kann in **mindestens 3 Stufen** (z.B. Pause, 1x, 10x, 100x) gesteuert werden.
* **Umfassende Eingabeparameter:** Die Simulation wird durch eine Vielzahl von Parametern (übertrifft die Anforderung von 7) gesteuert:
    * **Kassen-Setup:**
        * Anzahl Kassen (Typ: Bedient)
        * Anzahl Kassen (Typ: Barrierefrei)
        * Anzahl Kassen (Typ: SB-Kasse)
    * **Personal-Setup:**
        * Dynamische Rollenzuweisung (Profi/Azubi) für jede einzelne bediente Kasse.
    * **Kunden-Setup:**
        * Kundendichte (Kunden pro Stunde).
        * Anteil Rollstuhlfahrer (in %).
    * **Geschwindigkeiten (Scan-Logik):**
        * Scangeschwindigkeit: Profi
        * Scangeschwindigkeit: Azubi
        * Scangeschwindigkeit: Rollstuhlfahrer (an SB-Kasse)
    * **SB-Kassen-Logik:**
        * Wahrscheinlichkeit einer SB-Störung (in %).
        * Artikellimit für SB-Kassen.
* **Zufallsverteilungen (Erweiterte Steuerung):** Die Simulation integriert **drei verschiedene Zufallsverteilungen** und erlaubt dem Nutzer (optional mit der Bedingung, dass jede Verteilung einmal vorhanden ist) die Konfiguration:
    1.  **Kundenankunft:** (Default: **Exponentialverteilung**). *Erweitert: Nutzer kann Verteilung wählen.*
    2.  **Artikelanzahl:** (Default: **Normalverteilung**). *Erweitert: Nutzer kann Verteilung wählen.*
        * Mittelwert für Artikelanzahl (Default: 20)
    3.  **Bezahlvorgang-Dauer:** (Default: **Gleichverteilung**). *Erweitert: Nutzer kann Verteilung wählen.*
        * Minimalzeit (Default: 10 Sek.)
        * Maximalzeit (Default: 30 Sek.)
* **Visuelle Auswertung & Darstellung:** Die Simulationsergebnisse werden dynamisch (live) und in einer finalen Übersicht grafisch mit **`PyQtGraph`** dargestellt (z.B. Auslastung der Kassen, mittlere Wartezeit).
* **Kleine Animation:** Eine simple 2D-Visualisierung (mittels `QGraphicsView`) zeigt schematisch die Kassen (mit Rollen-Symbolen) und die sich aufbauenden Warteschlangen.
* **Intuitive GUI:** Eine grafische Benutzeroberfläche (mittels **`PyQt6`**), die nach den Interaktionsprinzipien der **ISO 9241-110** gestaltet ist.

## 🛠️ Technisches Konzept & Architektur

Das Projekt wird in Python 3 umgesetzt und folgt einer klaren Trennung von Logik (SimPy) und Darstellung (PyQt6), um die Kriterien für Clean Code und Testbarkeit zu erfüllen.

* **Kernlogik (Model):** Die zeitabhängige, diskrete Ereignissimulation wird mit **`SimPy`** realisiert. `SimPy` verwaltet die Prozesslogik, die Zeitsteuerung und die Ressourcen (Kassen).
* **Benutzeroberfläche (View):** Die gesamte GUI wird mit **`PyQt6`** erstellt. `QGraphicsView` wird für die 2D-Animation genutzt.
* **Visualisierung:** Live-Plots und finale Auswertungsdiagramme werden mit **`PyQtGraph`** implementiert, da es für die Darstellung von Live-Daten in PyQt optimiert ist.
* **Zufall/Daten:** Die Generierung der Zufallsverteilungen (exponentiell, normal, uniform) wird über die **`NumPy`**-Bibliothek realisiert.
* **Deployment:** Um die Anforderung "ausführbare Datei" und "Lauffähigkeit auf Schulrechnern" zu erfüllen, wird die Anwendung mittels **`PyInstaller`** in eine einzelne `.exe`-Datei kompiliert.

## 🖱️ UI/UX-Konzept

Die Benutzeroberfläche orientiert sich an der **ISO 9241-110**.

* **UI-Fluss (Tab-basiert):**
    1.  **Tab "Konfiguration":** Enthält alle Eingabeparameter (Kassenanzahl, Rollen, Kundendaten). Enthält einen "Experten-Modus"-Button, der die Parameter der Zufallsverteilungen (Defaults) freischaltet.
    2.  **Tab "Simulation":** Zeigt die Live-Plots (Wartezeit-Entwicklung) und die 2D-Animation der Warteschlangen. Enthält die Steuerungselemente (Start, Pause, Geschwindigkeit).
    3.  **Tab "Auswertung":** (Nach Simulationsende) Zeigt eine Zusammenfassung der wichtigsten Kennzahlen (KPIs) und finale Graphen (z.B. Histogramm der Wartezeiten, Balkendiagramm der Kassenauslastung).

## 🚀 Tech Stack (Bestätigt)

* **Sprache:** Python (Version 3.10+)
* **GUI:** PyQt6
* **Simulation (Kern):** SimPy
* **Visualisierung (Plots):** PyQtGraph
* **Daten/Zufall:** NumPy
* **Deployment:** PyInstaller
* **Plattform:** Windows (64-bit)

## 📂 Projektmanagement

* **Vorgehensmodell:** Das Projekt folgt dem **Wasserfallmodell**, da die Anforderungen (siehe `REQUIREMENTS.md`) von Beginn an klar und unveränderlich durch den Projektauftrag definiert sind.
* **Abgabetermin:** 06.02.2026
* **Dokumentation:** Die vollständige Projektdokumentation nach IHK-Standard und ein digitales Benutzerhandbuch werden separat erstellt.
