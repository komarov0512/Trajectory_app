import tkinter as tk
import customtkinter
import serial
import glob
import sys
from PIL import Image
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import time
import threading

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
    print("Refresh")


def optionmenu_callback(choice):
    print("optionmenu dropdown clicked:", choice)


def buttonConnect_callback():
    while True:
        time.sleep(1)
        print("Connected")


def buttonRecord_callback():
    print("Record")


def buttonStopRecord_callback():
    print("Stop record")


app = customtkinter.CTk()
# app.attributes("-fullscreen", True)
# w = 1280  # width for the Tk root
# h = 960  # height for the Tk root
# ws = app.winfo_screenwidth()
# hs = app.winfo_screenheight()
# x = (ws/2) - (w/2)
# y = (hs/2) - (h/2) - hs*0.02
# app.geometry('%dx%d+%d+%d' % (w, h, x, y))
app.geometry("1000x750")
app.title("Trajectory app")


# Frame
frame_port = customtkinter.CTkFrame(master=app, width=200)  # ,fg_color='gray92')
frame_port.grid(row=0, column=0, padx=10, pady=10, sticky='NSWE')

# Button refresh
buttonRefresh = customtkinter.CTkButton(master=frame_port,
                                        width=30,
                                        height=30,
                                        image=refresh_icon,
                                        text='',
                                        command=buttonRefresh_callback)
buttonRefresh.grid(row=0, column=1, padx=(5, 10), pady=(10, 0))

# OptionMenu for choose port
portlist = get_portlist()
comboboxPortlist = customtkinter.CTkOptionMenu(master=frame_port,
                                               height=30,
                                               values=portlist,
                                               command=optionmenu_callback)
comboboxPortlist.grid(row=0, column=0, padx=(10, 5), pady=(10, 0))
comboboxPortlist.set("Port")

# Button connect to port
buttonConnect = customtkinter.CTkButton(master=frame_port,
                                        text='Connect',
                                        command=threading.Thread(target=buttonConnect_callback).start())
buttonConnect.grid(row=2, column=0, columnspan=2, padx=10, pady=(10, 10), sticky="we")

# Button start record
buttonRecord = customtkinter.CTkButton(master=frame_port,
                                       text='Record',
                                       command=buttonRecord_callback)
buttonRecord.grid(row=3, column=0, columnspan=2, padx=10, pady=(10, 0), sticky="we")

# Button stop record
buttonStopRecord = customtkinter.CTkButton(master=frame_port,
                                           text='Stop record',
                                           command=buttonStopRecord_callback)
buttonStopRecord.grid(row=4, column=0, columnspan=2, padx=10, pady=10, sticky="we")

# Plot figure
fig, ax = plt.subplots()
ax.set_aspect(1)
ax.grid(True)
ax.set_xlim(-200, 200)
ax.set_ylim(-200, 200)
ax.set_xlabel('X')
ax.set_ylabel('Y')
canvas = FigureCanvasTkAgg(fig, master=app)
canvas.get_tk_widget().grid(row=0, column=1, padx=(0, 10), pady=(10, 10), sticky="NSWE")

app.after(0, lambda: app.state('zoomed'))
app.columnconfigure(1, weight=1)
app.rowconfigure(0, weight=1)
app.mainloop()
