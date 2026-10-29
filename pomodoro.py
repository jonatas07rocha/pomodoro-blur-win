"""
========================================================================================
POMODORO BLUR - EXTENSÃO DE SISTEMA (BACKGROUND UTILITY)
========================================================================================
Conceito:
- Utilitário de sistema em segundo plano (sem janelas na barra de tarefas ou Alt+Tab).
- Técnica Pomodoro fiel: 4 ciclos de foco com pausas curtas e uma pausa longa final.
- Suporte multi-monitor diferenciado:
    * Monitor Principal: Contagem regressiva limpa e indicador de ciclo.
    * Monitor Secundário: Citações clássicas de sabedoria (Marco Aurélio, Sêneca, etc.) sem repetição.
- Tipografia 100% branca na tela de pausa.
- Estilo minimalista puro, sem emojis.
========================================================================================
"""

import sys
import os
import time
import json
import random
import traceback
import threading
from enum import Enum
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional

from PIL import Image, ImageFilter, ImageEnhance

from PyQt6.QtWidgets import (
    QApplication, QWidget, QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QSpinBox, QSystemTrayIcon, QMenu
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal, QRectF
from PyQt6.QtGui import (
    QImage, QPixmap, QPainter, QPen, QBrush, QColor, QFont,
    QFontDatabase, QKeyEvent, QIcon
)


# ======================================================================================
# 1. CONFIGURAÇÕES & PERSISTÊNCIA
# ======================================================================================

APP_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(APP_DIR, "config.json")
QUOTES_FILE = os.path.join(APP_DIR, "assets", "quotes.json")
STARTUP_LINK = os.path.join(
    os.environ.get("APPDATA", ""),
    r"Microsoft\Windows\Start Menu\Programs\Startup\Pomodoro.lnk"
)

@dataclass
class PomodoroConfig:
    work_duration_min: int = 25
    short_break_min: int = 5
    long_break_min: int = 15
    cycles_before_long_break: int = 4
    
    blur_radius: int = 16
    dim_factor: float = 0.35
    
    enable_sound: bool = True
    enable_tray_notifications: bool = True
    auto_start_break: bool = True
    auto_start_work: bool = True
    allow_esc_skip: bool = True

    def save(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(asdict(self), f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar configurações: {e}")

    @classmethod
    def load(cls) -> "PomodoroConfig":
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})
            except Exception:
                pass
        config = cls()
        config.save()
        return config


def is_autostart_enabled() -> bool:
    return os.path.exists(STARTUP_LINK)


def set_autostart(enable: bool):
    try:
        if enable:
            pythonw = sys.executable.replace("python.exe", "pythonw.exe")
            script = os.path.join(APP_DIR, "main.py")
            cmd = f'$sh = New-Object -ComObject WScript.Shell; $s = $sh.CreateShortcut("{STARTUP_LINK}"); $s.TargetPath = "{pythonw}"; $s.Arguments = "\"{script}\""; $s.WorkingDirectory = "{APP_DIR}"; $s.Save()'
            import subprocess
            subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True)
        else:
            if os.path.exists(STARTUP_LINK):
                os.remove(STARTUP_LINK)
    except Exception as e:
        print(f"Erro ao alternar inicialização automática: {e}")


# ======================================================================================
# 2. GERENCIADOR DE PENSAMENTOS & CITAÇÕES CLÁSSICAS
# ======================================================================================

class QuoteManager:
    """Gerencia um banco amplo de pensamentos clássicos com sorteio sem repetição frequente."""
    def __init__(self):
        self.quotes: List[Dict[str, str]] = []
        self.available_indices: List[int] = []
        self._load_quotes()

    def _load_quotes(self):
        if os.path.exists(QUOTES_FILE):
            try:
                with open(QUOTES_FILE, "r", encoding="utf-8") as f:
                    self.quotes = json.load(f)
            except Exception:
                self.quotes = []

        if not self.quotes:
            self.quotes = [
                {"quote": "Você tem poder sobre a sua mente, não sobre os acontecimentos externos. Perceba isso e encontrará a sua força.", "author": "Marco Aurélio"},
                {"quote": "Não é porque as coisas são difíceis que não ousamos; é porque não ousamos que elas são difíceis.", "author": "Sêneca"},
                {"quote": "A tranquilidade nada mais é do que a boa ordenação da própria mente.", "author": "Marco Aurélio"},
                {"quote": "Aquele que conquista a si mesmo é o guerreiro mais poderoso.", "author": "Confúcio"},
                {"quote": "A simplicidade é o último grau de sofisticação.", "author": "Leonardo da Vinci"},
                {"quote": "Somos o que fazemos repetidamente. A excelência, portanto, não é um ato, mas um hábito.", "author": "Aristóteles"}
            ]

        self._reset_pool()

    def _reset_pool(self):
        self.available_indices = list(range(len(self.quotes)))
        random.shuffle(self.available_indices)

    def get_next_quote(self) -> Dict[str, str]:
        if not self.available_indices:
            self._reset_pool()
        idx = self.available_indices.pop()
        return self.quotes[idx]


# ======================================================================================
# 3. MOTOR DE SONS NATIVO (WINDOWS)
# ======================================================================================

class SoundEngine:
    @staticmethod
    def _play_break():
        try:
            import winsound
            notes = [(523, 110), (659, 110), (784, 130), (1046, 320)]
            for freq, dur in notes:
                winsound.Beep(freq, dur)
        except Exception:
            pass

    @staticmethod
    def _play_work():
        try:
            import winsound
            notes = [(784, 90), (659, 90), (523, 260)]
            for freq, dur in notes:
                winsound.Beep(freq, dur)
        except Exception:
            pass

    @classmethod
    def play_break(cls):
        threading.Thread(target=cls._play_break, daemon=True).start()

    @classmethod
    def play_work(cls):
        threading.Thread(target=cls._play_work, daemon=True).start()


# ======================================================================================
# 4. TIPOGRAFIA & ÍCONES VETORIAIS (LUCIDE)
# ======================================================================================

FONT_FAMILY = "Segoe UI"
_LUCIDE_GLYPHS = {}
_FONTS_LOADED = False

def init_resources():
    global FONT_FAMILY, _FONTS_LOADED, _LUCIDE_GLYPHS
    if _FONTS_LOADED:
        return
        
    font_path = os.path.join(APP_DIR, "assets", "Inter.ttf")
    if os.path.exists(font_path):
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id != -1:
            families = QFontDatabase.applicationFontFamilies(font_id)
            if families:
                FONT_FAMILY = families[0]

    lucide_path = os.path.join(APP_DIR, "assets", "lucide.ttf")
    if os.path.exists(lucide_path):
        QFontDatabase.addApplicationFont(lucide_path)

    glyphs_path = os.path.join(APP_DIR, "assets", "lucide_glyphs.json")
    if os.path.exists(glyphs_path):
        try:
            with open(glyphs_path, "r", encoding="utf-8") as f:
                _LUCIDE_GLYPHS = json.load(f)
        except Exception:
            _LUCIDE_GLYPHS = {}
            
    _FONTS_LOADED = True


def get_font(size: int = 12, weight: QFont.Weight = QFont.Weight.Normal) -> QFont:
    font = QFont(FONT_FAMILY, size)
    font.setWeight(weight)
    return font


def get_lucide_icon(name: str, color: str = "#94a3b8", size: int = 16) -> QIcon:
    """Gera um QIcon vetorizado e nítido a partir da fonte Lucide."""
    init_resources()
    char = _LUCIDE_GLYPHS.get(name, "")
    if not char:
        return QIcon()

    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

    font = QFont("lucide")
    font.setPixelSize(int(size * 0.90))
    painter.setFont(font)
    painter.setPen(QColor(color))
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, char)
    painter.end()

    return QIcon(pixmap)


def get_app_icon(session_type: "SessionType" = None) -> QIcon:
    if session_type == SessionType.SHORT_BREAK or session_type == SessionType.LONG_BREAK:
        ico_file = os.path.join(APP_DIR, "assets", "pomodoro_break.ico")
    else:
        ico_file = os.path.join(APP_DIR, "assets", "pomodoro.ico")
        
    if os.path.exists(ico_file):
        return QIcon(ico_file)
    pix = QPixmap(32, 32)
    pix.fill(QColor("#2563eb"))
    return QIcon(pix)


# ======================================================================================
# 5. MOTOR DA TÉCNICA POMODORO (4 CICLOS + PAUSA LONGA + LOOP AUTOMÁTICO)
# ======================================================================================

class SessionType(Enum):
    WORK = "Foco"
    SHORT_BREAK = "Pausa Curta"
    LONG_BREAK = "Pausa Longa"


class TimerStatus(Enum):
    IDLE = "Pronto"
    RUNNING = "Em andamento"
    PAUSED = "Pausado"


class PomodoroEngine(QWidget):
    tick = pyqtSignal(int, int, str)
    state_changed = pyqtSignal(SessionType, int)
    status_changed = pyqtSignal(TimerStatus)
    break_started = pyqtSignal(SessionType, int, int)
    work_started = pyqtSignal(int)
    break_finished = pyqtSignal(int, int)

    def __init__(self, config: PomodoroConfig):
        super().__init__()
        self.config = config
        self.session_type = SessionType.WORK
        self.status = TimerStatus.IDLE
        self.cycle_count = 1  # 1 a 4

        self.total_seconds = self.config.work_duration_min * 60
        self.remaining_seconds = self.total_seconds

        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._on_tick)

    @property
    def is_in_break(self) -> bool:
        return self.session_type in (SessionType.SHORT_BREAK, SessionType.LONG_BREAK)

    @property
    def is_running(self) -> bool:
        return self.status == TimerStatus.RUNNING

    @staticmethod
    def format_time(seconds: int) -> str:
        m, s = divmod(seconds, 60)
        return f"{m:02d}:{s:02d}"

    def start(self):
        self.status = TimerStatus.RUNNING
        self._timer.start()
        self.status_changed.emit(self.status)

    def pause(self):
        self.status = TimerStatus.PAUSED
        self._timer.stop()
        self.status_changed.emit(self.status)

    def toggle_play_pause(self):
        if self.status == TimerStatus.RUNNING:
            self.pause()
        else:
            self.start()

    def restart_current(self):
        self._timer.stop()
        self.total_seconds = self._duration_for_session()
        self.remaining_seconds = self.total_seconds
        self.status = TimerStatus.IDLE
        self.status_changed.emit(self.status)
        self.tick.emit(self.remaining_seconds, self.total_seconds, self.format_time(self.remaining_seconds))

    def skip_session(self):
        """Pula para a próxima etapa da técnica."""
        self._timer.stop()
        self.status = TimerStatus.IDLE
        self.status_changed.emit(self.status)
        self._advance()

    def set_session_type(self, session_type: SessionType):
        self._timer.stop()
        self.session_type = session_type
        self.status = TimerStatus.IDLE
        self.total_seconds = self._duration_for_session()
        self.remaining_seconds = self.total_seconds
        self.state_changed.emit(self.session_type, self.cycle_count)
        self.status_changed.emit(self.status)
        self.tick.emit(self.remaining_seconds, self.total_seconds, self.format_time(self.remaining_seconds))

    def _duration_for_session(self) -> int:
        if self.session_type == SessionType.WORK:
            return self.config.work_duration_min * 60
        elif self.session_type == SessionType.SHORT_BREAK:
            return self.config.short_break_min * 60
        else:
            return self.config.long_break_min * 60

    def _on_tick(self):
        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            self.tick.emit(self.remaining_seconds, self.total_seconds, self.format_time(self.remaining_seconds))
            if self.remaining_seconds == 0:
                self._timer.stop()
                self.status = TimerStatus.IDLE
                self.status_changed.emit(self.status)
                if self.is_in_break:
                    next_cycle = 1 if self.session_type == SessionType.LONG_BREAK else self.cycle_count + 1
                    self.break_finished.emit(next_cycle, self.config.cycles_before_long_break)
                else:
                    self._advance()

    def start_next_work_cycle(self):
        """Inicia conscientemente o próximo bloco de foco da técnica."""
        if self.session_type == SessionType.LONG_BREAK:
            self.cycle_count = 1
        else:
            self.cycle_count += 1

        self.session_type = SessionType.WORK
        self.total_seconds = self._duration_for_session()
        self.remaining_seconds = self.total_seconds
        self.state_changed.emit(self.session_type, self.cycle_count)
        self.tick.emit(self.remaining_seconds, self.total_seconds, self.format_time(self.remaining_seconds))
        self.work_started.emit(self.cycle_count)
        self.start()

    def _advance(self):
        """Avanço oficial dos ciclos da Técnica Pomodoro."""
        if self.session_type == SessionType.WORK:
            # Ao terminar o 4º ciclo de foco, a pausa é longa
            if self.cycle_count >= self.config.cycles_before_long_break:
                self.session_type = SessionType.LONG_BREAK
            else:
                self.session_type = SessionType.SHORT_BREAK

            self.total_seconds = self._duration_for_session()
            self.remaining_seconds = self.total_seconds
            self.state_changed.emit(self.session_type, self.cycle_count)
            self.tick.emit(self.remaining_seconds, self.total_seconds, self.format_time(self.remaining_seconds))
            self.break_started.emit(self.session_type, self.total_seconds, self.cycle_count)

            # Transição automática para a pausa
            if self.config.auto_start_break:
                self.status = TimerStatus.RUNNING
                self._timer.start()
                self.status_changed.emit(self.status)
        else:
            # Pausa encerrada -> Volta ao foco no próximo ciclo
            if self.session_type == SessionType.LONG_BREAK:
                # Reinicia a sequência de 4 blocos
                self.cycle_count = 1
            else:
                self.cycle_count += 1

            self.session_type = SessionType.WORK
            self.total_seconds = self._duration_for_session()
            self.remaining_seconds = self.total_seconds
            self.state_changed.emit(self.session_type, self.cycle_count)
            self.tick.emit(self.remaining_seconds, self.total_seconds, self.format_time(self.remaining_seconds))
            self.work_started.emit(self.cycle_count)

            # Transição automática para o próximo foco
            if self.config.auto_start_work:
                self.status = TimerStatus.RUNNING
                self._timer.start()
                self.status_changed.emit(self.status)


# ======================================================================================
# 6. OVERLAY ZEN MULTI-MONITOR (DESFOQUE + TIMER + PENSAMENTO FILOSÓFICO)
# ======================================================================================

def generate_blurred_pixmap(pixmap: QPixmap, blur_radius: int = 16, dim_factor: float = 0.35) -> QPixmap:
    try:
        qimg = pixmap.toImage().convertToFormat(QImage.Format.Format_RGBA8888)
        w, h = qimg.width(), qimg.height()
        ptr = qimg.bits()
        ptr.setsize(h * w * 4)
        img = Image.frombuffer("RGBA", (w, h), bytes(ptr), "raw", "RGBA", 0, 1)

        scale = 4
        small = img.resize((max(1, w // scale), max(1, h // scale)), Image.Resampling.BILINEAR)
        blurred = small.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        dimmed = ImageEnhance.Brightness(blurred).enhance(dim_factor)
        result = dimmed.resize((w, h), Image.Resampling.BICUBIC)

        out_bytes = result.tobytes("raw", "RGBA")
        qimg_out = QImage(out_bytes, w, h, QImage.Format.Format_RGBA8888)
        return QPixmap.fromImage(qimg_out)
    except Exception as e:
        print(f"Erro no processamento do blur: {e}")
        return pixmap


class SingleScreenOverlay(QWidget):
    dismiss_requested = pyqtSignal()
    start_focus_requested = pyqtSignal()

    def __init__(self, screen, blurred_pixmap: QPixmap, is_main_screen: bool, config: PomodoroConfig, quote: Optional[Dict[str, str]] = None):
        super().__init__(None)
        self.screen_ref = screen
        self.config = config
        self.is_main_screen = is_main_screen
        self.blurred_pixmap = blurred_pixmap
        self.is_prompt_mode = False

        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_QuitOnClose, False)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowOpacity(0.0)

        geo = screen.geometry()
        self.setGeometry(geo)

        # Fundo fosco
        self.bg_label = QLabel(self)
        self.bg_label.setGeometry(0, 0, geo.width(), geo.height())
        self.bg_label.setPixmap(self.blurred_pixmap.scaled(
            geo.width(), geo.height(),
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        ))

        # Conteúdo diferenciado por monitor (todas as fontes brancas, zero emojis)
        if self.is_main_screen:
            # MONITOR PRINCIPAL: Subtítulo + Timer / Pergunta de confirmação consciente
            self.center_box = QWidget(self)
            self.c_lay = QVBoxLayout(self.center_box)
            self.c_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.c_lay.setSpacing(14)

            self.lbl_sub = QLabel("PAUSA", self.center_box)
            self.lbl_sub.setFont(get_font(13, QFont.Weight.DemiBold))
            self.lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.lbl_sub.setStyleSheet("color: #ffffff; letter-spacing: 5px; background: transparent;")
            self.c_lay.addWidget(self.lbl_sub)

            self.timer_label = QLabel("05:00", self.center_box)
            self.timer_label.setFont(get_font(92, QFont.Weight.Bold))
            self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.timer_label.setStyleSheet("color: #ffffff; background: transparent; font-variant-numeric: tabular-nums;")
            self.c_lay.addWidget(self.timer_label)

            self.lbl_prompt = QLabel("", self.center_box)
            self.lbl_prompt.setFont(get_font(24, QFont.Weight.DemiBold))
            self.lbl_prompt.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.lbl_prompt.setStyleSheet("color: #ffffff; background: transparent;")
            self.lbl_prompt.hide()
            self.c_lay.addWidget(self.lbl_prompt)

            self.btn_confirm = QPushButton("Iniciar Foco", self.center_box)
            self.btn_confirm.setCursor(Qt.CursorShape.PointingHandCursor)
            self.btn_confirm.setFont(get_font(14, QFont.Weight.DemiBold))
            self.btn_confirm.setStyleSheet("""
                QPushButton {
                    background-color: #2563eb;
                    color: #ffffff;
                    border: none;
                    border-radius: 8px;
                    padding: 12px 36px;
                }
                QPushButton:hover {
                    background-color: #1d4ed8;
                }
                QPushButton:pressed {
                    background-color: #1e40af;
                }
            """)
            self.btn_confirm.clicked.connect(self.start_focus_requested.emit)
            self.btn_confirm.hide()
            self.c_lay.addWidget(self.btn_confirm, alignment=Qt.AlignmentFlag.AlignCenter)

            self.lbl_esc = QLabel("Pressione Esc ou clique para voltar ao trabalho", self.center_box)
            self.lbl_esc.setFont(get_font(11, QFont.Weight.Normal))
            self.lbl_esc.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.lbl_esc.setStyleSheet("color: rgba(255, 255, 255, 0.45); background: transparent;")
            self.c_lay.addWidget(self.lbl_esc)

            box_w, box_h = 750, 270
            self.center_box.setFixedSize(box_w, box_h)
            self.center_box.move((geo.width() - box_w) // 2, (geo.height() - box_h) // 2)

        else:
            # MONITOR SECUNDÁRIO: Pensamento clássico de sabedoria / reflexão
            center_box = QWidget(self)
            c_lay = QVBoxLayout(center_box)
            c_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
            c_lay.setSpacing(18)

            q_text = quote["quote"] if quote else "A tranquilidade nada mais é do que a boa ordenação da própria mente."
            q_author = quote["author"] if quote else "Marco Aurélio"

            lbl_quote = QLabel(f'"{q_text}"', center_box)
            lbl_quote.setFont(get_font(23, QFont.Weight.Normal))
            lbl_quote.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_quote.setWordWrap(True)
            lbl_quote.setStyleSheet("color: #ffffff; line-height: 1.4; background: transparent;")
            c_lay.addWidget(lbl_quote)

            lbl_author = QLabel(f"— {q_author.upper()}", center_box)
            lbl_author.setFont(get_font(13, QFont.Weight.DemiBold))
            lbl_author.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_author.setStyleSheet("color: rgba(255, 255, 255, 0.65); letter-spacing: 4px; background: transparent;")
            c_lay.addWidget(lbl_author)

            box_w = min(850, int(geo.width() * 0.75))
            box_h = 320
            center_box.setFixedSize(box_w, box_h)
            center_box.move((geo.width() - box_w) // 2, (geo.height() - box_h) // 2)

    def set_content(self, session: SessionType, cycle: int, max_cycles: int, remaining_seconds: int):
        if self.is_main_screen:
            self.is_prompt_mode = False
            self.lbl_prompt.hide()
            self.btn_confirm.hide()
            self.timer_label.show()
            self.lbl_esc.setText("Pressione Esc ou clique para voltar ao trabalho")
            if session == SessionType.LONG_BREAK:
                title = "PAUSA LONGA • 4 CICLOS CONCLUÍDOS"
            else:
                title = f"PAUSA CURTA • CICLO {cycle} DE {max_cycles}"
            self.lbl_sub.setText(title)
            self.timer_label.setText(PomodoroEngine.format_time(remaining_seconds))

    def show_prompt_for_focus(self, next_cycle: int, max_cycles: int):
        if self.is_main_screen:
            self.is_prompt_mode = True
            self.lbl_sub.setText("PAUSA CONCLUÍDA")
            self.timer_label.hide()
            self.lbl_prompt.setText(f"Pronto para iniciar o Ciclo {next_cycle} de {max_cycles}?")
            self.lbl_prompt.show()
            self.btn_confirm.show()
            self.lbl_esc.setText("Pressione Enter ou Espaço para iniciar o foco")
            self.btn_confirm.setFocus()

    def update_timer(self, remaining: int, total: int, formatted: str):
        if self.is_main_screen and not self.is_prompt_mode:
            self.timer_label.setText(formatted)

    def keyPressEvent(self, event: QKeyEvent):
        if self.is_prompt_mode:
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
                self.start_focus_requested.emit()
            elif event.key() == Qt.Key.Key_Escape:
                self.dismiss_requested.emit()
        else:
            if event.key() == Qt.Key.Key_Escape and self.config.allow_esc_skip:
                self.dismiss_requested.emit()
            else:
                super().keyPressEvent(event)

    def mousePressEvent(self, event):
        if self.is_prompt_mode:
            self.start_focus_requested.emit()
        else:
            if self.config.allow_esc_skip:
                self.dismiss_requested.emit()
            else:
                super().mousePressEvent(event)


class BlurOverlayManager(QWidget):
    skip_requested = pyqtSignal()
    start_focus_confirmed = pyqtSignal()

    def __init__(self, config: PomodoroConfig):
        super().__init__()
        self.config = config
        self.quote_manager = QuoteManager()
        self.overlays: List[SingleScreenOverlay] = []
        self.fade_animations: List[QPropertyAnimation] = []
        self.is_active = False

    def show_break_overlay(self, session: SessionType, cycle: int, max_cycles: int, remaining: int):
        if self.is_active:
            return

        self.close_overlay()
        self.is_active = True
        screens = QApplication.screens()
        primary = QApplication.primaryScreen()

        # Seleciona uma nova reflexão para o monitor secundário (sem repetições)
        current_quote = self.quote_manager.get_next_quote()

        for screen in screens:
            pixmap = screen.grabWindow(0)
            blurred = generate_blurred_pixmap(pixmap, self.config.blur_radius, self.config.dim_factor)

            is_main = (screen == primary)
            overlay = SingleScreenOverlay(screen, blurred, is_main, self.config, current_quote)
            overlay.set_content(session, cycle, max_cycles, remaining)
            overlay.dismiss_requested.connect(self._on_dismiss)
            overlay.start_focus_requested.connect(self.start_focus_confirmed.emit)
            self.overlays.append(overlay)

            overlay.showFullScreen()
            overlay.raise_()
            overlay.activateWindow()

            anim = QPropertyAnimation(overlay, b"windowOpacity")
            anim.setDuration(350)
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            self.fade_animations.append(anim)
            anim.start()

    def prompt_start_focus(self, next_cycle: int, max_cycles: int):
        """Apresenta a pergunta de confirmação consciente mantendo a tela desfocada."""
        if not self.is_active:
            return
        for overlay in self.overlays:
            overlay.show_prompt_for_focus(next_cycle, max_cycles)

    def update_timer(self, remaining: int, total: int, formatted: str):
        if not self.is_active:
            return
        for overlay in self.overlays:
            overlay.update_timer(remaining, total, formatted)

    def _on_dismiss(self):
        self.close_overlay()
        self.skip_requested.emit()

    def close_overlay(self):
        if not self.is_active and not self.overlays:
            return

        for anim in self.fade_animations:
            anim.stop()
        self.fade_animations.clear()

        for overlay in self.overlays:
            overlay.hide()
            overlay.deleteLater()
        self.overlays.clear()
        self.is_active = False


# ======================================================================================
# 7. DIÁLOGO DISCRETO DE CONFIGURAÇÃO DE TEMPOS
# ======================================================================================

class QuickSettingsDialog(QDialog):
    def __init__(self, config: PomodoroConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Configurar Tempos")
        self.setFixedSize(300, 270)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self.setStyleSheet("""
            QDialog {
                background-color: #0f172a;
                color: #e2e8f0;
            }
            QLabel {
                color: #cbd5e1;
                font-size: 13px;
            }
            QSpinBox {
                background: #1e293b;
                color: #ffffff;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 13px;
                min-width: 60px;
            }
            QPushButton {
                border-radius: 6px;
                padding: 7px 14px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton#btnSave {
                background: #2563eb;
                color: #ffffff;
                border: none;
            }
            QPushButton#btnSave:hover {
                background: #1d4ed8;
            }
            QPushButton#btnCancel {
                background: transparent;
                color: #94a3b8;
                border: 1px solid #334155;
            }
            QPushButton#btnCancel:hover {
                background: #1e293b;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = QLabel("Durações dos Ciclos (minutos)")
        title.setFont(get_font(12, QFont.Weight.Bold))
        title.setStyleSheet("color: #f8fafc;")
        layout.addWidget(title)

        def make_row(label_text: str, val: int, min_val: int, max_val: int):
            row = QHBoxLayout()
            lbl = QLabel(label_text)
            sp = QSpinBox()
            sp.setRange(min_val, max_val)
            sp.setValue(val)
            row.addWidget(lbl)
            row.addStretch()
            row.addWidget(sp)
            return row, sp

        r1, self.sp_work = make_row("Sessão de Foco:", self.config.work_duration_min, 1, 120)
        r2, self.sp_short = make_row("Pausa Curta:", self.config.short_break_min, 1, 60)
        r3, self.sp_long = make_row("Pausa Longa:", self.config.long_break_min, 1, 90)

        layout.addLayout(r1)
        layout.addLayout(r2)
        layout.addLayout(r3)
        layout.addStretch()

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("btnCancel")
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)

        btn_save = QPushButton("Salvar")
        btn_save.setObjectName("btnSave")
        btn_save.clicked.connect(self._save)
        btn_row.addWidget(btn_save)

        layout.addLayout(btn_row)

    def _save(self):
        self.config.work_duration_min = self.sp_work.value()
        self.config.short_break_min = self.sp_short.value()
        self.config.long_break_min = self.sp_long.value()
        self.config.save()
        self.accept()


# ======================================================================================
# 8. EXTENSÃO DA BANDEJA DO SISTEMA (ZERO EMOJIS, 100% TIPOGRÁFICO)
# ======================================================================================

class PomodoroSystemExtension(QWidget):
    def __init__(self):
        super().__init__()
        init_resources()
        self.config = PomodoroConfig.load()
        self.engine = PomodoroEngine(self.config)
        self.blur_manager = BlurOverlayManager(self.config)

        # Ícone nativo na bandeja
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(get_app_icon())
        self.tray.activated.connect(self._on_tray_activated)

        # Sinais
        self.engine.tick.connect(self._on_tick)
        self.engine.state_changed.connect(self._on_state_changed)
        self.engine.status_changed.connect(self._on_status_changed)
        self.engine.break_started.connect(self._on_break_started)
        self.engine.work_started.connect(self._on_work_started)
        self.engine.break_finished.connect(self._on_break_finished)

        self.blur_manager.skip_requested.connect(self.engine.skip_session)
        self.blur_manager.start_focus_confirmed.connect(self._on_start_focus_confirmed)
        self.engine.tick.connect(self.blur_manager.update_timer)

        self._update_tray_tooltip()
        self._rebuild_menu()
        self.tray.show()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.engine.toggle_play_pause()

    def _update_tray_tooltip(self):
        time_str = PomodoroEngine.format_time(self.engine.remaining_seconds)
        session_label = self.engine.session_type.value
        cycle_info = f"Ciclo {self.engine.cycle_count} de {self.config.cycles_before_long_break}"

        if self.engine.status == TimerStatus.RUNNING:
            self.tray.setToolTip(f"Pomodoro: {session_label} em andamento ({cycle_info} • {time_str} restantes)\nClique para pausar")
        elif self.engine.status == TimerStatus.PAUSED:
            self.tray.setToolTip(f"Pomodoro: {session_label} pausado ({cycle_info} • {time_str})\nClique para retomar")
        else:
            self.tray.setToolTip(f"Pomodoro: Pronto para {session_label} ({cycle_info} • {time_str})\nClique para iniciar")

    def _on_tick(self, remaining: int, total: int, formatted: str):
        self._update_tray_tooltip()

    def _update_tray_icon(self):
        self.tray.setIcon(get_app_icon(self.engine.session_type))

    def _on_state_changed(self, session: SessionType, cycle: int):
        self._update_tray_icon()
        self._update_tray_tooltip()
        self._rebuild_menu()

    def _on_status_changed(self, status: TimerStatus):
        self._update_tray_icon()
        self._update_tray_tooltip()
        self._rebuild_menu()

    def _on_break_started(self, session: SessionType, total: int, cycle: int):
        if self.config.enable_sound:
            SoundEngine.play_break()
        if self.config.enable_tray_notifications:
            if session == SessionType.LONG_BREAK:
                title = "Pausa Longa"
                msg = f"{self.config.cycles_before_long_break} ciclos de foco concluídos com sucesso. Descanse por {self.config.long_break_min} minutos."
            else:
                title = "Hora da Pausa"
                msg = f"Ciclo {cycle} de {self.config.cycles_before_long_break} concluído. Descanse os olhos e respire fundo."
            self.tray.showMessage(title, msg, QSystemTrayIcon.MessageIcon.Information, 3500)

        self.blur_manager.show_break_overlay(
            session, cycle, self.config.cycles_before_long_break, self.engine.remaining_seconds
        )

    def _on_work_started(self, cycle: int):
        self.blur_manager.close_overlay()
        if self.config.enable_sound:
            SoundEngine.play_work()
        if self.config.enable_tray_notifications:
            title = "Hora de Focar"
            msg = f"Ciclo {cycle} de {self.config.cycles_before_long_break} iniciado. Bom trabalho!"
            self.tray.showMessage(title, msg, QSystemTrayIcon.MessageIcon.Information, 3500)

    def _on_break_finished(self, next_cycle: int, max_cycles: int):
        if self.config.enable_sound:
            SoundEngine.play_break()
        if self.config.enable_tray_notifications:
            self.tray.showMessage(
                "Pausa Concluída",
                f"Pronto para iniciar o Ciclo {next_cycle} de {max_cycles}?",
                QSystemTrayIcon.MessageIcon.Information,
                4000
            )
        self.blur_manager.prompt_start_focus(next_cycle, max_cycles)

    def _on_start_focus_confirmed(self):
        self.blur_manager.close_overlay()
        self.engine.start_next_work_cycle()
        if self.config.enable_sound:
            SoundEngine.play_work()
        if self.config.enable_tray_notifications:
            title = "Hora de Focar"
            msg = f"Ciclo {self.engine.cycle_count} de {self.config.cycles_before_long_break} iniciado. Bom trabalho!"
            self.tray.showMessage(title, msg, QSystemTrayIcon.MessageIcon.Information, 3500)

    def _rebuild_menu(self):
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background: #0f172a;
                color: #e2e8f0;
                border: 1px solid rgba(255, 255, 255, 0.10);
                padding: 6px;
                border-radius: 8px;
                font-family: "Segoe UI", sans-serif;
                font-size: 12px;
            }
            QMenu::item {
                padding: 6px 16px 6px 10px;
                border-radius: 5px;
            }
            QMenu::item:selected {
                background: #2563eb;
                color: #ffffff;
            }
            QMenu::item:disabled {
                color: #94a3b8;
                font-weight: 600;
            }
            QMenu::icon {
                padding-left: 4px;
            }
            QMenu::separator {
                height: 1px;
                background: rgba(255, 255, 255, 0.08);
                margin: 5px 4px;
            }
        """)

        # Cabeçalho Informativo com ícone temático Lucide
        is_work = (self.engine.session_type == SessionType.WORK)
        h_icon = get_lucide_icon("clock" if is_work else "coffee", "#38bdf8" if is_work else "#34d399", 16)
        session_label = self.engine.session_type.value
        time_str = PomodoroEngine.format_time(self.engine.remaining_seconds)
        cycle_info = f"Ciclo {self.engine.cycle_count} de {self.config.cycles_before_long_break}"
        state_label = self.engine.status.value

        header_act = menu.addAction(h_icon, f"{session_label}: {time_str} ({cycle_info} • {state_label})")
        header_act.setEnabled(False)

        menu.addSeparator()

        # Ações de Controle com ícones Lucide
        if self.engine.is_running:
            act_toggle = menu.addAction(get_lucide_icon("pause", "#f59e0b", 16), "Pausar")
        else:
            action_text = "Iniciar" if self.engine.status == TimerStatus.IDLE else "Retomar"
            act_toggle = menu.addAction(get_lucide_icon("play", "#38bdf8", 16), action_text)
        act_toggle.triggered.connect(self.engine.toggle_play_pause)

        next_target = "Pausa" if is_work else "Foco"
        act_skip = menu.addAction(get_lucide_icon("skip-forward", "#94a3b8", 16), f"Pular para {next_target}")
        act_skip.triggered.connect(self.engine.skip_session)

        act_restart = menu.addAction(get_lucide_icon("rotate-ccw", "#94a3b8", 16), "Reiniciar Sessão Atual")
        act_restart.triggered.connect(self.engine.restart_current)

        menu.addSeparator()

        # Presets de Duração com ícone Lucide
        menu_presets = menu.addMenu(get_lucide_icon("clock", "#94a3b8", 16), "Durações")
        menu_presets.setStyleSheet(menu.styleSheet())
        
        act_p1 = menu_presets.addAction("25 min Foco / 5 min Pausa (Padrão)")
        act_p1.setCheckable(True)
        act_p1.setChecked(self.config.work_duration_min == 25 and self.config.short_break_min == 5)
        act_p1.triggered.connect(lambda: self._set_preset(25, 5, 15))

        act_p2 = menu_presets.addAction("50 min Foco / 10 min Pausa")
        act_p2.setCheckable(True)
        act_p2.setChecked(self.config.work_duration_min == 50 and self.config.short_break_min == 10)
        act_p2.triggered.connect(lambda: self._set_preset(50, 10, 20))

        act_p3 = menu_presets.addAction("15 min Foco / 3 min Pausa")
        act_p3.setCheckable(True)
        act_p3.setChecked(self.config.work_duration_min == 15 and self.config.short_break_min == 3)
        act_p3.triggered.connect(lambda: self._set_preset(15, 3, 10))

        menu_presets.addSeparator()
        act_custom = menu_presets.addAction(get_lucide_icon("sliders", "#94a3b8", 16), "Personalizar Tempos...")
        act_custom.triggered.connect(self._open_custom_dialog)

        # Testar Blur
        act_test = menu.addAction(get_lucide_icon("eye", "#94a3b8", 16), "Testar Tela de Pausa (Preview)")
        act_test.triggered.connect(self._test_blur)

        menu.addSeparator()

        # Preferências Rápidas
        act_sound = menu.addAction(get_lucide_icon("volume-2", "#94a3b8", 16), "Efeitos Sonoros")
        act_sound.setCheckable(True)
        act_sound.setChecked(self.config.enable_sound)
        act_sound.triggered.connect(self._toggle_sound)

        act_notif = menu.addAction(get_lucide_icon("bell", "#94a3b8", 16), "Notificações do Windows")
        act_notif.setCheckable(True)
        act_notif.setChecked(self.config.enable_tray_notifications)
        act_notif.triggered.connect(self._toggle_notif)

        act_auto = menu.addAction(get_lucide_icon("power", "#94a3b8", 16), "Iniciar com o Windows")
        act_auto.setCheckable(True)
        act_auto.setChecked(is_autostart_enabled())
        act_auto.triggered.connect(self._toggle_autostart)

        menu.addSeparator()

        act_quit = menu.addAction(get_lucide_icon("x", "#f87171", 16), "Fechar Pomodoro")
        act_quit.triggered.connect(QApplication.quit)

        self.tray.setContextMenu(menu)

    def _set_preset(self, work: int, short: int, long_b: int):
        self.config.work_duration_min = work
        self.config.short_break_min = short
        self.config.long_break_min = long_b
        self.config.save()
        self.engine.restart_current()

    def _open_custom_dialog(self):
        dlg = QuickSettingsDialog(self.config)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.engine.restart_current()

    def _toggle_sound(self):
        self.config.enable_sound = not self.config.enable_sound
        self.config.save()

    def _toggle_notif(self):
        self.config.enable_tray_notifications = not self.config.enable_tray_notifications
        self.config.save()

    def _toggle_autostart(self):
        new_state = not is_autostart_enabled()
        set_autostart(new_state)

    def _test_blur(self):
        self.blur_manager.show_break_overlay(
            SessionType.SHORT_BREAK,
            self.engine.cycle_count,
            self.config.cycles_before_long_break,
            self.config.short_break_min * 60
        )


# ======================================================================================
# 9. PONTO DE ENTRADA DO SISTEMA
# ======================================================================================

def setup_exception_logging():
    def excepthook(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        log_path = os.path.join(APP_DIR, "crash_error.log")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"\n--- Erro [{time.strftime('%Y-%m-%d %H:%M:%S')}] ---\n")
            traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
    sys.excepthook = excepthook


def main():
    setup_exception_logging()
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName("PomodoroBlur")
    app.setQuitOnLastWindowClosed(False)

    service = PomodoroSystemExtension()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
