import customtkinter
from CTkMessagebox import CTkMessagebox
from tkinter import filedialog
import serial
import glob
import sys
import time
import math
import threading
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime
from scipy.optimize import minimize
from matplotlib.figure import Figure

# For timer
counter = 0
# For stop reading data
reading_data_is_available = True
# For stop recording
record_start = False
# Success connect
connect_check = False
# Port Data Variable
temp_data = []
temp_coord = []
# Recording data array
data_recording = []
# Upload icon for buttonRefresh
refresh_icon = customtkinter.CTkImage(light_image=Image.open('refresh.png'),
                                      dark_image=Image.open('refresh.png'),
                                      size=(20, 20))


def get_portlist():
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result


def buttonRefresh_callback():
    listp = get_portlist()
    comboboxPortlist.configure(values=listp)


def read_serial_data():
    ser = serial.Serial(number_port.get(), baudrate=9600)
    if ser.isOpen():
        global connect_check
        connect_check = True
        CTkMessagebox(message="Port is successfully connected.\nPlease, wait at least 5sec.",
                      icon="check", option_1="Thanks", height=150, width=300)
    while reading_data_is_available:
        try:
            if ser.in_waiting:

                w1, w2, w3, w4 = [], [], [], []
                for k in range(5):
                    packet = ser.readline()
                    packetFloat = [float(i) for i in packet.decode('utf-8').rstrip('\n').split(';')]
                    w1.append(packetFloat[0])
                    w2.append(packetFloat[1])
                    w3.append(packetFloat[2])
                    w4.append(packetFloat[3])
                global temp_data
                temp_data = [float(np.round(np.mean(w1), 2)),
                             float(np.round(np.mean(w2), 2)),
                             float(np.round(np.mean(w3), 2)),
                             float(np.round(np.mean(w4), 2))]
        except Exception as e:
            print(f"Ошибка чтения данных: {e}")
    ser.close()


def buttonConnect_callback():
    if not number_port.get() == "Port":
        threading.Thread(target=read_serial_data).start()
        update_plot()
    else:
        CTkMessagebox(title="Error", message="Click on refresh button and choose a port!",
                      icon="cancel", height=150, width=300)


def recording_data():
    global data_recording
    hertz = 1 / int(hz.get()[0])
    while record_start and reading_data_is_available:
        data_recording.append(temp_coord)
        time.sleep(hertz)


def buttonRecord_callback():
    global record_start, data_recording
    data_recording = []
    if connect_check and not record_start:
        record_start = True
        threading.Thread(target=recording_data).start()
        timer_update()
    else:
        CTkMessagebox(title="Warning!", message="Connect port!",
                      icon="warning", height=150, width=300)


def buttonStopRecord_callback():
    global record_start
    record_start = False


def buttonSaveFile_callback():
    if data_recording:
        types = [("Image", "*.png")]
        file_path = filedialog.asksaveasfilename(title="Save File",
                                                 initialdir=".",
                                                 defaultextension=".txt",
                                                 filetypes=types, )
        if file_path:
            fig1, ax1 = plt.subplots()
            ax1.set_aspect(1)
            ax1.grid(True)
            ax1.set_xlim(-200, 200)
            ax1.set_ylim(-200, 200)
            ax1.set_xlabel('X')
            ax1.set_ylabel('Y')
            points = np.array(data_recording)
            ax1.plot(points[:, 0], points[:, 1])
            fig1.savefig(file_path)
            file = open(file_path.rpartition('.')[0] + ".txt", 'w')
            for row in data_recording:
                file.write(';'.join([str(a) for a in row]) + '\n')
            file.close()
            CTkMessagebox(message="File is successfully saved.",
                          icon="check", option_1="Thanks", height=150, width=300)
    else:
        CTkMessagebox(title="Warning!", message="Recording the data, please.",
                      icon="warning", height=150, width=300)


def timer_update():
    global counter
    counter = 0

    def count():
        global counter
        if record_start:
            display = datetime.fromtimestamp(counter).strftime("%M:%S")
            labelTimer.configure(text=str("Recording:  " + display))
            labelTimer.after(1000, count)
            counter += 1

    # Triggering the start of the counter.
    count()


def compute(points):
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
    if check == 2:
        circles.pop(id1)
        circles.pop(id2)
    elif max(points) - min(points) > 30:
        circles.pop(points.index(min(points)))
    solution = minimize(lambda x: objective(x, circles), initial_guess)

    def correcting(k):
        if k > 200:
            return 200
        elif k < -200:
            return -200
        else:
            return k
    return correcting(solution.x[0]), correcting(solution.x[1])


def update_plot():
    global temp_coord
    try:
        if not len(temp_data) == 0:
            x, y = compute(temp_data)
            temp_coord = [int(x), int(y)]
            labelInfo.configure(text="Coord:(" + str(int(x)) + ";" + str(int(y)) + ")")
            ax.clear()
            ax.plot(x, y, 'ro')
            ax.grid(True)
            ax.set_xlim(-200, 200)
            ax.set_ylim(-200, 200)
            ax.set_xlabel('X')
            ax.set_ylabel('Y')
            canvas.draw()
    except Exception as e:
        print(f"Ошибка обновления графика: {e}")
    buttonConnect.after(500, update_plot)


def buttonThread_callback():
    print("Active:", threading.active_count())
    print(threading.enumerate())


app = customtkinter.CTk()
app.geometry("1000x750")
app.title("Trajectory app")


# Function for close app
def quit_me():
    global reading_data_is_available
    reading_data_is_available = False
    app.quit()
    app.destroy()


app.protocol("WM_DELETE_WINDOW", quit_me)

# Frame
frame_tools = customtkinter.CTkFrame(master=app, width=200)  # ,fg_color='gray92')
frame_tools.grid(row=0, column=0, padx=10, pady=10, sticky='NSWE')

# Button refresh
buttonRefresh = customtkinter.CTkButton(master=frame_tools,
                                        width=30,
                                        height=30,
                                        image=refresh_icon,
                                        text='',
                                        command=buttonRefresh_callback)
buttonRefresh.grid(row=0, column=1, padx=(5, 10), pady=(10, 0))

# Variable with name of port
number_port = customtkinter.StringVar(value="Port")
# OptionMenu for choose port
portlist = get_portlist()
comboboxPortlist = customtkinter.CTkOptionMenu(master=frame_tools,
                                               height=30,
                                               values=portlist,
                                               variable=number_port)
comboboxPortlist.grid(row=0, column=0, padx=(10, 5), pady=(10, 0))
comboboxPortlist.set("Port")

# Button connect to port
buttonConnect = customtkinter.CTkButton(master=frame_tools,
                                        text='Connect',
                                        command=buttonConnect_callback)
buttonConnect.grid(row=2, column=0, columnspan=2, padx=10, pady=(10, 10), sticky="we")

# X and Y coordinates
labelInfo = customtkinter.CTkLabel(master=frame_tools, font=('Comic Sans MS', 20), text="Coord:(00;00)", )
labelInfo.grid(row=3, column=0, columnspan=2, padx=10, pady=(10, 10), sticky="w")

# Parameter record
# Variable Hz
hz = customtkinter.StringVar(value="1hz")
# OptionMenu for choose Hz
comboboxHZlist = customtkinter.CTkOptionMenu(master=frame_tools,
                                             height=30,
                                             values=["1hz", "2hz"],
                                             variable=hz)
comboboxHZlist.grid(row=4, column=0, columnspan=2, padx=10, pady=(10, 0), sticky="we")
comboboxHZlist.set("1hz")

# Button start record
buttonRecord = customtkinter.CTkButton(master=frame_tools,
                                       text='Record',
                                       command=buttonRecord_callback)
buttonRecord.grid(row=5, column=0, columnspan=2, padx=10, pady=(10, 0), sticky="we")

# Button stop record
buttonStopRecord = customtkinter.CTkButton(master=frame_tools,
                                           text='Stop record',
                                           command=buttonStopRecord_callback)
buttonStopRecord.grid(row=6, column=0, columnspan=2, padx=10, pady=(10, 0), sticky="we")

# Timer record
labelTimer = customtkinter.CTkLabel(master=frame_tools, text="Recording:  00:00", font=('Comic Sans MS', 18))
labelTimer.grid(row=7, column=0, columnspan=2, padx=10, pady=10, sticky="w")

# Button save file
buttonSaveFile = customtkinter.CTkButton(master=frame_tools,
                                         text='Save file',
                                         command=buttonSaveFile_callback)
buttonSaveFile.grid(row=8, column=0, columnspan=2, padx=10, pady=10, sticky="we")

# Plot figure
fig = Figure()
ax = fig.add_subplot()
ax.set_aspect(1)
ax.grid(True)
ax.set_xlim(-200, 200)
ax.set_ylim(-200, 200)
ax.set_xlabel('X')
ax.set_ylabel('Y')
canvas = FigureCanvasTkAgg(fig, master=app)
canvas.get_tk_widget().grid(row=0, column=1, padx=(0, 10), pady=(10, 10), sticky="NSWE")

# Application
app.after(0, lambda: app.state('zoomed'))
app.columnconfigure(1, weight=1)
app.rowconfigure(0, weight=1)
app.mainloop()
