from PyQt5.QtWidgets import QMainWindow, QLineEdit

from main_window_ui import Ui_MainWindow
from notifications import Notifications
from calculations import Calculations

class MainWindowLogic(QMainWindow):

    def __init__(self):
        super().__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.notification = Notifications(self)
        self.calculations = Calculations(self)

        self.ui.push_button_window_results.clicked.connect(self.clickedButtonWindowResults)
        self.ui.push_button_window_calculation.clicked.connect(self.clickedButtonWindowCalculations)
        self.ui.push_button_simulate.clicked.connect(self.clickedButtonSimulate)

        self.ui.push_button_import_temperature_distribution_csv.clicked.connect(self.clickedPushButtonImportTemperatureDistributionCsv)
        self.ui.push_button_import_energy_data_csv.clicked.connect(self.clickedPushButtonImportEnergyDataCsv)
        self.ui.push_button_import_all_xlsx.clicked.connect(self.clickedPushButtonImportAllXlsx)

 
    def clickedPushButtonImportTemperatureDistributionCsv(self):
        self.calculations.export_temperature_data()


    def clickedPushButtonImportEnergyDataCsv(self):
        self.calculations.export_energy_data()
    
    
    def clickedPushButtonImportAllXlsx(self):
        self.calculations.export_all_data()
        

    def clickedButtonWindowResults(self):
        self.ui.stackedWidget.setCurrentIndex(1)


    def clickedButtonWindowCalculations(self):        
        self.ui.stackedWidget.setCurrentIndex(0)


    def clickedButtonSimulate(self):
        try:
            for row in range(self.ui.grid_layout_line_text.rowCount()):
                for col in range(self.ui.grid_layout_line_text.columnCount()):
                    item = self.ui.grid_layout_line_text.itemAtPosition(row, col)

                    line_edit_widget = item.widget()

                    if not isinstance(line_edit_widget, QLineEdit):
                        continue

                    value = line_edit_widget.text()
                    value = float(value)

            self.calculations = Calculations(self)
            self.calculations.start_calculations()
            self.notification.start_notification("img/success_modeling.png")
        except ValueError:
            print("error convert to float")
            self.notification.start_notification("img/error.png")