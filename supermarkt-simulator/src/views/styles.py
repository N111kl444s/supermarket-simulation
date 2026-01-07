"""
Application styles.

This module provides the central CSS stylesheet for the application.
Updated:
- BUTTONS: Increased min-height to 38px for better clickability.
- INPUTS: Adjusted heights to match new button sizes.
"""

from config import COLOR_BG_MAIN, COLOR_ACCENT, COLOR_TEXT_MAIN, COLOR_BORDER

def get_application_style():
    """
    Generates the QSS (Qt Style Sheet) string for the application.
    """
    
    bg_main = COLOR_BG_MAIN.name()       # e.g. #F5F7FA
    accent = COLOR_ACCENT.name()         # e.g. #3B82F6
    border = COLOR_BORDER.name()         # e.g. #D1D5DB
    text_main = COLOR_TEXT_MAIN.name()   # e.g. #1F2937

    return f"""
    /* --- GLOBAL --- */
    QMainWindow {{
        background-color: {bg_main};
    }}
    
    QWidget {{
        font-family: "Segoe UI", "Helvetica Neue", "Arial", sans-serif;
        font-size: 13px;
        color: {text_main};
    }}
    
    /* --- CONFIG SIDEBAR LABELS --- */
    QWidget#ConfigContent QLabel {{
        font-size: 15px;
        font-weight: 500;
        color: {text_main};
        padding: 2px 0;
    }}
    
    /* --- UHR --- */
    #ClockLabel {{
        font-size: 26px;
        font-weight: 800;
        color: {text_main};
        padding: 4px 20px;
        background-color: #FFFFFF;
        border: 2px solid {accent};
        border-radius: 8px;
    }}
    
    #ToolbarFrame {{
        background-color: #FFFFFF;
        border-bottom: 1px solid {border};
    }}
    
    /* --- CONTAINER --- */
    QWidget#ConfigContent {{
        background-color: {bg_main};
    }}
    QScrollArea {{
        border: none;
        background-color: {bg_main};
    }}
    QGroupBox {{
        font-weight: 700;
        font-size: 14px;
        border: 1px solid {border};
        border-radius: 8px;
        margin-top: 24px;
        padding-top: 20px; 
        padding-bottom: 12px;
        padding-left: 12px;
        padding-right: 12px;
        color: {accent};
        background-color: transparent; 
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 6px;
        left: 10px;
        background-color: {bg_main}; 
    }}

    /* --- INPUTS & BUTTONS (Big & Clickable) --- */
    
    /* Inputs: Native Look aber groß */
    QSpinBox, QDoubleSpinBox, QTimeEdit {{
        background-color: #FFFFFF;
        font-weight: bold;
        color: {text_main};
        min-height: 38px; /* Match Button Height */
        font-size: 14px;
    }}

    QComboBox {{
        background-color: #FFFFFF;
        font-weight: bold;
        color: {text_main};
        min-height: 38px;
        font-size: 14px;
        border: 1px solid {border};
        border-radius: 6px;
        padding-left: 10px;
    }}
    QComboBox:hover {{
        border: 1px solid {accent};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 30px;
    }}
    QComboBox QAbstractItemView {{
        background-color: #FFFFFF;
        color: {text_main};
        selection-background-color: {accent};
        selection-color: #FFFFFF;
        border: 1px solid {border};
        outline: none;
    }}

    /* Buttons: Großzügig */
    QPushButton {{
        background-color: #FFFFFF;
        border: 1px solid {border};
        border-radius: 6px;
        padding: 0px 16px; /* Vertikales Padding reduziert, da min-height greift */
        color: {text_main};
        font-weight: 700;
        font-size: 14px;
        min-height: 38px; /* Größerer Klickbereich */
    }}
    QPushButton:hover {{
        background-color: #F8FAFC;
        border-color: {accent};
        color: {accent};
    }}
    QPushButton:pressed {{
        background-color: {accent};
        color: #FFFFFF;
    }}
    QPushButton:checked {{
        background-color: {accent};
        color: #FFFFFF;
        border: 1px solid {accent};
    }}
    
    /* --- TABS & LISTS --- */
    QTabWidget::pane {{
        border: 1px solid {border};
        border-radius: 6px;
        background: {bg_main};
        top: -1px;
    }}
    QTabBar::tab {{
        background: #E2E8F0;
        border: 1px solid {border};
        padding: 10px 24px; /* Auch Tabs etwas größer */
        margin-right: 4px;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
        color: #64748B;
        font-weight: 600;
    }}
    QTabBar::tab:selected {{
        background: {bg_main};
        border-bottom-color: {bg_main};
        color: {accent};
        font-weight: bold;
    }}
    QListWidget {{
        background-color: #FFFFFF;
        border: 1px solid {border};
        border-radius: 6px;
        padding: 5px;
    }}
    """