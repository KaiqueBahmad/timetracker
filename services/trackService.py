
import datetime
from services.companyService import get_company_id
from services.databaseConfig import getConnection
from utils.dateFormat import format_duration


def check_active_session():
    """Verificar se existe uma sessão ativa"""
    conn = getConnection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, empresa_id, inicio FROM registros WHERE fim IS NULL")
    resultado = cursor.fetchone()
    
    conn.close()
    
    if resultado:
        return resultado
    return None


def start_tracking(nome_empresa):
    """Iniciar rastreamento de tempo para uma empresa"""
    # Verificar se já existe uma sessão ativa
    sessao_ativa = check_active_session()
    if sessao_ativa:
        conn = getConnection()
        cursor = conn.cursor()
        cursor.execute("SELECT nome FROM empresas WHERE id = ?", (sessao_ativa[1],))
        empresa = cursor.fetchone()[0]
        conn.close()
        
        inicio = datetime.datetime.fromisoformat(sessao_ativa[2])
        print(f"Erro: Já existe uma sessão ativa para '{empresa}' iniciada em {inicio.strftime('%d/%m/%Y %H:%M:%S')}")
        print("Finalize a sessão atual com 'timetracker stop' antes de iniciar uma nova.")
        return
    
    # Iniciar nova sessão
    empresa_id = get_company_id(nome_empresa)
    now = datetime.datetime.now()
    
    conn = getConnection()
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO registros (empresa_id, inicio, fim, duracao) VALUES (?, ?, NULL, NULL)",
        (empresa_id, now.isoformat())
    )
    
    conn.commit()
    conn.close()
    
    print(f"Iniciando rastreamento para '{nome_empresa}' em {now.strftime('%d/%m/%Y %H:%M:%S')}")

def stop_tracking():
    """Finalizar rastreamento de tempo ativo"""
    sessao_ativa = check_active_session()
    
    if not sessao_ativa:
        print("Erro: Não há sessão ativa para finalizar.")
        return
    
    registro_id, empresa_id, inicio_str = sessao_ativa
    inicio = datetime.datetime.fromisoformat(inicio_str)
    now = datetime.datetime.now()
    
    # Calcular duração em segundos
    duracao = int((now - inicio).total_seconds())
    
    conn = getConnection()
    cursor = conn.cursor()
    
    # Atualizar registro
    cursor.execute(
        "UPDATE registros SET fim = ?, duracao = ? WHERE id = ?",
        (now.isoformat(), duracao, registro_id)
    )
    
    # Obter nome da empresa
    cursor.execute("SELECT nome FROM empresas WHERE id = ?", (empresa_id,))
    nome_empresa = cursor.fetchone()[0]
    
    conn.commit()
    conn.close()
    
    # Formatar duração
    duracao_formatada = format_duration(duracao)
    
    print(f"Finalizando rastreamento para '{nome_empresa}'")
    print(f"Iniciado em: {inicio.strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"Finalizado em: {now.strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"Duração: {duracao_formatada}")

