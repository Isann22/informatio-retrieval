import sys
import os
import platform
import subprocess
from collections import Counter
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLineEdit, QPushButton, QLabel, 
                             QTextBrowser, QProgressBar, QMessageBox, QFileDialog,
                             QStackedWidget, QListWidget, QTableWidget, 
                             QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from pipeline import Pipeline


# --- WORKER THREAD (Agar UI tidak macet saat proses berat) ---
class Worker(QThread):
    status = pyqtSignal(str)
    result_stats = pyqtSignal(list)
    result_search = pyqtSignal(list)

    def __init__(self, ir, task, **kwargs):
        super().__init__()
        self.ir = ir
        self.task = task
        self.data = kwargs

    def run(self):
        # -- Logika Preprocessing --
        if self.task == 'process':
            folder = self.data['folder']
            try:
                self.status.emit("Membangun Index LSI...")
                self.ir.read_directory(folder)
                self.ir.save_model()

                self.status.emit("Menghitung Statistik Kata...")
                all_stems = []
                for c in self.ir.raw_contents:
                    stems = self.ir.preprocess(c)
                    all_stems.extend(stems)
                
                # Ambil 500 kata terbanyak
                stats = Counter(all_stems).most_common(500)
                self.result_stats.emit(stats)
            except Exception as e:
                self.status.emit(f"Error: {e}")

        # -- Logika Searching --
        elif self.task == 'search':
            query = self.data['query']
            if not self.ir.engine: return
            
            q_stems = self.ir.preprocess(query)
            results = self.ir.engine.display_lsi_details(q_stems)
            
            output = []
            for doc_id, score in results:
                fname = self.ir.file_names[doc_id]
                raw = self.ir.raw_contents[doc_id]
                snippet = raw[:200].replace('\n', ' ') + "..."
                output.append((fname, score, snippet))
            
            self.result_search.emit(output)

# --- CLASS GUI UTAMA ---
class GUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ir = Pipeline()
        self.folder_path = ""

        self.setWindowTitle("Sistem IR - Wizard Mode")
        self.setGeometry(100, 100, 900, 650)

        # Container Utama (Stack)
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Setup Halaman
        self.setup_page1_folder()
        self.setup_page2_process()
        self.setup_page3_search()

    # ==========================================
    # HALAMAN 1: PILIH FOLDER & LIST FILE
    # ==========================================
    def setup_page1_folder(self):
        page = QWidget()
        layout = QVBoxLayout()

        # Judul
        lbl_title = QLabel("LANGKAH 1: Pilih Dataset")
        lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
        lbl_title.setAlignment(Qt.AlignCenter)

        # Area Tombol
        h_lay = QHBoxLayout()
        self.btn_browse = QPushButton("Buka Folder")
        self.btn_browse.setFixedHeight(40)
        self.btn_browse.clicked.connect(self.action_browse)
        
        self.lbl_path = QLabel("Belum ada folder dipilih")
        self.lbl_path.setStyleSheet("border: 1px solid #ccc; padding: 5px; background: #fff;")
        
        h_lay.addWidget(self.btn_browse)
        h_lay.addWidget(self.lbl_path)

        # List File Viewer
        self.list_files = QListWidget()
        
        # Tombol Lanjut
        self.btn_next_1 = QPushButton("Lanjut ke Preprocessing >>")
        self.btn_next_1.setFixedHeight(45)
        self.btn_next_1.setEnabled(False) # Mati sebelum pilih folder
        self.btn_next_1.clicked.connect(lambda: self.stack.setCurrentIndex(1))

        layout.addWidget(lbl_title)
        layout.addLayout(h_lay)
        layout.addWidget(QLabel("Daftar File:"))
        layout.addWidget(self.list_files)
        layout.addWidget(self.btn_next_1)
        
        page.setLayout(layout)
        self.stack.addWidget(page)

    # ==========================================
    # HALAMAN 2: PREPROCESSING & STATISTIK
    # ==========================================
    def setup_page2_process(self):
        page = QWidget()
        layout = QVBoxLayout()

        lbl_title = QLabel("LANGKAH 2: Preprocessing & Statistik")
        lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
        lbl_title.setAlignment(Qt.AlignCenter)

        # Tombol Mulai
        self.btn_start_process = QPushButton("Mulai Proses (Indexing & Stemming)")
        self.btn_start_process.setFixedHeight(50)
        self.btn_start_process.clicked.connect(self.action_process)

        # Progress & Status
        self.pbar = QProgressBar()
        self.pbar.setVisible(False)
        self.lbl_process_status = QLabel("Klik tombol di atas untuk memulai.")
        self.lbl_process_status.setAlignment(Qt.AlignCenter)

        # Tabel Statistik
        self.table_stats = QTableWidget()
        self.table_stats.setColumnCount(2)
        self.table_stats.setHorizontalHeaderLabels(["Kata Dasar", "Frekuensi"])
        self.table_stats.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Tombol Navigasi
        h_nav = QHBoxLayout()
        btn_back = QPushButton("<< Kembali")
        btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        
        self.btn_next_2 = QPushButton("Lanjut ke Pencarian >>")
        self.btn_next_2.setFixedHeight(45)
        self.btn_next_2.setEnabled(False) # Mati sebelum proses selesai
        self.btn_next_2.clicked.connect(lambda: self.stack.setCurrentIndex(2))

        h_nav.addWidget(btn_back)
        h_nav.addWidget(self.btn_next_2)

        layout.addWidget(lbl_title)
        layout.addWidget(self.btn_start_process)
        layout.addWidget(self.lbl_process_status)
        layout.addWidget(self.pbar)
        layout.addWidget(self.table_stats)
        layout.addLayout(h_nav)

        page.setLayout(layout)
        self.stack.addWidget(page)

    # ==========================================
    # HALAMAN 3: PENCARIAN (SEARCHING)
    # ==========================================
    def setup_page3_search(self):
        page = QWidget()
        layout = QVBoxLayout()

        lbl_title = QLabel("LANGKAH 3: Pencarian Dokumen")
        lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
        lbl_title.setAlignment(Qt.AlignCenter)

        # Input Search
        h_search = QHBoxLayout()
        self.input_query = QLineEdit()
        self.input_query.setPlaceholderText("Masukkan kata kunci...")
        self.input_query.setFixedHeight(40)
        self.input_query.returnPressed.connect(self.action_search)
        
        btn_cari = QPushButton("Cari")
        btn_cari.setFixedHeight(40)
        btn_cari.clicked.connect(self.action_search)

        h_search.addWidget(self.input_query)
        h_search.addWidget(btn_cari)

        # Hasil
        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(False)
        self.browser.anchorClicked.connect(self.action_open_file)

        # Tombol Reset
        btn_reset = QPushButton("<< Cari Folder Baru (Reset)")
        btn_reset.clicked.connect(self.action_reset)

        layout.addWidget(lbl_title)
        layout.addLayout(h_search)
        layout.addWidget(self.browser)
        layout.addWidget(btn_reset)

        page.setLayout(layout)
        self.stack.addWidget(page)

    # ==========================================
    # LOGIKA APLIKASI
    # ==========================================

    # --- Page 1 Logic ---
    def action_browse(self):
        path = QFileDialog.getExistingDirectory(self, "Pilih Folder")
        if path:
            self.folder_path = path
            self.lbl_path.setText(path)
            self.scan_files_visual(path)
            self.btn_next_1.setEnabled(True) # Buka kunci tombol lanjut

    def scan_files_visual(self, folder):
        # Menampilkan list file tanpa proses berat (hanya nama)
        self.list_files.clear()
        for root, dirs, files in os.walk(folder):
            for f in files:
                if f.endswith(('.txt', '.docx', '.pdf')):
                    parent = os.path.basename(root).upper()
                    self.list_files.addItem(f"[{parent}] {f}")

    # --- Page 2 Logic ---
    def action_process(self):
        self.btn_start_process.setEnabled(False)
        self.btn_next_2.setEnabled(False)
        self.pbar.setVisible(True)
        self.pbar.setRange(0, 0) # Infinite loading
        
        # Jalankan Thread
        self.worker = Worker(self.ir, 'process', folder=self.folder_path)
        self.worker.status.connect(lambda s: self.lbl_process_status.setText(s))
        self.worker.result_stats.connect(self.finish_process)
        self.worker.start()

    def finish_process(self, stats):
        self.pbar.setVisible(False)
        self.lbl_process_status.setText("Selesai. Data siap dicari.")
        self.btn_next_2.setEnabled(True) # Buka kunci tombol lanjut
        self.btn_start_process.setEnabled(True)

        # Isi Tabel
        self.table_stats.setRowCount(len(stats))
        for row, (kata, jumlah) in enumerate(stats):
            self.table_stats.setItem(row, 0, QTableWidgetItem(kata))
            self.table_stats.setItem(row, 1, QTableWidgetItem(str(jumlah)))

    # --- Page 3 Logic ---
    def action_search(self):
        q = self.input_query.text().strip()
        if not q: return
        
        self.browser.setText("Mencari...")
        
        # Jalankan Thread Search
        self.worker = Worker(self.ir, 'search', query=q)
        self.worker.result_search.connect(self.display_results)
        self.worker.start()

    def display_results(self, data):
        if not data:
            self.browser.setHtml("<h3>Tidak ditemukan.</h3>")
            return

        html = ""
        for i, (fname, score, snippet) in enumerate(data):
            html += f"""
            <div style='margin-bottom:15px; border-bottom:1px solid #ccc;'>
                <b>#{i+1}</b> <span style='color:green'>Score: {score:.4f}</span><br>
                <a href="{fname}" style='font-size:14px; text-decoration:none; color:blue;'>{fname}</a>
                <p style='color:#666;'>{snippet}</p>
            </div>
            """
        self.browser.setHtml(html)

    def action_open_file(self, url):
        # Fungsi buka file standard
        filename = url.toString()
        paths = [
            os.path.join(self.folder_path, filename),
            os.path.join(self.folder_path, 'txt', filename),
            os.path.join(self.folder_path, 'docx', filename),
            os.path.join(self.folder_path, 'pdf', filename)
        ]
        for p in paths:
            if os.path.exists(p):
                if platform.system() == 'Windows': os.startfile(p)
                elif platform.system() == 'Darwin': subprocess.call(('open', p))
                else: subprocess.call(('xdg-open', p))
                return
        QMessageBox.warning(self, "Error", "File fisik tidak ditemukan.")

    def action_reset(self):
        # Reset ke halaman 1
        self.stack.setCurrentIndex(0)
        self.list_files.clear()
        self.table_stats.setRowCount(0)
        self.browser.clear()
        self.input_query.clear()
        self.btn_next_1.setEnabled(False)
        self.btn_next_2.setEnabled(False)
        self.lbl_path.setText("Belum ada folder dipilih")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    font = app.font()
    font.setPointSize(10)
    app.setFont(font)
    window = GUI()
    window.show()
    sys.exit(app.exec_())