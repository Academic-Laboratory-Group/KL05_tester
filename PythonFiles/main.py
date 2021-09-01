import glob
import os
import sys
import time
import subprocess

import PySimpleGUI as sg
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import serial.tools.list_ports
import win32api

g_possibleTypesOfTest = ['ADC', 'Power Supply']


# -------------------------------------------
# Function to find all available serial ports
# -------------------------------------------
def serial_ports():
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

    if not result:
        result.append('unconnected')

    return result


# -------------------------------------
# Function to find all available drives
# -------------------------------------
def drive_list():
    drives = win32api.GetLogicalDriveStrings()
    drives = drives.split('\000')[:-1]

    return drives


# ------------------------------
# Function to create main layout
# ------------------------------
def create_layout():
    serialList = serial_ports()
    driveList = drive_list()
    col1 = [[sg.Text('Test', size=(10, 1),
                     font='Helvetica 14'),
            sg.Combo(g_possibleTypesOfTest, size=(20, 1), pad=((20, 0), 3),
                     default_value=g_possibleTypesOfTest[0],
                     enable_events=True,
                     key="-TESTTYPE-")],
            [sg.Text('Disk KL05', size=(10, 1),
                     font='Helvetica 14'),
            sg.Combo(driveList, size=(20, 1), pad=((20, 0), 3),
                     default_value=driveList[0], key="-KLDRIVE-")],
            [sg.Text('COM KL05', size=(10, 1),
                     font='Helvetica 14'),
            sg.Combo(serialList, size=(20, 1), pad=((20, 0), 3), default_value=serialList[0], key="-KLCOM-")],
            [sg.Text('Disk STM32', size=(10, 1),
                     font='Helvetica 14'),
            sg.Combo(driveList, size=(20, 1), pad=((20, 0), 3), default_value=driveList[0], key="-STMDRIVE-")],
            [sg.Text('COM STM32', size=(10, 1),
                     font='Helvetica 14'),
            sg.Combo(serialList, size=(20, 1), pad=((20, 0), 3), default_value=serialList[0], key="-STMCOM-")]]
    col2 = [[sg.Button('Start', key="-STARTBUTTON-",
                       size=(15, 0), pad=((20, 0), 3), font='Helvetica 12',
                       button_color="GREEN"),
             sg.Button('Refresh ports', key="-REFRESHBUTTON-", size=(15, 0), pad=((20, 0), 3), font='Helvetica 12',
                       button_color="BLUE")],
            [sg.Text(text="", key="-OUTPUTTEXT-", size=(30, 5),
                     pad=((20, 0), 3), font='Helvetica 14')]]
    layout = [[sg.Text('KL05 Tester', size=(40, 1),
                       justification='center', font='Helvetica 20')],
              [sg.Graph((640, 480), (0, 0), (640, 480), key='-CANVAS-')],
              [sg.Column(col1, vertical_alignment='top'), sg.Column(col2, vertical_alignment='top')]]

    return layout


# ----------------
# Open serial port
# ----------------
def serial_open(port_number, speed):
    ser = []
    try:
        ser = serial.Serial(port_number, speed, timeout=2)
    except:
        sg.popup("Serial disconnected: " + port_number)
    return ser


# ---------------------
# Read line from serial
# ---------------------
def serial_receive(my_serial):
    data = my_serial.readline()
    if data:
        return data.decode()
    return []


# ---------------------------
# Send data using serial port
# ---------------------------
def serial_send(my_serial, data):
    my_serial.write(data.encode())


# -----------------------------------------------------------------
# Flash microcontroler using file that is in the hexFile folder
# Flashing is done by copying the .hex file to the appropriate disk
# -----------------------------------------------------------------
def flash_micro(file, drive):
    currentpath = os.path.dirname(os.path.abspath(__file__))
    command = 'cmd /c "copy ' + currentpath + \
        '\\hexFiles\\{} {}"'.format(file, drive)
    print(command)
    if os.system(command):
        raise Exception(subprocess.check_output(['ls', '-l']))


# -----------------------------------------------------------------
# Exception info on popup window
# -----------------------------------------------------------------
def process_exception(window, values, message):
    sg.popup(message)
    window.Element(
        '-OUTPUTTEXT-').Update(values['-TESTTYPE-'] + " test interrupted. " + message)
    window.refresh()


# ---------------------------------------
# Function to draw on a matplotlib canvas
# ---------------------------------------
def update_figADC(fig, ax, ax2, x, y, c, label):
    ax2.cla()
    ax2.set_yticks([])
    ax.cla()
    ax.grid()
    ax.set_xlabel("Given value")
    ax.set_ylabel("Measured value")
    ax.set_xlim([-1, 4200])
    ax.set_ylim([-1, 4200])
    ax.plot(x, y, c, label=label)
    fig.tight_layout()
    plt.legend(loc="upper left")
    fig.canvas.draw()


# ---------------------------------------
# Function to draw on a matplotlib canvas
# figure for Power Supply test
# ---------------------------------------
def update_figPS(fig, ax1, ax2, x, y1, y2, c1, c2):
    ax1.cla()
    ax2.cla()
    ax1.grid()
    ax2.grid()
    ax1.set_xlabel("Time [s]")
    ax1.set_ylabel("Voltage [V]")
    line1 = ax1.plot(x, y1, c1, label="Voltage [V]")
    ax2.set_ylabel("Current [A]")
    line2 = ax2.plot(x, y2, c2, label="Current [A]")

    # added these three lines
    lns = line1+line2
    labs = [l.get_label() for l in lns]
    ax1.legend(lns, labs, loc="upper right")
    fig.tight_layout()
    fig.canvas.draw()


# -----------------------------------------------------------------
# Init GUI with options to the default test
# -----------------------------------------------------------------
def refresh_GUI(window, test, fig, ax, ax2):
    if test == "ADC":
        window.Element('-KLDRIVE-').Update(disabled=False)
        window.Element('-KLCOM-').Update(disabled=False)
        update_figADC(fig, ax, ax2, 0, 0, "b.", "")

    elif test == "Power Supply":
        window.Element('-KLDRIVE-').Update(disabled=True)
        window.Element('-KLCOM-').Update(disabled=True)
        update_figPS(fig, ax, ax2, 0, 0, 0, "b.", "r.")

    window.refresh()


# -----------------------------------------------------------------
# Parse data from PowerSupply test
# -----------------------------------------------------------------
def parse_power_supply_received_data(data):
    values = data.lstrip("\x00").rstrip("\n\r").split(';')
    if len(values) == 1:
        return [float(-1), float(-1), float(-1)]
    else:
        return [float(values[0]), float(values[1]), float(values[2])]


# ------------
# Main program
# ------------
def main():
    # define the form layout
    layout = create_layout()

    # create the form and show it without the plot
    window = sg.Window('KL05 Tester', layout, finalize=True)

    # Default settings for matplotlib graphics
    fig, ax = plt.subplots()
    ax2 = ax.twinx()

    # Link matplotlib to PySimpleGUI Graph
    canvas = FigureCanvasTkAgg(fig, window['-CANVAS-'].Widget)
    plot_widget = canvas.get_tk_widget()
    plot_widget.grid(row=0, column=0)

    # draw the initial plot in the window
    refresh_GUI(window, 'ADC', fig, ax, ax2)

    window.Element('-OUTPUTTEXT-').Update("")

    # program loop
    while True:
        event, values = window.read(timeout=10)

        if event in ('Exit', None):
            exit(0)

        # check ports on refresh button pressed
        elif event in '-REFRESHBUTTON-':
            serialList = serial_ports()
            driveList = drive_list()
            window.Element('-KLCOM-').Update(values=serialList,
                                             value=serialList[0])
            window.Element('-STMCOM-').Update(values=serialList,
                                              value=serialList[0])
            window.Element('-KLDRIVE-').Update(values=driveList,
                                               value=driveList[0])
            window.Element('-STMDRIVE-').Update(values=driveList,
                                                value=driveList[0])

        elif event in '-TESTTYPE-':
            refresh_GUI(window, values['-TESTTYPE-'], fig, ax, ax2)

        # check if start button was pressed
        elif event in '-STARTBUTTON-':

            # if selected test is ADC
            if values['-TESTTYPE-'] == "ADC":

                window.Element('-OUTPUTTEXT-').Update("Starting ADC test")
                window.refresh()

                # flash devices and then open serial ports
                try:
                    flash_micro("STM.ADC.hex", values['-STMDRIVE-'])
                except Exception as e:
                    process_exception(window, values,
                                      "Error during flashing STM with serial port: " + values['-STMDRIVE-'] + "\n" + str(e))
                    continue
                time.sleep(5)
                try:
                    serialSTM = serial_open(values['-STMCOM-'], 115200)
                except Exception as e:
                    process_exception(window, values,
                                      "Error during opening serial to STM with serial port: " + values['-STMCOM-'] + "\n" + str(e))
                    continue

                try:
                    flash_micro("KL.ADC.hex", values['-KLDRIVE-'])
                except Exception as e:
                    process_exception(window, values,
                                      "Error during flashing KL with serial port: " + values['-KLDRIVE-'] + "\n" + str(e))
                    continue
                time.sleep(5)
                try:
                    serialKL = serial_open(values['-KLCOM-'], 28800)
                except Exception as e:
                    process_exception(window, values,
                                      "Error during opening serial to KL with serial port: " + values['-KLCOM-'] + "\n" + str(e))
                    continue

                if serialSTM == [] and serialKL == [] or serialSTM == serialKL:
                    window.Element(
                        '-OUTPUTTEXT-').Update("Disconnected, check ports settings")
                    window.refresh()

                else:
                    color = ["b.", "r.", "y.", "g.", "c.", "m."]

                    # for each ADC channel
                    for i in range(0, 6):
                        DataX = np.array([])
                        DataY = np.array([])

                        window.Element(
                            '-OUTPUTTEXT-').Update("Testing ADC {}".format(i))
                        window.refresh()
                        # set on KL next ADC channel
                        serial_send(serialKL, str(i + 1) + '\n')
                        serial_receive(serialKL)

                        # send popup to connect next channel
                        sg.popup_ok("Connect next channel {}".format(i))

                        # for each tenth value from 0 to 4095
                        for x in range(0, 4096, 10):
                            # set new DAC value on Nucleo and save it as X value
                            serial_send(serialSTM, "{:04d}".format(x) + '\n')
                            data = str(serial_receive(serialSTM))
                            DataX = np.append(DataX, int(data))

                            # read value from KL and save it as Y value
                            serial_send(serialKL, '0\n')
                            data = str(serial_receive(serialKL))
                            DataY = np.append(DataY, int(data))

                        # update canvas and refresh window
                        update_figADC(fig, ax, ax2, DataX, DataY,
                                      color[i], "ADC {}".format(i))
                        window.refresh()

                    window.Element('-OUTPUTTEXT-').Update("End of the test")
                    # free serial ports
                    serialSTM.close()
                    serialKL.close()

            # if selected test is Power Supply
            elif values['-TESTTYPE-'] == "Power Supply":

                window.Element(
                    '-OUTPUTTEXT-').Update("Starting Power Supply test")
                window.refresh()

                # flash devices and then open serial ports
                try:
                    flash_micro('STM.SupplyTest.hex', values['-STMDRIVE-'])
                except Exception as e:
                    process_exception(window, values,
                                      "Error during flashing STM with serial port: " + values['-STMDRIVE-'] + "\n" + str(e) + '. Remember to check if disk is properly choosen!')
                    continue
                time.sleep(5)

                try:
                    serialSTM = serial_open(values['-STMCOM-'], 115200)
                except Exception as e:
                    process_exception(window, values,
                                      "Error during opening serial to STM with serial port: " + values['-STMCOM-'] + "\n" + str(e))
                    continue

                if serialSTM == []:
                    window.Element(
                        '-OUTPUTTEXT-').Update("Disconnected, check ports settings")
                    window.refresh()
                else:
                    conf = [["3V3", "b.", "r."]]  # , ["+5V", "b.", "r."]]

                    # for each VDD pin channel
                    for powerSupply, v_color, c_color in conf:
                        d_time = np.array([])
                        d_voltage = np.array([])
                        d_current = np.array([])

                        # send popup to ensure that power supply pins are connected to STM
                        sg.popup_ok(
                            "Is " + powerSupply + " pin connected to A0 pin and ready for the test?")

                        # Some logs for user
                        window.Element(
                            '-OUTPUTTEXT-').Update("Testing Power Supply: " + powerSupply)
                        window.refresh()

                        # Send test case to STM
                        serial_send(serialSTM, powerSupply)

                        # Receive data from measurement
                        # for each tenth value from 0 to 4095
                        while True:
                            try:
                                data = str(serial_receive(serialSTM))
                            except Exception as e:
                                process_exception(window, values,
                                                  "Error during UART transmission: " + values['-STMCOM-'] + "\n" + str(e))
                                break

                            try:
                                [v, c, t] = parse_power_supply_received_data(
                                    data)
                                if t == -1:
                                    break
                            except Exception as e:
                                process_exception(window, values,
                                                  "Error during UART transmission: " + values['-STMCOM-'] + "\n" + str(e))
                                break

                            d_time = np.append(d_time, t)
                            d_voltage = np.append(d_voltage, v)
                            d_current = np.append(d_current, c)

                            # update canvas and refresh window
                            update_figPS(fig, ax, ax2, d_time, d_voltage, d_current,
                                         v_color, c_color)
                            window.refresh()

                window.Element('-OUTPUTTEXT-').Update("End of the test")

                # free serial ports
                serialSTM.close()
    window.close()


# entry point
if __name__ == '__main__':
    main()
