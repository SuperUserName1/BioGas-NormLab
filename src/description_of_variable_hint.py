from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QLineEdit
from PyQt5.QtGui import QIcon
from img_resource_path import resource_path

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
            self.line_edit_reactor_parameters: "(L)Длина реактора в метрах(м)",
            self.line_edit_initial_temperature: "(T)Начальная температура материала градус Цельсия(° C)",
            self.line_edit_temperatur_walls: "(T_стенки)Температура стенок реактора градус Цельсия(° C)",
            self.line_edit_time_step: "(dt)Шаг по времени в секундах(с)",
            self.line_edit_density: "(p)Плотность субстрата в (кг/м³)",
            self.line_edit_heat_capacity: "(Cp)Удельная теплоемкость субстрата в (Дж/(кг·K))",
            self.line_edit_humidity: "(H)Влажность субстрата в %",
            self.line_edit_length_step: "(dx)Шаг по длине реактора в метрах(м)",
            self.line_edit_total_time: "(t_max)Общее время моделирования в секундах(с)",
            self.line_edit_thermal_conductivity: "(𝜆0)Коэфицент теплопроводности субстрата (Вт/(м·K))"
    }
    
    for line_edit in line_edits:
            action = QAction(MainWindow)
            action.setIcon(QIcon(resource_path("img/icon1.png")))
            action.setToolTip(tooltips.get(line_edit, "Информация"))
            line_edit.addAction(action, QLineEdit.TrailingPosition)
            
            # Добавляем отступ
            current_style = line_edit.styleSheet()
            line_edit.setStyleSheet(current_style + "\npadding-right: 25px;")