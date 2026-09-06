import sqlite3
import os
import re

DB_PATH = os.path.join(os.path.dirname(__file__), "ultron_knowledge.db")

class UltronKnowledgeEngine:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # FTS5 Virtual Table for Lightning Fast Full-Text Search
            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
                    category,
                    topic,
                    keywords,
                    content,
                    formula
                );
            """)
            
            conn.commit()
        
        # Check if DB is empty and auto-seed initial knowledge base
        if self.get_count() == 0:
            self.seed_core_knowledge()

    def seed_core_knowledge(self):
        core_data = [
            # Physics & Thermodynamics
            ("Physics", "Ideal Gas Law", "pv nrt gas thermodynamics temperature pressure", 
             "Ideal Gas State Equation: P * V = n * R * T. R = 8.314 J/(mol·K).", "P * V = n * R * T"),
            
            ("Physics", "Newton Second Law", "force mass acceleration newton motion f ma", 
             "Force equals mass times acceleration.", "F = m * a"),
            
            ("Physics", "Einstein Mass Energy", "relativity energy mass speed light e mc2", 
             "Mass-energy equivalence equation.", "E = m * c^2"),
            
            ("Physics", "Universal Gravitation", "gravity force attraction mass radius distance g", 
             "Gravitational force between two masses: F = G * (m1 * m2) / r^2. G = 6.674e-11.", "F = G * (m1 * m2) / r^2"),

            # Cryptography & Computer Science
            ("Cryptography", "ML-KEM", "ml-kem mlkem kem kyber pqc lattice quantum post quantum encryption", 
             "ML-KEM (FIPS 203) is a lattice-based post-quantum key encapsulation mechanism based on Module-LWE.", "Lattice Module-LWE"),
            
            ("Cryptography", "ML-DSA", "dilithium pqc signature post quantum verification", 
             "ML-DSA (FIPS 204) is a post-quantum digital signature algorithm based on Module-LWE lattices.", "Lattice Module-LWE"),

            # Chemistry
            ("Chemistry", "Photosynthesis", "biology plant glucose oxygen carbon dioxide light", 
             "6CO2 + 6H2O + Light -> C6H12O6 + 6O2. Plants convert sunlight into glucose.", "6CO2 + 6H2O -> C6H12O6 + 6O2"),
            
            ("Chemistry", "Molar Volume", "stp gas volume moles chemistry 22.4 liters", 
             "1 mole of any ideal gas occupies 22.4 Liters at Standard Temperature and Pressure (STP).", "V = n * 22.4 L")
        ]
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany("""
                INSERT INTO knowledge_fts (category, topic, keywords, content, formula)
                VALUES (?, ?, ?, ?, ?)
            """, core_data)
            conn.commit()

    def get_count(self) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM knowledge_fts;")
            return cursor.fetchone()[0]

        def query(self, search_text: str, limit=2):
            # Clean query terms: Hyphens ko space se replace karo taaki ML-KEM -> ML KEM bane
            cleaned_text = re.sub(r'[^a-zA-Z0-9\s]', ' ', search_text)
            clean_terms = cleaned_text.strip().split()
            if not clean_terms:
                return None
              
            # Build search query
            fts_query = " OR ".join([f'"{term}*"' for term in clean_terms if len(term) >= 2])
            if not fts_query:
                return None
               
            with self._get_connection() as conn:
                cursor = conn.cursor()
                try:
                    cursor.execute("""
                            SELECT topic, content, formula, rank 
                            FROM knowledge_fts 
                            WHERE knowledge_fts MATCH ? 
                            ORDER BY rank 
                            LIMIT ?;
                    """, (fts_query, limit))
                       
                    results = cursor.fetchall()
                    if results:
                        return results
                except sqlite3.OperationalError:
                    return None
            return None

# Singleton instance
kb_engine = UltronKnowledgeEngine()
