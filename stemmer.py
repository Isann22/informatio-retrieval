
class Stemmer():
    
    # Constants untuk Flags 
    REMOVED_KE = 'removed_ke'
    REMOVED_PENG = 'removed_peng'
    REMOVED_DI = 'removed_di'
    REMOVED_MENG = 'removed_meng'
    REMOVED_TER = 'removed_ter'
    REMOVED_BER = 'removed_ber'
    REMOVED_PE = 'removed_pe'
    
    def __init__(self):
        self.num_syllables = 0
        self.stem_derivational = True
        self.flags = set()
        self.word = ""

    def stem(self, word):
        self.flags = set()
        self.word = word
        self._update_syllables()
        
        # 1. Hapus Partikel (lah, kah, pun)
        if self.num_syllables > 2:
            self._remove_particle()
            
        # 2. Hapus Possessive Pronoun (ku, mu, nya)
        if self.num_syllables > 2:
            self._remove_possessive_pronoun()
            
        # 3. Masuk ke logika utama (Prefix First)
        if self.stem_derivational:
            self._stem_derivational()
        
        return self.word
    
    def _update_syllables(self):
        "Hitung ulang jumlah suku kata (vokal)"
        self.num_syllables = len([c for c in self.word if self._is_vowel(c)])

    def _is_vowel(self, letter):
        return letter in ['a', 'e', 'i', 'o', 'u']
    
    def _remove_particle(self):
        if self.word.endswith('kah') or self.word.endswith('lah') or self.word.endswith('pun'):
            self.word = self.word[:-3]
            self._update_syllables()
            
    def _remove_possessive_pronoun(self):
        if self.word.endswith('ku') or self.word.endswith('mu'):
            self.word = self.word[:-2]
            self._update_syllables()
        elif self.word.endswith('nya'):
            self.word = self.word[:-3]
            self._update_syllables()

    def _stem_derivational(self):
        old_length = len(self.word)
        
        # --- LANGKAH 1: Cek Prefix Orde Pertama (Meng, Peng, Di, Ter, Ke) ---
        if self.num_syllables > 2:
            self._remove_first_order_prefix()
        
        if len(self.word) != old_length: 
         
            
            # Cek Suffix
            old_len_suffix = len(self.word)
            if self.num_syllables > 2:
                self._remove_suffix()
            
            # Jika Suffix juga dihapus, cek Prefix Orde Kedua
            if len(self.word) != old_len_suffix:
                if self.num_syllables > 2:
                    self._remove_second_order_prefix()
                    
        else: 
            # Cek Prefix Orde Kedua (Ber, Per, Bel, Pe) dulu
            if self.num_syllables > 2:
                self._remove_second_order_prefix()
            
            # Cek Suffix
            if self.num_syllables > 2:
                self._remove_suffix()

    def _remove_first_order_prefix(self):
        " Menangani Prefix: Meng-, Peng-, Di-, Ter-, Ke- "
        
        # --- MENG- (dan varian peluluhannya) ---
        if self.word.startswith('meng'):
            self.flags.add(self.REMOVED_MENG)
            self.word = self.word[4:]
            self._update_syllables()
            return
        
        if self.word.startswith('meny') and len(self.word) > 4 and self._is_vowel(self.word[4]):
            self.flags.add(self.REMOVED_MENG)
            self.word = 's' + self.word[4:] 
            self._update_syllables()
            return
            
        if self.word.startswith('mem') and len(self.word) > 3 and self._is_vowel(self.word[3]):
            self.flags.add(self.REMOVED_MENG)
            self.word = 'p' + self.word[3:]
            self._update_syllables()
            return
        
        if self.word.startswith('mem'):
            self.flags.add(self.REMOVED_MENG)
            self.word = self.word[3:]
            self._update_syllables()
            return

        if self.word.startswith('men') and len(self.word) > 3 and self._is_vowel(self.word[3]):
            self.flags.add(self.REMOVED_MENG)
            self.word = 't' + self.word[3:]
            self._update_syllables()
            return
        
        if self.word.startswith('men'):
            self.flags.add(self.REMOVED_MENG)
            self.word = self.word[3:]
            self._update_syllables()
            return
        
        if self.word.startswith('me'):
            self.flags.add(self.REMOVED_MENG)
            self.word = self.word[2:]
            self._update_syllables()
            return

        # --- PENG- (dan varian peluluhannya) ---
        if self.word.startswith('peng'):
            self.flags.add(self.REMOVED_PENG)
            self.word = self.word[4:]
            self._update_syllables()
            return        
            
        if self.word.startswith('peny') and len(self.word) > 4 and self._is_vowel(self.word[4]):
             self.flags.add(self.REMOVED_PENG)
             self.word = 's' + self.word[4:]
             self._update_syllables()
             return        
        
        if self.word.startswith('pem') and len(self.word) > 3 and self._is_vowel(self.word[3]):
            self.flags.add(self.REMOVED_PENG)
            self.word = 'p' + self.word[3:] 
            self._update_syllables()
            return
            
        if self.word.startswith('pem'):
            self.flags.add(self.REMOVED_PENG)
            self.word = self.word[3:]
            self._update_syllables()
            return

        if self.word.startswith('pen') and len(self.word) > 3 and self._is_vowel(self.word[3]):
            self.flags.add(self.REMOVED_PENG)
            self.word = 't' + self.word[3:] 
            self._update_syllables()
            return
            
        if self.word.startswith('pen'):
            self.flags.add(self.REMOVED_PENG)
            self.word = self.word[3:]
            self._update_syllables()
            return
        
        # --- SIMPLE PREFIX ---
        if self.word.startswith('di'):
            self.flags.add(self.REMOVED_DI)
            self.word = self.word[2:]
            self._update_syllables()
            return
        
        if self.word.startswith('ter'):
            self.flags.add(self.REMOVED_TER)
            self.word = self.word[3:]
            self._update_syllables()
            return 
        
        if self.word.startswith('ke'):
            self.flags.add(self.REMOVED_KE)
            self.word = self.word[2:]
            self._update_syllables()
            return        
        
    def _remove_second_order_prefix(self):
        " Menangani Prefix: Ber-, Per-, Bel-, Pe- "
        
        if self.word.startswith('ber'):
            self.flags.add(self.REMOVED_BER)
            self.word = self.word[3:]
            self._update_syllables()
            return
            
        if self.word == 'belajar':
            self.flags.add(self.REMOVED_BER)
            self.word = 'ajar'
            self._update_syllables()
            return
        
        # Rule: be- + ajar/kerja (umumnya be- muncul pada be-kerja, be-lajar)
        if self.word.startswith('be') and len(self.word) > 4 and \
           not self._is_vowel(self.word[2]) and \
           self.word[3] == 'e' and self.word[4] == 'r':
            self.flags.add(self.REMOVED_BER)
            self.word = self.word[2:]
            self._update_syllables()
            return
        
        if self.word.startswith('per'):
            self.word = self.word[3:]
            self._update_syllables()
            return
        
        if self.word == 'pelajar':
            self.word = 'ajar'
            self._update_syllables()
            return
        
        if self.word.startswith('pe'):
            self.flags.add(self.REMOVED_PE)
            self.word = self.word[2:]
            self._update_syllables()
            return
            
    def _remove_suffix(self):
        """ Menangani Suffix: -kan, -an, -i """
        # Suffix -kan
        if self.word.endswith('kan') \
           and self.REMOVED_KE not in self.flags \
           and self.REMOVED_PENG not in self.flags \
           and self.REMOVED_PE not in self.flags:
            self.word = self.word[:-3]
            self._update_syllables()
            return
        
        # Suffix -an
        if self.word.endswith('an') \
           and self.REMOVED_DI not in self.flags \
           and self.REMOVED_MENG not in self.flags \
           and self.REMOVED_TER not in self.flags:
            self.word = self.word[:-2]
            self._update_syllables()
            return
        
        # Suffix -i
        if self.word.endswith('i') \
           and not self.word.endswith('si') \
           and self.REMOVED_BER not in self.flags \
           and self.REMOVED_KE not in self.flags \
           and self.REMOVED_PENG not in self.flags:
            self.word = self.word[:-1]
            self._update_syllables()
            return