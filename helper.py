

import argparse


class Helper():

    @staticmethod
    def initializeParser():
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
        
        # Comando 'export'
        export_parser = subparsers.add_parser('export', help='Exportar relatório em formato específico')
        export_parser.add_argument('formato', help='Formato de exportação (ex: csv, pdf, xlsx)')
        export_parser.add_argument('empresa', help='Nome da empresa')
        export_parser.add_argument('data', nargs='?', help='Mês/Ano no formato MM/YY (ex: 02/25)')

        return parser
