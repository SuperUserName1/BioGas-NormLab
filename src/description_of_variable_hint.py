from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QLineEdit
from PyQt5.QtGui import QIcon

def add_info_icons_to_line_edits(self, MainWindow):
    line_edits = [
            self.line_edit_reactor_parameters,
            self.line_edit_initial_temperature,
            self.line_edit_temperatur_walls,
            self.line_edit_time_step,
            self.line_edit_density,
            self.line_edit_heat_capacity,
            self.line_edit_humidity,
            self.line_edit_length_step,
            self.line_edit_total_time,
            self.line_edit_thermal_conductivity
    ]
    
    tooltips = {
            self.line_edit_reactor_parameters: "Длина реактора в метрах",
            self.line_edit_initial_temperature: "Начальная температура материала",
            self.line_edit_temperatur_walls: "Температура стенок реактора",
            self.line_edit_time_step: "Шаг по времени в секундах",
            self.line_edit_density: "Плотность материала в кг/м³",
            self.line_edit_heat_capacity: "Удельная теплоемкость в Дж/(кг·K)",
            self.line_edit_humidity: "Влажность материала в %",
            self.line_edit_length_step: "Шаг по длине реактора в метрах",
            self.line_edit_total_time: "Общее время моделирования в секундах",
            self.line_edit_thermal_conductivity: "Теплопроводимость :)"
    }
    
    for line_edit in line_edits:
            action = QAction(MainWindow)
            action.setIcon(QIcon("img/icon.png"))
            action.setToolTip(tooltips.get(line_edit, "Информация"))
            line_edit.addAction(action, QLineEdit.TrailingPosition)
            
            # Добавляем отступ
            current_style = line_edit.styleSheet()
            line_edit.setStyleSheet(current_style + "\npadding-right: 25px;")