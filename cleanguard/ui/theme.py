"""
CleanGuard Design System and Multi-Theme Styling.
Supports 4 Professional Themes:
  1. dark      - CleanGuard Dark Pro (Obsidian Slate & Emerald Neon)
  2. midnight  - Cyberpunk Midnight (Deep Obsidian Navy & Electric Cyan)
  3. stealth   - Stealth OLED (Pure AMOLED & Vibrant Violet)
  4. light     - Clean Light Enterprise (Soft Slate, Pure White Cards & Royal Blue)
"""

from typing import Dict

THEMES = {
    "dark": "CleanGuard Dark Pro",
    "midnight": "Cyberpunk Midnight",
    "stealth": "Stealth OLED",
    "light": "Clean Light Enterprise",
}

THEME_PALETTES: Dict[str, Dict[str, str]] = {
    "dark": {
        "bg_main": "#0B0F19",
        "bg_sidebar": "#111827",
        "sidebar_border": "#1F2937",
        "bg_card": "#1F2937",
        "bg_card_hover": "#283548",
        "border_color": "#374151",
        "border_focus": "#10B981",
        "text_primary": "#F9FAFB",
        "text_secondary": "#9CA3AF",
        "text_muted": "#6B7280",
        "accent_primary": "#10B981",
        "accent_primary_hover": "#059669",
        "accent_primary_pressed": "#047857",
        "nav_btn_color": "#9CA3AF",
        "nav_btn_hover_bg": "#1F2937",
        "nav_btn_hover_text": "#F9FAFB",
        "nav_checked_bg": "#064E3B",
        "nav_checked_text": "#34D399",
        "nav_checked_border": "#10B981",
        "table_bg": "#0F172A",
        "table_alt_bg": "#131E32",
        "table_border": "#1E293B",
        "table_item_border": "#172235",
        "table_item_hover": "#1E293B",
        "table_selected_bg": "#1E3A8A",
        "table_selected_text": "#FFFFFF",
        "header_bg": "#111827",
        "header_hover": "#1F2937",
        "header_text": "#94A3B8",
        "header_text_hover": "#F8FAFC",
        "progress_bg": "#111827",
        "progress_border": "#374151",
        "progress_chunk": "#10B981",
        "scrollbar_bg": "#111827",
        "scrollbar_handle": "#374151",
        "scrollbar_handle_hover": "#4B5563",
        "scan_btn_grad": "stop:0 #1E293B, stop:0.75 #0F172A, stop:1 #06B6D4",
        "scan_btn_border": "#06B6D4",
        "scan_btn_hover_grad": "stop:0 #064E3B, stop:0.75 #0F172A, stop:1 #10B981",
        "scan_btn_hover_border": "#10B981",
        "scan_btn_pressed_bg": "#0D9488",
        "scan_btn_pressed_border": "#22D3EE",
        "fix_btn_grad": "stop:0 #059669, stop:0.55 #10B981, stop:1 #06B6D4",
        "fix_btn_hover_grad": "stop:0 #047857, stop:0.55 #059669, stop:1 #0891B2",
        "fix_btn_pressed_bg": "#064E3B",
        "fix_btn_border": "#34D399",
        "care_card_bg": "#111827",
        "care_card_border": "#1E293B",
        "care_card_hover_bg": "#162238",
        "care_card_hover_border": "#10B981",
        "chk_border": "#4B5563",
        "chk_bg": "#1F2937",
        "chk_checked_bg": "#10B981",
        "input_bg": "#1F2937",
        "input_focus_bg": "#1A2332",
        "input_border": "#374151",
        "combo_popup_bg": "#111827",
        "dialog_bg": "#111827",
    },
    "midnight": {
        "bg_main": "#060B18",
        "bg_sidebar": "#0B132B",
        "sidebar_border": "#1E335E",
        "bg_card": "#131E3D",
        "bg_card_hover": "#1C2B54",
        "border_color": "#1E335E",
        "border_focus": "#00D2FF",
        "text_primary": "#F0F6FC",
        "text_secondary": "#93B5D6",
        "text_muted": "#5B7B9E",
        "accent_primary": "#00D2FF",
        "accent_primary_hover": "#00B4D8",
        "accent_primary_pressed": "#0096C7",
        "nav_btn_color": "#93B5D6",
        "nav_btn_hover_bg": "#131E3D",
        "nav_btn_hover_text": "#F0F6FC",
        "nav_checked_bg": "#0F2A4A",
        "nav_checked_text": "#38BDF8",
        "nav_checked_border": "#00D2FF",
        "table_bg": "#070F26",
        "table_alt_bg": "#0D1838",
        "table_border": "#1A2B50",
        "table_item_border": "#132140",
        "table_item_hover": "#16284D",
        "table_selected_bg": "#0284C7",
        "table_selected_text": "#FFFFFF",
        "header_bg": "#0B132B",
        "header_hover": "#131E3D",
        "header_text": "#93B5D6",
        "header_text_hover": "#F0F6FC",
        "progress_bg": "#0B132B",
        "progress_border": "#1E335E",
        "progress_chunk": "#00D2FF",
        "scrollbar_bg": "#0B132B",
        "scrollbar_handle": "#1E335E",
        "scrollbar_handle_hover": "#2B477D",
        "scan_btn_grad": "stop:0 #131E3D, stop:0.75 #0B132B, stop:1 #00D2FF",
        "scan_btn_border": "#00D2FF",
        "scan_btn_hover_grad": "stop:0 #0F2A4A, stop:0.75 #071324, stop:1 #38BDF8",
        "scan_btn_hover_border": "#38BDF8",
        "scan_btn_pressed_bg": "#0284C7",
        "scan_btn_pressed_border": "#38BDF8",
        "fix_btn_grad": "stop:0 #0284C7, stop:0.55 #00D2FF, stop:1 #38BDF8",
        "fix_btn_hover_grad": "stop:0 #0369A1, stop:0.55 #0284C7, stop:1 #00D2FF",
        "fix_btn_pressed_bg": "#075985",
        "fix_btn_border": "#38BDF8",
        "care_card_bg": "#0D1733",
        "care_card_border": "#1B2C52",
        "care_card_hover_bg": "#15244D",
        "care_card_hover_border": "#00D2FF",
        "chk_border": "#2B477D",
        "chk_bg": "#131E3D",
        "chk_checked_bg": "#00D2FF",
        "input_bg": "#131E3D",
        "input_focus_bg": "#18274E",
        "input_border": "#1E335E",
        "combo_popup_bg": "#0B132B",
        "dialog_bg": "#0B132B",
    },
    "stealth": {
        "bg_main": "#000000",
        "bg_sidebar": "#09090B",
        "sidebar_border": "#18181B",
        "bg_card": "#141417",
        "bg_card_hover": "#202025",
        "border_color": "#27272A",
        "border_focus": "#8B5CF6",
        "text_primary": "#FAFAFA",
        "text_secondary": "#A1A1AA",
        "text_muted": "#71717A",
        "accent_primary": "#8B5CF6",
        "accent_primary_hover": "#7C3AED",
        "accent_primary_pressed": "#6D28D9",
        "nav_btn_color": "#A1A1AA",
        "nav_btn_hover_bg": "#18181B",
        "nav_btn_hover_text": "#FAFAFA",
        "nav_checked_bg": "#2E1065",
        "nav_checked_text": "#C084FC",
        "nav_checked_border": "#8B5CF6",
        "table_bg": "#09090B",
        "table_alt_bg": "#101014",
        "table_border": "#27272A",
        "table_item_border": "#18181B",
        "table_item_hover": "#1C1C21",
        "table_selected_bg": "#5B21B6",
        "table_selected_text": "#FFFFFF",
        "header_bg": "#09090B",
        "header_hover": "#18181B",
        "header_text": "#A1A1AA",
        "header_text_hover": "#FAFAFA",
        "progress_bg": "#09090B",
        "progress_border": "#27272A",
        "progress_chunk": "#8B5CF6",
        "scrollbar_bg": "#09090B",
        "scrollbar_handle": "#27272A",
        "scrollbar_handle_hover": "#3F3F46",
        "scan_btn_grad": "stop:0 #18181B, stop:0.75 #09090B, stop:1 #8B5CF6",
        "scan_btn_border": "#8B5CF6",
        "scan_btn_hover_grad": "stop:0 #2E1065, stop:0.75 #09090B, stop:1 #A855F7",
        "scan_btn_hover_border": "#A855F7",
        "scan_btn_pressed_bg": "#6D28D9",
        "scan_btn_pressed_border": "#C084FC",
        "fix_btn_grad": "stop:0 #7C3AED, stop:0.55 #8B5CF6, stop:1 #C084FC",
        "fix_btn_hover_grad": "stop:0 #6D28D9, stop:0.55 #7C3AED, stop:1 #A855F7",
        "fix_btn_pressed_bg": "#4C1D95",
        "fix_btn_border": "#C084FC",
        "care_card_bg": "#0D0D11",
        "care_card_border": "#1F1F24",
        "care_card_hover_bg": "#181820",
        "care_card_hover_border": "#8B5CF6",
        "chk_border": "#3F3F46",
        "chk_bg": "#141417",
        "chk_checked_bg": "#8B5CF6",
        "input_bg": "#141417",
        "input_focus_bg": "#1C1C22",
        "input_border": "#27272A",
        "combo_popup_bg": "#09090B",
        "dialog_bg": "#09090B",
    },
    "light": {
        "bg_main": "#F1F5F9",
        "bg_sidebar": "#FFFFFF",
        "sidebar_border": "#E2E8F0",
        "bg_card": "#FFFFFF",
        "bg_card_hover": "#F8FAFC",
        "border_color": "#CBD5E1",
        "border_focus": "#2563EB",
        "text_primary": "#0F172A",
        "text_secondary": "#475569",
        "text_muted": "#94A3B8",
        "accent_primary": "#2563EB",
        "accent_primary_hover": "#1D4ED8",
        "accent_primary_pressed": "#1E40AF",
        "nav_btn_color": "#475569",
        "nav_btn_hover_bg": "#F1F5F9",
        "nav_btn_hover_text": "#0F172A",
        "nav_checked_bg": "#EFF6FF",
        "nav_checked_text": "#1D4ED8",
        "nav_checked_border": "#2563EB",
        "table_bg": "#FFFFFF",
        "table_alt_bg": "#F8FAFC",
        "table_border": "#E2E8F0",
        "table_item_border": "#F1F5F9",
        "table_item_hover": "#F1F5F9",
        "table_selected_bg": "#DBEAFE",
        "table_selected_text": "#1E40AF",
        "header_bg": "#F8FAFC",
        "header_hover": "#EDF2F7",
        "header_text": "#475569",
        "header_text_hover": "#0F172A",
        "progress_bg": "#E2E8F0",
        "progress_border": "#CBD5E1",
        "progress_chunk": "#2563EB",
        "scrollbar_bg": "#F8FAFC",
        "scrollbar_handle": "#CBD5E1",
        "scrollbar_handle_hover": "#94A3B8",
        "scan_btn_grad": "stop:0 #FFFFFF, stop:0.75 #F1F5F9, stop:1 #3B82F6",
        "scan_btn_border": "#3B82F6",
        "scan_btn_hover_grad": "stop:0 #EFF6FF, stop:0.75 #E0E7FF, stop:1 #2563EB",
        "scan_btn_hover_border": "#2563EB",
        "scan_btn_pressed_bg": "#1D4ED8",
        "scan_btn_pressed_border": "#60A5FA",
        "fix_btn_grad": "stop:0 #2563EB, stop:0.55 #3B82F6, stop:1 #60A5FA",
        "fix_btn_hover_grad": "stop:0 #1D4ED8, stop:0.55 #2563EB, stop:1 #3B82F6",
        "fix_btn_pressed_bg": "#1E40AF",
        "fix_btn_border": "#93C5FD",
        "care_card_bg": "#FFFFFF",
        "care_card_border": "#E2E8F0",
        "care_card_hover_bg": "#F8FAFC",
        "care_card_hover_border": "#2563EB",
        "chk_border": "#94A3B8",
        "chk_bg": "#FFFFFF",
        "chk_checked_bg": "#2563EB",
        "input_bg": "#FFFFFF",
        "input_focus_bg": "#F8FAFC",
        "input_border": "#CBD5E1",
        "combo_popup_bg": "#FFFFFF",
        "dialog_bg": "#FFFFFF",
    },
}


def generate_stylesheet(p: Dict[str, str]) -> str:
    """Dynamically render the complete application QSS stylesheet using palette tokens."""
    return f"""
QMainWindow {{
    background-color: {p["bg_main"]};
}}

QWidget {{
    color: {p["text_primary"]};
    font-family: 'Segoe UI', 'Roboto', 'Helvetica Neue', sans-serif;
    font-size: 13px;
}}

/* Sidebar Navigation */
QFrame#Sidebar {{
    background-color: {p["bg_sidebar"]};
    border-right: 1px solid {p["sidebar_border"]};
}}

QScrollArea#NavScrollArea {{
    background-color: transparent;
    border: none;
}}

QScrollArea#NavScrollArea > QWidget > QWidget {{
    background-color: transparent;
}}

QScrollArea#NavScrollArea QScrollBar:vertical {{
    background: transparent;
    width: 4px;
    margin: 0px;
}}

QScrollArea#NavScrollArea QScrollBar::handle:vertical {{
    background: {p["scrollbar_handle"]};
    min-height: 25px;
    border-radius: 2px;
}}

QScrollArea#NavScrollArea QScrollBar::handle:vertical:hover {{
    background: {p["accent_primary"]};
}}

QScrollArea#NavScrollArea QScrollBar::add-line:vertical,
QScrollArea#NavScrollArea QScrollBar::sub-line:vertical {{
    height: 0px;
    border: none;
    background: transparent;
}}

QPushButton#NavButton {{
    background-color: transparent;
    color: {p["nav_btn_color"]};
    text-align: left;
    padding: 8px 12px;
    font-size: 13px;
    font-weight: 500;
    border: none;
    border-radius: 6px;
    margin: 1px 4px;
}}

QPushButton#NavButton:hover {{
    background-color: {p["nav_btn_hover_bg"]};
    color: {p["nav_btn_hover_text"]};
}}

QPushButton#NavButton:checked {{
    background-color: {p["nav_checked_bg"]};
    color: {p["nav_checked_text"]};
    border-left: 3px solid {p["nav_checked_border"]};
    font-weight: 600;
}}

/* Primary Action Buttons */
QPushButton#PrimaryButton {{
    background-color: {p["accent_primary"]};
    color: #FFFFFF;
    font-size: 14px;
    font-weight: 600;
    padding: 10px 24px;
    border: none;
    border-radius: 8px;
}}

QPushButton#PrimaryButton:hover {{
    background-color: {p["accent_primary_hover"]};
}}

QPushButton#PrimaryButton:pressed {{
    background-color: {p["accent_primary_pressed"]};
}}

QPushButton#SecondaryButton {{
    background-color: {p["bg_card"]};
    color: {p["text_primary"]};
    font-size: 13px;
    font-weight: 500;
    padding: 8px 18px;
    border: 1px solid {p["border_color"]};
    border-radius: 6px;
}}

QPushButton#SecondaryButton:hover {{
    background-color: {p["bg_card_hover"]};
    border-color: {p["border_focus"]};
}}

QPushButton#DangerButton {{
    background-color: #DC2626;
    color: #FFFFFF;
    font-size: 13px;
    font-weight: 600;
    padding: 8px 18px;
    border: none;
    border-radius: 6px;
}}

QPushButton#DangerButton:hover {{
    background-color: #B91C1C;
}}

/* Cards */
QFrame#SurfaceCard {{
    background-color: {p["bg_card"]};
    border: 1px solid {p["border_color"]};
    border-radius: 10px;
    padding: 16px;
}}

/* Tables */
QTableView, QTableWidget, QTreeWidget, QTreeView, QListWidget {{
    background-color: {p["table_bg"]};
    alternate-background-color: {p["table_alt_bg"]};
    color: {p["text_primary"]};
    border: 1px solid {p["table_border"]};
    border-radius: 8px;
    gridline-color: transparent;
    selection-background-color: {p["table_selected_bg"]};
    selection-color: {p["table_selected_text"]};
    outline: none;
}}

QTableView::item, QTableWidget::item, QTreeWidget::item, QTreeView::item, QListWidget::item {{
    padding: 6px 10px;
    border-bottom: 1px solid {p["table_item_border"]};
}}

QTableView::item:hover, QTableWidget::item:hover, QTreeWidget::item:hover, QTreeView::item:hover, QListWidget::item:hover {{
    background-color: {p["table_item_hover"]};
}}

QTableView::item:selected, QTableWidget::item:selected, QTreeWidget::item:selected, QTreeView::item:selected, QListWidget::item:selected {{
    background-color: {p["table_selected_bg"]};
    color: {p["table_selected_text"]};
}}

QHeaderView::section {{
    background-color: {p["header_bg"]};
    color: {p["header_text"]};
    font-weight: 600;
    font-size: 12px;
    padding: 10px 12px;
    border: none;
    border-bottom: 2px solid {p["table_border"]};
    border-right: 1px solid {p["table_item_border"]};
}}

QHeaderView::section:hover {{
    background-color: {p["header_hover"]};
    color: {p["header_text_hover"]};
}}

/* Progress Bar */
QProgressBar {{
    background-color: {p["progress_bg"]};
    border: 1px solid {p["progress_border"]};
    border-radius: 6px;
    text-align: center;
    color: {p["text_primary"]};
    height: 14px;
}}

QProgressBar::chunk {{
    background-color: {p["progress_chunk"]};
    border-radius: 5px;
}}

/* Scrollbars */
QScrollBar:vertical {{
    background: {p["scrollbar_bg"]};
    width: 10px;
    margin: 0px;
}}

QScrollBar::handle:vertical {{
    background: {p["scrollbar_handle"]};
    min-height: 20px;
    border-radius: 5px;
}}

QScrollBar::handle:vertical:hover {{
    background: {p["scrollbar_handle_hover"]};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

/* ==================== Care Center Elements ==================== */

QPushButton#CircularScanButton {{
    background: qradialgradient(cx:0.5, cy:0.5, radius:0.8, fx:0.5, fy:0.5, {p["scan_btn_grad"]});
    border: 3px solid {p["scan_btn_border"]};
    border-radius: 70px;
    color: #FFFFFF;
    font-size: 22px;
    font-weight: 800;
    letter-spacing: 1.5px;
    min-width: 140px;
    max-width: 140px;
    min-height: 140px;
    max-height: 140px;
}}

QPushButton#CircularScanButton:hover {{
    background: qradialgradient(cx:0.5, cy:0.5, radius:0.8, fx:0.5, fy:0.5, {p["scan_btn_hover_grad"]});
    border: 3px solid {p["scan_btn_hover_border"]};
}}

QPushButton#CircularScanButton:pressed {{
    background: {p["scan_btn_pressed_bg"]};
    border: 3px solid {p["scan_btn_pressed_border"]};
}}

QPushButton#FixNowButton {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, {p["fix_btn_grad"]});
    color: #FFFFFF;
    font-size: 15px;
    font-weight: 800;
    padding: 12px 30px;
    border-radius: 10px;
    border: 1px solid {p["fix_btn_border"]};
    letter-spacing: 0.6px;
}}

QPushButton#FixNowButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, {p["fix_btn_hover_grad"]});
    border-color: #FFFFFF;
}}

QPushButton#FixNowButton:pressed {{
    background: {p["fix_btn_pressed_bg"]};
    border-color: {p["accent_primary"]};
}}

QPushButton#FixNowButton:disabled {{
    background: {p["bg_card"]};
    color: {p["text_muted"]};
    border: 1px solid {p["border_color"]};
}}

QFrame#CareCard {{
    background-color: {p["care_card_bg"]};
    border: 1px solid {p["care_card_border"]};
    border-radius: 10px;
    padding: 12px 16px;
}}

QFrame#CareCard:hover {{
    background-color: {p["care_card_hover_bg"]};
    border: 1px solid {p["care_card_hover_border"]};
}}

QFrame#ModuleStageCard {{
    background-color: {p["care_card_bg"]};
    border: 1px solid {p["care_card_border"]};
    border-radius: 10px;
    padding: 10px 16px;
}}

QFrame#ModuleStageCard:hover {{
    background-color: {p["care_card_hover_bg"]};
    border: 1px solid {p["accent_primary"]};
}}

/* Health Status Banners */
QFrame#HealthBannerGood {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(16, 185, 129, 0.15), stop:1 rgba(16, 185, 129, 0.04));
    border: 1px solid rgba(16, 185, 129, 0.4);
    border-radius: 10px;
}}

QFrame#HealthBannerFair {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(245, 158, 11, 0.18), stop:1 rgba(245, 158, 11, 0.04));
    border: 1px solid rgba(245, 158, 11, 0.45);
    border-radius: 10px;
}}

QFrame#HealthBannerCritical {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(239, 68, 68, 0.20), stop:1 rgba(239, 68, 68, 0.05));
    border: 1px solid rgba(239, 68, 68, 0.5);
    border-radius: 10px;
}}

/* Checkboxes */
QCheckBox {{
    color: {p["text_primary"]};
    font-size: 13px;
    font-weight: 500;
    spacing: 10px;
}}

QCheckBox::indicator,
QTableView::indicator,
QTableWidget::indicator,
QTreeWidget::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid {p["chk_border"]};
    background-color: {p["chk_bg"]};
}}

QCheckBox::indicator:hover,
QTableView::indicator:hover,
QTableWidget::indicator:hover,
QTreeWidget::indicator:hover {{
    border-color: {p["accent_primary"]};
}}

QCheckBox::indicator:checked,
QTableView::indicator:checked,
QTableWidget::indicator:checked,
QTreeWidget::indicator:checked {{
    background-color: {p["chk_checked_bg"]};
    border-color: {p["chk_checked_bg"]};
    image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='white'%3E%3Cpath d='M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z'/%3E%3C/svg%3E");
}}

/* Text Inputs */
QLineEdit {{
    background-color: {p["input_bg"]};
    border: 1px solid {p["input_border"]};
    border-radius: 6px;
    padding: 7px 12px;
    color: {p["text_primary"]};
    font-size: 13px;
    selection-background-color: {p["table_selected_bg"]};
    selection-color: #FFFFFF;
}}

QLineEdit:hover {{
    border-color: {p["border_color"]};
}}

QLineEdit:focus {{
    border: 1px solid {p["border_focus"]};
    background-color: {p["input_focus_bg"]};
}}

QLineEdit:disabled {{
    background-color: {p["bg_sidebar"]};
    color: {p["text_muted"]};
    border-color: {p["border_color"]};
}}

/* Dropdowns */
QComboBox {{
    background-color: {p["input_bg"]};
    border: 1px solid {p["input_border"]};
    border-radius: 6px;
    padding: 6px 12px;
    color: {p["text_primary"]};
    font-size: 13px;
    min-height: 22px;
}}

QComboBox:hover {{
    border-color: {p["border_focus"]};
}}

QComboBox:focus {{
    border: 1px solid {p["border_focus"]};
}}

QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border-left: none;
}}

QComboBox::down-arrow {{
    image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6' viewBox='0 0 10 6'%3E%3Cpath fill='%239CA3AF' d='M0 0l5 6 5-6z'/%3E%3C/svg%3E");
    width: 10px;
    height: 6px;
}}

QComboBox QAbstractItemView {{
    background-color: {p["combo_popup_bg"]};
    border: 1px solid {p["border_color"]};
    border-radius: 6px;
    color: {p["text_primary"]};
    selection-background-color: {p["accent_primary"]};
    selection-color: #FFFFFF;
    outline: none;
    padding: 4px;
}}

/* SpinBox */
QSpinBox {{
    background-color: {p["input_bg"]};
    border: 1px solid {p["input_border"]};
    border-radius: 6px;
    padding: 6px 10px;
    color: {p["text_primary"]};
    font-size: 13px;
}}

QSpinBox:hover {{
    border-color: {p["border_focus"]};
}}

QSpinBox:focus {{
    border: 1px solid {p["border_focus"]};
}}

QSpinBox::up-button, QSpinBox::down-button {{
    background-color: {p["bg_sidebar"]};
    border: none;
    width: 18px;
}}

QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
    background-color: {p["border_color"]};
}}

/* Radio Buttons */
QRadioButton {{
    color: {p["text_primary"]};
    font-size: 13px;
    spacing: 10px;
}}

QRadioButton::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 9px;
    border: 1px solid {p["chk_border"]};
    background-color: {p["chk_bg"]};
}}

QRadioButton::indicator:hover {{
    border-color: {p["accent_primary"]};
}}

QRadioButton::indicator:checked {{
    background-color: {p["accent_primary"]};
    border: 3px solid {p["chk_bg"]};
}}

/* Dialogs & Messages */
QDialog, QMessageBox {{
    background-color: {p["dialog_bg"]};
    color: {p["text_primary"]};
}}

QMessageBox QLabel {{
    color: {p["text_primary"]};
    font-size: 13px;
}}

QMessageBox QPushButton {{
    background-color: {p["bg_card"]};
    color: {p["text_primary"]};
    border: 1px solid {p["border_color"]};
    border-radius: 6px;
    padding: 6px 18px;
    font-size: 13px;
    font-weight: 500;
    min-width: 70px;
}}

QMessageBox QPushButton:hover {{
    background-color: {p["bg_card_hover"]};
    border-color: {p["border_focus"]};
}}

/* Tooltips */
QToolTip {{
    background-color: {p["bg_card"]};
    color: {p["text_primary"]};
    border: 1px solid {p["border_color"]};
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}}
"""


def get_theme_stylesheet(theme_id: str = "dark") -> str:
    """Retrieve the generated QSS stylesheet for the given theme ID."""
    palette = THEME_PALETTES.get(theme_id, THEME_PALETTES["dark"])
    return generate_stylesheet(palette)


def get_available_themes() -> Dict[str, str]:
    """Return dictionary of supported theme IDs and user-facing names."""
    return THEMES.copy()


# Backward compatibility default stylesheet
DARK_STYLESHEET = get_theme_stylesheet("dark")
