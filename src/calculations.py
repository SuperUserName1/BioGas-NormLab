import numpy as np
import matplotlib.pyplot as plt

class AdvancedHeatModel:
    def __init__(self, params):
        # Параметры модели
        self.L = params['L']  # длина реактора, м
        self.T_init = params['T_init']  # начальная температура, °C
        self.T_wall = params['T_wall']  # температура стенки, °C
        self.dt = params['dt']  # шаг по времени, с
        self.t_max = params['t_max']  # общее время моделирования, с
        self.rho = params['rho']  # плотность, кг/м3
        self.H = params['H']  # влажность
        self.dx = params['dx']  # шаг по пространству, м
        
        # Физические константы
        self.Cp_dry = 2500
        self.Cp_water = 4186
        self.lambda_dry = 0.2
        self.lambda_water = 0.6
        self.b = 1e-3
        self.T0 = 30
        self.S = 1.0  # площадь поперечного сечения, м²
        
        # Производные параметры
        self.Nx = int(self.L / self.dx) + 1
        self.Nt = int(self.t_max / self.dt)
        self.x = np.linspace(0, self.L, self.Nx)
        self.t = np.arange(0, self.Nt) * self.dt
        
        # Теплофизические свойства
        self.Cp = self.Cp_dry * (1 - self.H) + self.Cp_water * self.H
        self.lambda0 = self.lambda_dry * (1 - self.H) + self.lambda_water * self.H
        
        # Проверка устойчивости
        self._check_stability()
        
        # Инициализация массивов
        self.T = np.full(self.Nx, self.T_init)
        self.T[0] = self.T_wall
        self.T[-1] = self.T_wall
        self.T_history = []
        self.energy = np.zeros(self.Nt)
        self.Q_heating = 0.0
        self.eta = np.zeros(self.Nt)
    
    def _check_stability(self):
        """Проверка устойчивости явной схемы"""
        alpha = self.lambda0 / (self.rho * self.Cp)
        sigma = alpha * self.dt / self.dx**2
        if sigma > 0.5:
            raise ValueError(
                f"Схема неустойчива! Число Куранта = {sigma:.2f} > 0.5. "
                f"Уменьшите dt до {0.5*self.dx**2/alpha:.2f} с или меньше."
            )
    
    def calc_lambda(self, T):
        """Теплопроводность от температуры"""
        return self.lambda0 * (1 + self.b * (T - self.T0))
    
    def solve(self):
        """Решение уравнения теплопроводности"""
        for n in range(self.Nt):
            # Теплопроводность и коэффициент температуропроводности
            lambdas = self.calc_lambda(self.T)
            alpha = lambdas / (self.rho * self.Cp)
            
            # Явная схема
            T_new = self.T.copy()
            for i in range(1, self.Nx-1):
                laplacian = self.T[i+1] - 2*self.T[i] + self.T[i-1]
                T_new[i] = self.T[i] + alpha[i] * self.dt / self.dx**2 * laplacian
            
            # Граничные условия
            T_new[0] = self.T_wall
            T_new[-1] = self.T_wall
            self.T = T_new
            
            # Сохранение истории
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


class Calculations:
    def __init__(self, main_window):
        self.main_window = main_window
        self.ui = main_window.ui
        
        # Получение параметров из UI
        params = {
            'L': self.get_float(self.ui.line_edit_reactor_parameters, 1.0),
            'T_init': self.get_float(self.ui.line_edit_initial_temperature, 15.0),
            'T_wall': self.get_float(self.ui.line_edit_temperatur_walls, 120.0),
            'dt': self.get_float(self.ui.line_edit_time_step, 10.0),
            't_max': self.get_float(self.ui.line_edit_total_time, 10400.0),
            'rho': self.get_float(self.ui.line_edit_density, 1000.0),
            'H': self.get_float(self.ui.line_edit_humidity, 0.7) / 100.0,  
            'dx': self.get_float(self.ui.line_edit_length_step, 0.001)
        }
        
        # Проверка плотности
        if params['rho'] < 100:
            print(f"Предупреждение: Нереально низкая плотность {params['rho']} кг/м³!")
        
        # Создание и запуск модели
        self.model = AdvancedHeatModel(params)
        self.model.solve()
    
    def get_float(self, widget, default):
        """Получение float-значения из виджета"""
        text = widget.text().strip()
        return float(text) if text else default
    
    def start_calculations(self):
        """Выполнение расчетов и визуализация"""
        # Основные результаты
        print(f"Итоговая энергия: {self.model.energy[-1]:.2e} Дж")
        print(f"Подведённое тепло: {self.model.Q_heating:.2e} Дж")
        print(f"КПД системы: {self.model.eta[-1]*100:.2f}%")
        
        # Временные метки для сохненных профилей
        save_indices = [0, self.model.Nt//4, self.model.Nt//2, 3*self.model.Nt//4, self.model.Nt-1]
        saved_profiles = [self.model.T_history[i] for i in save_indices]
        time_labels = [f"{(i * self.model.dt)/3600:.1f} ч" for i in save_indices]
        
        # 1. График температурных профилей
        plt.figure(figsize=(10, 6))
        for profile, label in zip(saved_profiles, time_labels):
            plt.plot(self.model.x, profile, label=label)
        plt.xlabel('Длина реактора, м')
        plt.ylabel('Температура, °C')
        plt.title('Температурные профили во времени')
        plt.legend()
        plt.grid(True)
        plt.ylim(0, self.model.T_wall + 10)  # Фиксированный диапазон
        plt.show()
        
        # 2. График накопленной энергии
        plt.figure(figsize=(10, 6))
        plt.plot(self.model.t / 3600, self.model.energy / 1e6)
        plt.xlabel('Время, ч')
        plt.ylabel('Аккумулированная энергия, МДж')
        plt.title('Накопленная тепловая энергия')
        plt.grid(True)
        plt.show()
        
        # 3. График КПД
        plt.figure(figsize=(10, 6))
        plt.plot(self.model.t / 3600, self.model.eta * 100)
        plt.xlabel('Время, ч')
        plt.ylabel('КПД, %')
        plt.title('Эффективность системы')
        plt.grid(True)
        plt.ylim(0, 100)  # Ограничение 0-100%
        plt.show()
        
        # 4. График температуры в контрольных точках
        plt.figure(figsize=(10, 6))
        idx1, idx2, idx3 = int(self.model.Nx*0.25), int(self.model.Nx*0.5), int(self.model.Nx*0.75)
        plt.plot(self.model.t / 3600, [T[idx1] for T in self.model.T_history], label=f'x={self.model.x[idx1]:.2f} м')
        plt.plot(self.model.t / 3600, [T[idx2] for T in self.model.T_history], label=f'x={self.model.x[idx2]:.2f} м')
        plt.plot(self.model.t / 3600, [T[idx3] for T in self.model.T_history], label=f'x={self.model.x[idx3]:.2f} м')
        plt.xlabel('Время, ч')
        plt.ylabel('Температура, °C')
        plt.title('Температура в фиксированных срезах')
        plt.legend()
        plt.grid(True)
        plt.show()