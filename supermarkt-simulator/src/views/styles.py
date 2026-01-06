"""
Application styles.
Refactored:
- SPINBOXES: Removed ALL custom arrow/button styling.
  -> This restores the native OS (Windows) arrows which are bug-free.
  -> Kept custom Size (Height/Padding) and Colors (White/Black) as requested.
"""

from config import COLOR_BG_MAIN, COLOR_ACCENT, COLOR_TEXT_MAIN

def get_application_style():
    return f"""
    /* --- GLOBAL --- */
    QMainWindow {{
        background-color: {COLOR_BG_MAIN.name()};
    }}
    
    QLabel {{
        color: #000000;
        font-size: 13px;
        font-weight: 500;
    }}
    
    /* --- UHR --- */
    #ClockLabel {{
        font-size: 26px;
        font-weight: 800;
        color: #1F2937;
        padding: 6px 20px;
        background-color: #FFFFFF;
        border: 3px solid {COLOR_ACCENT.name()};
        border-radius: 8px;
    }}
    
    #ToolbarFrame {{
        background-color: #FFFFFF;
        border-bottom: 2px solid #D1D5DB;
    }}
    
    /* --- INPUT TAB --- */
    QWidget#ConfigContent {{
        background-color: #FFFFFF;
    }}
    
    QGroupBox {{
        font-weight: 800;
        border: 2px solid #9CA3AF;
        border-radius: 8px;
        margin-top: 16px;
        padding-top: 24px; 
        padding-bottom: 16px;
        padding-left: 12px;
        padding-right: 12px;
        color: {COLOR_ACCENT.name()};
        background-color: #FFFFFF;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 5px;
        left: 10px;
        background-color: #FFFFFF; 
    }}

    /* --- COMBOBOX --- */
    QComboBox {{
        background-color: #FFFFFF;
        border: 2px solid #6B7280;
        border-radius: 6px;
        padding: 4px 10px;
        color: #000000;
        font-size: 13px;
        min-width: 100px;
        min-height: 28px;
    }}
    QComboBox:hover {{
        border: 2px solid {COLOR_ACCENT.name()};
        background-color: #F9FAFB;
    }}
    QComboBox::drop-down {{
        border: none;
        background: #E5E7EB;
        width: 30px;
        border-left: 2px solid #6B7280;
    }}
    /* Einfacher CSS Pfeil für ComboBox bleibt, da ComboBoxen seltener glitchen */
    QComboBox::down-arrow {{
        width: 0; 
        height: 0; 
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 6px solid #000000;
        margin-left: 2px;
    }}
    QComboBox QAbstractItemView {{
        background-color: #FFFFFF;
        color: #000000;
        border: 2px solid #6B7280;
        selection-background-color: {COLOR_ACCENT.name()};
        selection-color: #FFFFFF;
        outline: none;
    }}

    /* --- SPINBOXEN (Werte) --- */
    /* Wir definieren NUR den Container. 
       Keine ::up-button oder ::down-arrow Styles mehr! */
    QSpinBox, QDoubleSpinBox, QTimeEdit {{
        background-color: #FFFFFF;
        color: #000000;
        font-weight: bold;
        font-size: 13px;
        padding: 4px 10px;
        min-height: 28px; /* Größe bleibt */
        selection-background-color: {COLOR_ACCENT.name()};
        selection-color: white;
    }}

    /* --- SCROLLBAR --- */
    QScrollArea {{
        border: none;
        background-color: #FFFFFF;
    }}
    QScrollBar:vertical {{
        border: none;
        background: #F3F4F6;
        width: 16px;
        margin: 0px;
    }}
    QScrollBar::handle:vertical {{
        background: #9CA3AF;
        min-height: 40px;
        border-radius: 8px;
        margin: 3px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: #6B7280;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    /* --- BUTTONS --- */
    QPushButton {{
        background-color: #F3F4F6;
        border: 2px solid #9CA3AF;
        border-radius: 6px;
        padding: 8px 16px;
        color: #000000;
        font-size: 13px;
        font-weight: 700;
        min-height: 28px;
    }}
    QPushButton:hover {{
        background-color: #E5E7EB;
        border-color: #4B5563;
        color: #000000;
    }}
    QPushButton:checked {{
        background-color: {COLOR_ACCENT.name()};
        color: white;
        border: 2px solid {COLOR_ACCENT.name()};
    }}
    
    /* --- TABS --- */
    QTabWidget::pane {{
        border: 2px solid #D1D5DB;
        background: #FFFFFF;
    }}
    QTabBar::tab {{
        background: #F3F4F6;
        border: 1px solid #D1D5DB;
        padding: 10px 20px;
        margin-right: 2px;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
        color: #4B5563;
        font-size: 13px;
        font-weight: 600;
    }}
    QTabBar::tab:selected {{
        background: #FFFFFF;
        border-bottom-color: #FFFFFF;
        font-weight: bold;
        color: {COLOR_ACCENT.name()};
        border-top: 4px solid {COLOR_ACCENT.name()};
    }}
    
    QListWidget {{
        background-color: #FFFFFF;
        border: 2px solid #E5E7EB;
        color: #000000;
        border-radius: 4px;
        font-family: "Consolas", "Courier New", monospace;
    }}
    """