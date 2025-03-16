import datetime
import sqlite3

from services.databaseConfig import getConnection
from services.trackService import check_active_session
from utils.dateFormat import format_duration


def show_records(empresa=None, data_inicio=None, data_fim=None):
    """Mostrar registros de tempo"""
    conn = getConnection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = """
    SELECT e.nome as empresa, r.inicio, r.fim, r.duracao
    FROM registros r
    JOIN empresas e ON r.empresa_id = e.id
    WHERE r.fim IS NOT NULL
    """
    params = []
    
    if empresa:
        query += " AND e.nome LIKE ?"
        params.append(f"%{empresa}%")
    
    if data_inicio:
        query += " AND date(r.inicio) >= ?"
        params.append(data_inicio)
    
    if data_fim:
        query += " AND date(r.inicio) <= ?"
        params.append(data_fim)
    
    query += " ORDER BY r.inicio DESC"
    
    cursor.execute(query, params)
    registros = cursor.fetchall()
    
    # Verificar se há registros
    if not registros:
        print("Nenhum registro encontrado.")
        conn.close()
        return
    
    # Calcular total
    total_segundos = 0
    
    print(f"\n{'EMPRESA':<20} {'INÍCIO':<20} {'FIM':<20} {'DURAÇÃO':<10}")
    print("-" * 75)
    
    for reg in registros:
        inicio = datetime.datetime.fromisoformat(reg['inicio'])
        fim = datetime.datetime.fromisoformat(reg['fim'])
        
        duracao_formatada = format_duration(reg['duracao'])
        total_segundos += reg['duracao']
        
        print(f"{reg['empresa']:<20} {inicio.strftime('%d/%m/%Y %H:%M:%S'):<20} {fim.strftime('%d/%m/%Y %H:%M:%S'):<20} {duracao_formatada:<10}")
    
    print("-" * 75)
    print(f"Total: {format_duration(total_segundos)}")
    
    conn.close()


def get_active_session_info():
    """Obter informações da sessão ativa"""
    sessao_ativa = check_active_session()
    if not sessao_ativa:
        return None
    
    registro_id, empresa_id, inicio_str = sessao_ativa
    inicio = datetime.datetime.fromisoformat(inicio_str)
    now = datetime.datetime.now()
    
    # Duração até agora
    duracao = int((now - inicio).total_seconds())
    
    conn = getConnection()
    cursor = conn.cursor()
    cursor.execute("SELECT nome FROM empresas WHERE id = ?", (empresa_id,))
    nome_empresa = cursor.fetchone()[0]
    conn.close()
    
    return {
        'empresa': nome_empresa,
        'inicio': inicio,
        'duracao': duracao
    }


def get_current_status():
    sessao_ativa = check_active_session()
    if sessao_ativa:
        registro_id, empresa_id, inicio_str = sessao_ativa
        inicio = datetime.datetime.fromisoformat(inicio_str)
        now = datetime.datetime.now()
        
        # Duração até agora
        duracao = int((now - inicio).total_seconds())
        duracao_formatada = format_duration(duracao)
        
        conn = getConnection()
        cursor = conn.cursor()
        cursor.execute("SELECT nome FROM empresas WHERE id = ?", (empresa_id,))
        nome_empresa = cursor.fetchone()[0]
        conn.close()
        
        print(f"Sessão ativa para: {nome_empresa}")
        print(f"Iniciada em: {inicio.strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"Duração até agora: {duracao_formatada}")
        return
    print("Nenhuma sessão ativa no momento.")

def calcular_saldo(empresa=None, meta_horas_diarias=8):
    conn = getConnection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = """
    SELECT date(r.inicio) as data, sum(r.duracao) as segundos_trabalhados
    FROM registros r
    JOIN empresas e ON r.empresa_id = e.id
    WHERE r.fim IS NOT NULL
    """
    params = []
    if empresa:
        query += " AND e.nome LIKE ?"
        params.append(f"%{empresa}%")
    
    query += " GROUP BY date(r.inicio) ORDER BY date(r.inicio)"
    
    cursor.execute(query, params)
    dias = cursor.fetchall()
    
    if not dias:
        print("Nenhum registro encontrado para calcular saldo.")
        conn.close()
        return
    
    meta_segundos = meta_horas_diarias * 3600
    
    total_segundos_trabalhados = 0
    total_segundos_meta = 0
    
    print(f"\n{'DATA':<15} {'HORAS TRAB.':<15} {'META':<15} {'SALDO':<15}")
    print("-" * 60)
    
    for dia in dias:
        data = dia['data']
        segundos_trabalhados = dia['segundos_trabalhados']
        
        saldo_dia = segundos_trabalhados - meta_segundos
        
        total_segundos_trabalhados += segundos_trabalhados
        total_segundos_meta += meta_segundos
        
        print(f"{data:<15} {format_duration(segundos_trabalhados):<15} {format_duration(meta_segundos):<15} {format_duration(saldo_dia):<15}")
    
    saldo_total = total_segundos_trabalhados - total_segundos_meta
    
    print("-" * 60)
    print(f"Total: {format_duration(total_segundos_trabalhados):<15} {format_duration(total_segundos_meta):<15} {format_duration(saldo_total):<15}")
    
    conn.close()