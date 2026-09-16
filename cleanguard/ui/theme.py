"""
CleanGuard Design System and Dark Theme Styling.
"""

# Color Palette Tokens
BG_MAIN = "#0B0F19"         # Deep Slate Black
BG_SIDEBAR = "#111827"      # Dark Charcoal Navy
BG_CARD = "#1F2937"         # Elevated Surface
BG_CARD_HOVER = "#283548"   # Card Hover
BORDER_COLOR = "#374151"    # Subdued Slate Border
BORDER_FOCUS = "#3B82F6"    # Primary Blue Border Focus

TEXT_PRIMARY = "#F9FAFB"    # Crisp White
TEXT_SECONDARY = "#9CA3AF"  # Cool Gray
TEXT_MUTED = "#6B7280"      # Subdued Gray

ACCENT_EMERALD = "#10B981"  # Success / Safe Emerald
ACCENT_BLUE = "#3B82F6"     # Primary Action Blue
ACCENT_BLUE_HOVER = "#2563EB"
ACCENT_AMBER = "#F59E0B"    # Review Warning Amber
ACCENT_RED = "#EF4444"      # Blocked Danger Crimson


DARK_STYLESHEET = """
QMainWindow {
    background-color: #0B0F19;
}

QWidget {
    color: #F9FAFB;
    font-family: 'Segoe UI', 'Roboto', 'Helvetica Neue', sans-serif;
    font-size: 13px;
}

/* Sidebar Navigation */
QFrame#Sidebar {
    background-color: #111827;
    border-right: 1px solid #1F2937;
}

QPushButton#NavButton {
    background-color: transparent;
    color: #9CA3AF;
    text-align: left;
    padding: 12px 18px;
    font-size: 14px;
    font-weight: 500;
    border: none;
    border-radius: 8px;
    margin: 2px 8px;
}

QPushButton#NavButton:hover {
    background-color: #1F2937;
    color: #F9FAFB;
}

QPushButton#NavButton:checked {
    background-color: #1E3A8A;
    color: #60A5FA;
    font-weight: 600;
}

/* Primary Action Buttons */
QPushButton#PrimaryButton {
    background-color: #10B981;
    color: #FFFFFF;
    font-size: 14px;
    font-weight: 600;
    padding: 10px 24px;
    border: none;
    border-radius: 8px;
}

QPushButton#PrimaryButton:hover {
    background-color: #059669;
}

QPushButton#PrimaryButton:pressed {
    background-color: #047857;
}

QPushButton#SecondaryButton {
    background-color: #1F2937;
    color: #F9FAFB;
    font-size: 13px;
    font-weight: 500;
    padding: 8px 18px;
    border: 1px solid #374151;
    border-radius: 6px;
}

QPushButton#SecondaryButton:hover {
    background-color: #283548;
    border-color: #4B5563;
}

QPushButton#DangerButton {
    background-color: #DC2626;
    color: #FFFFFF;
    font-size: 13px;
    font-weight: 600;
    padding: 8px 18px;
    border: none;
    border-radius: 6px;
}

QPushButton#DangerButton:hover {
    background-color: #B91C1C;
}

/* Cards */
QFrame#SurfaceCard {
    background-color: #1F2937;
    border: 1px solid #374151;
    border-radius: 10px;
    padding: 16px;
}

/* Tables */
QTableWidget {
    background-color: #111827;
    border: 1px solid #1F2937;
    border-radius: 8px;
    gridline-color: #1F2937;
    selection-background-color: #1E3A8A;
    selection-color: #FFFFFF;
}

QHeaderView::section {
    background-color: #1F2937;
    color: #9CA3AF;
    font-weight: 600;
    font-size: 12px;
    padding: 8px;
    border: none;
    border-bottom: 1px solid #374151;
}

/* Progress Bar */
QProgressBar {
    background-color: #111827;
    border: 1px solid #374151;
    border-radius: 6px;
    text-align: center;
    color: #F9FAFB;
    height: 14px;
}

QProgressBar::chunk {
    background-color: #10B981;
    border-radius: 5px;
}

/* Scrollbars */
QScrollBar:vertical {
    background: #111827;
    width: 10px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #374151;
    min-height: 20px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background: #4B5563;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""
