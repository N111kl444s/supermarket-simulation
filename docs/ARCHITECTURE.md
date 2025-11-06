# Architektur-Dokument: "Piep - Der Takt der Kasse"

## 1. Gesamtsystem-Architektur (Model-View-Controller)

Das Projekt folgt einer **Model-View-Controller (MVC)**-Architektur, um eine klare Trennung der Verantwortlichkeiten (Single Responsibility Principle) zu gewährleisten und die Clean-Code-Anforderungen zu erfüllen.

* **Model (Modell):**
    * Enthält die gesamte **Kernlogik der Simulation** und die Datenmodelle.
    * Es ist komplett vom UI entkoppelt und weiß nichts über die Existenz von Fenstern oder Knöpfen.
    * **Technologien:** `SimPy` (für die diskrete Ereignissimulation, Zeitsteuerung, Ressourcen-Management), `NumPy` (für Zufallsverteilungen), reine Python-Klassen (z.B. `Customer`, `Cashier`).

* **View (Ansicht):**
    * Repräsentiert das **User Interface (UI)**, das mit **PyQt6** umgesetzt wird.
    * Es ist für die Darstellung der Simulation (Animation, Graphen) und die Erfassung der Benutzereingaben (Parameter) verantwortlich.
    * Die View ist "dumm"; sie speichert keine Logik, sondern delegiert alle Aktionen an den Controller.
    * **Technologien:** `PyQt6` (Fenster, Knöpfe, Tab-Layout), `PyQtGraph` (Live-Plots, Auswertung), `QGraphicsView` (2D-Animation).

* **Controller (Steuerung):**
    * Dient als **Vermittler** zwischen Model und View.
    * Er nutzt das **Signals & Slots-Konzept** von PyQt, um auf UI-Ereignisse zu reagieren.
    * Er verarbeitet Ereignisse aus der View (z.B. "Start-Button geklickt"), leitet die Anfragen an das Model weiter (`simulation.start()`), ruft die Simulationsdaten ab und aktualisiert die View.
    * **Technologien:** Reine Python-Klasse, die `PyQt Signals & Slots` nutzt, um Model und View zu verbinden.

Diese Struktur stellt sicher, dass Änderungen am UI die Simulationslogik nicht beeinträchtigen und umgekehrt, was die Wartbarkeit und Testbarkeit (Anforderung LF 11) des Systems massiv erhöht.

## 2. Datenfluss

Der Datenfluss im System ist unidirektional und klar definiert:

1.  **Benutzereingabe:** Der Benutzer ändert über ein UI-Steuerelement (z.B. einen Slider im **View**) einen Parameter wie die "Kundendichte".
2.  **Eingabeverarbeitung:** Der **Controller** fängt dieses Ereignis (z.B. `signal_kundendichte_geändert`) ab und ruft eine entsprechende Methode im **Model** auf (z.B. `model.set_parameter(...)`).
3.  **Simulations-Logik:** Das **Model** (die `SimPy`-Engine) verarbeitet die neuen Parameter. Wenn die Simulation läuft, generiert sie Ereignisse (Kundenankunft, Kassen-Interaktion, Störung).
4.  **Datenabfrage:** Der **Controller** wird vom Model (via Signal) über Updates informiert oder fragt zyklisch die aktualisierten Daten (z.B. aktuelle Warteschlangenlängen, Kassenauslastung) aus dem **Model** ab.
5.  **View-Aktualisierung:** Der **Controller** übergibt die abgerufenen Daten (z.B. `[5, 3, 7]`) an die **View**, die sie in Echtzeit aktualisiert (z.B. Update der `PyQtGraph`-Plots und der `QGraphicsView`-Animation).

## 3. Kern-Komponenten (Geplante Klassen)

Die folgenden Klassen bilden das Rückgrat der Anwendung:

* **Model-Schicht:**
    * `Customer`: Datenklasse (POJO). Speichert Attribute wie `article_count`, `is_wheelchair_user`, `sb_affinity`.
    * `Cashier`: Datenklasse. Speichert Attribute wie `role` (Profi/Azubi), `type` (Bedient/SB/Barrierefrei).
    * `SimulationEngine`: Die zentrale Klasse des Models. Sie enthält die `SimPy`-Umgebung (`env`), verwaltet die `SimPy`-Ressourcen (die Kassen) und startet die `SimPy`-Prozesse (z.B. `customer_generator`, `customer_process`).

* **Controller-Schicht:**
    * `SimulationController`: Der zentrale **Controller**. Erstellt die Instanzen von `SimulationEngine` und `MainWindow`. Er verbindet alle Signale und Slots und steuert den Haupt-Datenfluss.

* **View-Schicht:**
    * `MainWindow`: Die zentrale Klasse des **Views** (z.B. `QMainWindow`). Sie baut das PyQt6-Frontend (Tabs, Parameter-Boxen) auf und hält die Instanzen der untergeordneten View-Elemente.
    * `PlotWidget`: Eine spezialisierte `PyQtGraph`-Klasse zur Anzeige der Live-Statistiken.
    * `AnimationView`: Eine spezialisierte `QGraphicsView`-Klasse zur 2D-Darstellung der Warteschlangen.

## 4. Modellierung der Zufallselemente

Die Simulation nutzt die folgenden drei, im Projektauftrag geforderten, Zufallsverteilungen. Diese sind als Eingabeparameter (teils optional) konfigurierbar.

* **Kundenankunft (Exponentialverteilung):**
    * Die Zeitabstände zwischen dem Eintreffen neuer Kunden folgen einer **Exponentialverteilung**.
    * **Begründung:** Dies ist das Standardmodell (Poisson-Prozess) zur Simulation von zufälligen, voneinander unabhängigen Ankunftsereignissen (z.B. Anrufe im Callcenter, Kunden im Supermarkt).

* **Artikelanzahl (Normalverteilung):**
    * Die Anzahl der Artikel im Einkaufswagen eines Kunden folgt einer **Normalverteilung**.
    * **Begründung:** Die meisten Kunden kaufen eine "durchschnittliche" Menge (Mittelwert), während sehr wenige Kunden extrem viel oder extrem wenig kaufen. Dies wird durch die Glockenkurve der Normalverteilung realistisch abgebildet.

* **Bezahlvorgang (Gleichverteilung):**
    * Die Dauer des reinen Bezahlvorgangs (PIN-Eingabe, Einpacken) folgt einer **Gleichverteilung** (Uniform Distribution).
    * **Begründung:** Wir definieren eine klare Minimal- und Maximalzeit (z.B. 10-30 Sek.). Jede Dauer innerhalb dieses Bereichs wird als gleich wahrscheinlich angenommen, da der Prozess (z.B. PIN-Eingabe) wenig Varianz aufweist.

* **Zusätzliche Zufallsereignisse:**
    * **SB-Kassen-Störung:** Ein binäres Zufallsereignis (z.B. 5% Wahrscheinlichkeit pro Kunde), das eine Verzögerung (Intervention) auslöst.
