#!/usr/bin/env python3
import argparse
import datetime
import os
import sqlite3
import sys
import time
import curses
from pathlib import Path

# Definir o caminho para o banco de dados
DB_PATH = Path.home() / ".timetracker.db"

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

def get_company_id(nome_empresa):
    """Obter ID da empresa ou criar se não existir"""
    conn = sqlite3.connect(DB_PATH)
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

def check_active_session():
    """Verificar se existe uma sessão ativa"""
    conn = sqlite3.connect(DB_PATH)
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
        conn = sqlite3.connect(DB_PATH)
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
    
    conn = sqlite3.connect(DB_PATH)
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
    
    conn = sqlite3.connect(DB_PATH)
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

def format_duration(seconds):
    """Formatar duração em segundos para formato legível"""
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def show_records(empresa=None, data_inicio=None, data_fim=None):
    """Mostrar registros de tempo"""
    conn = sqlite3.connect(DB_PATH)
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

def calcular_saldo(empresa=None, meta_horas_diarias=8):
    """Calcular saldo de horas trabalhadas"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Consulta para obter dias trabalhados
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
    
    # Meta em segundos
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
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT nome FROM empresas WHERE id = ?", (empresa_id,))
    nome_empresa = cursor.fetchone()[0]
    conn.close()
    
    return {
        'empresa': nome_empresa,
        'inicio': inicio,
        'duracao': duracao
    }

def watch_time(stdscr):
    """Mostrar tempo em execução em tempo real"""
    # Configurar cores
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Ativo
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)    # Inativo
    curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK) # Título
    
    # Configurar tela
    curses.curs_set(0)  # Esconder cursor
    stdscr.clear()
    
    # Definir taxa de atualização (em segundos)
    refresh_rate = 1
    
    # Loop principal
    running = True
    while running:
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        
        # Título
        title = "TIMETRACKER MONITOR"
        stdscr.addstr(1, (width - len(title)) // 2, title, curses.color_pair(3) | curses.A_BOLD)
        
        # Data e hora atual
        now = datetime.datetime.now()
        data_hora = now.strftime("%d/%m/%Y %H:%M:%S")
        stdscr.addstr(3, 2, f"Data/Hora atual: {data_hora}")
        
        # Verificar sessão ativa
        session_info = get_active_session_info()
        
        if session_info:
            # Status
            status = "ATIVO"
            stdscr.addstr(5, 2, f"Status: ", curses.A_BOLD)
            stdscr.addstr(status, curses.color_pair(1) | curses.A_BOLD)
            
            # Empresa
            stdscr.addstr(7, 2, f"Empresa: {session_info['empresa']}")
            
            # Horário de início
            inicio_str = session_info['inicio'].strftime("%d/%m/%Y %H:%M:%S")
            stdscr.addstr(8, 2, f"Início: {inicio_str}")
            
            # Duração
            duracao_str = format_duration(session_info['duracao'])
            stdscr.addstr(9, 2, f"Duração: ", curses.A_BOLD)
            stdscr.addstr(duracao_str, curses.A_BOLD)
            
            # Tempo decorrido em formato de barra de progresso (8h = 100%)
            progress_width = width - 20
            horas_meta = 8 * 3600  # 8 horas em segundos
            progress_filled = min(int((session_info['duracao'] / horas_meta) * progress_width), progress_width)
            
            stdscr.addstr(11, 2, "Progresso (8h): ")
            stdscr.addstr(12, 2, "[")
            stdscr.addstr(12, 3, "=" * progress_filled, curses.color_pair(1))
            stdscr.addstr(12, 3 + progress_filled, " " * (progress_width - progress_filled))
            stdscr.addstr(12, 3 + progress_width, "]")
            
            # Percentual
            percent = min(100, int((session_info['duracao'] / horas_meta) * 100))
            stdscr.addstr(12, 5 + progress_width, f"{percent}%")
        else:
            # Status
            status = "INATIVO"
            stdscr.addstr(5, 2, f"Status: ", curses.A_BOLD)
            stdscr.addstr(status, curses.color_pair(2) | curses.A_BOLD)
            
            stdscr.addstr(7, 2, "Nenhuma sessão ativa no momento.")
            stdscr.addstr(9, 2, "Use 'timetracker start <empresa>' para iniciar uma nova sessão.")
        
        # Instruções
        stdscr.addstr(height-3, 2, "Pressione 'q' para sair", curses.A_DIM)
        
        # Atualizar tela
        stdscr.refresh()
        
        # Checar input com timeout
        stdscr.timeout(refresh_rate * 1000)
        key = stdscr.getch()
        
        # Sair se 'q' for pressionado
        if key == ord('q'):
            running = False

def main():
    # Configurar o banco de dados
    setup_database()
    
    # Configurar o parser de argumentos
    parser = argparse.ArgumentParser(description='Gerenciador de horas de serviço')
    subparsers = parser.add_subparsers(dest='comando', help='Comandos disponíveis')
    
    # Comando 'start'
    start_parser = subparsers.add_parser('start', help='Iniciar rastreamento de tempo')
    start_parser.add_argument('empresa', help='Nome da empresa')
    
    # Comando 'stop'
    subparsers.add_parser('stop', help='Finalizar rastreamento de tempo')
    
    # Comando 'show'
    show_parser = subparsers.add_parser('show', help='Mostrar registros de tempo')
    show_parser.add_argument('-e', '--empresa', help='Filtrar por empresa')
    show_parser.add_argument('-i', '--inicio', help='Data de início (YYYY-MM-DD)')
    show_parser.add_argument('-f', '--fim', help='Data de fim (YYYY-MM-DD)')
    
    # Comando 'saldo'
    saldo_parser = subparsers.add_parser('saldo', help='Calcular saldo de horas')
    saldo_parser.add_argument('-e', '--empresa', help='Filtrar por empresa')
    saldo_parser.add_argument('-m', '--meta', type=float, default=8.0, help='Meta de horas diárias (padrão: 8.0)')
    
    # Comando 'status'
    subparsers.add_parser('status', help='Verificar status atual')
    
    # Comando 'watch'
    subparsers.add_parser('watch', help='Mostrar tempo em execução em tempo real')
    
    args = parser.parse_args()
    
    # Executar comando apropriado
    if args.comando == 'start':
        start_tracking(args.empresa)
    elif args.comando == 'stop':
        stop_tracking()
    elif args.comando == 'show':
        show_records(args.empresa, args.inicio, args.fim)
    elif args.comando == 'saldo':
        calcular_saldo(args.empresa, args.meta)
    elif args.comando == 'status':
        sessao_ativa = check_active_session()
        if sessao_ativa:
            registro_id, empresa_id, inicio_str = sessao_ativa
            inicio = datetime.datetime.fromisoformat(inicio_str)
            now = datetime.datetime.now()
            
            # Duração até agora
            duracao = int((now - inicio).total_seconds())
            duracao_formatada = format_duration(duracao)
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT nome FROM empresas WHERE id = ?", (empresa_id,))
            nome_empresa = cursor.fetchone()[0]
            conn.close()
            
            print(f"Sessão ativa para: {nome_empresa}")
            print(f"Iniciada em: {inicio.strftime('%d/%m/%Y %H:%M:%S')}")
            print(f"Duração até agora: {duracao_formatada}")
        else:
            print("Nenhuma sessão ativa no momento.")
    elif args.comando == 'watch':
        try:
            curses.wrapper(watch_time)
        except KeyboardInterrupt:
            # Sair graciosamente em caso de Ctrl+C
            pass
    else:
        parser.print_help()

if __name__ == "__main__":
    main()