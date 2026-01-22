import sys
import os
import yt_dlp
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QLineEdit, QPushButton, QLabel, QComboBox, 
                             QMessageBox, QProgressBar, QFileDialog, QHBoxLayout)
from PySide6.QtCore import Qt, QThread, Signal

class DownloadThread(QThread):
    progress_signal = Signal(float)
    finished_signal = Signal(bool, str)

    def __init__(self, url, opts):
        super().__init__()
        self.url = url
        self.opts = opts

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            p = d.get('_percent_str', '0%').replace('%','')
            try:
                self.progress_signal.emit(float(p))
            except ValueError:
                pass

    def run(self):
        try:
            self.opts['progress_hooks'] = [self.progress_hook]
            with yt_dlp.YoutubeDL(self.opts) as ydl:
                ydl.download([self.url])
            self.finished_signal.emit(True, "¡Descarga completada con éxito!")
        except Exception as e:
            self.finished_signal.emit(False, str(e))

class ModernDownloader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyDownloader Pro")
        self.setFixedSize(500, 380)
        self.save_path = os.path.expanduser("~") # Ruta por defecto: Carpeta de usuario
        
        # Estilos generales
        self.setStyleSheet("""
            QMainWindow { background-color: #ffffff; }
            QLabel { color: #2c3e50; font-size: 13px; font-weight: 500; }
            QLineEdit { padding: 10px; border: 1px solid #dcdde1; border-radius: 6px; background: #f9f9f9; }
            QPushButton#mainBtn { background-color: #e74c3c; color: white; border-radius: 8px; padding: 12px; font-weight: bold; }
            QPushButton#mainBtn:hover { background-color: #c0392b; }
            QPushButton#pathBtn { background-color: #7f8c8d; color: white; border-radius: 4px; padding: 5px; font-size: 11px; }
        """)

        layout = QVBoxLayout()
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # UI
        layout.addWidget(QLabel("URL del Video de YouTube:"))
        self.url_input = QLineEdit()
        layout.addWidget(self.url_input)

        # Selector de carpeta
        layout.addWidget(QLabel("Guardar en:"))
        path_layout = QHBoxLayout()
        self.path_label = QLineEdit(self.save_path)
        self.path_label.setReadOnly(True)
        self.btn_browse = QPushButton("Cambiar...")
        self.btn_browse.setObjectName("pathBtn")
        self.btn_browse.clicked.connect(self.choose_directory)
        path_layout.addWidget(self.path_label)
        path_layout.addWidget(self.btn_browse)
        layout.addLayout(path_layout)

        layout.addWidget(QLabel("Formato de salida:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Video + Audio (Mejor calidad)", "Solo Audio (MP3)", "Solo Video (Sin audio)"])
        layout.addWidget(self.type_combo)

        layout.addStretch()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("QProgressBar { height: 15px; text-align: center; }")
        layout.addWidget(self.progress_bar)

        self.btn_download = QPushButton("DESCARGAR AHORA")
        self.btn_download.setObjectName("mainBtn")
        self.btn_download.clicked.connect(self.start_download)
        layout.addWidget(self.btn_download)

    def choose_directory(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta de destino", self.save_path)
        if folder:
            self.save_path = folder
            self.path_label.setText(folder)

    def start_download(self):
        url = self.url_input.text().strip()
        if not url:
            return QMessageBox.warning(self, "Error", "Pega un enlace primero")

        # Configuración de ruta y nombre de archivo
        ydl_opts = {
            'outtmpl': f'{self.save_path}/%(title)s.%(ext)s',
        }

        option = self.type_combo.currentIndex()
        if option == 1: # MP3
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}]
            })
        elif option == 2: # Solo Video
            ydl_opts['format'] = 'bestvideo'
        else: # Video + Audio
            ydl_opts['format'] = 'bestvideo+bestaudio/best'

        self.btn_download.setEnabled(False)
        self.thread = DownloadThread(url, ydl_opts)
        self.thread.progress_signal.connect(self.progress_bar.setValue)
        self.thread.finished_signal.connect(self.on_finished)
        self.thread.start()

    def on_finished(self, success, message):
        self.btn_download.setEnabled(True)
        if success:
            QMessageBox.information(self, "Completado", message)
            self.progress_bar.setValue(0)
        else:
            QMessageBox.critical(self, "Error", f"Ocurrió un problema: {message}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ModernDownloader()
    window.show()
    sys.exit(app.exec())