"""Application Launcher - manages screen navigation and initialization."""

from PyQt6.QtWidgets import QMainWindow, QStackedWidget, QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from views.screens.main_menu_screen import MainMenuScreen
from views.screens.settings_screen import SettingsScreen
from views.screens.info_screen import InfoScreen
from views.main_window import MainWindow
from views.styles import get_application_style
from controllers.main_controller import MainController
from config import DEFAULT_SETTINGS, DEFAULT_LANGUAGE
from i18n import TranslationManager
from pathlib import Path
import json

SETTINGS_FILE = Path(__file__).parent.parent / "settings.json"


class ApplicationLauncher(QMainWindow):
    """Main application window that manages different screens."""
    
    SCREEN_MENU = 0
    SCREEN_SETTINGS = 1
    SCREEN_INFO = 2
    SCREEN_SIMULATION = 3
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Supermarkt Simulator")
        self.showFullScreen()
        
        # Load settings
        self.settings = DEFAULT_SETTINGS.copy()
        self._load_settings()
        
        # Create translator with saved language
        language = self.settings.get("language", DEFAULT_LANGUAGE)
        self.translator = TranslationManager(language)
        
        # Create stacked widget for screen navigation
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Create screens
        self.menu_screen = MainMenuScreen(self.translator)
        self.settings_screen = SettingsScreen(self.settings, self.translator)
        self.info_screen = InfoScreen(self.translator)
        self.simulation_controller = None
        self.simulation_screen = None
        
        # Add screens to stacked widget
        self.stacked_widget.addWidget(self.menu_screen)
        self.stacked_widget.addWidget(self.settings_screen)
        self.stacked_widget.addWidget(self.info_screen)
        
        # Connect signals
        self._connect_signals()
        
        # Apply style
        self.setStyleSheet(get_application_style())
        
        # Show main menu first
        self.show_menu()
    
    def _connect_signals(self):
        """Connect signals between screens and launcher."""
        # Main menu
        self.menu_screen.on_start_clicked = self.show_simulation
        self.menu_screen.on_settings_clicked = self.show_settings
        self.menu_screen.on_info_clicked = self.show_info
        self.menu_screen.on_exit_clicked = self.close
        
        # Settings
        self.settings_screen.settings_changed.connect(self._on_settings_changed)
        self.settings_screen.back_requested.connect(self.show_menu)
        
        # Info
        self.info_screen.back_requested.connect(self.show_menu)
        
        # Translator language change
        self.translator.language_changed.connect(self._on_language_changed)
    
    def show_menu(self):
        """Show main menu screen."""
        self.stacked_widget.setCurrentIndex(self.SCREEN_MENU)
    
    def show_settings(self):
        """Show settings screen."""
        self.stacked_widget.setCurrentIndex(self.SCREEN_SETTINGS)
    
    def show_info(self):
        """Show info screen."""
        self.stacked_widget.setCurrentIndex(self.SCREEN_INFO)
    
    def show_simulation(self):
        """Show simulation screen (create if needed)."""
        # Always create a fresh simulation with current translator
        if self.simulation_screen is not None:
            # Remove old simulation from stacked widget
            self.stacked_widget.removeWidget(self.simulation_screen)
            # Clean up old simulation
            self.simulation_screen.deleteLater()
            self.simulation_controller = None
            self.simulation_screen = None
        
        # Create new simulation screen with current translator
        self.simulation_controller = MainController(self.translator)
        self.simulation_screen = self.simulation_controller.view
        
        # Connect back-to-menu signal
        self.simulation_screen.back_to_menu_requested.connect(self._on_back_from_simulation)
        
        self.stacked_widget.addWidget(self.simulation_screen)
        self.stacked_widget.setCurrentIndex(self.SCREEN_SIMULATION)
    
    def _on_back_from_simulation(self):
        """Handle returning from simulation to main menu."""
        # Stop and cleanup simulation completely
        if self.simulation_controller:
            if self.simulation_controller.sim_manager.is_running:
                self.simulation_controller.sim_manager.pause()
            
            # Remove simulation screen from stack
            if self.simulation_screen:
                self.stacked_widget.removeWidget(self.simulation_screen)
                self.simulation_screen.deleteLater()
                self.simulation_screen = None
            
            self.simulation_controller = None
        
        # Return to menu
        self.show_menu()
    
    def _add_back_button_to_simulation(self):
        """Add a back to menu button to the simulation screen."""
        # Create a back button in the toolbar or somewhere visible
        # For now, we'll use the window close event
        pass
    
    def _on_settings_changed(self, settings):
        """Handle settings changes."""
        self.settings.update(settings)
        self._save_settings()
        
        # Update language
        language = settings.get("language", self.settings.get("language"))
        self.translator.set_language(language)
        
        # Update simulator if it exists
        if self.simulation_controller:
            self.simulation_controller.translator = self.translator
    
    def _on_language_changed(self, language):
        """Handle language change - update all screens."""
        # Update main menu screen
        self.menu_screen.update_translations()
        # Update settings screen
        self.settings_screen.update_translations()
        # Update info screen
        self.info_screen.update_translations()
    
    def _load_settings(self):
        """Load settings from file."""
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, "r") as f:
                    self.settings.update(json.load(f))
            except Exception as e:
                print(f"Error loading settings: {e}")
    
    def _save_settings(self):
        """Save settings to file."""
        try:
            with open(SETTINGS_FILE, "w") as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def keyPressEvent(self, event):
        """Handle key press events."""
        # Escape key goes back to main menu (except in simulation)
        if event.key() == Qt.Key.Key_Escape:
            current_index = self.stacked_widget.currentIndex()
            if current_index != self.SCREEN_SIMULATION:
                self.show_menu()
            else:
                # In simulation, could add a dialog asking to return
                pass
        super().keyPressEvent(event)
    
    def closeEvent(self, event):
        """Handle window close event."""
        # Save settings before closing
        self._save_settings()
        event.accept()
