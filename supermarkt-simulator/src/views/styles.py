"""
Application styles and themes.
Refactored: 
- Added Modern Scrollbar Styling (Light Theme).
- Refined SpinBox Arrows (Cleaner look).
- Maintained previous fixes (White Inputs, Clock).
"""

from config import COLOR_BG_MAIN, COLOR_ACCENT, COLOR_TEXT_MAIN

def get_application_style():
    return f"""
    QMainWindow {{
        background-color: {COLOR_BG_MAIN.name()};
    }}
    
    QLabel {{
        color: {COLOR_TEXT_MAIN.name()};
        font-size: 12px;
    }}
    
    /* --- CLOCK DESIGN --- */
    #ClockLabel {{
        font-size: 24px;
        font-weight: bold;
        color: #1F2937;
        padding: 5px 15px;
        background-color: #FFFFFF;
        border: 2px solid {COLOR_ACCENT.name()};
        border-radius: 8px;
    }}
    
    #ToolbarFrame {{
        background-color: #FFFFFF;
        border-bottom: 1px solid #D1D5DB;
    }}
    
    /* --- INPUT TAB CONTAINER --- */
    QWidget#ConfigContent {{
        background-color: #FFFFFF;
    }}
    
    /* --- SCROLLBAR STYLING --- */
    QScrollArea {{
        border: none;
        background-color: #FFFFFF;
    }}
    
    QScrollBar:vertical {{
        border: none;
        background: #F3F4F6;
        width: 10px;
        margin: 0px;
    }}
    QScrollBar::handle:vertical {{
        background: #D1D5DB;
        min-height: 20px;
        border-radius: 5px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: #9CA3AF;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    
    /* --- GROUP BOX --- */
    QGroupBox {{
        font-weight: bold;
        border: 1px solid #E5E7EB;
        border-radius: 6px;
        margin-top: 12px;
        padding-top: 20px; 
        padding-bottom: 10px;
        padding-left: 10px;
        padding-right: 10px;
        color: #1F2937;
        background-color: #FFFFFF;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 5px;
        left: 10px;
    }}
    
    /* --- SPINBOX STYLING --- */
    QSpinBox, QDoubleSpinBox, QTimeEdit {{
        background-color: #FFFFFF;
        color: #111827;
        border: 1px solid #D1D5DB;
        border-radius: 4px;
        padding: 4px 8px; /* Mehr Platz für Text */
        min-height: 22px;
        selection-background-color: {COLOR_ACCENT.name()};
    }}
    
    QSpinBox:hover, QDoubleSpinBox:hover, QTimeEdit:hover {{
        border: 1px solid {COLOR_ACCENT.name()};
    }}

    /* Buttons (Up/Down) Container */
    QSpinBox::up-button, QDoubleSpinBox::up-button, QTimeEdit::up-button {{
        subcontrol-origin: border;
        subcontrol-position: top right;
        width: 20px;
        border-left: 1px solid #E5E7EB;
        border-bottom: 1px solid #E5E7EB;
        background-color: #F9FAFB;
        border-top-right-radius: 4px;
    }}
    
    QSpinBox::down-button, QDoubleSpinBox::down-button, QTimeEdit::down-button {{
        subcontrol-origin: border;
        subcontrol-position: bottom right;
        width: 20px;
        border-left: 1px solid #E5E7EB;
        border-top: 0px solid #E5E7EB; 
        background-color: #F9FAFB;
        border-bottom-right-radius: 4px;
    }}
    
    QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover {{
        background-color: #E5E7EB;
    }}
    QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
        background-color: #E5E7EB;
    }}

    /* CSS Arrows (Clean & Small) */
    QSpinBox::up-arrow, QDoubleSpinBox::up-arrow, QTimeEdit::up-arrow {{
        width: 0; 
        height: 0; 
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-bottom: 5px solid #4B5563; /* Dark Grey Arrow */
    }}

    QSpinBox::down-arrow, QDoubleSpinBox::down-arrow, QTimeEdit::down-arrow {{
        width: 0; 
        height: 0; 
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 5px solid #4B5563; /* Dark Grey Arrow */
    }}

    /* --- BUTTONS --- */
    QPushButton {{
        background-color: #FFFFFF;
        border: 1px solid #D1D5DB;
        border-radius: 6px;
        padding: 6px 12px;
        color: {COLOR_TEXT_MAIN.name()};
        font-weight: 500;
    }}
    QPushButton:hover {{
        background-color: #F3F4F6;
        border-color: #9CA3AF;
    }}
    QPushButton:checked {{
        background-color: {COLOR_ACCENT.name()};
        color: white;
        border: 1px solid {COLOR_ACCENT.name()};
    }}
    
    QComboBox {{
        background-color: #FFFFFF;
        border: 1px solid #D1D5DB;
        border-radius: 4px;
        padding: 4px;
        color: #111827;
    }}
    QComboBox::drop-down {{
        border: none;
        background: transparent;
        width: 20px;
    }}
    QComboBox::down-arrow {{
        image: none;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 6px solid #4B5563;
        margin-right: 8px;
    }}
    
    /* --- TABS --- */
    QTabWidget::pane {{
        border: 1px solid #E5E7EB;
        background: #FFFFFF;
    }}
    QTabBar::tab {{
        background: #F3F4F6;
        border: 1px solid #E5E7EB;
        padding: 8px 16px;
        margin-right: 2px;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
        color: #4B5563; /* Dark Grey for inactive */
    }}
    QTabBar::tab:selected {{
        background: #FFFFFF;
        border-bottom-color: #FFFFFF;
        font-weight: bold;
        color: {COLOR_ACCENT.name()}; /* Blue for active */
    }}
    
    QListWidget {{
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        color: #000000;
        border-radius: 4px;
    }}
    """