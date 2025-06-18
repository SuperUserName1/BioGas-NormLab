import sys

from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QMainWindow

from main_window_ui import Ui_MainWindow

class MainWindowLogic(QMainWindow):

    def __init__(self):
        super().__init__()
        
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.push_button_window_results.clicked.connect(self.clickedButtonWindowResults)
        self.ui.push_button_window_calculation.clicked.connect(self.clickedButtonWindowCalculations)
        
        

    def clickedButtonWindowResults(self):
        self.ui.stackedWidget.setCurrentIndex(1)


    def clickedButtonWindowCalculations(self):        
        self.ui.stackedWidget.setCurrentIndex(0)