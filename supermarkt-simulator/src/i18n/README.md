# Internationalization (i18n) System

## Overview

Die Anwendung unterstützt jetzt mehrsprachige UI. Das System basiert auf:

- **TranslationManager**: Zentrale Klasse zum Laden und Verwalten von Translations
- **JSON-Dateien**: Strukturierte Übersetzungsdateien für jede Sprache

## Struktur

```
src/i18n/
├── __init__.py              # Package init
├── translations.py          # TranslationManager Klasse
├── de.json                  # Deutsche Übersetzungen
└── en.json                  # Englische Übersetzungen
```

## Verwendung in Code

### TranslationManager initialisieren

```python
from i18n import TranslationManager

# Deutsch (Standard)
translator = TranslationManager('de')

# Englisch
translator = TranslationManager('en')
```

### Strings abrufen

```python
# Einfache Keys
title = translator.get('window.title')

# Mit Default-Wert falls Key nicht gefunden
text = translator.get('some.missing.key', 'Fallback Text')

# Aktuelle Sprache
current = translator.get_current_language()  # Returns: 'de' or 'en'
```

### Sprache wechseln

```python
translator.set_language('en')
```

### Verfügbare Sprachen auflisten

```python
available = translator.get_available_languages()
# Returns: ['de', 'en']
```

## View-Komponenten mit Translator

### Beispiel: Sidebar

```python
from views.components.sidebar import Sidebar

# Mit Translator
sidebar = Sidebar(translator=translator)

# Sidebar wird automatisch mit Translation initialisiert
```

### Beispiel: MainWindow

```python
from views.main_window import MainWindow

window = MainWindow(translator=translator)
```

## Neue Sprache hinzufügen

1. Neue JSON-Datei erstellen (z.B. `src/i18n/fr.json`)
2. Struktur von `de.json` oder `en.json` kopieren
3. Alle Strings übersetzen
4. TranslationManager lädt sie automatisch

Beispiel-Struktur fr.json:

```json
{
  "window": {
    "title": "Simulateur de Supermarché - Etabli"
  },
  "sidebar": {
    "tabs": {
      "input": "Entrée",
      ...
    }
  }
}
```

## Verfügbare Übersetzungs-Keys

Die Keys sind hierarchisch organisiert nach UI-Komponenten:

- `window.*` - Fenster-Titel
- `sidebar.*` - Sidebar Komponente
- `toolbar.*` - Toolbar Komponente
- `dialogs.*` - Dialog Fenster
- `tooltips.*` - Hilfe-Tooltips

## Settings-Integration

Die aktive Sprache wird in `settings.json` gespeichert:

```json
{
  "language": "de"
}
```

Diese wird beim Start automatisch geladen und wiederhergestellt.

## Controller Integration

Im MainController:

```python
language = self.settings.get("language", DEFAULT_LANGUAGE)
self.translator = TranslationManager(language)

# Sprachwechsel vom UI
self.view.sidebar_component.language_changed.connect(self.on_language_changed)
```

## Hinweise

- UI-Updates bei Sprachwechsel erfordern **Neustart der Anwendung**
- Missing Keys werden mit dem Key-String selbst zurückgegeben (Fallback)
- Alle View-Klassen sollten im Constructor einen optionalen `translator` Parameter haben
