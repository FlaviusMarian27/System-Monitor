import sys
import ctypes
import os
import socket
from datetime import datetime

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QGridLayout, QFrame,
                             QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
                             QHeaderView, QStyledItemDelegate, QAbstractItemView, QStyle,
                             QGraphicsDropShadowEffect)
from PyQt6.QtCore import QTimer, Qt, QRectF, QVariantAnimation, QEasingCurve
from PyQt6.QtGui import (QPainter, QColor, QPen, QFont, QLinearGradient, QConicalGradient,
                         QBrush, QGradient, QPainterPath)
import pyqtgraph as pg

MAX_CORES = 64
MAX_PROCESSES = 30
LEN_LINE = 512
STR_LEN = 256


class ProcessData(ctypes.Structure):
    _fields_ = [
        ("pid", ctypes.c_int),
        ("name", ctypes.c_char * STR_LEN),
        ("cpu_percent", ctypes.c_double),
        ("ram_percent", ctypes.c_double),
        ("user", ctypes.c_char * STR_LEN)
    ]


class SystemMetrics(ctypes.Structure):
    _fields_ = [
        ("cpu_model", ctypes.c_char * LEN_LINE),
        ("core_count", ctypes.c_int),
        ("cpu_freq_mhz", ctypes.c_double),
        ("cpu_usage_percent", ctypes.c_double),
        ("cpu_cores_usage", ctypes.c_double * MAX_CORES),
        ("ram_total_gb", ctypes.c_double),
        ("ram_used_gb", ctypes.c_double),
        ("ram_usage_percent", ctypes.c_double),
        ("disk_total_gb", ctypes.c_double),
        ("disk_used_gb", ctypes.c_double),
        ("disk_usage_percent", ctypes.c_double),
        ("uptime_seconds", ctypes.c_long),
        ("os_name", ctypes.c_char * LEN_LINE),
        ("kernel_version", ctypes.c_char * LEN_LINE),
        ("gpu_name", ctypes.c_char * LEN_LINE),
        ("gpu_usage_percent", ctypes.c_double),
        ("gpu_memory_total_gb", ctypes.c_double),
        ("gpu_memory_used_gb", ctypes.c_double),
        ("process_count", ctypes.c_int),
        ("processes", ProcessData * MAX_PROCESSES),
        # Network speed fields - must match order in core.h
        ("net_rx_kbps", ctypes.c_double),
        ("net_tx_kbps", ctypes.c_double),
    ]


current_dir = os.path.dirname(os.path.abspath(__file__))
lib_path = os.path.abspath(os.path.join(current_dir, '../../build/libmonitor.so'))
monitor_lib = ctypes.CDLL(lib_path)
monitor_lib.get_system_metrics.argtypes = [ctypes.POINTER(SystemMetrics)]
monitor_lib.get_system_metrics.restype = None


# ─── COLOR PALETTE (neschimbata) ─────────────────────────────────────────────
BG_DARK      = "#0d0e1a"   # main background - deep navy black
BG_PANEL     = "#12132a"   # panel background - slightly lighter
BG_PANEL2    = "#161830"   # alternate panel color used for table headers
ACCENT_BLUE  = "#4db8ff"   # electric blue accent - used for CPU and highlights
ACCENT_VIOLET= "#9d7ff5"   # soft violet accent - used for RAM
ACCENT_GREEN = "#4dffb4"   # neon green accent - used for disk storage
TEXT_PRIMARY = "#e2e8ff"   # primary text color - light blue-white
TEXT_DIM     = "#5a6080"   # secondary/dimmed text - muted blue-grey
BORDER_GLOW  = "#1e2045"   # subtle panel border color

# Fonturi cu fallback: pe Linux nu exista Consolas
MONO_FAMILIES = ["JetBrains Mono", "Cascadia Code", "Fira Code", "Ubuntu Mono",
                 "DejaVu Sans Mono", "Consolas", "monospace"]


def mono(size, weight=QFont.Weight.Normal, spacing=0.0):
    f = QFont()
    f.setFamilies(MONO_FAMILIES)
    f.setPointSizeF(size)
    f.setWeight(weight)
    if spacing:
        f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, spacing)
    return f


def rgba(hex_color, alpha):
    c = QColor(hex_color)
    c.setAlpha(alpha)
    return c


def css_rgba(hex_color, alpha):
    c = QColor(hex_color)
    return f"rgba({c.red()}, {c.green()}, {c.blue()}, {alpha})"


def read_distro_name():
    try:
        with open("/etc/os-release") as f:
            for line in f:
                if line.startswith("PRETTY_NAME="):
                    return line.split("=", 1)[1].strip().strip('"')
    except OSError:
        pass
    return "Linux"


# ─── WIDGETS ─────────────────────────────────────────────────────────────────
class CircularGauge(QWidget):
    """Gauge circular: track + arc cu gradient, glow si animatie lina a valorii."""

    def __init__(self, color=ACCENT_BLUE, label="", parent=None):
        super().__init__(parent)
        self.value = 0.0
        self.color = QColor(color)
        self.label = label
        self.setMinimumSize(150, 150)

        self._anim = QVariantAnimation(self)
        self._anim.setDuration(600)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.valueChanged.connect(self._on_anim)

    def _on_anim(self, v):
        self.value = float(v)
        self.update()

    def set_value(self, value):
        value = max(0.0, min(100.0, float(value)))
        self._anim.stop()
        self._anim.setStartValue(self.value)
        self._anim.setEndValue(value)
        self._anim.start()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        side = min(w, h) - 30
        rect = QRectF((w - side) / 2, (h - side) / 2, side, side)
        thickness = max(8.0, side * 0.075)

        # Fundal interior subtil
        inner = rect.adjusted(thickness, thickness, -thickness, -thickness)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(rgba(self.color, 10))
        p.drawEllipse(inner)

        # Tick-uri fine in jurul cercului
        p.save()
        p.translate(rect.center())
        tick_pen = QPen(rgba(TEXT_DIM, 70), 1)
        p.setPen(tick_pen)
        r_out = side / 2 + thickness * 1.15
        r_in = r_out - 4
        for i in range(40):
            p.drawLine(0, int(-r_in), 0, int(-r_out))
            p.rotate(9)
        p.restore()

        # Track
        pen_track = QPen(QColor(BORDER_GLOW), thickness)
        pen_track.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen_track)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawArc(rect, 0, 360 * 16)

        span = int(-(self.value / 100.0) * 360 * 16)
        if self.value > 0.3:
            # Glow
            for width, alpha in ((thickness * 2.4, 18), (thickness * 1.7, 35)):
                pen_glow = QPen(rgba(self.color, alpha), width)
                pen_glow.setCapStyle(Qt.PenCapStyle.RoundCap)
                p.setPen(pen_glow)
                p.drawArc(rect, 90 * 16, span)

            # Arc cu gradient conic (accent stins -> accent plin)
            grad = QConicalGradient(rect.center(), 90)
            grad.setColorAt(0.0, self.color.lighter(125))
            grad.setColorAt(max(0.01, 1 - self.value / 100.0), rgba(self.color, 150))
            grad.setColorAt(1.0, self.color.lighter(125))
            pen_fg = QPen(QBrush(grad), thickness)
            pen_fg.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(pen_fg)
            p.drawArc(rect, 90 * 16, span)

        # Valoare
        p.setPen(QColor(TEXT_PRIMARY))
        p.setFont(mono(max(14, side * 0.13), QFont.Weight.Bold))
        p.drawText(QRectF(rect.x(), rect.y() + side * 0.30, side, side * 0.30),
                   Qt.AlignmentFlag.AlignCenter, f"{self.value:.1f}%")

        if self.label:
            p.setPen(self.color)
            p.setFont(mono(7.5, QFont.Weight.Bold, 2))
            p.drawText(QRectF(rect.x(), rect.y() + side * 0.58, side, side * 0.15),
                       Qt.AlignmentFlag.AlignCenter, self.label)
        p.end()


class CoreBars(QWidget):
    """Bare verticale mici, cate una pe nucleu."""

    def __init__(self, color=ACCENT_BLUE, parent=None):
        super().__init__(parent)
        self.color = QColor(color)
        self.values = []
        self.setFixedHeight(46)

    def set_values(self, values):
        self.values = list(values)
        self.update()

    def paintEvent(self, event):
        if not self.values:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        n = len(self.values)
        gap = 4
        label_h = 12
        bar_w = min(34.0, max(4.0, (self.width() - gap * (n - 1)) / n))
        bar_h = self.height() - label_h - 2
        p.setFont(mono(6.5))
        for i, v in enumerate(self.values):
            x = i * (bar_w + gap)
            track = QRectF(x, 0, bar_w, bar_h)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(BORDER_GLOW))
            p.drawRoundedRect(track, 2, 2)

            fill_h = bar_h * max(0.0, min(100.0, v)) / 100.0
            if fill_h > 0.5:
                fr = QRectF(x, bar_h - fill_h, bar_w, fill_h)
                g = QLinearGradient(fr.topLeft(), fr.bottomLeft())
                g.setColorAt(0, self.color.lighter(120))
                g.setColorAt(1, rgba(self.color, 110))
                p.setBrush(QBrush(g))
                p.drawRoundedRect(fr, 2, 2)

            p.setPen(QColor(TEXT_DIM))
            p.drawText(QRectF(x - 4, bar_h + 2, bar_w + 8, label_h),
                       Qt.AlignmentFlag.AlignCenter, str(i))
        p.end()


class HBar(QWidget):
    """Bara orizontala subtire (folosita la VRAM / disk)."""

    def __init__(self, color, height=6, parent=None):
        super().__init__(parent)
        self.color = QColor(color)
        self.value = 0.0
        self.setFixedHeight(height)

    def set_value(self, v):
        self.value = max(0.0, min(100.0, v))
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(0, 0, self.width(), self.height())
        rad = self.height() / 2
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(BORDER_GLOW))
        p.drawRoundedRect(r, rad, rad)
        if self.value > 0:
            fr = QRectF(0, 0, max(self.height(), r.width() * self.value / 100), r.height())
            g = QLinearGradient(fr.topLeft(), fr.topRight())
            g.setColorAt(0, rgba(self.color, 120))
            g.setColorAt(1, self.color)
            p.setBrush(QBrush(g))
            p.drawRoundedRect(fr, rad, rad)
        p.end()


class PercentBarDelegate(QStyledItemDelegate):
    """Celula de tabel cu text procentual + mini bara dedesubt."""

    def __init__(self, color, scale=100.0, parent=None):
        super().__init__(parent)
        self.color = QColor(color)
        self.scale = scale

    def paint(self, painter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.initStyleOption(option, index)
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, QColor(BORDER_GLOW))
        elif option.state & QStyle.StateFlag.State_MouseOver:
            painter.fillRect(option.rect, rgba(ACCENT_BLUE, 14))

        value = index.data(Qt.ItemDataRole.UserRole) or 0.0
        r = option.rect.adjusted(10, 0, -14, 0)

        text_color = self.color if value >= 5 else QColor(TEXT_DIM) if value < 1 else QColor(TEXT_PRIMARY)
        painter.setPen(text_color)
        painter.setFont(mono(9))
        text_w = 56
        painter.drawText(QRectF(r.x(), r.y(), text_w, r.height()),
                         Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
                         f"{value:.1f}%")

        bar = QRectF(r.x() + text_w + 10, r.center().y() - 2, max(10, r.width() - text_w - 10), 4)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(BORDER_GLOW))
        painter.drawRoundedRect(bar, 2, 2)
        frac = max(0.0, min(1.0, value / self.scale))
        if frac > 0:
            painter.setBrush(rgba(self.color, 90 + int(165 * frac)))
            painter.drawRoundedRect(QRectF(bar.x(), bar.y(), max(4, bar.width() * frac), bar.height()), 2, 2)

        # separator rand
        painter.setPen(QPen(rgba(BORDER_GLOW, 160), 1))
        painter.drawLine(option.rect.bottomLeft(), option.rect.bottomRight())
        painter.restore()


class Panel(QFrame):
    """Card cu bara de accent, titlu si zona optionala in dreapta titlului."""

    def __init__(self, title, accent=ACCENT_BLUE, parent=None):
        super().__init__(parent)
        self.setObjectName("panel")
        self.accent = accent
        self.setStyleSheet(f"""
            QFrame#panel {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 {BG_PANEL2}, stop:1 {BG_PANEL});
                border: 1px solid {BORDER_GLOW};
                border-radius: 14px;
            }}
            QFrame#panel:hover {{
                border: 1px solid {css_rgba(accent, 90)};
            }}
            QLabel {{ background: transparent; border: none; }}
        """)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(28)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(0, 0, 0, 140))
        self.setGraphicsEffect(shadow)

        self.layout_ = QVBoxLayout(self)
        self.layout_.setContentsMargins(18, 14, 18, 16)
        self.layout_.setSpacing(10)

        header = QHBoxLayout()
        header.setSpacing(10)
        bar = QFrame()
        bar.setFixedSize(3, 16)
        bar.setStyleSheet(f"background: {accent}; border-radius: 1px; border: none;")
        self.title = QLabel(title)
        self.title.setFont(mono(9.5, QFont.Weight.Bold, 2.2))
        self.title.setStyleSheet(f"color: {TEXT_PRIMARY};")
        header.addWidget(bar)
        header.addWidget(self.title)
        header.addStretch()
        self.header = header
        self.layout_.addLayout(header)

    def add_header_widget(self, w):
        self.header.addWidget(w)


def make_label(text="", color=TEXT_DIM, size=9, weight=QFont.Weight.Normal, spacing=0.0):
    lbl = QLabel(text)
    lbl.setFont(mono(size, weight, spacing))
    lbl.setStyleSheet(f"color: {color}; background: transparent; border: none;")
    return lbl


def make_chip(text, color):
    lbl = QLabel(text)
    lbl.setFont(mono(8, QFont.Weight.Bold, 1))
    lbl.setStyleSheet(f"""
        color: {color};
        background: {css_rgba(color, 22)};
        border: 1px solid {css_rgba(color, 60)};
        border-radius: 9px;
        padding: 2px 9px;
    """)
    return lbl


def stat_block(title, color=TEXT_PRIMARY, value_size=12):
    """Mini bloc: eticheta mica deasupra, valoare dedesubt."""
    box = QVBoxLayout()
    box.setSpacing(2)
    t = make_label(title, TEXT_DIM, 7.5, QFont.Weight.Bold, 1.5)
    v = make_label("—", color, value_size, QFont.Weight.Bold)
    t.setAlignment(Qt.AlignmentFlag.AlignCenter)
    v.setAlignment(Qt.AlignmentFlag.AlignCenter)
    box.addWidget(t)
    box.addWidget(v)
    return box, v


def style_plot(plot):
    plot.setBackground(None)
    plot.setStyleSheet("background: transparent; border: none;")
    plot.hideAxis('bottom')
    plot.hideAxis('left')
    plot.showGrid(x=False, y=True, alpha=0.07)
    plot.setMouseEnabled(x=False, y=False)
    plot.hideButtons()
    plot.setMenuEnabled(False)
    plot.getPlotItem().getViewBox().setDefaultPadding(0.0)


def gradient_brush(hex_color, top_alpha=90):
    g = QLinearGradient(0, 0, 0, 1)
    g.setCoordinateMode(QGradient.CoordinateMode.ObjectMode)
    g.setColorAt(0.0, rgba(hex_color, top_alpha))
    g.setColorAt(1.0, rgba(hex_color, 0))
    return QBrush(g)


# ─── MAIN WINDOW ─────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    HISTORY = 90

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Linux System Monitor")
        self.resize(1400, 900)
        self.setMinimumSize(1100, 760)

        self.setStyleSheet(f"""
            QMainWindow {{ background: {BG_DARK}; }}
            QWidget {{ color: {TEXT_PRIMARY}; }}
            QWidget#central {{
                background: qradialgradient(cx:0.15, cy:0.0, radius:1.2, fx:0.15, fy:0.0,
                            stop:0 #13153a, stop:0.55 {BG_DARK}, stop:1 {BG_DARK});
            }}
            QScrollBar:vertical {{
                background: transparent; width: 6px; margin: 2px;
            }}
            QScrollBar::handle:vertical {{
                background: {css_rgba(ACCENT_BLUE, 120)}; border-radius: 3px; min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{ background: {ACCENT_BLUE}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                height: 0px; background: transparent;
            }}
            QToolTip {{
                background: {BG_PANEL2}; color: {TEXT_PRIMARY};
                border: 1px solid {BORDER_GLOW}; padding: 4px;
            }}
        """)

        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(20, 16, 20, 20)
        outer.setSpacing(14)

        outer.addLayout(self.build_header())

        self.main_layout = QGridLayout()
        self.main_layout.setSpacing(14)
        self.main_layout.setRowStretch(0, 3)
        self.main_layout.setRowStretch(1, 4)
        self.main_layout.setRowStretch(2, 3)
        for col, stretch in enumerate((9, 9, 9, 10, 10)):
            self.main_layout.setColumnStretch(col, stretch)
        outer.addLayout(self.main_layout, 1)

        self.metrics = SystemMetrics()
        self.cpu_history = [0.0] * self.HISTORY
        self.rx_history = [0.0] * self.HISTORY
        self.tx_history = [0.0] * self.HISTORY
        self.x_axis = list(range(self.HISTORY))

        self.init_ui()

        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(1000)
        self.update_clock()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_dashboard)
        self.timer.start(1000)
        self.update_dashboard()

    # ── Header ──────────────────────────────────────────────────────────────
    def build_header(self):
        row = QHBoxLayout()
        row.setSpacing(14)

        logo = QLabel("◆")
        logo.setFont(mono(18, QFont.Weight.Bold))
        logo.setStyleSheet(f"color: {ACCENT_BLUE}; background: transparent;")

        titles = QVBoxLayout()
        titles.setSpacing(0)
        t = make_label("SYSTEM MONITOR", TEXT_PRIMARY, 13, QFont.Weight.Bold, 4)
        self.lbl_subtitle = make_label(f"{socket.gethostname()}  ·  {read_distro_name()}",
                                       TEXT_DIM, 8.5, spacing=0.5)
        titles.addWidget(t)
        titles.addWidget(self.lbl_subtitle)

        row.addWidget(logo)
        row.addLayout(titles)
        row.addStretch()

        self.live_dot = QLabel("●")
        self.live_dot.setFont(mono(9))
        self.live_dot.setStyleSheet(f"color: {ACCENT_GREEN}; background: transparent;")
        live = make_label("LIVE · 1s", ACCENT_GREEN, 8, QFont.Weight.Bold, 1.5)

        self.lbl_clock = make_label("", TEXT_PRIMARY, 15, QFont.Weight.Bold, 1)
        self.lbl_date = make_label("", TEXT_DIM, 8, spacing=1)
        clock_col = QVBoxLayout()
        clock_col.setSpacing(0)
        clock_col.addWidget(self.lbl_clock, alignment=Qt.AlignmentFlag.AlignRight)
        clock_col.addWidget(self.lbl_date, alignment=Qt.AlignmentFlag.AlignRight)

        row.addWidget(self.live_dot)
        row.addWidget(live)
        row.addSpacing(18)
        row.addLayout(clock_col)
        return row

    def update_clock(self):
        now = datetime.now()
        self.lbl_clock.setText(now.strftime("%H:%M:%S"))
        self.lbl_date.setText(now.strftime("%a %d %b %Y").upper())

    # ── UI ──────────────────────────────────────────────────────────────────
    def init_ui(self):
        # ═══ ROW 0 ═══
        # CPU
        self.cpu_panel = Panel("CPU USAGE", ACCENT_BLUE)
        self.lbl_cpu_big = make_label("0.0%", ACCENT_BLUE, 18, QFont.Weight.Bold)
        self.cpu_panel.add_header_widget(self.lbl_cpu_big)

        chips = QHBoxLayout()
        chips.setSpacing(8)
        self.chip_model = make_chip("CPU", ACCENT_BLUE)
        self.chip_cores = make_chip("— CORES", ACCENT_VIOLET)
        self.chip_freq = make_chip("— MHz", ACCENT_GREEN)
        for c in (self.chip_model, self.chip_cores, self.chip_freq):
            chips.addWidget(c)
        chips.addStretch()
        self.cpu_panel.layout_.addLayout(chips)

        self.cpu_graph = pg.PlotWidget()
        style_plot(self.cpu_graph)
        self.cpu_graph.setYRange(0, 100, padding=0)
        self.cpu_graph.setXRange(0, self.HISTORY - 1, padding=0)
        self.cpu_line = self.cpu_graph.plot(pen=pg.mkPen(color=ACCENT_BLUE, width=2), antialias=True)
        self.cpu_line.setFillLevel(0)
        self.cpu_line.setBrush(gradient_brush(ACCENT_BLUE, 110))
        self.cpu_panel.layout_.addWidget(self.cpu_graph, 1)

        self.core_bars = CoreBars(ACCENT_BLUE)
        self.cpu_panel.layout_.addWidget(self.core_bars)
        self.main_layout.addWidget(self.cpu_panel, 0, 0, 1, 3)

        # RAM
        self.ram_panel = Panel("RAM USAGE", ACCENT_VIOLET)
        self.ram_gauge = CircularGauge(ACCENT_VIOLET, "MEMORY")
        self.ram_panel.layout_.addWidget(self.ram_gauge, 1)
        stats = QHBoxLayout()
        b1, self.lbl_ram_used = stat_block("USED", ACCENT_VIOLET)
        b2, self.lbl_ram_free = stat_block("FREE")
        b3, self.lbl_ram_total = stat_block("TOTAL")
        for b in (b1, b2, b3):
            stats.addLayout(b)
        self.ram_panel.layout_.addLayout(stats)
        self.main_layout.addWidget(self.ram_panel, 0, 3)

        # GPU
        self.gpu_panel = Panel("GPU LOAD", ACCENT_BLUE)
        self.gpu_gauge = CircularGauge(ACCENT_BLUE, "GPU LOAD")
        self.gpu_panel.layout_.addWidget(self.gpu_gauge, 1)
        self.lbl_gpu_name = make_label("—", TEXT_PRIMARY, 8.5, QFont.Weight.Bold)
        self.lbl_gpu_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_gpu_name.setWordWrap(True)
        self.gpu_panel.layout_.addWidget(self.lbl_gpu_name)
        vram_row = QHBoxLayout()
        vram_row.addWidget(make_label("VRAM", TEXT_DIM, 7.5, QFont.Weight.Bold, 1.5))
        vram_row.addStretch()
        self.lbl_vram = make_label("0.0 / 0.0 GB", TEXT_DIM, 8)
        vram_row.addWidget(self.lbl_vram)
        self.gpu_panel.layout_.addLayout(vram_row)
        self.vram_bar = HBar(ACCENT_BLUE, 5)
        self.gpu_panel.layout_.addWidget(self.vram_bar)
        self.main_layout.addWidget(self.gpu_panel, 0, 4)

        # ═══ ROW 1 ═══
        # Processes
        self.proc_panel = Panel("ACTIVE PROCESSES", ACCENT_BLUE)
        self.chip_proc = make_chip("TOP 0 · BY CPU", ACCENT_BLUE)
        self.proc_panel.add_header_widget(self.chip_proc)

        self.proc_table = QTableWidget(0, 5)
        self.proc_table.setHorizontalHeaderLabels(["PID", "NAME", "CPU", "RAM", "USER"])
        hh = self.proc_table.horizontalHeader()
        hh.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        hh.setHighlightSections(False)
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.proc_table.setColumnWidth(0, 90)
        self.proc_table.setColumnWidth(4, 120)
        hh.setFont(mono(8, QFont.Weight.Bold, 1.8))
        hh.setStyleSheet(f"""
            QHeaderView {{ background: transparent; border: none; }}
            QHeaderView::section {{
                background: {css_rgba(ACCENT_BLUE, 12)};
                color: {ACCENT_BLUE};
                border: none;
                border-bottom: 1px solid {css_rgba(ACCENT_BLUE, 60)};
                padding: 7px 12px;
            }}
        """)
        self.proc_table.setFont(mono(9))
        self.proc_table.setStyleSheet(f"""
            QTableWidget {{
                background: transparent;
                color: {TEXT_PRIMARY};
                border: none;
                outline: 0;
            }}
            QTableWidget::item {{
                padding: 0px 12px;
                border-bottom: 1px solid {css_rgba(BORDER_GLOW, 160)};
            }}
            QTableWidget::item:hover {{ background: {css_rgba(ACCENT_BLUE, 14)}; }}
            QTableWidget::item:selected {{ background: {BORDER_GLOW}; color: {ACCENT_BLUE}; }}
            QTableCornerButton::section {{ background: transparent; border: none; }}
        """)
        self.proc_table.verticalHeader().setVisible(False)
        self.proc_table.verticalHeader().setDefaultSectionSize(32)
        self.proc_table.setShowGrid(False)
        self.proc_table.setMouseTracking(True)
        self.proc_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.proc_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.proc_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.proc_table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.proc_table.setItemDelegateForColumn(2, PercentBarDelegate(ACCENT_BLUE, 100.0, self.proc_table))
        self.proc_table.setItemDelegateForColumn(3, PercentBarDelegate(ACCENT_VIOLET, 25.0, self.proc_table))
        self.proc_panel.layout_.addWidget(self.proc_table)
        self.main_layout.addWidget(self.proc_panel, 1, 0, 1, 4)

        # Uptime
        self.uptime_panel = Panel("SYSTEM UPTIME", ACCENT_BLUE)
        self.lbl_uptime = QLabel()
        self.lbl_uptime.setTextFormat(Qt.TextFormat.RichText)
        self.lbl_uptime.setFont(mono(22, QFont.Weight.Bold))
        self.lbl_uptime.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_uptime.setStyleSheet(f"color: {ACCENT_BLUE};")
        self.lbl_boot = make_label("", TEXT_DIM, 8, spacing=1)
        self.lbl_boot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.uptime_panel.layout_.addStretch()
        self.uptime_panel.layout_.addWidget(self.lbl_uptime)
        self.uptime_panel.layout_.addWidget(self.lbl_boot)
        self.uptime_panel.layout_.addStretch()

        # System info (kernel etc.)
        self.kernel_panel = Panel("SYSTEM INFO", ACCENT_VIOLET)
        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(10)
        self.info_values = {}
        for r, key in enumerate(("KERNEL", "OS", "ARCH", "CORES")):
            k = make_label(key, TEXT_DIM, 7.5, QFont.Weight.Bold, 1.5)
            v = make_label("—", TEXT_PRIMARY, 9)
            v.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            grid.addWidget(k, r, 0)
            grid.addWidget(v, r, 1)
            self.info_values[key] = v
        self.info_values["OS"].setText(read_distro_name())
        self.info_values["ARCH"].setText(os.uname().machine)
        self.kernel_panel.layout_.addStretch()
        self.kernel_panel.layout_.addLayout(grid)
        self.kernel_panel.layout_.addStretch()

        right_col = QWidget()
        right_col.setStyleSheet("background: transparent;")
        rl = QVBoxLayout(right_col)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(14)
        rl.addWidget(self.uptime_panel)
        rl.addWidget(self.kernel_panel)
        self.main_layout.addWidget(right_col, 1, 4)

        # ═══ ROW 2 ═══
        # Storage
        self.disk_panel = Panel("STORAGE  ·  ROOT /", ACCENT_GREEN)
        self.disk_gauge = CircularGauge(ACCENT_GREEN, "DISK")
        self.disk_gauge.setFixedSize(170, 170)

        disk_info = QVBoxLayout()
        disk_info.setSpacing(12)
        disk_info.addWidget(make_label("ROOT PARTITION", TEXT_DIM, 8, QFont.Weight.Bold, 2))
        self.lbl_disk_big = make_label("— GB", TEXT_PRIMARY, 18, QFont.Weight.Bold)
        disk_info.addWidget(self.lbl_disk_big)
        self.disk_bar = HBar(ACCENT_GREEN, 8)
        self.disk_bar.setMinimumWidth(260)
        disk_info.addWidget(self.disk_bar)
        dstats = QHBoxLayout()
        dstats.setSpacing(24)
        b1, self.lbl_disk_used = stat_block("USED", ACCENT_GREEN, 11)
        b2, self.lbl_disk_free = stat_block("FREE", TEXT_PRIMARY, 11)
        b3, self.lbl_disk_total = stat_block("TOTAL", TEXT_PRIMARY, 11)
        for b in (b1, b2, b3):
            dstats.addLayout(b)
        dstats.addStretch()
        disk_info.addLayout(dstats)

        disk_hz = QHBoxLayout()
        disk_hz.addStretch(1)
        disk_hz.addWidget(self.disk_gauge)
        disk_hz.addSpacing(36)
        disk_hz.addLayout(disk_info, 2)
        disk_hz.addStretch(1)
        self.disk_panel.layout_.addStretch()
        self.disk_panel.layout_.addLayout(disk_hz)
        self.disk_panel.layout_.addStretch()
        self.main_layout.addWidget(self.disk_panel, 2, 0, 1, 3)

        # Network
        self.net_panel = Panel("NETWORK ACTIVITY", ACCENT_GREEN)
        net_stats = QHBoxLayout()
        net_stats.setSpacing(12)
        self.lbl_rx, self.lbl_rx_peak = self._net_card(net_stats, "▼  DOWNLOAD", ACCENT_GREEN)
        self.lbl_tx, self.lbl_tx_peak = self._net_card(net_stats, "▲  UPLOAD", ACCENT_VIOLET)
        self.net_panel.layout_.addLayout(net_stats)

        self.net_graph = pg.PlotWidget()
        style_plot(self.net_graph)
        self.net_graph.setXRange(0, self.HISTORY - 1, padding=0)
        self.net_graph.setMinimumHeight(80)
        self.net_rx_line = self.net_graph.plot(pen=pg.mkPen(color=ACCENT_GREEN, width=2), antialias=True)
        self.net_rx_line.setFillLevel(0)
        self.net_rx_line.setBrush(gradient_brush(ACCENT_GREEN, 70))
        self.net_tx_line = self.net_graph.plot(pen=pg.mkPen(color=ACCENT_VIOLET, width=2), antialias=True)
        self.net_tx_line.setFillLevel(0)
        self.net_tx_line.setBrush(gradient_brush(ACCENT_VIOLET, 70))
        self.net_panel.layout_.addWidget(self.net_graph, 1)
        self.main_layout.addWidget(self.net_panel, 2, 3, 1, 2)

    def _net_card(self, parent_layout, title, color):
        card = QFrame()
        card.setObjectName("netcard")
        card.setStyleSheet(f"""
            QFrame#netcard {{
                background: {css_rgba(color, 14)};
                border: 1px solid {css_rgba(color, 50)};
                border-radius: 10px;
            }}
        """)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(12, 8, 12, 8)
        lay.setSpacing(2)
        top = QHBoxLayout()
        top.addWidget(make_label(title, color, 7.5, QFont.Weight.Bold, 1.5))
        top.addStretch()
        peak = make_label("PEAK —", TEXT_DIM, 7.5)
        top.addWidget(peak)
        val = make_label("0.0 KB/s", TEXT_PRIMARY, 14, QFont.Weight.Bold)
        lay.addLayout(top)
        lay.addWidget(val)
        parent_layout.addWidget(card)
        return val, peak

    # ── Update ──────────────────────────────────────────────────────────────
    @staticmethod
    def fmt_speed(kbps):
        if kbps >= 1024:
            return f"{kbps / 1024:.1f} MB/s"
        return f"{kbps:.1f} KB/s"

    @staticmethod
    def short_cpu_name(model):
        for junk in ("(R)", "(TM)", "CPU", "Processor", "12th Gen", "13th Gen", "14th Gen", "11th Gen"):
            model = model.replace(junk, "")
        return " ".join(model.split())

    def update_dashboard(self):
        monitor_lib.get_system_metrics(ctypes.byref(self.metrics))
        m = self.metrics

        # CPU
        model = m.cpu_model.decode('utf-8', 'replace').strip()
        self.lbl_cpu_big.setText(f"{m.cpu_usage_percent:.1f}%")
        self.chip_model.setText(self.short_cpu_name(model) or "CPU")
        self.chip_model.setToolTip(model)
        self.chip_cores.setText(f"{m.core_count} THREADS")
        self.chip_freq.setText(f"{m.cpu_freq_mhz:.0f} MHz")
        self.cpu_history.append(m.cpu_usage_percent)
        self.cpu_history.pop(0)
        self.cpu_line.setData(self.x_axis, self.cpu_history)
        n_cores = max(0, min(m.core_count, MAX_CORES))
        self.core_bars.set_values([m.cpu_cores_usage[i] for i in range(n_cores)])

        # RAM
        self.ram_gauge.set_value(m.ram_usage_percent)
        self.lbl_ram_used.setText(f"{m.ram_used_gb:.1f} GB")
        self.lbl_ram_free.setText(f"{max(0.0, m.ram_total_gb - m.ram_used_gb):.1f} GB")
        self.lbl_ram_total.setText(f"{m.ram_total_gb:.1f} GB")

        # GPU
        gpu_name = m.gpu_name.decode('utf-8', 'replace').strip()
        self.gpu_gauge.set_value(m.gpu_usage_percent)
        self.lbl_gpu_name.setText(gpu_name.replace("NVIDIA ", ""))
        self.lbl_vram.setText(f"{m.gpu_memory_used_gb:.1f} / {m.gpu_memory_total_gb:.1f} GB")
        vram_pct = 100 * m.gpu_memory_used_gb / m.gpu_memory_total_gb if m.gpu_memory_total_gb else 0
        self.vram_bar.set_value(vram_pct)

        # Disk
        self.disk_gauge.set_value(m.disk_usage_percent)
        free = max(0.0, m.disk_total_gb - m.disk_used_gb)
        self.lbl_disk_big.setText(f"{free:.1f} GB free")
        self.disk_bar.set_value(m.disk_usage_percent)
        self.lbl_disk_used.setText(f"{m.disk_used_gb:.1f} GB")
        self.lbl_disk_free.setText(f"{free:.1f} GB")
        self.lbl_disk_total.setText(f"{m.disk_total_gb:.1f} GB")

        # Uptime
        secs = int(m.uptime_seconds)
        d, rem = divmod(secs, 86400)
        h, rem = divmod(rem, 3600)
        mi, s = divmod(rem, 60)
        unit = f"<span style='color:{TEXT_DIM}; font-size:12pt;'>"
        parts = []
        if d:
            parts.append(f"{d}{unit}d</span>")
        parts.append(f"{h:02d}{unit}h</span>")
        parts.append(f"{mi:02d}{unit}m</span>")
        parts.append(f"{s:02d}{unit}s</span>")
        self.lbl_uptime.setText(" ".join(parts))
        boot = datetime.fromtimestamp(datetime.now().timestamp() - secs)
        self.lbl_boot.setText(f"SINCE {boot.strftime('%d %b, %H:%M').upper()}")

        # System info
        self.info_values["KERNEL"].setText(m.kernel_version.decode('utf-8', 'replace').strip())
        self.info_values["CORES"].setText(str(m.core_count))

        # Network
        rx, tx = m.net_rx_kbps, m.net_tx_kbps
        self.rx_history.append(rx)
        self.rx_history.pop(0)
        self.tx_history.append(tx)
        self.tx_history.pop(0)
        self.lbl_rx.setText(self.fmt_speed(rx))
        self.lbl_tx.setText(self.fmt_speed(tx))
        self.lbl_rx_peak.setText(f"PEAK {self.fmt_speed(max(self.rx_history))}")
        self.lbl_tx_peak.setText(f"PEAK {self.fmt_speed(max(self.tx_history))}")
        max_val = max(max(self.rx_history), max(self.tx_history), 1.0)
        self.net_graph.setYRange(0, max_val * 1.25, padding=0)
        self.net_rx_line.setData(self.x_axis, self.rx_history)
        self.net_tx_line.setData(self.x_axis, self.tx_history)

        # Processes
        count = m.process_count
        self.chip_proc.setText(f"TOP {count} · BY CPU")
        self.proc_table.setRowCount(count)
        for i in range(count):
            proc = m.processes[i]
            pid_item = QTableWidgetItem(str(proc.pid))
            pid_item.setForeground(QColor(TEXT_DIM))
            name_item = QTableWidgetItem(proc.name.decode('utf-8', 'replace').strip())
            name_item.setFont(mono(9, QFont.Weight.Bold))
            cpu_item = QTableWidgetItem()
            cpu_item.setData(Qt.ItemDataRole.UserRole, float(proc.cpu_percent))
            ram_item = QTableWidgetItem()
            ram_item.setData(Qt.ItemDataRole.UserRole, float(proc.ram_percent))
            user = proc.user.decode('utf-8', 'replace').strip()
            user_item = QTableWidgetItem(user)
            user_item.setForeground(QColor(ACCENT_VIOLET if user == "root" else TEXT_DIM))

            for col, item in enumerate((pid_item, name_item, cpu_item, ram_item, user_item)):
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.proc_table.setItem(i, col, item)

        # Puls pe indicatorul LIVE
        self._pulse = not getattr(self, "_pulse", False)
        self.live_dot.setStyleSheet(
            f"color: {ACCENT_GREEN if self._pulse else css_rgba(ACCENT_GREEN, 90)}; background: transparent;")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(mono(9))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())