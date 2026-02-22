import sys
import ctypes
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QGridLayout,
                             QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import QTimer, Qt, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QFont
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

# 2. WIDGET PERSONALIZAT: CERCUL NEON (GAUGE)
class CircularGauge(QWidget):
    def __init__(self, color="#7dcfff",title="",parent=None):
        super().__init__(parent)
        self.value = 0.0
        self.color = color
        self.title = title
        self.setMinimumSize(120,120)

    def set_value(self, value):
        self.value = value
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(10,10,self.width() - 20,self.height() - 20)

        #Desenam cercul de fundal(gri inchis)
        pen_bg = QPen(QColor("#1f2335"),12)
        pen_bg.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_bg)
        painter.drawArc(rect,0,360 * 16)

        #desenam arcul de cerc colorat
        pen_fg = QPen(QColor(self.color), 12)
        pen_fg.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_fg)

        start_angle = -90 * 16
        span_angle = int(-(self.value / 100.0) * 360 * 16)
        painter.drawArc(rect, start_angle, span_angle)

        painter.setPen(QColor("#a9b1d6"))
        painter.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, f"{self.value:.1f}%")

        painter.end()

# 3. FEREASTRA PRINCIPALA (UI & GRID)
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Linux System Monitor")
        self.resize(1300, 850)
        self.setStyleSheet("background-color: #1a1b26; color: #a9b1d6;")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.layout = QGridLayout(central_widget)
        self.layout.setContentsMargins(20,20,20,20)
        self.layout.setSpacing(15)

        self.init_ui()

        self.metrics = SystemMetrics()
        self.cpu_history = [0] * 60

        #upgrade timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_dashboard)
        self.timer.setInterval(1000)

    def create_panel(self, title):
        """Functie utilitara pentru a crea o 'cutie' eleganta ca in design"""
        panel = QWidget()
        panel.setStyleSheet("background-color: #24283b; border-radius: 10px;")
        layout = QVBoxLayout(panel)

        lbl_title = QLabel(title)
        lbl_title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        lbl_title.setStyleSheet("color: #c0caf5; padding-bottom: 5px;")
        layout.addWidget(lbl_title)

        return panel, layout

    def init_ui(self):
        #rand 0
        #CPU
        self.cpu_panel, cpu_layout = self.create_panel("CPU Usage")
        self.lbl_cpu_info = QLabel("Loading...")
        self.lbl_cpu_info.setStyleSheet("color: #7aa2f7;")
        cpu_layout.addWidget(self.lbl_cpu_info)

        self.cpu_graph = pg.PlotWidget()
        self.cpu_graph.setBackground('#24283b')
        self.cpu_graph.showGrid(x=False, y=True, alpha=0.1)
        self.cpu_graph.setYRange(0, 100)
        self.cpu_graph.getAxis('bottom').setStyle(showValues=False)
        self.cpu_graph.getAxis('left').setStyle(showValues=False)
        self.cpu_graph.getAxis('left').setPen(pg.mkPen(color='#24283b'))

        pen = pg.mkPen(color='#7dcfff', width=2)
        self.cpu_line = self.cpu_graph.plot(pen=pen)
        self.cpu_line.setBrush(pg.mkBrush(color=(125, 207, 255, 50)))
        self.cpu_line.setFillLevel(0)
        cpu_layout.addWidget(self.cpu_graph)
        self.layout.addWidget(self.cpu_panel, 0, 0, 1, 2)

        #RAM in migloc
        self.ram_panel, ram_layout = self.create_panel("RAM Usage")
        self.ram_gauge = CircularGauge(color="#bb9af7")
        self.lbl_ram_info = QLabel("Loading...")
        self.lbl_ram_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ram_layout.addWidget(self.ram_gauge, alignment=Qt.AlignmentFlag.AlignCenter)
        ram_layout.addWidget(self.lbl_ram_info)
        self.layout.addWidget(self.ram_panel, 0, 2)

        #GPU in dreapta
        self.gpu_panel, gpu_layout = self.create_panel("GPU Load")
        self.gpu_gauge = CircularGauge(color="#7dcfff")
        self.lbl_gpu_info = QLabel("Loading...")
        self.lbl_gpu_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        gpu_layout.addWidget(self.gpu_gauge, alignment=Qt.AlignmentFlag.AlignCenter)
        gpu_layout.addWidget(self.lbl_gpu_info)
        self.layout.addWidget(self.gpu_panel, 0, 3)

        #rand 1
        #procese active
        self.proc_panel, proc_layout = self.create_panel("Active Processes")
        self.proc_table = QTableWidget(0, 5)
        self.proc_table.setHorizontalHeaderLabels(["PID", "Name", "CPU %", "RAM %", "User"])
        self.proc_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.proc_table.horizontalHeader().setStyleSheet("background-color: #1f2335; color: #7aa2f7;")
        self.proc_table.setStyleSheet("""
                    QTableWidget { background-color: #24283b; color: #a9b1d6; border: none; gridline-color: #1f2335; }
                    QTableWidget::item { padding: 5px; }
                """)
        self.proc_table.verticalHeader().setVisible(False)
        proc_layout.addWidget(self.proc_table)
        self.layout.addWidget(self.proc_panel, 1, 0, 1, 3)

        #rand 2
        #storage
        self.disk_panel, disk_layout = self.create_panel("Storage (Root /)")
        self.disk_gauge = CircularGauge(color="#9ece6a")
        self.lbl_disk_info = QLabel("Loading...")
        self.lbl_disk_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        disk_hz = QHBoxLayout()  # Punem elementele orizontal
        disk_hz.addWidget(self.disk_gauge)
        disk_hz.addWidget(self.lbl_disk_info)
        disk_layout.addLayout(disk_hz)
        self.layout.addWidget(self.disk_panel, 2, 0, 1, 3)

        #system info
        self.sys_panel, sys_layout = self.create_panel("System Info")
        self.lbl_uptime = QLabel("Uptime: Loading...")
        self.lbl_kernel = QLabel("Kernel: Loading...")
        self.lbl_uptime.setStyleSheet("font-size: 16px; color: #7aa2f7;")
        self.lbl_kernel.setStyleSheet("font-size: 12px;")
        sys_layout.addWidget(self.lbl_uptime)
        sys_layout.addWidget(self.lbl_kernel)
        sys_layout.addStretch()
        self.layout.addWidget(self.sys_panel, 1, 3, 2, 1)

    def update_dashboard(self):
        #preluam datele din c
        monitor_lib.get_system_metrics(ctypes.byref(self.metrics))

        #update date din cpu
        model = self.metrics.cpu_model.decode('utf-8').strip()
        self.lbl_cpu_info.setText(f"Model: {model} | Freq: {self.metrics.cpu_freq_mhz:.0f} MHz")
        self.cpu_history.append(self.metrics.cpu_usage_percent)
        self.cpu_history.pop(0)
        self.cpu_line.setData(self.cpu_history)

        #update RAM
        self.ram_gauge.set_value(self.metrics.ram_usage_percent)
        self.lbl_ram_info.setText(f"Used: {self.metrics.ram_used_gb:.1f} GB / {self.metrics.ram_total_gb:.1f} GB")

        #update GPU
        gpu_name = self.metrics.gpu_name.decode('utf-8').strip()
        self.gpu_gauge.set_value(self.metrics.gpu_usage_percent)
        self.lbl_gpu_info.setText(
            f"{gpu_name}\nVRAM: {self.metrics.gpu_memory_used_gb:.1f} GB / {self.metrics.gpu_memory_total_gb:.1f} GB")

        #update disk
        self.disk_gauge.set_value(self.metrics.disk_usage_percent)
        self.lbl_disk_info.setText(
            f"Root Partition (/)\nUsed: {self.metrics.disk_used_gb:.1f} GB\nTotal: {self.metrics.disk_total_gb:.1f} GB")

        #sysinfo
        m, s = divmod(self.metrics.uptime_seconds, 60)
        h, m = divmod(m, 60)
        kernel = self.metrics.kernel_version.decode('utf-8').strip()
        self.lbl_uptime.setText(f"Uptime\n{h}h {m}m {s}s")
        self.lbl_kernel.setText(f"Kernel Version\n{kernel}")

        #update process table
        self.proc_table.setRowCount(self.metrics.process_count)
        for i in range(self.metrics.process_count):
            proc = self.metrics.processes[i]
            self.proc_table.setItem(i, 0, QTableWidgetItem(str(proc.pid)))
            self.proc_table.setItem(i, 1, QTableWidgetItem(proc.name.decode('utf-8').strip()))
            self.proc_table.setItem(i, 2, QTableWidgetItem(f"{proc.cpu_percent:.1f}%"))
            self.proc_table.setItem(i, 3, QTableWidgetItem(f"{proc.ram_percent:.1f}%"))
            self.proc_table.setItem(i, 4, QTableWidgetItem(proc.user.decode('utf-8').strip()))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())