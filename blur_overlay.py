from typing import List
from PIL import Image, ImageFilter, ImageEnhance
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap, QColor, QFont, QKeyEvent, QMouseEvent, QCursor

from config import PomodoroConfig
from timer_engine import SessionType
from icon_helper import get_inter_font

def generate_blurred_pixmap(pixmap: QPixmap, blur_radius: int = 12, dim_factor: float = 0.45) -> QPixmap:
    """Aplica desfoque gaussiano acelerado e escurecimento cinematográfico."""
    try:
        qimg = pixmap.toImage().convertToFormat(QImage.Format.Format_RGBA8888)
        w, h = qimg.width(), qimg.height()
        ptr = qimg.bits()
        ptr.setsize(h * w * 4)
        img = Image.frombuffer("RGBA", (w, h), bytes(ptr), "raw", "RGBA", 0, 1)

        scale = 3
        small_w = max(1, w // scale)
        small_h = max(1, h // scale)
        small_img = img.resize((small_w, small_h), Image.Resampling.BILINEAR)
        blurred_small = small_img.filter(ImageFilter.GaussianBlur(radius=blur_radius))

        enhancer = ImageEnhance.Brightness(blurred_small)
        dimmed_small = enhancer.enhance(dim_factor)

        result_img = dimmed_small.resize((w, h), Image.Resampling.BICUBIC)
        out_bytes = result_img.tobytes("raw", "RGBA")
        qimg_out = QImage(out_bytes, w, h, QImage.Format.Format_RGBA8888)
        return QPixmap.fromImage(qimg_out)
    except Exception as e:
        print(f"Erro ao gerar blur: {e}")
        return pixmap


class SingleScreenOverlay(QWidget):
    """Tela de pausa minimalista: apenas o desktop em blur e o cronômetro central."""
    dismiss_requested = pyqtSignal()

    def __init__(self, screen, blurred_pixmap: QPixmap, is_main_screen: bool, config: PomodoroConfig):
        super().__init__(None)
        self.screen_ref = screen
        self.config = config
        self.is_main_screen = is_main_screen
        self.blurred_pixmap = blurred_pixmap
        
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_QuitOnClose, False)
        
        geo = screen.geometry()
        self.setGeometry(geo)
        
        # Fundo desfocado
        self.bg_label = QLabel(self)
        self.bg_label.setGeometry(0, 0, geo.width(), geo.height())
        self.bg_label.setPixmap(self.blurred_pixmap.scaled(
            geo.width(), geo.height(),
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        ))
        
        if self.is_main_screen:
            self._build_minimal_ui()

    def _build_minimal_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(6)

        # Rótulo sutil superior
        self.lbl_subtitle = QLabel("PAUSA", self)
        self.lbl_subtitle.setFont(get_inter_font(13, QFont.Weight.DemiBold))
        self.lbl_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_subtitle.setStyleSheet("""
            color: rgba(255, 255, 255, 0.45);
            letter-spacing: 6px;
        """)
        root_layout.addWidget(self.lbl_subtitle)

        # CRONÔMETRO GIGANTE (O foco exclusivo do modo blur)
        self.timer_label = QLabel("05:00", self)
        self.timer_label.setFont(get_inter_font(120, QFont.Weight.Bold))
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_label.setStyleSheet("""
            color: #ffffff;
            font-family: 'Inter', system-ui, sans-serif;
        """)
        root_layout.addWidget(self.timer_label)

        # Dica quase invisível no rodapé
        lbl_hint = QLabel("pressione esc para fechar", self)
        lbl_hint.setFont(get_inter_font(11, QFont.Weight.Normal))
        lbl_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_hint.setStyleSheet("""
            color: rgba(255, 255, 255, 0.25);
            letter-spacing: 2px;
            margin-top: 10px;
        """)
        root_layout.addWidget(lbl_hint)

    def update_timer(self, remaining: int, total: int, formatted_time: str):
        if self.is_main_screen:
            self.timer_label.setText(formatted_time)

    def update_session_info(self, session_type: SessionType):
        if self.is_main_screen:
            if session_type == SessionType.LONG_BREAK:
                self.lbl_subtitle.setText("PAUSA LONGA")
                self.lbl_subtitle.setStyleSheet("color: rgba(167, 139, 250, 0.6); letter-spacing: 6px;")
            else:
                self.lbl_subtitle.setText("PAUSA")
                self.lbl_subtitle.setStyleSheet("color: rgba(52, 211, 153, 0.6); letter-spacing: 6px;")

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self.dismiss_requested.emit()
            event.accept()
            return
        super().keyPressEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        # Permite dispensar com um clique na tela se desejar
        super().mousePressEvent(event)


class BlurOverlayManager(QWidget):
    closed = pyqtSignal()
    skip_requested = pyqtSignal()
    extend_requested = pyqtSignal(int)
    toggle_pause_requested = pyqtSignal()

    def __init__(self, config: PomodoroConfig):
        super().__init__()
        self.config = config
        self.overlay_windows: List[SingleScreenOverlay] = []
        self.is_active = False
        self.anim_group = []

    def show_break_overlay(self, session_type: SessionType, cycle_count: int, remaining: int, total: int):
        self.close_overlay()
        self.is_active = True

        app = QApplication.instance()
        screens = app.screens()
        cursor_pos = QCursor.pos()
        active_screen = app.screenAt(cursor_pos) or app.primaryScreen()

        for screen in screens:
            pixmap = screen.grabWindow(0)
            blurred = generate_blurred_pixmap(
                pixmap,
                blur_radius=self.config.blur_radius,
                dim_factor=self.config.dim_factor
            )

            is_main = (screen == active_screen)
            overlay = SingleScreenOverlay(screen, blurred, is_main, self.config)
            overlay.dismiss_requested.connect(self._on_dismiss)

            overlay.update_session_info(session_type)
            overlay.update_timer(remaining, total, self._format_time(remaining))

            overlay.setWindowOpacity(0.0)
            overlay.showFullScreen()
            overlay.raise_()
            overlay.activateWindow()

            anim = QPropertyAnimation(overlay, b"windowOpacity")
            anim.setDuration(260)
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            anim.start()
            self.anim_group.append(anim)

            self.overlay_windows.append(overlay)

    def update_timer(self, remaining: int, total: int, formatted_time: str):
        if self.is_active:
            for w in self.overlay_windows:
                w.update_timer(remaining, total, formatted_time)

    def set_pause_button_state(self, is_paused: bool):
        pass

    def close_overlay(self):
        if not self.is_active and not self.overlay_windows:
            return
        self.is_active = False
        for w in self.overlay_windows:
            w.close()
            w.deleteLater()
        self.overlay_windows.clear()
        self.anim_group.clear()
        self.closed.emit()

    def _on_dismiss(self):
        self.close_overlay()
        self.skip_requested.emit()

    def _format_time(self, seconds: int) -> str:
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins:02d}:{secs:02d}"
