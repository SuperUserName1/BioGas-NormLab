import numpy as np
import pandas as pd
from PyQt5.QtWidgets import (QVBoxLayout, QFileDialog, QMessageBox)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import openpyxl

class Calculations:
    def __init__(self, main_window):
        self.main_window = main_window
        self.ui = main_window.ui

        # Инициализация параметров и модели
        self.setup_parameters()
        
        # Создаем холсты для графиков
        self.setup_graph_widgets()
        
        self.temperature_exported = False
        self.energy_exported = False
        self.all_exported = False
 
    def clear_layout(self, layout):
        """Очистка содержимого layout"""
        if layout is None:  # Добавленная проверка
            return
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def setup_graph_widgets(self):
        """Создаем холсты и панели инструментов для графиков"""
        # Очищаем существующие виджеты
        self.clear_layout(self.ui.graph_temperature_profiles.layout())
        self.clear_layout(self.ui.graph_thermal_energy.layout())
        self.clear_layout(self.ui.graph_temperature_change.layout())
        
        # График 1: Температурные профили в разные моменты времени
        self.figure1 = Figure()
        self.canvas1 = FigureCanvas(self.figure1)
        self.toolbar1 = NavigationToolbar(self.canvas1, self.ui.graph_temperature_profiles)
        
        # Проверяем и создаем новый layout, если нужно
        if self.ui.graph_temperature_profiles.layout() is None:
            layout1 = QVBoxLayout(self.ui.graph_temperature_profiles)
        else:
            layout1 = self.ui.graph_temperature_profiles.layout()
        layout1.addWidget(self.toolbar1)
        layout1.addWidget(self.canvas1)
        
        # График 2: Накопленная энергия
        self.figure2 = Figure()
        self.canvas2 = FigureCanvas(self.figure2)
        self.toolbar2 = NavigationToolbar(self.canvas2, self.ui.graph_thermal_energy)
        
        if self.ui.graph_thermal_energy.layout() is None:
            layout2 = QVBoxLayout(self.ui.graph_thermal_energy)
        else:
            layout2 = self.ui.graph_thermal_energy.layout()
        layout2.addWidget(self.toolbar2)
        layout2.addWidget(self.canvas2)
        
        # График 3: Температура в срезах
        self.figure3 = Figure()
        self.canvas3 = FigureCanvas(self.figure3)
        self.toolbar3 = NavigationToolbar(self.canvas3, self.ui.graph_temperature_change)
        
        if self.ui.graph_temperature_change.layout() is None:
            layout3 = QVBoxLayout(self.ui.graph_temperature_change)
        else:
            layout3 = self.ui.graph_temperature_change.layout()
        layout3.addWidget(self.toolbar3)
        layout3.addWidget(self.canvas3)

    def setup_parameters(self):
        """Инициализация параметров модели"""
        # Получение значений из интерфейса
        self.T_wall = self.get_float_value(self.ui.line_edit_temperatur_walls.text(), 20.0)
        self.L = self.get_float_value(self.ui.line_edit_reactor_parameters.text(), 1.0)                  
        self.T_init = self.get_float_value(self.ui.line_edit_initial_temperature.text(), 20.0)
        self.dt = self.get_float_value(self.ui.line_edit_time_step.text(), 1.0)                    
        self.t_max = self.get_float_value(self.ui.line_edit_total_time.text(), 10.0)            
        self.rho = self.get_float_value(self.ui.line_edit_density.text(), 1000.0)               
        self.H = self.get_float_value(self.ui.line_edit_humidity.text(), 0.5)
        self.dx = self.get_float_value(self.ui.line_edit_length_step.text(), 0.01)
        self.Cp_dry =  self.get_float_value(self.ui.line_edit_heat_capacity.text(), 2500.0)
        self.lambda_dry = self.get_float_value(self.ui.line_edit_thermal_conductivity.text(), 0.1)
        
        self.Cp_water = 4186.0
        
        # Теплопроводности
        self.lambda_water = 0.6
        self.b = 1e-3
        self.T0 = 45
        
        # Расчет производных параметров
        self.Nx = int(self.L / self.dx) + 1 if self.dx > 0 else 101
        self.Nt = int(self.t_max / self.dt) if self.dt > 0 else 100
        
        # Расчет теплоемкости с учетом влажности
        self.Cp = self.calculate_cp(self.H / 100.0)  # преобразуем % в долю
        
        # Расчет базовой теплопроводности
        self.lambda0 = self.lambda_dry * (1 - self.H / 100.0) + self.lambda_water * (self.H / 100.0)

        # Инициализация температурного поля
        self.T = np.full(self.Nx, self.T_init)
        self.T[0] = self.T_wall
        self.T[-1] = self.T_wall

        # Проверка устойчивости
        self.check_stability()

    def calculate_cp(self, H_fraction):
        """Расчет удельной теплоемкости с учетом влажности"""
        return self.Cp_dry * (1 - H_fraction) + self.Cp_water * H_fraction

    def check_stability(self):
        """Проверка устойчивости явной схемы"""
        alpha = self.lambda0 / (self.rho * self.Cp)
        sigma = alpha * self.dt / self.dx**2
        if sigma > 0.5:
            print(f"Предупреждение: Схема может быть неустойчивой! Число Куранта = {sigma:.2f} > 0.5")
            print(f"Рекомендуется уменьшить шаг по времени до {0.5*self.dx**2/alpha:.2f} с")


    def get_float_value(self, text, default=0.0):
        """Получение float-значения из текста"""
        if text.strip() == "":
            return default
        try:
            return float(text)
        except ValueError:
            return default


    def start_calculations(self):
        """Основной расчетный цикл (без использования площади сечения)"""
        # Обновляем параметры перед расчетом
        self.setup_parameters()
        
        # Массивы для результатов
        self.energy = np.zeros(self.Nt)  # Удельная энергия (Дж/м)
        self.eta = np.zeros(self.Nt)
        self.T_history = []
        self.x = np.linspace(0, self.L, self.Nx)
        
        # Переменные для тепловых потоков
        self.Q_heating = 0.0  # Суммарное удельное подведенное тепло (Дж/м)
        self.energy_initial = 0.0  # Начальная энергия

        # Расчет начальной энергии
        for i in range(self.Nx):
            self.energy_initial += self.rho * self.Cp * (self.T[i] - self.T_init) * self.dx

        # Основной цикл
        for n in range(self.Nt):
            # Теплопроводность и коэффициент температуропроводности
            lambdas = self.lambda0 * (1 + self.b * (self.T - self.T0))
            alpha = lambdas / (self.rho * self.Cp)

            # Явная схема
            T_new = self.T.copy()
            for i in range(1, self.Nx-1):
                T_new[i] = self.T[i] + alpha[i] * self.dt / self.dx**2 * (self.T[i+1] - 2*self.T[i] + self.T[i-1])
            
            # Граничные условия
            T_new[0] = self.T_wall
            T_new[-1] = self.T_wall
            self.T = T_new
            self.T_history.append(self.T.copy())

            # Тепловые потоки на границах (Вт/м)
            q_left = -lambdas[0] * (self.T[1] - self.T[0]) / self.dx
            q_right = -lambdas[-1] * (self.T[-1] - self.T[-2]) / self.dx
            
            # Удельное подведенное тепло (Дж/м)
            dQ_heating = (q_left - q_right) * self.dt
            self.Q_heating += dQ_heating
            
            # Удельная аккумулированная энергия (Дж/м)
            accumulated_energy = 0.0
            for i in range(self.Nx):
                accumulated_energy += self.rho * self.Cp * (self.T[i] - self.T_init) * self.dx
            self.energy[n] = accumulated_energy - self.energy_initial
            
            # КПД системы
            if self.Q_heating > 0 and self.energy[n] > 0:
                self.eta[n] = min(1.0, self.energy[n] / self.Q_heating)
            else:
                self.eta[n] = 0.0

        # Вывод результатов
        print(f"Итоговая аккумулированная энергия: {self.energy[-1]:.2e} Дж/м")
        print(f"Подведённое тепло: {self.Q_heating:.2e} Дж/м")
        print(f"КПД системы: {self.eta[-1]*100:.2f}%")
        print(f"Количество ячеек: {self.Nx}")
        print(f"Длина ячейки dx: {self.dx:.6f} м")

        # Обновляем метки с результатами
        self.ui.label_accumulated_thermal_energy.setText(f"{self.energy[-1]/1e6:.2f} МДж/м")
        self.ui.label_cop_base_heating.setText(f"{self.eta[-1]*100:.2f} %")
        
        # Обновление графиков
        self.update_plots()


    def update_plots(self):
        """Обновление всех графиков"""
        self.plot_temperature_profiles()
        self.plot_accumulated_energy()
        self.plot_temperature_slices()
        
        # Перерисовка холстов
        self.canvas1.draw()
        self.canvas2.draw()
        self.canvas3.draw()

    def plot_temperature_profiles(self):
        """Температурные профили в разные моменты времени (для graph_temperature_profiles)"""
        self.figure1.clear()
        ax = self.figure1.add_subplot(111)
        
        # Выбор моментов времени для отображения
        save_indices = [0, self.Nt//4, self.Nt//2, 3*self.Nt//4, self.Nt-1]
        time_labels = [f"{(i * self.dt)/3600:.1f} ч" for i in save_indices]
        
        for i, idx in enumerate(save_indices):
            ax.plot(self.x, self.T_history[idx], label=time_labels[i])
        
        ax.set_xlabel('Длина реактора, м')
        ax.set_ylabel('Температура, °C')
        ax.set_title('Температурные профили во времени')
        ax.legend()
        ax.grid(True)       
        
        # Определение границ по Y
        y_min = min(self.T_init, self.T_wall) - 5
        y_max = max(self.T_init, self.T_wall) + 10
        ax.set_ylim(y_min, y_max)
        
    def plot_accumulated_energy(self):
        """График накопленной энергии (для graph_thermal_energy)"""
        self.figure2.clear()
        ax = self.figure2.add_subplot(111)
        
        time_hours = np.arange(self.Nt) * self.dt / 3600
        ax.plot(time_hours, self.energy / 1e6)
        
        ax.set_xlabel('Время, ч')
        ax.set_ylabel('Аккумулированная энергия, МДж')
        ax.set_title('Накопленная тепловая энергия')
        ax.grid(True)

    def plot_temperature_slices(self):
        """Температура в фиксированных срезах (для graph_temperature_change)"""
        self.figure3.clear()
        ax = self.figure3.add_subplot(111)
        
        time_hours = np.arange(self.Nt) * self.dt / 3600
        
        # Выбор трех точек: начало, середина и конец реактора
        idx1 = 0  # начало
        idx2 = self.Nx // 2  # середина
        idx3 = self.Nx - 1  # конец
        
        ax.plot(time_hours, [T[idx1] for T in self.T_history], label=f'x={self.x[idx1]:.2f} м (начало)')
        ax.plot(time_hours, [T[idx2] for T in self.T_history], label=f'x={self.x[idx2]:.2f} м (середина)')
        ax.plot(time_hours, [T[idx3] for T in self.T_history], label=f'x={self.x[idx3]:.2f} м (конец)')
        
        ax.set_xlabel('Время, ч')
        ax.set_ylabel('Температура, °C')
        ax.set_title('Температура в фиксированных срезах')
        ax.legend()
        ax.grid(True)
  
  
    def export_temperature_data(self):
        """Экспорт температурных данных в CSV в том же формате, что и в листе Temperature"""
        if not hasattr(self, 'T_history') or len(self.T_history) == 0:
            QMessageBox.warning(self.main_window, "Нет данных", "Сначала выполните расчеты")
            return
            
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self.main_window,
                "Экспорт температурных данных",
                "temperature_data.csv",
                "CSV Files (*.csv)"
            )
            
            if not filename:
                return
                
            # Выбор моментов времени для экспорта (те же, что и в export_all_data)
            save_indices = [0, self.Nt//4, self.Nt//2, 3*self.Nt//4, self.Nt-1]
            time_points = [i * self.dt for i in save_indices]
            
            # Создаем данные для экспорта
            headers = ["x (м)"] + [f"t = {tp:.1f} с" for tp in time_points]
            data = [headers]
            
            # Добавляем строки с данными
            for i, x_val in enumerate(self.x):
                row = [f"{x_val:.3f}".replace('.', ',')]  # Заменяем точку на запятую в координате X
                for idx in save_indices:
                    # Форматируем температуру с запятой в качестве разделителя
                    temp_str = f"{self.T_history[idx][i]:.8f}".replace('.', ',')
                    row.append(temp_str)
                data.append(row)
            
            # Записываем данные в CSV с правильным разделителем
            with open(filename, 'w', encoding='utf-8-sig') as f:
                # Используем точку с запятой в качестве разделителя
                for row in data:
                    f.write(";".join(row) + "\n")
            
            QMessageBox.information(self.main_window, "Успех", 
                                   "Температурные данные успешно экспортированы в формате CSV!")
            
        except Exception as e:
            QMessageBox.critical(self.main_window, "Ошибка", 
                                f"Ошибка экспорта: {str(e)}")

    def export_energy_data(self):
        """Экспорт энергетических данных в CSV с разделением по времени"""
        if not hasattr(self, 'energy') or len(self.energy) == 0:
            QMessageBox.warning(self.main_window, "Нет данных", "Сначала выполните расчеты")
            return
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self.main_window,
                "Экспорт энергетических данных",
                "thermal_energy.csv",
                "CSV Files (*.csv)"
            )
            if not filename:
                return
            
            # Создание DataFrame с энергетическими параметрами
            energy_data = {
                't (с)': np.arange(self.Nt) * self.dt,
                't (ч)': np.arange(self.Nt) * self.dt / 3600,
                'Энергия (Дж)': self.energy,
                'КПД (%)': self.eta * 100
            }
            energy_df = pd.DataFrame(energy_data)
            
            # Сохранение в CSV с правильной кодировкой
            energy_df.to_csv(filename, 
                            index=False, 
                            sep=';', 
                            decimal=',',
                            encoding='utf-8-sig')  # Добавлена правильная кодировка
            
            QMessageBox.information(self.main_window, "Успех", "Энергетические данные успешно экспортированы!")
        except Exception as e:
            QMessageBox.critical(self.main_window, "Ошибка", f"Ошибка экспорта: {str(e)}")
   

    def export_all_data(self):
        """Экспорт всех данных в Excel"""
        if not hasattr(self, 'T_history') or not hasattr(self, 'energy'):
            QMessageBox.warning(self.main_window, "Нет данных", "Сначала выполните расчеты")
            return
            
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self.main_window,
                "Экспорт всех данных",
                "simulation_results.xlsx",
                "Excel Files (*.xlsx)"
            )
            
            if not filename:
                return
                
            # Создаем Excel writer
            with pd.ExcelWriter(filename) as writer:
                # Экспорт температурных данных
                save_indices = [0, self.Nt//4, self.Nt//2, 3*self.Nt//4, self.Nt-1]
                time_points = [i * self.dt for i in save_indices]
                
                temp_data = {'x (м)': self.x}
                for i, idx in enumerate(save_indices):
                    temp_data[f"t = {time_points[i]:.1f} с"] = self.T_history[idx]
                
                temp_df = pd.DataFrame(temp_data)
                temp_df.to_excel(writer, sheet_name='Temperature', index=False)
                
                # Экспорт энергетических данных
                energy_data = {
                    't (с)': np.arange(self.Nt) * self.dt,
                    't (ч)': np.arange(self.Nt) * self.dt / 3600,
                    'Энергия (Дж)': self.energy,
                    'КПД (%)': self.eta * 100
                }
                
                energy_df = pd.DataFrame(energy_data)
                energy_df.to_excel(writer, sheet_name='Energy', index=False)
                
                # Экспорт параметров модели
                params_data = {
                    'Параметр': ['Длина реактора', 'Температура стенки', 'Начальная температура',
                                 'Шаг по времени', 'Общее время', 'Плотность', 'Влажность',
                                 'Теплоемкость сухого вещества', 'Теплоемкость воды'],
                    'Значение': [self.L, self.T_wall, self.T_init, self.dt, self.t_max,
                                 self.rho, self.H, self.Cp_dry, self.Cp_water],
                    'Единицы': ['м', '°C', '°C', 'с', 'с', 'кг/м³', '%', 'Дж/(кг·K)', 'Дж/(кг·K)']
                }
                
                params_df = pd.DataFrame(params_data)
                params_df.to_excel(writer, sheet_name='Parameters', index=False)
            
            QMessageBox.information(self.main_window, "Успех", "Все данные успешно экспортированы в Excel!")
            
        except Exception as e:
            QMessageBox.critical(self.main_window, "Ошибка", f"Ошибка экспорта: {str(e)}")