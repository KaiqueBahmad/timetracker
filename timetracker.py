from controller import TimetrackerController
from helper import Helper
from services.databaseConfig import setup_database

def main():
    setup_database()
    parser = Helper.initializeParser()
    args = parser.parse_args()
    TimetrackerController.handleRequisition(args, parser)

if __name__ == "__main__":
    main()