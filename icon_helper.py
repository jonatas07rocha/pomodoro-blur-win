import os
import json
from PyQt6.QtGui import QFontDatabase, QFont, QPixmap, QPainter, QColor, QIcon
from PyQt6.QtCore import Qt

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
TTF_LUCIDE_PATH = os.path.join(ASSETS_DIR, "lucide.ttf")
TTF_INTER_PATH = os.path.join(ASSETS_DIR, "Inter.ttf")
GLYPHS_PATH = os.path.join(ASSETS_DIR, "lucide_glyphs.json")

_FONTS_LOADED = False
_GLYPHS_MAP = {}

def init_fonts():
    """Registra as fontes Inter e Lucide no motor de fontes do Qt."""
    global _FONTS_LOADED, _GLYPHS_MAP
    if _FONTS_LOADED:
        return

    # 1. Registrar Fonte Inter (usada em toda a tipografia, idêntico ao Foco Total / Tailwind)
    if os.path.exists(TTF_INTER_PATH):
        QFontDatabase.addApplicationFont(TTF_INTER_PATH)

    # 2. Registrar Fonte de Ícones Lucide
    if os.path.exists(TTF_LUCIDE_PATH):
        QFontDatabase.addApplicationFont(TTF_LUCIDE_PATH)

    # 3. Carregar mapeamento dos 2.100+ glifos Lucide
    if os.path.exists(GLYPHS_PATH):
        try:
            with open(GLYPHS_PATH, "r", encoding="utf-8") as f:
                _GLYPHS_MAP = json.load(f)
        except Exception as e:
            print(f"Erro ao carregar lucide_glyphs.json: {e}")

    _FONTS_LOADED = True

# Alias para compatibilidade
init_lucide = init_fonts

def get_glyph(name: str) -> str:
    """Retorna o caractere unicode do ícone Lucide."""
    init_fonts()
    return _GLYPHS_MAP.get(name, "")

def get_lucide_font(point_size: int = 14) -> QFont:
    """Retorna a QFont para desenhar ícones Lucide."""
    init_fonts()
    font = QFont("lucide")
    font.setPointSize(point_size)
    return font

def get_inter_font(point_size: int = 13, weight: QFont.Weight = QFont.Weight.Normal) -> QFont:
    """Retorna a QFont da família Inter com o peso desejado."""
    init_fonts()
    font = QFont("Inter")
    font.setPointSize(point_size)
    font.setWeight(weight)
    return font

def get_lucide_icon(name: str, color: str = "#ffffff", size: int = 20) -> QIcon:
    """Gera um QIcon perfeitamente vetorizado a partir de um glifo Lucide."""
    init_fonts()
    char = _GLYPHS_MAP.get(name, "")
    if not char:
        return QIcon()

    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

    font = QFont("lucide")
    font.setPixelSize(int(size * 0.85))
    painter.setFont(font)
    painter.setPen(QColor(color))
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, char)
    painter.end()

    return QIcon(pixmap)
