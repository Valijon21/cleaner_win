"""
Risk Badge UI Component.
"""

from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt
from cleanguard.core.contracts import RiskLevel
from cleanguard.localization import tr


class RiskBadge(QLabel):
    """Pill badge displaying risk level with distinct semantic colors."""

    def __init__(self, risk: RiskLevel, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedHeight(22)
        self.set_risk(risk)

    def set_risk(self, risk: RiskLevel) -> None:
        val = risk.value if isinstance(risk, RiskLevel) else str(risk)

        if val == "SAFE":
            text = tr("risk_safe")
            bg_color = "rgba(16, 185, 129, 0.15)"
            text_color = "#34D399"
            border = "1px solid rgba(16, 185, 129, 0.3)"
        elif val == "REVIEW":
            text = tr("risk_review")
            bg_color = "rgba(245, 158, 11, 0.15)"
            text_color = "#FBBF24"
            border = "1px solid rgba(245, 158, 11, 0.3)"
        else:  # BLOCKED
            text = tr("risk_blocked")
            bg_color = "rgba(239, 68, 68, 0.15)"
            text_color = "#F87171"
            border = "1px solid rgba(239, 68, 68, 0.3)"

        self.setText(f" {text} ")
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_color};
                color: {text_color};
                border: {border};
                border-radius: 4px;
                font-weight: 600;
                font-size: 11px;
                padding: 2px 6px;
            }}
        """)
