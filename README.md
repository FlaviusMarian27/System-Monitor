# System-Monitor
Dedicated system for monitoring computer resources.

```text
LinuxSystemMonitor/
│
├── build/                   # Aici se va genera librăria partajată (.so)
│   └── libmonitor.so        # Fișierul compilat din C
│
├── src/                     # Codul sursă
│   ├── backend/             # Tot ce ține de C
│   │   ├── include/         # Header files (.h)
│   │   │   ├── cpu.h
│   │   │   ├── gpu.h
│   │   │   ├── memory.h
│   │   │   └── disk.h
│   │   ├── cpu.c            # Implementare citire /proc/stat
│   │   ├── gpu.c            # Implementare detecție GPU
│   │   ├── memory.c         # Implementare citire RAM
│   │   ├── disk.c           # Implementare statvfs
│   │   └── core.c           # Fișierul principal care leagă funcțiile
│   │
│   └── frontend/            # Tot ce ține de Python
│       ├── assets/          # Icoane, fonturi, imagini (logo-uri)
│       ├── styles/          # Fișiere .qss (CSS pentru Qt) pentru design-ul Neon
│       │   └── dark_theme.qss
│       ├── components/      # Widget-uri refolosibile (ex: un grafic rotund)
│       │   ├── circular_gauge.py
│       │   └── line_chart.py
│       └── main.py          # Punctul de intrare în aplicație
│
├── Makefile                 # Script pentru a compila codul C automat
├── requirements.txt         # Lista librăriilor Python (PyQt6, psutil etc.)
├── run.sh                   # Script simplu bash să compileze și să ruleze totul
└── README.md                # Documentația proiectului

```