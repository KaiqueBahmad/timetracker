#!/usr/bin/env python3
import argparse
import datetime
import os
import sqlite3
import sys
import time
import curses
from pathlib import Path
import calendar
from collections import defaultdict, OrderedDict

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

def show_calendar(mes_offset=0):
    """
    Mostra um calendário visual do mês especificado com horas trabalhadas por empresa
    usando a interface curses para melhor visualização.
    
    Args:
        mes_offset (int): Deslocamento do mês em relação ao mês atual
                          0 = mês atual, -1 = mês anterior, 1 = próximo mês
    """
    # Função principal do curses
    curses.wrapper(calendar_curses, mes_offset)

def calendar_curses(stdscr, mes_offset=0):
    """
    Implementação principal do calendário usando curses
    
    Args:
        stdscr: Tela padrão do curses
        mes_offset (int): Deslocamento do mês
    """
    
    # Configurar cores
    curses.start_color()
    curses.use_default_colors()
    
    # Inicializar pares de cores
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)    # Cabeçalhos
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_GREEN)   # Dias com >8h
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_YELLOW)  # Dias com 4-8h
    curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_RED)     # Dias com <4h
    
    # Cores para as empresas
    EMPRESA_CORES = [
        curses.COLOR_BLUE,    # Azul
        curses.COLOR_GREEN,   # Verde
        curses.COLOR_RED,     # Vermelho
        curses.COLOR_MAGENTA, # Magenta
        curses.COLOR_CYAN,    # Ciano
        curses.COLOR_YELLOW,  # Amarelo
    ]
    
    # Inicializar mais pares de cores para as empresas
    for i, cor in enumerate(EMPRESA_CORES, start=10):
        curses.init_pair(i, cor, -1)  # Texto colorido em fundo normal
        curses.init_pair(i+20, curses.COLOR_BLACK, cor)  # Fundo colorido com texto preto
    
    # Cores definidas
    COR_TITULO = curses.color_pair(1) | curses.A_BOLD
    COR_DIA_NORMAL = curses.A_NORMAL
    COR_DIA_8H = curses.color_pair(2)
    COR_DIA_4H = curses.color_pair(3)
    COR_DIA_POUCO = curses.color_pair(4)
    COR_DESTAQUE = curses.A_BOLD
    COR_EMPRESA_BASE = 10  # Começamos a numerar do 10 para as empresas
    
    # Limpar tela
    stdscr.clear()
    stdscr.refresh()
    
    # Obter dimensões da tela
    max_y, max_x = stdscr.getmaxyx()
    
    # Obter o mês e ano com base no offset
    hoje = datetime.date.today()
    
    # Calcular o mês alvo
    mes_alvo = hoje.replace(day=1)
    if mes_offset > 0:
        for _ in range(mes_offset):
            # Avançar para o próximo mês
            if mes_alvo.month == 12:
                mes_alvo = mes_alvo.replace(year=mes_alvo.year + 1, month=1)
            else:
                mes_alvo = mes_alvo.replace(month=mes_alvo.month + 1)
    elif mes_offset < 0:
        for _ in range(abs(mes_offset)):
            # Retroceder para o mês anterior
            if mes_alvo.month == 1:
                mes_alvo = mes_alvo.replace(year=mes_alvo.year - 1, month=12)
            else:
                mes_alvo = mes_alvo.replace(month=mes_alvo.month - 1)
    
    ano = mes_alvo.year
    mes = mes_alvo.month
    
    # Nome do mês em português
    nomes_meses = [
        "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
    ]
    nome_mes = nomes_meses[mes - 1]
    
    # Obter o primeiro e último dia do mês
    _, ultimo_dia = calendar.monthrange(ano, mes)
    data_inicio = datetime.date(ano, mes, 1)
    data_fim = datetime.date(ano, mes, ultimo_dia)
    
    # Converter para string no formato SQLite
    data_inicio_str = f"{data_inicio.isoformat()} 00:00:00"
    data_fim_str = f"{data_fim.isoformat()} 23:59:59"
    
    # Consultar o banco de dados para obter os registros do mês
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = """
    SELECT 
        date(r.inicio) as data,
        e.nome as empresa,
        SUM(r.duracao) as segundos_trabalhados
    FROM registros r
    JOIN empresas e ON r.empresa_id = e.id
    WHERE r.fim IS NOT NULL
      AND datetime(r.inicio) >= datetime(?)
      AND datetime(r.inicio) <= datetime(?)
    GROUP BY date(r.inicio), e.nome
    ORDER BY date(r.inicio), e.nome
    """
    
    cursor.execute(query, (data_inicio_str, data_fim_str))
    registros = cursor.fetchall()
    
    # Organizar os dados por dia e empresa
    dados_por_dia = defaultdict(lambda: defaultdict(int))
    empresas_no_mes = set()
    
    for reg in registros:
        data = datetime.date.fromisoformat(reg['data'])
        empresa = reg['empresa']
        segundos = reg['segundos_trabalhados']
        
        # Armazenar os segundos trabalhados para esta empresa neste dia
        dados_por_dia[data.day][empresa] += segundos
        empresas_no_mes.add(empresa)
    
    # Converter empresas para lista ordenada
    empresas = sorted(empresas_no_mes)
    
    # Definir abreviações para empresas
    abreviacoes = {}
    cores_empresas = {}
    
    for i, empresa in enumerate(empresas):
        # Cor da empresa (texto)
        cores_empresas[empresa] = COR_EMPRESA_BASE + (i % len(EMPRESA_CORES))
        
        # Criar abreviações (2 primeiras letras ou iniciais para nomes compostos)
        if ' ' in empresa and len(empresa.split()) > 1:
            palavras = empresa.split()
            abreviacoes[empresa] = ''.join(p[0] for p in palavras).upper()[:2]
        else:
            abreviacoes[empresa] = empresa[:2].upper()
    
    # Preparar o calendário
    cal = calendar.monthcalendar(ano, mes)
    
    # Função para formatar horas:minutos
    def format_hm(segundos):
        horas = segundos // 3600
        minutos = (segundos % 3600) // 60
        return f"{horas:02d}:{minutos:02d}"
    
    # Função para obter código de cor baseado nas horas trabalhadas
    def get_color_for_hours(segundos):
        if segundos >= 8 * 3600:  # 8h ou mais
            return COR_DIA_8H
        elif segundos >= 4 * 3600:  # 4h ou mais
            return COR_DIA_4H
        elif segundos > 0:  # Menos de 4h
            return COR_DIA_POUCO
        else:  # Sem trabalho
            return COR_DIA_NORMAL
    
    # Calcular estatísticas do mês para o resumo
    dados_empresa_mes = defaultdict(int)
    dias_empresa_mes = defaultdict(set)
    dias_trabalho_mes = set()
    
    for dia, empresas_dia in dados_por_dia.items():
        if empresas_dia:
            dias_trabalho_mes.add(dia)
            for empresa, segundos in empresas_dia.items():
                dados_empresa_mes[empresa] += segundos
                dias_empresa_mes[empresa].add(dia)
    
    # Calculando total de horas no mês
    total_segundos_mes = sum(dados_empresa_mes.values())
    
    # Largura das células do calendário
    largura_celula = max_x // 7
    altura_celula = 4  # Altura de cada célula do calendário
    
    # Definir tamanho da janela do calendário
    altura_calendario = 8 + (altura_celula * len(cal))  # Cabeçalho + linhas do calendário
    largura_calendario = largura_celula * 7
    
    # Criar janela do calendário
    if altura_calendario > max_y:
        altura_calendario = max_y - 2
    
    # Criar pad para permitir rolagem
    calendar_pad = curses.newpad(altura_calendario + 30, largura_calendario)  # +30 para o resumo
    
    # Desenhar título
    titulo = f"CALENDÁRIO DE TRABALHO - {nome_mes.upper()} DE {ano}"
    calendar_pad.addstr(0, (largura_calendario - len(titulo)) // 2, titulo, COR_TITULO)
    
    # Desenhar legendas das empresas
    calendar_pad.addstr(2, 2, "EMPRESAS:", COR_DESTAQUE)
    linha_legenda = 3
    col_legenda = 2
    items_por_linha = max(1, largura_calendario // 30)
    
    for i, empresa in enumerate(empresas):
        cor_empresa = curses.color_pair(cores_empresas[empresa])
        cor_fundo = curses.color_pair(cores_empresas[empresa] + 20)
        
        # Organizar em colunas
        col_atual = (i % items_por_linha) * 30
        if i > 0 and i % items_por_linha == 0:
            linha_legenda += 1
        
        # Adicionar legenda com cor de fundo
        calendar_pad.addstr(linha_legenda, col_atual + 2, " " + abreviacoes[empresa] + " ", cor_fundo)
        calendar_pad.addstr(linha_legenda, col_atual + 7, "- " + empresa, cor_empresa)
    
    # Nomes dos dias da semana em português
    dias_semana = ["SEG", "TER", "QUA", "QUI", "SEX", "SÁB", "DOM"]
    
    # Linha inicial do calendário após legendas
    linha_inicio_cal = linha_legenda + 2
    
    # Desenhar cabeçalhos dos dias da semana
    for i, dia in enumerate(dias_semana):
        calendar_pad.addstr(linha_inicio_cal, i * largura_celula + (largura_celula - len(dia)) // 2, 
                          dia, COR_DESTAQUE)
    
    # Linha horizontal após cabeçalho
    for i in range(largura_calendario):
        calendar_pad.addch(linha_inicio_cal + 1, i, curses.ACS_HLINE)
    
    # Desenhar os dias do calendário
    linha_atual = linha_inicio_cal + 2
    
    for semana in cal:
        altura_max_linha = altura_celula
        
        for dia in semana:
            col = semana.index(dia) * largura_celula
            
            if dia == 0:
                # Dia não pertence ao mês
                continue
            
            # Dados do dia
            empresas_no_dia = dados_por_dia[dia]
            total_segundos_dia = sum(empresas_no_dia.values())
            total_hm = format_hm(total_segundos_dia)
            
            # Definir cor baseada no total de horas
            cor_dia = get_color_for_hours(total_segundos_dia)
            
            # Desenhar número do dia e total de horas
            if total_segundos_dia > 0:
                calendar_pad.addstr(linha_atual, col + 1, f"{dia:02d} ({total_hm})", cor_dia)
            else:
                calendar_pad.addstr(linha_atual, col + 1, f"{dia:02d}", COR_DIA_NORMAL)
            
            # Mostrar empresas
            linha_empresa = linha_atual + 1
            
            if empresas_no_dia:
                # Ordenar empresas por tempo trabalhado (decrescente)
                empresas_ordenadas = sorted(
                    empresas_no_dia.items(),
                    key=lambda x: x[1],
                    reverse=True
                )
                
                # Mostrar até 3 empresas ou quantas couberem
                for i, (empresa, segundos) in enumerate(empresas_ordenadas[:3]):
                    if linha_empresa + i < linha_atual + altura_celula:
                        cor_empresa = curses.color_pair(cores_empresas[empresa])
                        hm = format_hm(segundos)
                        texto = f"{abreviacoes[empresa]} {hm}"
                        calendar_pad.addstr(linha_empresa + i, col + 2, texto, cor_empresa)
                
                # Indicar se há mais empresas
                if len(empresas_ordenadas) > 3 and linha_empresa + 3 < linha_atual + altura_celula:
                    calendar_pad.addstr(linha_empresa + 3, col + 2, 
                                     f"+{len(empresas_ordenadas) - 3} mais")
        
        # Atualizar linha atual para a próxima semana
        linha_atual += altura_celula
        
        # Desenhar linha separadora entre semanas
        for i in range(largura_calendario):
            calendar_pad.addch(linha_atual - 1, i, curses.ACS_HLINE)
    
    # Linha para o resumo mensal
    linha_resumo = linha_atual + 1
    
    # Desenhar resumo mensal
    calendar_pad.addstr(linha_resumo, 2, "RESUMO MENSAL:", COR_DESTAQUE)
    linha_resumo += 1
    
    # Desenhar linha horizontal
    for i in range(largura_calendario - 4):
        calendar_pad.addch(linha_resumo, i + 2, curses.ACS_HLINE)
    linha_resumo += 1
    
    # Cabeçalho da tabela
    calendar_pad.addstr(linha_resumo, 2, "EMPRESA", COR_DESTAQUE)
    calendar_pad.addstr(linha_resumo, 22, "HORAS", COR_DESTAQUE)
    calendar_pad.addstr(linha_resumo, 32, "DIAS", COR_DESTAQUE)
    calendar_pad.addstr(linha_resumo, 40, "MÉDIA/DIA", COR_DESTAQUE)
    calendar_pad.addstr(linha_resumo, 52, "%TEMPO", COR_DESTAQUE)
    linha_resumo += 1
    
    # Desenhar linha horizontal
    for i in range(largura_calendario - 4):
        calendar_pad.addch(linha_resumo, i + 2, curses.ACS_HLINE)
    linha_resumo += 1
    
    # Ordenar empresas por total de horas (decrescente)
    empresas_ordenadas = sorted(dados_empresa_mes.items(), key=lambda x: x[1], reverse=True)
    
    # Exibir dados por empresa
    for empresa, segundos in empresas_ordenadas:
        cor_empresa = curses.color_pair(cores_empresas[empresa])
        horas = segundos / 3600
        dias = len(dias_empresa_mes[empresa])
        media_dia = horas / dias if dias > 0 else 0
        porcentagem = (segundos / total_segundos_mes * 100) if total_segundos_mes > 0 else 0
        
        calendar_pad.addstr(linha_resumo, 2, empresa[:18], cor_empresa)
        calendar_pad.addstr(linha_resumo, 22, f"{horas:>6.2f}h")
        calendar_pad.addstr(linha_resumo, 32, f"{dias:>3}d")
        calendar_pad.addstr(linha_resumo, 40, f"{media_dia:>6.2f}h")
        calendar_pad.addstr(linha_resumo, 52, f"{porcentagem:>6.2f}%")
        
        linha_resumo += 1
    
    # Desenhar linha horizontal
    for i in range(largura_calendario - 4):
        calendar_pad.addch(linha_resumo, i + 2, curses.ACS_HLINE)
    linha_resumo += 1
    
    # Total geral
    total_horas_mes = total_segundos_mes / 3600
    total_dias_trabalho = len(dias_trabalho_mes)
    media_diaria = total_horas_mes / total_dias_trabalho if total_dias_trabalho > 0 else 0
    
    calendar_pad.addstr(linha_resumo, 2, "TOTAL", COR_DESTAQUE)
    calendar_pad.addstr(linha_resumo, 22, f"{total_horas_mes:>6.2f}h", COR_DESTAQUE)
    calendar_pad.addstr(linha_resumo, 32, f"{total_dias_trabalho:>3}d", COR_DESTAQUE)
    calendar_pad.addstr(linha_resumo, 40, f"{media_diaria:>6.2f}h", COR_DESTAQUE)
    calendar_pad.addstr(linha_resumo, 52, f"{100:>6.2f}%", COR_DESTAQUE)
    
    linha_resumo += 2
    
    # Estatísticas adicionais
    calendar_pad.addstr(linha_resumo, 2, "ESTATÍSTICAS ADICIONAIS:", COR_DESTAQUE)
    linha_resumo += 1
    
    # Desenhar linha horizontal
    for i in range(largura_calendario - 4):
        calendar_pad.addch(linha_resumo, i + 2, curses.ACS_HLINE)
    linha_resumo += 1
    
    # Calcular dias úteis no mês (seg-sex)
    dias_uteis = sum(1 for semana in cal for dia in semana[:5] if dia != 0)
    porcentagem_dias_uteis = (total_dias_trabalho / dias_uteis * 100) if dias_uteis > 0 else 0
    
    calendar_pad.addstr(linha_resumo, 2, f"- Total de dias úteis no mês: {dias_uteis}")
    linha_resumo += 1
    calendar_pad.addstr(linha_resumo, 2, 
                     f"- Dias trabalhados: {total_dias_trabalho} ({porcentagem_dias_uteis:.2f}% dos dias úteis)")
    linha_resumo += 1
    
    # Meta de horas (8h por dia útil)
    meta_horas = dias_uteis * 8
    saldo_horas = total_horas_mes - meta_horas
    
    calendar_pad.addstr(linha_resumo, 2, f"- Meta mensal (8h/dia útil): {meta_horas:.2f}h")
    linha_resumo += 1
    
    if saldo_horas >= 0:
        calendar_pad.addstr(linha_resumo, 2, f"- Saldo de horas: +{saldo_horas:.2f}h", 
                         curses.color_pair(2))  # Verde
    else:
        calendar_pad.addstr(linha_resumo, 2, f"- Saldo de horas: {saldo_horas:.2f}h", 
                         curses.color_pair(4))  # Vermelho
    linha_resumo += 2
    
    # Instruções de navegação
    calendar_pad.addstr(linha_resumo, 2, "Navegação: 'p' = mês anterior, 'n' = próximo mês, 'q' = sair")
    
    # Altura total do conteúdo
    altura_total = linha_resumo + 2
    
    # Posição inicial de rolagem
    pos_y = 0
    
    # Loop principal
    while True:
        # Mostrar conteúdo visível do pad
        calendar_pad.refresh(pos_y, 0, 0, 0, min(max_y - 1, altura_total - pos_y), min(max_x - 1, largura_calendario - 1))
        
        # Capturar tecla
        key = stdscr.getch()
        
        # Processar tecla
        if key == ord('q'):  # Sair
            break
        elif key == ord('p'):  # Mês anterior
            calendar_curses(stdscr, mes_offset - 1)
            break
        elif key == ord('n'):  # Próximo mês
            calendar_curses(stdscr, mes_offset + 1)
            break
        elif key == curses.KEY_UP and pos_y > 0:  # Rolar para cima
            pos_y = max(0, pos_y - 1)
        elif key == curses.KEY_DOWN and pos_y < altura_total - max_y:  # Rolar para baixo
            pos_y = min(altura_total - max_y, pos_y + 1)
        elif key == curses.KEY_PPAGE:  # Page Up
            pos_y = max(0, pos_y - max_y // 2)
        elif key == curses.KEY_NPAGE:  # Page Down
            pos_y = min(altura_total - max_y, pos_y + max_y // 2)
        elif key == curses.KEY_HOME:  # Início
            pos_y = 0
        elif key == curses.KEY_END:  # Fim
            pos_y = max(0, altura_total - max_y)
    
    # Limpar
    conn.close()

# Adicionar o novo comando ao main()
def main():
    # Importar bibliotecas necessárias no escopo principal
    import argparse
    import datetime
    import os
    import sqlite3
    import sys
    import time
    import curses
    from pathlib import Path
    import calendar
    from collections import defaultdict, OrderedDict
    
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
    
    # Comando 'calendar'
    calendar_parser = subparsers.add_parser('calendar', help='Mostrar calendário visual do mês')
    calendar_parser.add_argument('offset', type=int, nargs='?', default=0, 
                               help='Deslocamento do mês (0=atual, -1=anterior, 1=próximo)')
    
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
    elif args.comando == 'calendar':
        show_calendar(args.offset)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()