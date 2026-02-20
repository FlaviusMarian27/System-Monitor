import sys
import ctypes
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QGridLayout
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont
import pyqtgraph as pg

MAX_CORES = 64
LEN_LINE = 512

class SystemMetrics(ctypes.Structure):
    _fields_ = [
        ("cpu_model", ctypes.c_char * LEN_LINE),
        ("core_count", ctypes.c_int),
        ("cpu_freq_mhz", ctypes.c_double),
        ("cpu_usage_percent", ctypes.c_double),
        ("cpu_cores_usage", ctypes.c_double * MAX_CORES)
    ]

current_dir = os.path.dirname(os.path.abspath(__file__))
lib_path = os.path.abspath(os.path.join(current_dir, '../../build/libmonitor.so'))
monitor_lib = ctypes.CDLL(lib_path)
monitor_lib.get_system_metrics.argtypes = [ctypes.POINTER(SystemMetrics)]
monitor_lib.get_system_metrics.restype = None

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Linux System Monitor Pro")
        self.resize(1200, 800)  # O facem mai mare din start
        self.setStyleSheet("background-color: #1a1b26; color: #a9b1d6;")

        # Structura ferestrei - Folosim Grid Layout acum
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.layout = QGridLayout(central_widget)
        self.layout.setContentsMargins(15, 15, 15, 15)  # O mică margine pe marginea ferestrei
        self.layout.setSpacing(15)  # Spațiu între "pătrate"

        # --- Modulul 1: CPU (Stânga Sus) ---
        # Creăm un "Container" doar pentru zona de CPU
        self.cpu_container = QWidget()
        self.cpu_container.setStyleSheet("background-color: #24283b; border-radius: 10px;")
        cpu_layout = QVBoxLayout(self.cpu_container)

        self.title_label = QLabel("Se citește procesorul...")
        self.title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: #7aa2f7; padding: 5px; border: none;")  # Eliminăm borderul moștenit
        cpu_layout.addWidget(self.title_label)

        # Graficul CPU
        self.graph = pg.PlotWidget()
        self.graph.setBackground('#24283b')  # La fel ca și containerul
        self.graph.showGrid(x=False, y=True, alpha=0.1)
        self.graph.setYRange(0, 100)
        self.graph.getAxis('bottom').setStyle(showValues=False)
        self.graph.getAxis('left').setStyle(showValues=False)
        self.graph.getAxis('left').setPen(pg.mkPen(color='#24283b'))

        # Efectul de Val (Neon)
        pen = pg.mkPen(color='#7dcfff', width=2)
        self.line = self.graph.plot(pen=pen)
        brush = pg.mkBrush(color=(125, 207, 255, 50))
        self.line.setBrush(brush)
        self.line.setFillLevel(0)

        cpu_layout.addWidget(self.graph)

        # Adăugăm Containerul CPU în Grid (Rândul 0, Coloana 0, Ocupă 1 Rând, Ocupă 2 Coloane)
        self.layout.addWidget(self.cpu_container, 0, 0, 1, 2)

        # --- Placeholder pentru RAM (Mijloc Sus) ---
        self.ram_placeholder = QLabel("Modul RAM\n(În curând)")
        self.ram_placeholder.setStyleSheet("background-color: #24283b; border-radius: 10px;")
        self.ram_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Metoda corectă în PyQt6
        self.layout.addWidget(self.ram_placeholder, 0, 2, 1, 1)

        # --- Placeholder pentru GPU (Dreapta Sus) ---
        self.gpu_placeholder = QLabel("Modul GPU\n(În curând)")
        self.gpu_placeholder.setStyleSheet("background-color: #24283b; border-radius: 10px;")
        self.gpu_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.gpu_placeholder, 0, 3, 1, 1)

        # --- Restul logicii rămâne la fel ---
        self.metrics = SystemMetrics()
        self.data_history = [0] * 60

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_dashboard)
        self.timer.start(1000)

    #cerem datele din c
    def update_dashboard(self):
        monitor_lib.get_system_metrics(ctypes.byref(self.metrics))

        model_name = self.metrics.cpu_model.decode('utf-8').strip()
        usage = self.metrics.cpu_usage_percent
        freq = self.metrics.cpu_freq_mhz

        self.title_label.setText(f"CPU: {model_name} | {freq:.2f} MHz | Use: {usage:.1f}%")
        self.data_history.append(usage)
        self.data_history.pop(0)

        self.line.setData(self.data_history) #resetem linia

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())