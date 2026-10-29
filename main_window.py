from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter, QPen

from config import PomodoroConfig
from timer_engine import PomodoroEngine, SessionType, TimerStatus
from settings_dialog import SettingsDialog
from icon_helper import get_lucide_icon, get_inter_font


THEME_COLORS = {
    SessionType.WORK: {
        "primary": "#3b82f6",
        "hover": "#2563eb",
        "glow": "rgba(59, 130, 246, 0.15)",
        "track": "rgba(59, 130, 246, 0.12)",
    },
    SessionType.SHORT_BREAK: {
        "primary": "#10b981",
        "hover": "#059669",
        "glow": "rgba(16, 185, 129, 0.15)",
        "track": "rgba(16, 185, 129, 0.12)",
    },
    SessionType.LONG_BREAK: {
        "primary": "#8b5cf6",
        "hover": "#7c3aed",
        "glow": "rgba(139, 92, 246, 0.15)",
        "track": "rgba(139, 92, 246, 0.12)",
    },
}


class MinimalProgressRing(QWidget):
    """Anel circular estilizado com cantos arredondados e trilho suave."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(190, 190)
        self.progress_pct = 1.0
        self.color = QColor("#3b82f6")
        self.track_color = QColor(255, 255, 255, 15)

    def set_progress(self, progress: float, color_hex: str, track_color_str: str):
        self.progress_pct = max(0.0, min(1.0, progress))
        self.color = QColor(color_hex)
        self.track_color = QColor(track_color_str)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect().adjusted(10, 10, -10, -10)

        # Trilho de fundo
        bg_pen = QPen(self.track_color, 6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(bg_pen)
        painter.drawEllipse(rect)

        # Arco ativo de progresso
        if self.progress_pct > 0.002:
            fg_pen = QPen(self.color, 6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            painter.setPen(fg_pen)
            span_angle = int(-self.progress_pct * 360 * 16)
            start_angle = 90 * 16
            painter.drawArc(rect, start_angle, span_angle)


class MainWindow(QMainWindow):
    test_blur_requested = pyqtSignal()

    def __init__(self, engine: PomodoroEngine, config: PomodoroConfig):
        super().__init__()
        self.engine = engine
        self.config = config

        self.setWindowTitle("Pomodoro")
        self.setFixedSize(360, 510)

        self.setStyleSheet("""
            QMainWindow {
                background-color: #090d16;
            }
            QWidget#CentralWidget {
                background-color: #090d16;
                font-family: 'Inter', system-ui, -apple-system, sans-serif;
            }
        """)

        screen = QApplication.primaryScreen()
        if screen:
            screen_geo = screen.availableGeometry()
            x = screen_geo.x() + (screen_geo.width() - 360) // 2
            y = screen_geo.y() + (screen_geo.height() - 510) // 2
            self.move(x, y)

        central = QWidget(self)
        central.setObjectName("CentralWidget")
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(14)

        # 1. Barra de Cabeçalho
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)

        lbl_app_title = QLabel("Pomodoro", self)
        lbl_app_title.setFont(get_inter_font(15, QFont.Weight.Bold))
        lbl_app_title.setStyleSheet("color: #f1f5f9; letter-spacing: 0.3px;")
        top_bar.addWidget(lbl_app_title)

        top_bar.addStretch()

        self.btn_min = QPushButton(self)
        self.btn_min.setIcon(get_lucide_icon("minimize-2", "#64748b", 15))
        self.btn_min.setToolTip("Minimizar para a bandeja")
        self.btn_min.setFixedSize(32, 32)
        self.btn_min.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_min.setStyleSheet(self._icon_btn_style())
        self.btn_min.clicked.connect(self.hide)
        top_bar.addWidget(self.btn_min)

        self.btn_settings = QPushButton(self)
        self.btn_settings.setIcon(get_lucide_icon("settings-2", "#64748b", 15))
        self.btn_settings.setToolTip("Configurações")
        self.btn_settings.setFixedSize(32, 32)
        self.btn_settings.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_settings.setStyleSheet(self._icon_btn_style())
        self.btn_settings.clicked.connect(self._open_settings)
        top_bar.addWidget(self.btn_settings)

        main_layout.addLayout(top_bar)

        # 2. Seletor de Sessão em Pílula
        mode_frame = QFrame(self)
        mode_frame.setStyleSheet("""
            QFrame {
                background-color: #131d2e;
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 12px;
                padding: 3px;
            }
        """)
        mode_layout = QHBoxLayout(mode_frame)
        mode_layout.setContentsMargins(3, 3, 3, 3)
        mode_layout.setSpacing(4)

        self.btn_mode_work = QPushButton("Foco", mode_frame)
        self.btn_mode_short = QPushButton("Pausa Curta", mode_frame)
        self.btn_mode_long = QPushButton("Pausa Longa", mode_frame)

        self.mode_buttons = [self.btn_mode_work, self.btn_mode_short, self.btn_mode_long]
        modes = [SessionType.WORK, SessionType.SHORT_BREAK, SessionType.LONG_BREAK]

        for btn, mode in zip(self.mode_buttons, modes):
            btn.setCheckable(True)
            btn.setFixedHeight(30)
            btn.setFont(get_inter_font(11, QFont.Weight.Medium))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(self._mode_btn_style())
            btn.clicked.connect(lambda _, m=mode: self.engine.set_session_manually(m))
            mode_layout.addWidget(btn)

        main_layout.addWidget(mode_frame)

        # 3. Card do Cronômetro
        timer_card = QFrame(self)
        timer_card.setStyleSheet("""
            QFrame {
                background-color: #111827;
                border: 1px solid rgba(255, 255, 255, 0.04);
                border-radius: 16px;
            }
        """)
        card_layout = QVBoxLayout(timer_card)
        card_layout.setContentsMargins(12, 16, 12, 16)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        ring_container = QWidget(timer_card)
        ring_container.setFixedSize(190, 190)
        self.progress_ring = MinimalProgressRing(ring_container)

        ring_inner = QVBoxLayout(ring_container)
        ring_inner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ring_inner.setSpacing(4)

        self.lbl_time = QLabel("25:00", ring_container)
        self.lbl_time.setFont(get_inter_font(42, QFont.Weight.Bold))
        self.lbl_time.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_time.setStyleSheet("color: #ffffff; background: transparent;")

        # Dots integrados no próprio anel (limpa o layout)
        self.cycle_dots_layout = QHBoxLayout()
        self.cycle_dots_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cycle_dots_layout.setSpacing(6)
        self._build_cycle_dots()

        ring_inner.addWidget(self.lbl_time)
        ring_inner.addLayout(self.cycle_dots_layout)

        card_layout.addWidget(ring_container)
        main_layout.addWidget(timer_card)

        # 4. Ação Primária
        self.btn_main_action = QPushButton(self)
        self.btn_main_action.setFixedHeight(46)
        self.btn_main_action.setFont(get_inter_font(13, QFont.Weight.DemiBold))
        self.btn_main_action.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_main_action.clicked.connect(self.engine.toggle_play_pause)
        main_layout.addWidget(self.btn_main_action)

        # 5. Ações Secundárias Integradas
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(8)

        self.btn_reset = QPushButton("  Resetar", self)
        self.btn_reset.setIcon(get_lucide_icon("refresh-cw", "#94a3b8", 14))
        self.btn_reset.setFont(get_inter_font(12, QFont.Weight.Medium))
        self.btn_reset.setFixedHeight(36)
        self.btn_reset.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_reset.setStyleSheet(self._secondary_btn_style())
        self.btn_reset.clicked.connect(self.engine.reset)
        actions_layout.addWidget(self.btn_reset)

        self.btn_skip = QPushButton("  Pular", self)
        self.btn_skip.setIcon(get_lucide_icon("skip-forward", "#94a3b8", 14))
        self.btn_skip.setFont(get_inter_font(12, QFont.Weight.Medium))
        self.btn_skip.setFixedHeight(36)
        self.btn_skip.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_skip.setStyleSheet(self._secondary_btn_style())
        self.btn_skip.clicked.connect(self.engine.skip)
        actions_layout.addWidget(self.btn_skip)

        main_layout.addLayout(actions_layout)

        # 6. Botão de Teste (Estilo sutil inferior)
        self.btn_test_blur = QPushButton("  Pré-visualizar Overlay de Pausa", self)
        self.btn_test_blur.setIcon(get_lucide_icon("eye", "#475569", 13))
        self.btn_test_blur.setFont(get_inter_font(11, QFont.Weight.Medium))
        self.btn_test_blur.setFixedHeight(28)
        self.btn_test_blur.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_test_blur.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #64748b;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                color: #cbd5e1;
                background-color: rgba(255, 255, 255, 0.03);
            }
        """)
        self.btn_test_blur.clicked.connect(self.test_blur_requested.emit)
        main_layout.addWidget(self.btn_test_blur)

        # Conexões da engine
        self.engine.tick.connect(self._on_tick)
        self.engine.state_changed.connect(self._on_state_changed)
        self.engine.status_changed.connect(self._on_status_changed)

        self._update_all_ui()

    def _build_cycle_dots(self):
        while self.cycle_dots_layout.count():
            item = self.cycle_dots_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        total = self.config.cycles_before_long_break
        curr = self.engine.cycle_count
        theme = THEME_COLORS.get(self.engine.session_type, THEME_COLORS[SessionType.WORK])

        for i in range(1, total + 1):
            dot = QFrame()
            dot.setFixedSize(7, 7)
            if i < curr:
                dot.setStyleSheet(f"background-color: {theme['primary']}; border-radius: 3px;")
            elif i == curr:
                dot.setStyleSheet(f"background-color: #f8fafc; border-radius: 3px;")
            else:
                dot.setStyleSheet("background-color: rgba(255, 255, 255, 0.12); border-radius: 3px;")
            self.cycle_dots_layout.addWidget(dot)

    def _on_tick(self, remaining: int, total: int, formatted_time: str):
        self.lbl_time.setText(formatted_time)
        pct = remaining / max(1, total)
        theme = THEME_COLORS.get(self.engine.session_type, THEME_COLORS[SessionType.WORK])
        self.progress_ring.set_progress(pct, theme["primary"], theme["track"])

    def _on_state_changed(self, session: SessionType, cycle: int):
        self._update_all_ui()

    def _on_status_changed(self, status: TimerStatus):
        theme = THEME_COLORS.get(self.engine.session_type, THEME_COLORS[SessionType.WORK])
        primary_color = theme["primary"]
        hover_color = theme["hover"]

        if status == TimerStatus.RUNNING:
            self.btn_main_action.setIcon(get_lucide_icon("pause", "#ffffff", 16))
            self.btn_main_action.setText("  Pausar")
            self.btn_main_action.setStyleSheet(f"""
                QPushButton {{
                    background-color: #334155;
                    color: #ffffff;
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    border-radius: 12px;
                }}
                QPushButton:hover {{
                    background-color: #475569;
                }}
            """)
        elif status == TimerStatus.PAUSED:
            self.btn_main_action.setIcon(get_lucide_icon("play", "#ffffff", 16))
            self.btn_main_action.setText("  Retomar")
            self.btn_main_action.setStyleSheet(f"""
                QPushButton {{
                    background-color: {primary_color};
                    color: #ffffff;
                    border: none;
                    border-radius: 12px;
                }}
                QPushButton:hover {{
                    background-color: {hover_color};
                }}
            """)
        else:  # IDLE
            self.btn_main_action.setIcon(get_lucide_icon("play", "#ffffff", 16))
            action_label = "Iniciar Foco" if self.engine.session_type == SessionType.WORK else "Iniciar Pausa"
            self.btn_main_action.setText(f"  {action_label}")
            self.btn_main_action.setStyleSheet(f"""
                QPushButton {{
                    background-color: {primary_color};
                    color: #ffffff;
                    border: none;
                    border-radius: 12px;
                }}
                QPushButton:hover {{
                    background-color: {hover_color};
                }}
            """)

    def _update_all_ui(self):
        session = self.engine.session_type
        self.btn_mode_work.setChecked(session == SessionType.WORK)
        self.btn_mode_short.setChecked(session == SessionType.SHORT_BREAK)
        self.btn_mode_long.setChecked(session == SessionType.LONG_BREAK)

        self.lbl_time.setText(self.engine.format_time(self.engine.remaining_seconds))
        self._build_cycle_dots()
        self._on_status_changed(self.engine.status)

        theme = THEME_COLORS.get(session, THEME_COLORS[SessionType.WORK])
        pct = self.engine.remaining_seconds / max(1, self.engine.current_total_seconds)
        self.progress_ring.set_progress(pct, theme["primary"], theme["track"])

    def _open_settings(self):
        dialog = SettingsDialog(self.config, self)
        if dialog.exec():
            self.engine.set_config(self.config)
            self._update_all_ui()

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        if hasattr(self, "on_closed_to_tray") and self.on_closed_to_tray:
            self.on_closed_to_tray()

    def _icon_btn_style(self) -> str:
        return """
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.05);
            }
        """

    def _mode_btn_style(self) -> str:
        return """
            QPushButton {
                background-color: transparent;
                color: #64748b;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                color: #cbd5e1;
            }
            QPushButton:checked {
                background-color: #1e293b;
                color: #f8fafc;
                font-weight: 600;
            }
        """

    def _secondary_btn_style(self) -> str:
        return """
            QPushButton {
                background-color: #111827;
                color: #94a3b8;
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #1f2937;
                color: #f1f5f9;
                border-color: rgba(255, 255, 255, 0.1);
            }
            QPushButton:pressed {
                background-color: #0f172a;
            }
        """