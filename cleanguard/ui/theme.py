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
QTableView, QTableWidget {
    background-color: #0F172A;
    alternate-background-color: #131E32;
    color: #E2E8F0;
    border: 1px solid #1E293B;
    border-radius: 8px;
    gridline-color: transparent;
    selection-background-color: #1E3A8A;
    selection-color: #FFFFFF;
    outline: none;
}

QTableView::item, QTableWidget::item {
    padding: 6px 10px;
    border-bottom: 1px solid #172235;
}

QTableView::item:hover, QTableWidget::item:hover {
    background-color: #1E293B;
}

QTableView::item:selected, QTableWidget::item:selected {
    background-color: #1E3A8A;
    color: #FFFFFF;
}

QHeaderView::section {
    background-color: #111827;
    color: #94A3B8;
    font-weight: 600;
    font-size: 12px;
    padding: 10px 12px;
    border: none;
    border-bottom: 2px solid #1E293B;
    border-right: 1px solid #172235;
}

QHeaderView::section:hover {
    background-color: #1F2937;
    color: #F8FAFC;
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

/* ==================== IObit ASC Care Center Elements ==================== */

/* Circular Glowing SCAN Button */
QPushButton#CircularScanButton {
    background: qradialgradient(cx:0.5, cy:0.5, radius:0.8, fx:0.5, fy:0.5, stop:0 #1E293B, stop:0.75 #0F172A, stop:1 #06B6D4);
    border: 3px solid #06B6D4;
    border-radius: 70px;
    color: #FFFFFF;
    font-size: 22px;
    font-weight: 800;
    letter-spacing: 1.5px;
    min-width: 140px;
    max-width: 140px;
    min-height: 140px;
    max-height: 140px;
}

QPushButton#CircularScanButton:hover {
    background: qradialgradient(cx:0.5, cy:0.5, radius:0.8, fx:0.5, fy:0.5, stop:0 #064E3B, stop:0.75 #0F172A, stop:1 #10B981);
    border: 3px solid #10B981;
}

QPushButton#CircularScanButton:pressed {
    background: #0D9488;
    border: 3px solid #22D3EE;
}

/* Primary High-Impact FIX NOW Button */
QPushButton#FixNowButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #10B981);
    color: #FFFFFF;
    font-size: 15px;
    font-weight: 800;
    padding: 12px 28px;
    border-radius: 10px;
    border: 1px solid #34D399;
    letter-spacing: 0.5px;
}

QPushButton#FixNowButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #047857, stop:1 #059669);
    border-color: #6EE7B7;
}

QPushButton#FixNowButton:pressed {
    background: #065F46;
    border-color: #10B981;
}

QPushButton#FixNowButton:disabled {
    background: #1F2937;
    color: #6B7280;
    border: 1px solid #374151;
}

/* Care Grid Module Cards */
QFrame#CareCard {
    background-color: #111827;
    border: 1px solid #1F2937;
    border-radius: 10px;
    padding: 12px 16px;
}

QFrame#CareCard:hover {
    background-color: #151D2F;
    border: 1px solid #06B6D4;
}

/* Live Scan Pipeline Stage Cards */
QFrame#ModuleStageCard {
    background-color: #111827;
    border: 1px solid #1F2937;
    border-radius: 8px;
    padding: 12px 16px;
}

/* Health Status Banners */
QFrame#HealthBannerGood {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(16, 185, 129, 0.12), stop:1 rgba(16, 185, 129, 0.03));
    border: 1px solid rgba(16, 185, 129, 0.35);
    border-radius: 10px;
}

QFrame#HealthBannerFair {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(245, 158, 11, 0.15), stop:1 rgba(245, 158, 11, 0.03));
    border: 1px solid rgba(245, 158, 11, 0.4);
    border-radius: 10px;
}

QFrame#HealthBannerCritical {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(239, 68, 68, 0.18), stop:1 rgba(239, 68, 68, 0.04));
    border: 1px solid rgba(239, 68, 68, 0.45);
    border-radius: 10px;
}

/* Care Checkboxes */
QCheckBox {
    color: #F9FAFB;
    font-size: 13px;
    font-weight: 600;
    spacing: 10px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #4B5563;
    background-color: #1F2937;
}

QCheckBox::indicator:hover {
    border-color: #06B6D4;
}

QCheckBox::indicator:checked {
    background-color: #06B6D4;
    border-color: #06B6D4;
    image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='white'%3E%3Cpath d='M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z'/%3E%3C/svg%3E");
}
"""

