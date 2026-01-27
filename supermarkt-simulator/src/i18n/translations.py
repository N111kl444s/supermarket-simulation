"""
Translation Manager for multi-language support.
Loads translation files and provides access to translated strings.
"""

import json
from pathlib import Path
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal


class TranslationManager(QObject):
    """Manages translations for the application."""

    language_changed = pyqtSignal(str)  # Emits language code when changed

    def __init__(self, language: str = "de"):
        """
        Initialize TranslationManager.

        Args:
            language: Language code (e.g., 'de', 'en'). Defaults to 'de'.
        """
        super().__init__()
        self.i18n_dir = Path(__file__).parent
        self.translations = {}
        self.current_language = language
        self._load_language(language)

    def _load_language(self, language: str) -> None:
        """
        Load translation file for specified language.

        Args:
            language: Language code (e.g., 'de', 'en')
        """
        trans_file = self.i18n_dir / f"{language}.json"

        if not trans_file.exists():
            print(f"Warning: Translation file not found: {trans_file}")
            self.translations = {}
            return

        try:
            with open(trans_file, "r", encoding="utf-8") as f:
                self.translations = json.load(f)
                self.current_language = language
        except Exception as e:
            print(f"Error loading translations: {e}")
            self.translations = {}

    def get(self, key: str, default: Optional[str] = None) -> str:
        """
        Get translation for a key.

        Args:
            key: Dot-separated key (e.g., 'toolbar.reset')
            default: Default value if key not found

        Returns:
            Translated string or default value
        """
        keys = key.split(".")
        value = self.translations

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default or key

        return str(value) if value else (default or key)

    def set_language(self, language: str) -> None:
        """
        Change the current language.

        Args:
            language: Language code (e.g., 'de', 'en')
        """
        self._load_language(language)
        self.language_changed.emit(language)

    def get_current_language(self) -> str:
        """
        Get the currently active language code.

        Returns:
            Current language code
        """
        return self.current_language

    def get_available_languages(self) -> list:
        """
        Get list of available languages.

        Returns:
            List of available language codes
        """
        available = []
        for file in self.i18n_dir.glob("*.json"):
            lang_code = file.stem
            if lang_code not in ["__pycache__"]:
                available.append(lang_code)
        return sorted(available)
