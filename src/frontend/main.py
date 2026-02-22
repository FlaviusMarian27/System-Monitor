import sys
import ctypes
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QGridLayout,
                             QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import QTimer, Qt, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QLinearGradient, QConicalGradient, QRadialGradient, QBrush
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
        ("processes", ProcessData * MAX_PROCESSES)
    ]

current_dir = os.path.dirname(os.path.abspath(__file__))
lib_path = os.path.abspath(os.path.join(current_dir, '../../build/libmonitor.so'))
monitor_lib = ctypes.CDLL(lib_path)
monitor_lib.get_system_metrics.argtypes = [ctypes.POINTER(SystemMetrics)]
monitor_lib.get_system_metrics.restype = None


# ─── COLOR PALETTE ───────────────────────────────────────────────────────────
BG_DARK      = "#0d0e1a"   # main background - deep navy black
BG_PANEL     = "#12132a"   # panel background - slightly lighter
BG_PANEL2    = "#161830"   # alternate panel color used for table headers
ACCENT_BLUE  = "#4db8ff"   # electric blue accent - used for CPU and highlights
ACCENT_VIOLET= "#9d7ff5"   # soft violet accent - used for RAM
ACCENT_GREEN = "#4dffb4"   # neon green accent - used for disk storage
TEXT_PRIMARY = "#e2e8ff"   # primary text color - light blue-white
TEXT_DIM     = "#5a6080"   # secondary/dimmed text - muted blue-grey
BORDER_GLOW  = "#1e2045"   # subtle panel border color


class CircularGauge(QWidget):
    """Circular gauge with a double ring: background track + neon glowing arc."""

    def __init__(self, color="#4db8ff", label="", parent=None):
        super().__init__(parent)
        self.value = 0.0
        self.color = QColor(color)
        self.label = label
        self.setMinimumSize(140, 140)

    def set_value(self, value):
        self.value = value
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        margin = 18
        side = min(w, h) - margin * 2
        x = (w - side) / 2
        y = (h - side) / 2
        rect = QRectF(x, y, side, side)

        # ── Background track ring ──────────────────────────────────────────
        pen_track = QPen(QColor(BORDER_GLOW), 14)
        pen_track.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_track)
        painter.drawArc(rect, 0, 360 * 16)

        # ── Foreground value arc ───────────────────────────────────────────
        ring_color = QColor(self.color)
        pen_fg = QPen(ring_color, 10)
        pen_fg.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_fg)
        start_angle = 90 * 16          # arc starts from the top
        span_angle  = int(-(self.value / 100.0) * 360 * 16)
        painter.drawArc(rect, start_angle, span_angle)

        # ── Glow effect: wider semi-transparent arc drawn on top ──────────
        glow_color = QColor(self.color)
        glow_color.setAlpha(55)
        pen_glow = QPen(glow_color, 20)
        pen_glow.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_glow)
        painter.drawArc(rect, start_angle, span_angle)

        # ── Centered text: percentage value ───────────────────────────────
        painter.setPen(QColor(TEXT_PRIMARY))
        font_val = QFont("Consolas", 17, QFont.Weight.Bold)
        painter.setFont(font_val)
        text_rect = QRectF(x, y + side * 0.28, side, side * 0.35)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, f"{self.value:.1f}%")

        # ── Small label below the percentage ──────────────────────────────
        if self.label:
            painter.setPen(QColor(TEXT_DIM))
            font_lbl = QFont("Consolas", 8)
            painter.setFont(font_lbl)
            lbl_rect = QRectF(x, y + side * 0.58, side, side * 0.25)
            painter.drawText(lbl_rect, Qt.AlignmentFlag.AlignCenter, self.label)

        painter.end()


# ─── MAIN WINDOW ─────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Linux System Monitor")
        self.resize(1300, 850)

        # Global stylesheet - deep dark navy theme
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background-color: {BG_DARK};
                color: {TEXT_PRIMARY};
                font-family: 'Consolas', monospace;
            }}
            QScrollBar:vertical {{
                background: {BG_PANEL};
                width: 6px;
                border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: {ACCENT_BLUE};
                border-radius: 3px;
                min-height: 20px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QGridLayout(central_widget)
        self.main_layout.setContentsMargins(16, 16, 16, 16)
        self.main_layout.setSpacing(12)

        # Row stretch: row 1 (processes) gets more vertical space than rows 0 and 2
        self.main_layout.setRowStretch(0, 3)
        self.main_layout.setRowStretch(1, 4)
        self.main_layout.setRowStretch(2, 2)

        self.init_ui()

        self.metrics = SystemMetrics()
        self.cpu_history = [0.0] * 60

        # Refresh timer - updates all widgets every second
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_dashboard)
        self.timer.start(1000)

    def create_panel(self, title, accent_color=ACCENT_BLUE):
        """Helper to create a styled card panel with a colored dot title."""
        panel = QWidget()
        panel.setStyleSheet(f"""
            QWidget {{
                background-color: {BG_PANEL};
                border-radius: 12px;
                border: 1px solid {BORDER_GLOW};
            }}
        """)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(14, 10, 14, 14)
        layout.setSpacing(8)

        # Title row: colored dot + uppercase label
        title_row = QHBoxLayout()
        dot = QLabel("●")
        dot.setStyleSheet(f"color: {accent_color}; font-size: 10px; border: none; background: transparent;")
        dot.setFixedWidth(16)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(f"""
            color: {TEXT_PRIMARY};
            font-size: 11px;
            font-weight: bold;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            border: none;
            background: transparent;
        """)

        title_row.addWidget(dot)
        title_row.addWidget(lbl_title)
        title_row.addStretch()
        layout.addLayout(title_row)

        # Thin separator line below the title
        sep = QWidget()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {BORDER_GLOW}; border: none;")
        layout.addWidget(sep)

        return panel, layout

    def make_info_label(self, text="Loading...", color=TEXT_DIM, size=9):
        """Helper to create a simple styled info label."""
        lbl = QLabel(text)
        lbl.setStyleSheet(f"""
            color: {color};
            font-size: {size}px;
            background: transparent;
            border: none;
        """)
        return lbl

    def init_ui(self):
        # ═══ ROW 0 ═════════════════════════════════════════════════════════

        # 1. CPU Usage panel - spans columns 0-1
        self.cpu_panel, cpu_layout = self.create_panel("CPU USAGE", ACCENT_BLUE)
        self.lbl_cpu_info = self.make_info_label(color=ACCENT_BLUE, size=9)
        cpu_layout.addWidget(self.lbl_cpu_info)

        # CPU graph using pyqtgraph
        self.cpu_graph = pg.PlotWidget()
        self.cpu_graph.setBackground(BG_PANEL)
        self.cpu_graph.showGrid(x=False, y=True, alpha=0.06)
        self.cpu_graph.setYRange(0, 100)
        self.cpu_graph.getAxis('bottom').setStyle(showValues=False)
        self.cpu_graph.getAxis('left').setStyle(showValues=False)
        self.cpu_graph.getAxis('bottom').setPen(pg.mkPen(color=BORDER_GLOW))
        self.cpu_graph.getAxis('left').setPen(pg.mkPen(color=BORDER_GLOW))
        self.cpu_graph.setStyleSheet("border: none;")

        # Line plot with a blue filled area below
        pen = pg.mkPen(color=ACCENT_BLUE, width=2)
        self.cpu_line = self.cpu_graph.plot(pen=pen, antialias=True)
        self.cpu_line.setFillLevel(0)
        self.cpu_line.setBrush(pg.mkBrush(color=(30, 100, 200, 60)))
        cpu_layout.addWidget(self.cpu_graph)
        self.main_layout.addWidget(self.cpu_panel, 0, 0, 1, 2)

        # 2. RAM Usage panel
        self.ram_panel, ram_layout = self.create_panel("RAM USAGE", ACCENT_VIOLET)
        self.ram_gauge = CircularGauge(color=ACCENT_VIOLET, label="MEMORY")
        self.lbl_ram_info = self.make_info_label(color=TEXT_DIM, size=9)
        self.lbl_ram_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ram_layout.addWidget(self.ram_gauge, alignment=Qt.AlignmentFlag.AlignCenter)
        ram_layout.addWidget(self.lbl_ram_info)
        self.main_layout.addWidget(self.ram_panel, 0, 2)

        # 3. GPU Load panel
        self.gpu_panel, gpu_layout = self.create_panel("GPU LOAD", ACCENT_BLUE)
        self.gpu_gauge = CircularGauge(color=ACCENT_BLUE, label="GPU LOAD")
        self.lbl_gpu_info = self.make_info_label(color=TEXT_DIM, size=9)
        self.lbl_gpu_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_gpu_info.setWordWrap(True)
        gpu_layout.addWidget(self.gpu_gauge, alignment=Qt.AlignmentFlag.AlignCenter)
        gpu_layout.addWidget(self.lbl_gpu_info)
        self.main_layout.addWidget(self.gpu_panel, 0, 3)

        # ═══ ROW 1 ═════════════════════════════════════════════════════════

        # 4. Active Processes panel - spans columns 0-2
        self.proc_panel, proc_layout = self.create_panel("ACTIVE PROCESSES", ACCENT_BLUE)
        self.proc_table = QTableWidget(0, 5)
        self.proc_table.setHorizontalHeaderLabels(["PID", "Name", "CPU %", "RAM %", "User"])
        self.proc_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.proc_table.horizontalHeader().setStyleSheet(f"""
            QHeaderView::section {{
                background-color: {BG_PANEL2};
                color: {ACCENT_BLUE};
                border: none;
                border-bottom: 1px solid {BORDER_GLOW};
                padding: 5px;
                font-size: 9px;
                font-weight: bold;
                letter-spacing: 1px;
            }}
        """)
        self.proc_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {BG_PANEL};
                color: {TEXT_PRIMARY};
                border: none;
                gridline-color: transparent;
                font-size: 10px;
                selection-background-color: {BORDER_GLOW};
            }}
            QTableWidget::item {{
                padding: 5px 8px;
                border-bottom: 1px solid {BORDER_GLOW};
                background: transparent;
            }}
            QTableWidget::item:selected {{
                background-color: {BORDER_GLOW};
                color: {ACCENT_BLUE};
            }}
        """)
        self.proc_table.verticalHeader().setVisible(False)
        self.proc_table.setShowGrid(False)
        self.proc_table.setAlternatingRowColors(False)
        self.proc_table.verticalHeader().setDefaultSectionSize(28)  # compact row height ~28px fits 8-10 rows
        proc_layout.addWidget(self.proc_table)
        self.main_layout.addWidget(self.proc_panel, 1, 0, 1, 3)

        # 5. System Uptime panel - column 3, top half
        self.uptime_panel, uptime_layout = self.create_panel("SYSTEM UPTIME", ACCENT_BLUE)
        self.lbl_uptime = QLabel("Loading...")
        self.lbl_uptime.setStyleSheet(f"""
            font-size: 22px;
            color: {ACCENT_BLUE};
            font-weight: bold;
            background: transparent;
            border: none;
            font-family: 'Consolas', monospace;
        """)
        self.lbl_uptime.setAlignment(Qt.AlignmentFlag.AlignCenter)
        uptime_layout.addStretch()
        uptime_layout.addWidget(self.lbl_uptime)
        uptime_layout.addStretch()

        # 6. Kernel Version panel - column 3, bottom half
        self.kernel_panel, kernel_layout = self.create_panel("KERNEL VERSION", ACCENT_VIOLET)
        self.lbl_kernel = QLabel("Loading...")
        self.lbl_kernel.setStyleSheet(f"""
            font-size: 11px;
            color: {TEXT_PRIMARY};
            background: transparent;
            border: none;
            font-family: 'Consolas', monospace;
        """)
        self.lbl_kernel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_kernel.setWordWrap(True)
        kernel_layout.addStretch()
        kernel_layout.addWidget(self.lbl_kernel)
        kernel_layout.addStretch()

        # Stack both panels vertically inside a transparent container in column 3
        right_col_widget = QWidget()
        right_col_widget.setStyleSheet("background: transparent; border: none;")
        right_col_layout = QVBoxLayout(right_col_widget)
        right_col_layout.setContentsMargins(0, 0, 0, 0)
        right_col_layout.setSpacing(12)
        right_col_layout.addWidget(self.uptime_panel)
        right_col_layout.addWidget(self.kernel_panel)
        self.main_layout.addWidget(right_col_widget, 1, 3)

        # ═══ ROW 2 ═════════════════════════════════════════════════════════

        # 7. Storage panel - spans all 4 columns
        self.disk_panel, disk_layout = self.create_panel("STORAGE (ROOT /)", ACCENT_GREEN)
        self.disk_gauge = CircularGauge(color=ACCENT_GREEN, label="DISK")
        self.lbl_disk_info = self.make_info_label(color=TEXT_DIM, size=10)
        self.lbl_disk_info.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.lbl_disk_info.setStyleSheet(f"""
            color: {TEXT_DIM};
            font-size: 11px;
            line-height: 1.8;
            background: transparent;
            border: none;
            font-family: 'Consolas', monospace;
        """)

        disk_hz = QHBoxLayout()
        disk_hz.addStretch()
        disk_hz.addWidget(self.disk_gauge)
        disk_hz.addSpacing(30)
        disk_hz.addWidget(self.lbl_disk_info)
        disk_hz.addStretch()
        disk_layout.addLayout(disk_hz)
        self.main_layout.addWidget(self.disk_panel, 2, 0, 1, 4)

    def update_dashboard(self):
        """Fetch fresh metrics from the C library and update all widgets."""
        monitor_lib.get_system_metrics(ctypes.byref(self.metrics))

        # Update CPU info label and graph history
        model = self.metrics.cpu_model.decode('utf-8').strip()
        self.lbl_cpu_info.setText(
            f"Model: {model}   |   Freq: {self.metrics.cpu_freq_mhz:.0f} MHz   |   "
            f"Usage: {self.metrics.cpu_usage_percent:.1f}%"
        )
        self.cpu_history.append(self.metrics.cpu_usage_percent)
        self.cpu_history.pop(0)
        self.cpu_line.setData(self.cpu_history)

        # Update RAM gauge and info label
        self.ram_gauge.set_value(self.metrics.ram_usage_percent)
        self.lbl_ram_info.setText(
            f"{self.metrics.ram_used_gb:.1f} GB  /  {self.metrics.ram_total_gb:.1f} GB"
        )

        # Update GPU gauge and VRAM info
        gpu_name = self.metrics.gpu_name.decode('utf-8').strip()
        self.gpu_gauge.set_value(self.metrics.gpu_usage_percent)
        self.lbl_gpu_info.setText(
            f"{gpu_name}\nVRAM: {self.metrics.gpu_memory_used_gb:.1f} / {self.metrics.gpu_memory_total_gb:.1f} GB"
        )

        # Update disk gauge and partition info
        self.disk_gauge.set_value(self.metrics.disk_usage_percent)
        self.lbl_disk_info.setText(
            f"Root Partition  (/)\n\n"
            f"Used:   {self.metrics.disk_used_gb:.1f} GB\n"
            f"Total:  {self.metrics.disk_total_gb:.1f} GB"
        )

        # Update uptime display (convert seconds to h/m/s)
        m, s = divmod(self.metrics.uptime_seconds, 60)
        h, m = divmod(m, 60)
        self.lbl_uptime.setText(f"{h}h {m}m {s}s")

        # Update kernel version label
        kernel = self.metrics.kernel_version.decode('utf-8').strip()
        self.lbl_kernel.setText(kernel)

        # Update process table rows
        self.proc_table.setRowCount(self.metrics.process_count)
        for i in range(self.metrics.process_count):
            proc = self.metrics.processes[i]

            pid_item  = QTableWidgetItem(str(proc.pid))
            name_item = QTableWidgetItem(proc.name.decode('utf-8').strip())
            cpu_item  = QTableWidgetItem(f"{proc.cpu_percent:.1f}%")
            ram_item  = QTableWidgetItem(f"{proc.ram_percent:.1f}%")
            user_item = QTableWidgetItem(proc.user.decode('utf-8').strip())

            # Color-code CPU% based on load level
            if proc.cpu_percent > 20:
                cpu_item.setForeground(QColor(ACCENT_BLUE))
            elif proc.cpu_percent > 5:
                cpu_item.setForeground(QColor(ACCENT_VIOLET))
            else:
                cpu_item.setForeground(QColor(TEXT_DIM))

            # Make all cells read-only
            for item in [pid_item, name_item, cpu_item, ram_item, user_item]:
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

            self.proc_table.setItem(i, 0, pid_item)
            self.proc_table.setItem(i, 1, name_item)
            self.proc_table.setItem(i, 2, cpu_item)
            self.proc_table.setItem(i, 3, ram_item)
            self.proc_table.setItem(i, 4, user_item)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())