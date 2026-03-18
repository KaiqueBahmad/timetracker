#!/usr/bin/env python3
"""
Script de seed para popular o banco de dados do Timetracker
com dados de exemplo em datas recentes.
"""

import sqlite3
import random
from datetime import datetime, timedelta
from pathlib import Path

# Configuração do banco de dados
DB_PATH = Path.home() / ".timetracker.db"

# Empresas de exemplo
EMPRESAS = [
    "Acme Corp",
    "Tech Solutions",
    "Design Studio",
    "Startup XYZ",
    "Consultoria ABC"
]

# Configurações de seed
DIAS_HISTORICO = 30  # Quantos dias de histórico criar
MIN_HORAS_DIA = 2    # Mínimo de horas por sessão
MAX_HORAS_DIA = 8    # Máximo de horas por sessão
CHANCE_TRABALHAR = 0.7  # 70% de chance de trabalhar em um dia


def limpar_dados():
    """Remove todos os dados existentes do banco"""
    print("Limpando dados existentes...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM registros")
    cursor.execute("DELETE FROM empresas")

    conn.commit()
    conn.close()
    print("✓ Dados anteriores removidos")


def criar_empresas():
    """Cria as empresas de exemplo"""
    print("\nCriando empresas...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    empresa_ids = []
    for empresa in EMPRESAS:
        cursor.execute("INSERT INTO empresas (nome) VALUES (?)", (empresa,))
        empresa_ids.append(cursor.lastrowid)
        print(f"  ✓ {empresa}")

    conn.commit()
    conn.close()

    return empresa_ids


def gerar_horario_trabalho(data):
    """Gera um horário de início realista para um dia de trabalho"""
    # Horários de início possíveis: entre 8h e 11h
    hora_inicio = random.randint(8, 11)
    minuto_inicio = random.choice([0, 15, 30, 45])

    inicio = datetime(
        year=data.year,
        month=data.month,
        day=data.day,
        hour=hora_inicio,
        minute=minuto_inicio,
        second=0
    )

    return inicio


def criar_registros(empresa_ids):
    """Cria registros de tempo para os últimos dias"""
    print("\nCriando registros de tempo...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    hoje = datetime.now()
    total_registros = 0
    total_horas = 0

    # Criar registros para cada dia no período
    for dias_atras in range(DIAS_HISTORICO, 0, -1):
        data = hoje - timedelta(days=dias_atras)

        # Pular fins de semana (0 = Segunda, 6 = Domingo)
        if data.weekday() >= 5:
            continue

        # Chance aleatória de ter trabalhado neste dia
        if random.random() > CHANCE_TRABALHAR:
            continue

        # Escolher empresa aleatória
        empresa_id = random.choice(empresa_ids)

        # Gerar horário de início
        inicio = gerar_horario_trabalho(data)

        # Duração aleatória (em horas)
        horas = random.uniform(MIN_HORAS_DIA, MAX_HORAS_DIA)
        duracao_segundos = int(horas * 3600)

        # Calcular horário de fim
        fim = inicio + timedelta(seconds=duracao_segundos)

        # Inserir registro
        cursor.execute(
            """INSERT INTO registros (empresa_id, inicio, fim, duracao)
               VALUES (?, ?, ?, ?)""",
            (empresa_id, inicio.isoformat(), fim.isoformat(), duracao_segundos)
        )

        total_registros += 1
        total_horas += horas

        # Buscar nome da empresa
        cursor.execute("SELECT nome FROM empresas WHERE id = ?", (empresa_id,))
        nome_empresa = cursor.fetchone()[0]

        print(f"  ✓ {data.strftime('%d/%m/%Y')} - {nome_empresa} - {horas:.1f}h")

    # Criar uma sessão ativa (opcional - 30% de chance)
    if random.random() < 0.3:
        print("\nCriando sessão ativa...")
        empresa_id = random.choice(empresa_ids)

        # Iniciar entre 1 e 4 horas atrás
        horas_atras = random.uniform(1, 4)
        inicio = hoje - timedelta(hours=horas_atras)

        cursor.execute(
            """INSERT INTO registros (empresa_id, inicio, fim, duracao)
               VALUES (?, ?, NULL, NULL)""",
            (empresa_id, inicio.isoformat())
        )

        cursor.execute("SELECT nome FROM empresas WHERE id = ?", (empresa_id,))
        nome_empresa = cursor.fetchone()[0]

        print(f"  ✓ Sessão ativa para '{nome_empresa}' - {horas_atras:.1f}h em andamento")
        total_registros += 1

    conn.commit()
    conn.close()

    print(f"\n{'='*50}")
    print(f"Total de registros criados: {total_registros}")
    print(f"Total de horas trabalhadas: {total_horas:.1f}h")
    print(f"Média por dia útil: {total_horas/total_registros:.1f}h")
    print(f"{'='*50}")


def main():
    """Função principal do seed"""
    print("="*50)
    print("SEED DO TIMETRACKER")
    print("="*50)

    # Verificar se o banco existe
    if not DB_PATH.exists():
        print(f"\nErro: Banco de dados não encontrado em {DB_PATH}")
        print("Execute o timetracker primeiro para criar o banco de dados.")
        return

    # Confirmar com o usuário
    resposta = input("\nDeseja limpar os dados existentes e criar novos? (s/N): ")
    if resposta.lower() != 's':
        print("Operação cancelada.")
        return

    # Executar seed
    limpar_dados()
    empresa_ids = criar_empresas()
    criar_registros(empresa_ids)

    print("\n✓ Seed concluído com sucesso!")
    print(f"\nVocê pode visualizar os dados com:")
    print("  timetracker show")
    print("  timetracker calendar")


if __name__ == "__main__":
    main()
