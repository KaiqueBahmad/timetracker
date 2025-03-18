

from datetime import datetime
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

def get_company_id(empresa):
    conn = getConnection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM empresas WHERE nome = ?", (empresa,))
    result = cursor.fetchone()
    
    conn.close()
    
    return result[0] if result else None

def get_time_records(empresa_id, date_obj=None):
    conn = getConnection()
    cursor = conn.cursor()
    
    if date_obj is None:
        date_obj = datetime.now()
        
    first_day = datetime(date_obj.year, date_obj.month, 1)
    
    if date_obj.month == 12:
        last_day = datetime(date_obj.year + 1, 1, 1)
    else:
        last_day = datetime(date_obj.year, date_obj.month + 1, 1)
        
    first_day_str = first_day.strftime('%Y-%m-%d 00:00:00')
    last_day_str = last_day.strftime('%Y-%m-%d 00:00:00')
    
    cursor.execute("""
        SELECT id, inicio, fim, duracao 
        FROM registros 
        WHERE empresa_id = ? AND inicio >= ? AND inicio < ?
        ORDER BY inicio
    """, (empresa_id, first_day_str, last_day_str))
    
    records = cursor.fetchall()
    conn.close()
    
    return records