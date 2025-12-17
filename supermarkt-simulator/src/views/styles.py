"""
Style definitions for the application (QSS).
Implements a modern, clean LIGHT design.
Refined GroupBox titles to cut borders cleanly.
Fixed: Dialog backgrounds (specifically Offsets) and ScrollArea transparency.
"""

from config import (
    COLOR_BG_MAIN,
    COLOR_BG_PANEL,
    COLOR_BG_INPUT,
    COLOR_BORDER,
    COLOR_ACCENT,
    COLOR_TEXT_MAIN,
)


def get_application_style():
    """
    Returns the QSS stylesheet string for the entire application.
    """

    # Convert QColors to Hex strings
    c_bg = COLOR_BG_MAIN.name()
    c_panel = COLOR_BG_PANEL.name()
    c_input = COLOR_BG_INPUT.name()
    c_border = COLOR_BORDER.name()
    c_accent = COLOR_ACCENT.name()
    c_text = COLOR_TEXT_MAIN.name()

    return f"""
        QMainWindow {{
            background-color: {c_bg};
        }}
        
        /* --- DIALOGS --- */
        /* Standard Dialog Background matches Panels */
        QDialog {{
            background-color: {c_panel};
            color: {c_text};
        }}
        
        /* SPECIAL: Global Offsets Dialog -> White Background */
        QDialog[windowTitle="Globale Offsets"] {{
            background-color: #ffffff;
            color: {c_text};
        }}
        
        /* --- SCROLL AREA FIX --- */
        /* Ensures the white background of the dialog shines through the scroll area */
        QScrollArea {{
            background-color: transparent;
            border: none;
        }}
        QScrollArea > QWidget {{
            background-color: transparent;
        }}
        QScrollArea > QWidget > QWidget {{
            background-color: transparent;
        }}

        QWidget {{
            color: {c_text};
            font-family: 'Segoe UI', 'Roboto', sans-serif;
            font-size: 13px;
        }}
        
        /* --- LABELS --- */
        QLabel {{
            background-color: transparent;
            border: none;
            padding: 0px; 
            color: {c_text};
        }}
        
        /* --- TOOLBAR FRAME --- */
        QFrame#ToolbarFrame {{
            background-color: {c_panel};
            border-bottom: 1px solid {c_border};
        }}

        /* --- GROUP BOXES --- */
        QGroupBox {{
            background-color: {c_panel};
            border: 1px solid {c_border};
            border-radius: 6px;
            margin-top: 12px; /* Space for the title to sit on top */
            padding-top: 15px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            /* Padding creates space around text so border looks 'cut' */
            padding: 0px 5px; 
            /* Solid background matches panel to hide the border line behind text */
            background-color: {c_panel}; 
            color: {c_text};
            font-weight: bold;
            margin-left: 10px;
        }}

        /* --- BUTTONS --- */
        QPushButton {{
            background-color: {c_panel};
            border: 1px solid {c_border};
            border-radius: 4px;
            padding: 6px 12px;
            color: {c_text};
            margin: 1px;
        }}
        QPushButton:hover {{
            background-color: #E5E7EB;
            border: 1px solid {c_accent};
        }}
        QPushButton:pressed {{
            background-color: {c_accent};
            color: white;
            border: 1px solid {c_accent};
        }}
        
        /* Hide icons in Standard Dialog Buttons (Save/Cancel) for cleaner look */
        QDialogButtonBox QPushButton {{
            icon-size: 0px;
            min-width: 60px;
        }}

        /* --- TABS --- */
        QTabWidget::pane {{
            border: 1px solid {c_border};
            background-color: {c_panel};
            border-radius: 4px;
        }}
        QTabBar::tab {{
            background: {c_bg};
            color: {c_text};
            padding: 8px 16px;
            margin-right: 4px;
            border: 1px solid {c_border};
            border-bottom: none;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }}
        QTabBar::tab:selected {{
            background: {c_panel};
            font-weight: bold;
            border-bottom: 1px solid {c_panel};
            margin-bottom: -1px;
        }}
        QTabBar::tab:hover {{
            background: #E5E7EB;
        }}

        /* --- INPUTS & COMBOBOX --- */
        QLineEdit, QSpinBox, QComboBox {{
            background-color: {c_input};
            border: 1px solid {c_border};
            border-radius: 4px;
            padding: 4px;
            color: {c_text};
        }}
        QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
            border: 1px solid {c_accent};
        }}
        
        /* Combobox Popup Styling */
        QComboBox QAbstractItemView {{
            background-color: {c_input};
            border: 1px solid {c_border};
            selection-background-color: {c_accent};
            selection-color: white;
            outline: none;
        }}
        
        /* --- SPINBOX ARROWS --- */
        QSpinBox::up-button, QDoubleSpinBox::up-button, 
        QSpinBox::down-button, QDoubleSpinBox::down-button {{
            width: 20px;
            background-color: #F3F4F6;
            border-left: 1px solid {c_border};
        }}
        QSpinBox::up-button, QDoubleSpinBox::up-button {{
            subcontrol-origin: border;
            subcontrol-position: top right;
            border-bottom: 1px solid {c_border};
            border-top-right-radius: 4px;
        }}
        QSpinBox::down-button, QDoubleSpinBox::down-button {{
            subcontrol-origin: border;
            subcontrol-position: bottom right;
            border-bottom-right-radius: 4px;
        }}
        
        /* --- TABLES & LISTS --- */
        QListWidget, QTableWidget {{
            background-color: {c_input};
            border: 1px solid {c_border};
            border-radius: 4px;
            gridline-color: #F3F4F6;
            outline: none;
        }}
        QListWidget::item, QTableWidget::item {{
            padding: 4px;
            border-bottom: 1px solid #F3F4F6;
            color: {c_text};
        }}
        QListWidget::item:selected, QTableWidget::item:selected {{
            background-color: {c_accent};
            color: white;
            border-radius: 2px;
        }}
        QHeaderView::section {{
            background-color: #F9FAFB;
            color: {c_text};
            padding: 4px;
            border: none;
            border-bottom: 2px solid {c_border};
            font-weight: bold;
        }}
        
        /* --- SCROLLBARS --- */
        QScrollBar:vertical {{
            background: {c_bg};
            width: 10px;
            margin: 0px;
        }}
        QScrollBar::handle:vertical {{
            background: #9CA3AF;
            min-height: 20px;
            border-radius: 5px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {c_accent};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
        
        QScrollBar:horizontal {{
            background: {c_bg};
            height: 10px;
            margin: 0px;
        }}
        QScrollBar::handle:horizontal {{
            background: #9CA3AF;
            min-width: 20px;
            border-radius: 5px;
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0px; }}

        /* --- SPLITTER --- */
        QSplitter::handle {{
            background-color: {c_border};
        }}
    """
