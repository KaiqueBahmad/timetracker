from pathlib import Path
import sqlite3


DB_PATH = Path.home() / ".timetracker.db"

def getConnection():
    return sqlite3.connect(DB_PATH)

def setup_database():
    """Configurar o banco de dados se não existir"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Criar tabela de empresas
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS empresas (
        id INTEGER PRIMARY KEY,
        nome TEXT UNIQUE
    )
    ''')
    
    # Criar tabela de registros
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS registros (
        id INTEGER PRIMARY KEY,
        empresa_id INTEGER,
        inicio TIMESTAMP,
        fim TIMESTAMP,
        duracao INTEGER,
        FOREIGN KEY (empresa_id) REFERENCES empresas (id)
    )
    ''')
    
    conn.commit()
    conn.close()