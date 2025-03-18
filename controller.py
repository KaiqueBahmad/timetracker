from services.cursesService import show_calendar, show_watch_time
from services.dataConsultingService import get_current_status, show_records
from services.exportService import export_data
from services.trackService import start_tracking, stop_tracking


class TimetrackerController:
    
    routes = {
        "start"     :   lambda args:start_tracking(args.empresa),
        "stop"      :   lambda args:stop_tracking(),
        "show"      :   lambda args:show_records(args.empresa, args.inicio, args.fim),
        "saldo"     :   lambda args:print("Ainda não implementado"), #calcular_saldo(args.empresa, args.meta)
        "status"    :   lambda args:get_current_status(),
        "watch"     :   lambda args:show_watch_time(),
        "calendar"  :   lambda args:show_calendar(),
        "export"    :   lambda args: export_data(args.formato, args.empresa, args.data if hasattr(args, 'data') else None)

    }
    
    @staticmethod
    def handleRequisition(args, parser):
        if (args.comando in TimetrackerController.routes):
            TimetrackerController.routes[args.comando](args)
            return
        
        parser.print_help()


if __name__ == "__main__":
    class Teste:
        def __init__(self, comando):
            self.comando = comando
    TimetrackerController.handleRequisition(Teste("comando1"))


