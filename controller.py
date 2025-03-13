

class TimetrackerController:
    
    routes = {
        "comando1":1,
        "comando2":2
    }
    
    @staticmethod
    def handleRequisition(args):
        print(args.comando)
        if (args.comando in TimetrackerController.routes):
            print("aeiou")
        pass


class Teste:
    def __init__(self, comando):
        self.comando = comando

if __name__ == "__main__":
    TimetrackerController.handleRequisition(Teste("comando1"))


