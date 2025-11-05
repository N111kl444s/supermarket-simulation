# Clean Code Kriterien: Projekt "Piep - Der Takt der Kasse"

Dieses Dokument definiert die verbindlichen Clean-Code-Kriterien für die Entwicklung der Supermarkt-Simulation. Diese Regeln sind Teil der nichtfunktionalen Anforderungen und Grundlage für die Qualitätssicherung und Benotung.

## 1. Grundprinzipien (Architektur & Design)

* **KISS (Keep It Simple, Stupid):**
    * Es wird stets die einfachste, funktionierende Lösung implementiert. Komplexität wird aktiv vermieden.
* **DRY (Don't Repeat Yourself):**
    * Code-Duplizierung ist verboten. Logik, die mehrfach benötigt wird, muss in wiederverwendbare Funktionen oder Methoden ausgelagert werden.
* **SRP (Single Responsibility Principle):**
    * Jede Klasse und jede Funktion hat exakt *eine* klar definierte Aufgabe und Verantwortung.
    * **Anti-Pattern (Verboten):** "Gottklassen" (God Classes), die versuchen, alles zu steuern (z.B. Simulation, GUI und Datenhaltung in einer Klasse).

## 2. Python-Spezifische Regeln (Implementierung)

* **Styleguide (PEP 8):**
    * Der [PEP 8 Style Guide](https://peps.python.org/pep-0008/) ist verbindlich. Dies betrifft Einrückung (4 Spaces), Import-Sortierung und Leerraum-Nutzung.
* **Benennungskonventionen:**
    * **Sprache:** Alle Bezeichner (Variablen, Funktionen, Klassen) sind **Englisch** (z.B. `customer`, `calculate_wait_time`).
    * **Variablen & Funktionen:** `snake_case` (z.B. `new_customer`, `calculate_wait_time`). (Wir verwenden *kein* `camelCase` für Variablen).
    * **Klassen:** `PascalCase` (z.B. `SupermarketSimulation`, `Customer`).
    * **Konstanten:** `UPPER_SNAKE_CASE` (z.B. `MAX_CASHIERS`).
* **Sprechende Namen:**
    * Namen müssen selbsterklärend sein und ihre Absicht widerspiegeln.
    * **Gut:** `time_until_next_customer`
    * **Schlecht:** `tbnk`, `val1`, `data`
* **Keine "Magic Numbers":**
    * Hartkodierte, unerklärte Zahlen im Code sind verboten.
    * **Schlecht:** `if time > 3600:`
    * **Gut:** `SIMULATION_DURATION_SECONDS = 3600` (als Konstante definiert) ... `if time > SIMULATION_DURATION_SECONDS:`
* **Komplexitätsreduktion (Verschachtelung):**
    * Die "Zyklomatische Komplexität" muss niedrig gehalten werden.
    * **Anti-Pattern (Verboten):** "Zwiebel-Code" (tief verschachtelte `if/elif/else`-Blöcke oder `for`-Schleifen).
    * **Regel:** Mehr als 2-3 Verschachtelungsebenen sind zu vermeiden und müssen refaktorisiert werden (z.B. durch "Guard Clauses" oder Auslagerung in Funktionen).
* **Funktionen und Methoden:**
    * **Größe:** Funktionen müssen kurz sein (Richtwert: max. 20-30 Zeilen). Längere Methoden müssen explizit begründet werden (z.B. bei komplexer GUI-Initialisierung).
    * **Parameter:** Funktionen sollten wenige Übergabeparameter haben (Ideal: 0-3). Bei mehr Parametern muss geprüft werden, ob diese zu einem Datenobjekt (z.B. `dataclass`) zusammengefasst werden können.
* **Kommentare (Inline):**
    * Kommentare erklären das **Warum** (die Absicht, komplexe Design-Entscheidungen), nicht das **Was** (offensichtliche Code-Logik).
    * **Gut:** `# We use exponential distribution here, as it accurately models random arrivals.`
    * **Schlecht:** `# Increment i by 1`
* **Docstrings (Epytext Format):**
    * Jede Klasse und jede öffentliche Methode/Funktion *muss* einen Docstring im Epytext-Format haben.
    * **Inhalt:** Der Docstring muss eine klare Methodenbeschreibung und `@param`-Tags für alle Parameter enthalten.
    * **Rückgabetyp:** Die Verwendung von `@rtype` ist optional, da der Rückgabetyp bereits durch Type Hinting (siehe nächster Punkt) abgedeckt wird.
    * **Beispiel:**
        ```python
        def calculate_wait_time(self, arrival_time: float, cashier_id: int) -> float:
            """
            Calculates the customer's wait time based on cashier availability.

            @param arrival_time: The simulation time when the customer arrived.
            @param cashier_id: The ID of the target cashier.
            @return: The calculated waiting time in seconds.
            """
            # ... implementation ...
        ```
* **Type Hinting (PEP 484):**
    * Alle neuen Funktionen und Methoden *müssen* mit Python Type Hints versehen werden. Dies ist *zusätzlich* zu den Docstrings erforderlich.
    * **Beispiel:** `def calculate_arrival(sim_time: float) -> float:`
* **Exception Handling:**
    * Erwartete Fehler (z.B. ungültige Benutzereingaben, Datei nicht gefunden) müssen robust durch `try...except`-Blöcke abgefangen werden. Der Nutzer muss eine verständliche Fehlermeldung erhalten.

## 3. Qualitätssicherung (QA) & Testen

* **Testbarkeit ist obligatorisch:** Auch wenn das Schreiben von Unit-Tests laut Unterrichtsnotizen "optional" sein mag, ist die **Testbarkeit** des Codes für dieses Projekt (gem. Anforderung LF 11) zwingend.
* Code, der gegen die obigen Regeln (insb. SRP, Magic Numbers, Komplexität) verstößt, gilt als nicht testbar und somit als nicht "Clean".
