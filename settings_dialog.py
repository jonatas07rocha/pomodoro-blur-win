from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox,
    QComboBox, QSlider, QCheckBox, QPushButton, QGroupBox, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from config import PomodoroConfig
from icon_helper import get_glyph, get_lucide_icon, get_lucide_font

class SettingsDialog(QDialog):
    config_saved = pyqtSignal(PomodoroConfig)

    def __init__(self, current_config: PomodoroConfig, parent=None):
        super().__init__(parent)
        self.config = current_config
        self.setWindowTitle("Configurações do Pomodoro Blur")
        self.setFixedSize(500, 600)
        self.setStyleSheet("""
            QDialog {
                background-color: #0b0f19;
                color: #f1f5f9;
                font-family: 'Segoe UI', system-ui, sans-serif;
            }
            QLabel {
                color: #e2e8f0;
                font-size: 13px;
            }
            QGroupBox {
                border: 1px solid #1e293b;
                border-radius: 14px;
                margin-top: 16px;
                padding-top: 14px;
                font-weight: 700;
                color: #38bdf8;
                font-size: 13px;
                background-color: #111827;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 14px;
                padding: 0 8px;
            }
            QSpinBox {
                background-color: #1e293b;
                color: #f8fafc;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 6px 10px;
                font-size: 13px;
                min-width: 75px;
            }
            QSpinBox:focus {
                border-color: #38bdf8;
            }
            QComboBox {
                background-color: #1e293b;
                color: #f8fafc;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 13px;
                min-width: 140px;
            }
            QComboBox QAbstractItemView {
                background-color: #1e293b;
                color: #f8fafc;
                selection-background-color: #2563eb;
                border: 1px solid #334155;
            }
            QCheckBox {
                color: #cbd5e1;
                font-size: 13px;
                spacing: 10px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 5px;
                border: 1px solid #475569;
                background-color: #1e293b;
            }
            QCheckBox::indicator:checked {
                background-color: #2563eb;
                border-color: #38bdf8;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: #1e293b;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: #38bdf8;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #f8fafc;
                width: 16px;
                margin-top: -5px;
                margin-bottom: -5px;
                border-radius: 8px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 20, 28, 24)
        layout.setSpacing(14)

        # Header do Diálogo
        header_row = QHBoxLayout()
        icon_cfg = QLabel(get_glyph("settings"), self)
        icon_cfg.setFont(get_lucide_font(20))
        icon_cfg.setStyleSheet("color: #38bdf8;")
        header_row.addWidget(icon_cfg)

        title_lbl = QLabel("Preferências & Personalização", self)
        title_lbl.setStyleSheet("color: #f8fafc; font-size: 16px; font-weight: 700;")
        header_row.addWidget(title_lbl)
        header_row.addStretch()
        layout.addLayout(header_row)

        # Grupo: Tempos
        times_group = QGroupBox("Duração das Sessões (minutos)")
        times_layout = QVBoxLayout(times_group)
        times_layout.setContentsMargins(16, 16, 16, 16)
        times_layout.setSpacing(10)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Tempo de Foco (Trabalho):"))
        self.spin_work = QSpinBox()
        self.spin_work.setRange(1, 120)
        self.spin_work.setValue(self.config.work_duration_min)
        row1.addWidget(self.spin_work)
        times_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Pausa Curta:"))
        self.spin_short = QSpinBox()
        self.spin_short.setRange(1, 60)
        self.spin_short.setValue(self.config.short_break_min)
        row2.addWidget(self.spin_short)
        times_layout.addLayout(row2)

        row3 = QHBoxLayout()
        row3.addWidget(QLabel("Pausa Longa:"))
        self.spin_long = QSpinBox()
        self.spin_long.setRange(1, 90)
        self.spin_long.setValue(self.config.long_break_min)
        row3.addWidget(self.spin_long)
        times_layout.addLayout(row3)

        row4 = QHBoxLayout()
        row4.addWidget(QLabel("Ciclos até Pausa Longa:"))
        self.spin_cycles = QSpinBox()
        self.spin_cycles.setRange(1, 12)
        self.spin_cycles.setValue(self.config.cycles_before_long_break)
        row4.addWidget(self.spin_cycles)
        times_layout.addLayout(row4)

        layout.addWidget(times_group)

        # Grupo: Efeito Blur & Visual
        blur_group = QGroupBox("Efeito de Blur da Tela (Frosted Glass)")
        blur_layout = QVBoxLayout(blur_group)
        blur_layout.setContentsMargins(16, 16, 16, 16)
        blur_layout.setSpacing(10)

        row_blur = QHBoxLayout()
        row_blur.addWidget(QLabel("Intensidade do Desfoque:"))
        self.combo_blur = QComboBox()
        self.combo_blur.addItem("Suave (Leve)", 6)
        self.combo_blur.addItem("Padrão (Médio)", 10)
        self.combo_blur.addItem("Forte (Intenso)", 18)
        
        idx = 1
        if self.config.blur_radius <= 6:
            idx = 0
        elif self.config.blur_radius >= 16:
            idx = 2
        self.combo_blur.setCurrentIndex(idx)
        row_blur.addWidget(self.combo_blur)
        blur_layout.addLayout(row_blur)

        row_dim = QVBoxLayout()
        self.lbl_dim = QLabel(f"Escurecimento do Fundo: {int((1.0 - self.config.dim_factor) * 100)}%")
        row_dim.addWidget(self.lbl_dim)
        
        self.slider_dim = QSlider(Qt.Orientation.Horizontal)
        self.slider_dim.setRange(20, 80)
        self.slider_dim.setValue(int((1.0 - self.config.dim_factor) * 100))
        self.slider_dim.valueChanged.connect(self._on_dim_changed)
        row_dim.addWidget(self.slider_dim)
        blur_layout.addLayout(row_dim)

        layout.addWidget(blur_group)

        # Grupo: Comportamento
        pref_group = QGroupBox("Comportamento & Atalhos")
        pref_layout = QVBoxLayout(pref_group)
        pref_layout.setContentsMargins(16, 16, 16, 16)
        pref_layout.setSpacing(10)

        self.chk_sound = QCheckBox("Tocar sinal sonoro ao iniciar/finalizar ciclos")
        self.chk_sound.setChecked(self.config.enable_sound)
        pref_layout.addWidget(self.chk_sound)

        self.chk_auto_break = QCheckBox("Ativar tela de pausa automaticamente ao acabar o foco")
        self.chk_auto_break.setChecked(self.config.auto_start_break)
        pref_layout.addWidget(self.chk_auto_break)

        self.chk_esc = QCheckBox("Permitir fechar tela de blur com a tecla [ESC]")
        self.chk_esc.setChecked(self.config.allow_esc_skip)
        pref_layout.addWidget(self.chk_esc)

        layout.addWidget(pref_group)

        # Botões de Ação com Ícones Lucide
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_cancel = QPushButton(" Cancelar")
        btn_cancel.setIcon(get_lucide_icon("x", "#cbd5e1", 16))
        btn_cancel.setStyleSheet("""
            QPushButton {
                background: #1e293b; color: #cbd5e1; border: 1px solid #334155;
                border-radius: 10px; padding: 8px 18px; font-weight: 500; font-size: 13px;
            }
            QPushButton:hover { background: #334155; color: white; }
        """)
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        btn_save = QPushButton(" Salvar Alterações")
        btn_save.setIcon(get_lucide_icon("check", "#ffffff", 16))
        btn_save.setStyleSheet("""
            QPushButton {
                background: #2563eb; color: white; border: none;
                border-radius: 10px; padding: 8px 22px; font-weight: 600; font-size: 13px;
            }
            QPushButton:hover { background: #3b82f6; }
        """)
        btn_save.clicked.connect(self._save_settings)
        btn_layout.addWidget(btn_save)

        layout.addLayout(btn_layout)

    def _on_dim_changed(self, value):
        self.lbl_dim.setText(f"Escurecimento do Fundo: {value}%")

    def _save_settings(self):
        self.config.work_duration_min = self.spin_work.value()
        self.config.short_break_min = self.spin_short.value()
        self.config.long_break_min = self.spin_long.value()
        self.config.cycles_before_long_break = self.spin_cycles.value()
        
        self.config.blur_radius = self.combo_blur.currentData()
        dim_pct = self.slider_dim.value()
        self.config.dim_factor = max(0.1, round(1.0 - (dim_pct / 100.0), 2))
        
        self.config.enable_sound = self.chk_sound.isChecked()
        self.config.auto_start_break = self.chk_auto_break.isChecked()
        self.config.allow_esc_skip = self.chk_esc.isChecked()
        
        self.config.save()
        self.config_saved.emit(self.config)
        self.accept()
