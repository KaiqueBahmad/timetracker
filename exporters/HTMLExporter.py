import os
from datetime import datetime
from services.companyService import get_company_id, get_time_records


def exportToHTML(empresa, date_obj=None):
    """Exporta os registros de tempo para um arquivo HTML formatado"""
    try:
        empresa_id = get_company_id(empresa)
        if not empresa_id:
            print(f"Empresa '{empresa}' não encontrada")
            return False

        records = get_time_records(empresa_id, date_obj)

        if date_obj:
            month_year = date_obj.strftime('%B %Y')
            file_date = date_obj.strftime('%m_%Y')
        else:
            now = datetime.now()
            month_year = now.strftime('%B %Y')
            file_date = now.strftime('%m_%Y')

        # Calcular total (duração está em segundos no banco)
        total_seconds = sum(record[3] or 0 for record in records)
        total_minutes = total_seconds / 60
        total_hours = total_minutes / 60
        hours = int(total_hours)
        minutes = int((total_hours - hours) * 60)

        # Gerar HTML
        html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório de Horas - {empresa} - {month_year}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: Arial, sans-serif;
            background: #ffffff;
            padding: 40px 20px;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        .header {{
            background: #333333;
            color: white;
            padding: 30px;
            margin-bottom: 30px;
        }}

        .header h1 {{
            font-size: 1.8em;
            margin-bottom: 5px;
            font-weight: normal;
        }}

        .header p {{
            font-size: 1em;
            color: #cccccc;
        }}

        .summary {{
            background: #f5f5f5;
            padding: 20px;
            margin-bottom: 30px;
            border: 1px solid #dddddd;
        }}

        .summary h2 {{
            color: #333;
            font-size: 1.1em;
            margin-bottom: 10px;
            font-weight: normal;
        }}

        .summary .total {{
            font-size: 1.5em;
            color: #000000;
            font-weight: bold;
        }}

        .summary .details {{
            color: #666;
            margin-top: 5px;
            font-size: 0.9em;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            border: 1px solid #dddddd;
        }}

        thead {{
            background: #f5f5f5;
        }}

        th {{
            padding: 12px;
            text-align: left;
            font-weight: bold;
            font-size: 0.9em;
            border: 1px solid #dddddd;
        }}

        tbody tr {{
            border: 1px solid #dddddd;
        }}

        td {{
            padding: 12px;
            color: #333333;
            border: 1px solid #dddddd;
        }}

        .no-records {{
            text-align: center;
            padding: 60px 20px;
            color: #666666;
            border: 1px solid #dddddd;
        }}

        .footer {{
            text-align: center;
            padding: 20px;
            color: #666666;
            font-size: 0.85em;
            margin-top: 30px;
            border-top: 1px solid #dddddd;
        }}

        @media print {{
            body {{
                padding: 0;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Relatório de Horas</h1>
            <p>{empresa} - {month_year}</p>
        </div>

        <div class="summary">
            <h2>Total de Horas Trabalhadas</h2>
            <div class="total">{hours}h {minutes}min</div>
            <div class="details">{int(total_minutes)} minutos • {len(records)} registro(s)</div>
        </div>
"""

        if records:
            html_content += """
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Data Início</th>
                        <th>Hora Início</th>
                        <th>Data Fim</th>
                        <th>Hora Fim</th>
                        <th>Duração</th>
                    </tr>
                </thead>
                <tbody>
"""

            for record in records:
                record_id, inicio, fim, duracao = record

                inicio_dt = datetime.fromisoformat(inicio.replace(' ', 'T'))
                fim_dt = datetime.fromisoformat(fim.replace(' ', 'T')) if fim else None

                inicio_data = inicio_dt.strftime('%d/%m/%Y')
                inicio_hora = inicio_dt.strftime('%H:%M:%S')

                if fim_dt:
                    fim_data = fim_dt.strftime('%d/%m/%Y')
                    fim_hora = fim_dt.strftime('%H:%M:%S')
                    # Converter de segundos para minutos
                    duracao_minutos = duracao / 60
                    duracao_horas = int(duracao_minutos / 60)
                    duracao_mins = int(duracao_minutos % 60)
                    duracao_formatada = f"{duracao_horas}h {duracao_mins}min"
                else:
                    fim_data = '-'
                    fim_hora = '-'
                    duracao_formatada = 'Em andamento'

                html_content += f"""
                    <tr>
                        <td>{record_id}</td>
                        <td>{inicio_data}</td>
                        <td>{inicio_hora}</td>
                        <td>{fim_data}</td>
                        <td>{fim_hora}</td>
                        <td>{duracao_formatada}</td>
                    </tr>
"""

            html_content += """
                </tbody>
            </table>
"""
        else:
            html_content += """
            <div class="no-records">
                <p>Nenhum registro encontrado para este período</p>
            </div>
"""

        html_content += f"""
        </div>

        <div class="footer">
            Gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')} • Timetracker
        </div>
    </div>
</body>
</html>
"""

        # Criar diretório exports se não existir
        os.makedirs("exports", exist_ok=True)

        # Salvar arquivo
        filename = f"{empresa}_{file_date}.html"
        filepath = os.path.join("exports", filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"Relatório HTML exportado com sucesso para: {filepath}")
        return True

    except Exception as e:
        print(f"Erro ao exportar para HTML: {e}")
        return False
