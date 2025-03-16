

import sqlite3

from services.databaseConfig import getConnection


def get_company_id(nome_empresa):
    """Obter ID da empresa ou criar se não existir"""
    conn = getConnection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM empresas WHERE nome = ?", (nome_empresa,))
    resultado = cursor.fetchone()
    
    if resultado:
        empresa_id = resultado[0]
    else:
        cursor.execute("INSERT INTO empresas (nome) VALUES (?)", (nome_empresa,))
        empresa_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    
    return empresa_id