import sys

from PyQt5.QtWidgets import QApplication
from main_window import MainWindowLogic

def main(): 
    app = QApplication(sys.argv)
    window = MainWindowLogic()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()    

