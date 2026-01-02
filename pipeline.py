import os
import pickle
import re
from lsi import LSIRetrieval
from docx import Document
from pypdf import PdfReader


class Tokenizer:
    def __init__(self):
        pass

    def tokenize(self,text):
        if not text: 
            return []

        clean_text = re.sub(r'[^a-z0-9]', ' ', text.lower())
        return clean_text.split()
    
class Stopword:
    def __init__(self, file_path='data/tala-stopwords-indonesia.txt'):
        self.daftar_stopword = self._load_stopwords(file_path)

    def _load_stopwords(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Membaca setiap baris, menghapus spasi/newline, dan filter baris kosong
                stopwords = {line.strip() for line in f if line.strip()}
            return stopwords
        except FileNotFoundError:
            print(f"Peringatan: File {file_path} tidak ditemukan. Stopword removal akan kosong.")
            return set()

    def remove(self, tokens):
        return [word for word in tokens if word not in self.daftar_stopword]

class Pipeline:
    def __init__(self):
        self.tokenizer = Tokenizer()
        self.stopword = Stopword('data/tala-stopwords-indonesia.txt')
         
        """
        menggunakan library PyStemmer (Snowball) dengan algoritma stemming porter Bahasa Indonesia 
        yang dikembangkan oleh Fadillah Z Tala.
        Referensi: https://snowballstem.org/algorithms/indonesian/stemmer.html
        """
        import Stemmer
        self.stemmer = Stemmer.Stemmer('indonesian')
        
        # Temporary variabel
        self.file_names = []
        self.raw_contents = []
        self.engine = None

    # menjalankan proses tokenizing,stopword removal dan stemming
    def preprocess(self, teks):
        tokens = self.tokenizer.tokenize(teks)
        clen_tokens = self.stopword.remove(tokens)
        return [self.stemmer.stemWord(k) for k in clen_tokens]

    # method untuk membaca file ekstensi .txt
    def read_txt(self,file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                return content
        except Exception as e:
            print(f"[ERROR] Gagal TXT {file_path}: {e}")
            return ""

    # method untuk membaca file ekstensi .docx
    def read_docx(self, file_path):
        try:
            doc = Document(file_path)
            full_text = []
            for para in doc.paragraphs:
                full_text.append(para.text)
            return '\n'.join(full_text)
        except Exception as e:
            print(f"Error baca DOCX {file_path}: {e}")
            return ""

    # method untuk membaca file ekstensi .pdf
    def read_pdf(self, file_path):
        try:
            reader = PdfReader(file_path)
            full_text = []
            for page in reader.pages:
                # Extract text dan tambahkan spasi/newline
                text = page.extract_text()
                if text:
                    full_text.append(text)
            return '\n'.join(full_text)
        except Exception as e:
            print(f"Error baca PDF {file_path}: {e}")
            return ""

    # method untuk membaca direktori     
    def read_directory(self, folder_path):
            print(f"[*] Membaca file dari folder: '{folder_path}'...")
            
            # Reset data lama jika ada
            self.file_names = []
            self.raw_contents = []

            for root, _, files in os.walk(folder_path):
                for file in sorted(files):
                    file_path = os.path.join(root, file)
                    content = ""
                    
                    # Cek ekstensi dan baca
                    if file.endswith(".txt"):
                        content = self.read_txt(file_path)
                    elif file.endswith(".docx") and not file.startswith("~"):
                        content = self.read_docx(file_path)
                    elif file.endswith(".pdf"):
                        content = self.read_pdf(file_path)
                    
                    # Jika konten valid, simpan
                    if content.strip():
                        self.file_names.append(file)
                        self.raw_contents.append(content)

            print(f"[*] Selesai membaca. Ditemukan {len(self.raw_contents)} dokumen valid.")
        

    def save_model(self, filepath='ir_model.pkl'):
        if not self.engine: return
        print(f"Menyimpan model ke '{filepath}'...")
        data = {
            'engine': self.engine,
            'file_names': self.file_names,
            'raw_contents': self.raw_contents
        }
        try:
            with open(filepath, 'wb') as f:
                pickle.dump(data, f)
            print("Model berhasil disimpan.")
        except Exception as e:
            print(f"Gagal menyimpan model: {e}")

    def load_model(self, filepath='ir_model.pkl'):
        print(f"Memuat model dari '{filepath}'...")
        try:
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
                self.engine = data['engine']
                self.file_names = data['file_names']
                self.raw_contents = data['raw_contents']
            print("Model berhasil dimuat!")
            return True
        except Exception as e:
            print(f"Gagal memuat model: {e}")
            return False

    def run(self, folder_path, num_topics=15, model_path='ir_model.pkl'):
        # 1. Baca Dokumen
        self.read_directory(folder_path)
        
        if not self.raw_contents:
            print("[!] Proses dihentikan karena tidak ada dokumen.")
            return

        # 2. Preprocessing
        print("[*] Memulai Preprocessing (Tokenize -> Stopword -> Stemming)...")
        processed_docs = []
        for content in self.raw_contents:
            result = self.preprocess(content)
            processed_docs.append(result)
        
        print(f"[*] Preprocessing selesai untuk {len(processed_docs)} dokumen.")

        # 3. LSI 
        print("[*] Membangun Model LSI (SVD)...")
        self.engine = LSIRetrieval(processed_docs, num_topics)
        
        # 4. Simpan
        self.save_model(model_path)
        print("[*] Pipeline Selesai!")

    def search(self, query):
        if not self.engine:
            print("Error: Engine belum siap.")
            return []

        print(f"Searching: {query}")
        query_stems = self.preprocess(query)
        return self.engine.display_lsi_details(query_stems)
    

if __name__ == '__main__':
    pipeline = Pipeline()
    pipeline.run("dataset_ir")
