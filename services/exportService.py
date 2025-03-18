from datetime import datetime
import importlib
import sys
from pathlib import Path
from exporters.ExcelExporter import exportToExcel

format_implementations = {
    'xls': exportToExcel,
}

def export_data(formato, empresa, data=None):
    if formato not in format_implementations:
        supported_formats = ', '.join(format_implementations.keys())
        raise ValueError(f"Formato '{formato}' não suportado. Formatos disponíveis: {supported_formats}")
    
    try:
        date_obj = None
        if data:
            try:
                month, year = map(int, data.split('/'))
                year = 2000 + year if year < 100 else year
                date_obj = datetime(year, month, 1)
            except (ValueError, TypeError):
                raise ValueError("Formato de data inválido. Use MM/YY (ex: 02/25)")
        
        export_function = format_implementations[formato]
        return export_function(empresa, date_obj)
        
    except Exception as e:
        print(f"Erro ao exportar: {e}", file=sys.stderr)
        return False


if __name__ == "__main__":
    pass