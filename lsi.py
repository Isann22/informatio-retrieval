from gensim import corpora, models, similarities, matutils
import pandas as pd
import numpy as np

class LSIRetrieval:
    def __init__(self, cleaned_docs_list, num_topics=15):
        self.cleaned_docs_list = cleaned_docs_list
        self.dictionary = corpora.Dictionary(self.cleaned_docs_list)
        
        # 1. Bag of Words (BoW)
        self.corpus_bow = [self.dictionary.doc2bow(doc) for doc in self.cleaned_docs_list]
        
        # 2. TF-IDF Transformation
        self.tfidf_model = models.TfidfModel(self.corpus_bow)
        self.corpus_tfidf = self.tfidf_model[self.corpus_bow]
        
        # 3. LSI Model (SVD) - num_topics diset 8 sesuai jumlah kategori
        self.lsi_model = models.LsiModel(
            self.corpus_tfidf, 
            id2word=self.dictionary, 
            num_topics=num_topics
        )
        
        # 4. Similarity Index
        self.index = similarities.MatrixSimilarity(self.lsi_model[self.corpus_tfidf])

    def display_lsi_details(self, search_query):
        words = [self.dictionary[i] for i in range(len(self.dictionary))]
        doc_names = [f"Doc_{i}" for i in range(len(self.cleaned_docs_list))]

        # --- A. BAG OF WORDS (BoW) ---
        print("=== 1. BAG OF WORDS (BoW) REPRESENTATION ===")
        for i, bow in enumerate(self.corpus_bow):
            print(f"Doc_{i}: {bow}")
        
        # --- B. TERM FREQUENCY (TF) MATRIX ---
        print("\n=== 2. TERM FREQUENCY (TF) MATRIX ===")
        tf_matrix = matutils.corpus2dense(self.corpus_bow, num_terms=len(self.dictionary))
        print(pd.DataFrame(tf_matrix, index=words, columns=doc_names))
        
        # --- C. SVD MATRICES (U, S, V) ---
        u_matrix = self.lsi_model.get_topics() # Term-Topic
        s_matrix = self.lsi_model.projection.s # Singular Values
        
        corpus_lsi = self.lsi_model[self.corpus_tfidf]
        v_matrix = matutils.corpus2dense(corpus_lsi, num_terms=self.lsi_model.num_topics).T

        print("\n=== 3. MATRIX U (Term-Topic) - Word Weights per Topic ===")
        # Menampilkan bobot kata terhadap 8 topik (kategori)
        print(pd.DataFrame(u_matrix.T, index=words, columns=[f"T{i}" for i in range(u_matrix.shape[0])]))

        print("\n=== 4. MATRIX S (Singular Values) - Topic Strength ===")
        print(s_matrix)

        print("\n=== 5. MATRIX V (Document-Topic) - Doc Coordinates ===")
        print(pd.DataFrame(v_matrix, columns=[f"T{i}" for i in range(v_matrix.shape[1])]))

        # --- D. QUERY ANALYSIS ---
        query_bow = self.dictionary.doc2bow(search_query)
        query_tfidf = self.tfidf_model[query_bow]
        query_lsi = self.lsi_model[query_tfidf]
        
        query_vec = np.zeros(self.lsi_model.num_topics)
        for topic_id, value in query_lsi:
            query_vec[topic_id] = value

        print(f"\n=== 6. SEARCH QUERY ANALYSIS: '{' '.join(search_query)}' ===")
        print(f"Query BoW: {query_bow}")
        print(f"Query LSI Vector: {query_vec}")

        # --- E. FINAL RANKING ---
        sims = self.index[query_lsi]
        sorted_sims = sorted(enumerate(sims), key=lambda item: -item[1])
        for doc_id, score in sorted_sims[:10]:
            print(f"Document {doc_id} | Score: {score:.4f}")
       
        return sorted_sims[:10]
