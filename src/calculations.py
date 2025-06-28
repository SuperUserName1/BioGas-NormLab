import numpy as np
from PyQt5.QtWidgets import QVBoxLayout, QLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

class Calculations:
    def __init__(self, main_window):
        self.main_window = main_window
        self.ui = main_window.ui

        # Инициализация параметров и модели
        self.setup_parameters()
        
        # Создаем холсты для графиков
        self.setup_graph_widgets()
    
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
        
        # Шаг по длине из интерфейса
        self.dx = self.get_float_value(self.ui.line_edit_length_step.text(), 0.01)
        
        # Удельные теплоемкости из интерфейса
        self.Cp_dry = 2500.0
        self.Cp_water = 4186.0
        
        # Теплопроводности
        self.lambda_dry = 0.2
        self.lambda_water = 0.6
        self.b = 1e-3
        self.T0 = 30
        self.S = 1.0  # площадь поперечного сечения, м²
        
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
        """Основной расчетный цикл"""
        # Обновляем параметры перед расчетом
        self.setup_parameters()
        
        # Массивы для результатов
        self.energy = np.zeros(self.Nt)
        self.Q_heating = 0.0
        self.eta = np.zeros(self.Nt)
        self.T_history = []
        self.x = np.linspace(0, self.L, self.Nx)

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

            # Тепловые потоки на границах
            q_left = -lambdas[0] * (self.T[1] - self.T[0]) / self.dx
            q_right = -lambdas[-1] * (self.T[-1] - self.T[-2]) / self.dx
            
            # Подведенная энергия
            dQ_heating = self.S * (q_left - q_right) * self.dt
            self.Q_heating += dQ_heating
            
            # Аккумулированная энергия
            delta_T = self.T - self.T_init
            integral = 0.5 * (delta_T[0] + delta_T[-1]) + np.sum(delta_T[1:-1])
            self.energy[n] = self.rho * self.Cp * self.S * self.dx * integral
            
            # КПД системы
            if self.Q_heating > 0:
                self.eta[n] = (self.energy[n] - self.energy[0]) / self.Q_heating

        # Вывод результатов
        print(f"Итоговая аккумулированная энергия: {self.energy[-1]:.2e} Дж")
        print(f"Подведённое тепло: {self.Q_heating:.2e} Дж")
        print(f"КПД системы: {self.eta[-1]*100:.2f}%")

        # Обновляем метки с результатами
        self.ui.label_accumulated_thermal_energy.setText(f"{self.energy[-1]/1e6:.2f} МДж")
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