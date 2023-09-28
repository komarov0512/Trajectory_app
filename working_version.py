import math
import serial
import matplotlib.pyplot as plt
import threading
import numpy as np
from scipy.optimize import minimize

# Инициализация последовательного порта
ser = serial.Serial('COM3', baudrate=9600)  # Замените 'COM1' на ваш порт и настройки

# Очередь для хранения данных
data = []
# max_data_points = 5  # Максимальное количество точек для отображения
# x_data = []
# y_data = []


# Функция для чтения данных из порта и добавления их в очередь
def read_serial_data():
    while True:
        try:
            # if len(data) >= 20: break
            if ser.in_waiting:
                w1, w2, w3, w4 = [], [], [], []
                for k in range(5):
                    packet = ser.readline()
                    packetFloat = [float(i) for i in packet.decode('utf-8').rstrip('\n').split(';')]
                    w1.append(packetFloat[0])
                    w2.append(packetFloat[1])
                    w3.append(packetFloat[2])
                    w4.append(packetFloat[3])
                data.append([float(np.round(np.mean(w1), 2)),
                             float(np.round(np.mean(w2), 2)),
                             float(np.round(np.mean(w3), 2)),
                             float(np.round(np.mean(w4), 2))])
        except Exception as e:
            print(f"Ошибка чтения данных: {e}")


def compute(points):
    print(points)
    radiuses = []
    for point in points:
        r = 400 - (400 / sum(points) * point)
        radiuses.append(r)

    def distance(point, circle):
        center, radius = circle
        return math.sqrt((point[0] - center[0]) ** 2 + (point[1] - center[1]) ** 2) - radius

    def objective(point, circles):
        return np.sum([distance(point, circle) ** 2 for circle in circles])

    initial_guess = [1, 1]

    circles = [
        (np.array((-200, -200)), radiuses[0]),
        (np.array((200, -200)), radiuses[1]),
        (np.array((200, 200)), radiuses[2]),
        (np.array((-200, 200)), radiuses[3])
    ]

    check = 0
    id1 = id2 = -1
    for i in range(len(points)):
        if points[i] <= 2:
            if id1 == -1:
                id1 = i
                check += 1
            else:
                id2 = i - 1
                check += 1
                break
    # print('id1 =', id1, '; id2 = ', id2)
    if check == 2:
        circles.pop(id1)
        circles.pop(id2)
    elif max(points) - min(points) > 30:
        print('Hey!')
        circles.pop(points.index(min(points)))

    print("len: ", len(circles))

    solution = minimize(lambda x: objective(x, circles), initial_guess)

    def correcting(k):
        if k > 200:
            return 200
        elif k < -200:
            return -200
        else:
            return k

    print('solution: ', correcting(solution.x[0]), correcting(solution.x[1]))
    return correcting(solution.x[0]), correcting(solution.x[1])


# Функция для обновления графика в реальном времени
def update_plot():
    fig, ax = plt.subplots(figsize=(10, 10))
    while True:
        try:
            if not len(data) == 0:
                x, y = compute(data[-1])
                ax.clear()
                ax.plot(x, y, 'ro')
                ax.set_aspect(1)
                ax.grid(True)
                ax.set_xlim(-200, 200)
                ax.set_ylim(-200, 200)
                ax.set_xlabel('X')
                ax.set_ylabel('Y')
                plt.pause(1)  # Обновление графика с небольшой задержкой
        except Exception as e:
            print(f"Ошибка обновления графика: {e}")


# Создание и запуск потоков для чтения данных и обновления графика
serial_thread = threading.Thread(target=read_serial_data)
# plot_thread = threading.Thread(target=update_plot)

serial_thread.start()
update_plot()
# plot_thread.start()

# # Ожидание завершения потоков (или добавьте логику для их корректного завершения)
serial_thread.join()
# plot_thread.join()
