import threading
import queue
import time
import tkinter as tk
from tkinter import ttk
from dataclasses import dataclass
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import numpy as np
import csv
import os
import datetime
from tkinter import *
from pylablib.devices import Thorlabs #Thorlabs library

import sys
import clr
sys.path.append(r"C:\Windows\Microsoft.NET\assembly\GAC_64\Newport.XPS.CommandInterface\v4.0_2.3.1.0__9a267756cf640dcf")
clr.AddReference(r"C:\Windows\Microsoft.NET\assembly\GAC_64\Newport.XPS.CommandInterface\v4.0_2.3.1.0__9a267756cf640dcf\Newport.XPS.CommandInterface")
from CommandInterfaceXPS import XPS



# Create abort_event
abort_event = threading.Event()

#Class for holding the limit information, and performing the software limit checking
class Limits:
    def __init__(self, LowerLimit: float, UpperLimit: float):
        self.LL = LowerLimit
        self.UL = UpperLimit

    def CheckLimit(self, Position: float):
        if Position > self.LL and Position < self.UL:
            return True
        else:
            return False

# Struct for Queue messages
@dataclass
class LabelUpdate:
    label: int
    message: any

# Define what to do when the abort Button is pressed
def abort() -> None:
    abort_event.set()

#TODO set the correct limits

XAxisLimit = Limits(LowerLimit=-100, UpperLimit=100)
YAxisLimit = Limits(LowerLimit=-100, UpperLimit=100)
ZAxisLimit = Limits(LowerLimit=-100, UpperLimit=100)
RotAxisLimit = Limits(LowerLimit=-100, UpperLimit=100)

LimitList = [XAxisLimit, YAxisLimit, ZAxisLimit, RotAxisLimit]

#Scale for the Thorlabs actuators, translating microsteps to mm
KCubestepsPerMM = 34554.88  # Magic Number from datasheet
KCubeScale = (KCubestepsPerMM, KCubestepsPerMM * 53.68, KCubestepsPerMM / 90.9 / 2)
ZAxisStepsPerMM = 819200  # Magic Number from datasheet
ZAxisScale = (ZAxisStepsPerMM, ZAxisStepsPerMM * 53.68, ZAxisStepsPerMM / 90.9 / 2)


#Stage and actuator defining
XPSStage = XPS()
KCube = Thorlabs.KinesisMotor(str(27262610), scale=KCubeScale)
ZAxis = Thorlabs.KinesisMotor(str(70292334), is_rack_system=True, scale=ZAxisScale, default_channel=1)

#Keeping track of where the stages are
PositionList = [0.0, 0.0, 0.0, 0.0]

#Save the optimum position
OptimumList = [0.0, 0.0, 0.0, 0.0]


# TODO Remove after debugging
ReferencePower = 1.1
NumberOfPoints = 35
CouplingEfficiencyRatio = 0.5

def save_to_csv(filename, *lists):

    # Ensure all lists have equal length
    length = len(lists[0])

    # Transpose the lists to group them row-wise
    rows = zip(*lists)

    # Write to CSV file
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(rows)




# Function to be run in a separate thread (the worker thread)
def worker_thread(queue, gui_root):
    # Create object for sending messages to GUI thread
    messageObject = LabelUpdate(label=1, message='Test')
    for i in range(1, 11):

        # Abort if abort_event is set, either by abortButton or limit exceeded
        if abort_event.is_set():
            messageObject.message = 'Aborted!'
            queue.put(messageObject)
            gui_root.event_generate('<<UpdateLabel>>')
            return

        # Simulate some processing
        time.sleep(1)

        # Send progress to the GUI thread via the queue
        messageObject.message = f'Progress: {i * 10}%'
        queue.put(messageObject)
        # Generate a custom event to notify the main thread
        gui_root.event_generate('<<UpdateLabel>>')



    xAxis = np.arange(0, 20, 0.5).tolist()
    yAxis = np.random.normal(0, 1, 40)
    os.makedirs("../" + dt_string + "/")
    save_to_csv("../" + dt_string + "/output.csv", xAxis, yAxis)
    # Notify the main thread when the task is complete
    messageObject.message = 'Process Done'
    queue.put(messageObject)
    gui_root.event_generate('<<UpdateLabel>>')

# Event handler to update the label
def on_update_label(event) -> None:

    try:
        # Retrieve the next message from the queue
        message = q.get_nowait()

        match message.label:
            case 1:
                testLabelVar.set(message.message)
            case 2:
                voltageLabelVar.set(message.message)
            case 3:
                referencePowerLabelVar.set(message.message)
            case 4:
                xPosLabelVar.set(message.message)
            case 5:
                yPosLabelVar.set(message.message)
            case 6:
                zPosLabelVar.set(message.message)
            case 7:
                rotPosLabelVar.set(message.message)
            case 8:
                unitLabelPosVar.set(message.message)
            case 9:
                unitLabelLLVar.set(message.message)
            case 10:
                unitLabelULVar.set(message.message)
            case _:
                testLabelVar.set("WeirdIndex")

    except queue.Empty:
        pass


# Function to create and embed the matplotlib plot
def create_plot(frame, t, y):
    # Create a matplotlib figure and plot
    fig = Figure(figsize=(5, 4), dpi=100)
    ax = fig.add_subplot(111)

    # Sample plot (a simple sine wave)


    ax.plot(t, y)
    ax.set_title("Sample Plot")

    # Create a canvas to embed the matplotlib figure into Tkinter
    canvas = FigureCanvasTkAgg(fig, master=frame)  # A tk.DrawingArea
    canvas.draw()

    # Pack the canvas in the frame (or use .grid(), .place())
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

def add_to_plot():
    try:
        # Append the new values to t and y
        t.append(int(max(t) + 1))  # Increment the x-axis value
        y.append(float(addToPlotEntry.get()))  # Get the input value for the y-axis

        # Clear the previous plot and update the frame
        for widget in plot_frame.winfo_children():
            widget.destroy()  # Remove previous plot

        # Create the updated plot
        create_plot(plot_frame, t, y)
    except ValueError:
        print("Please enter a valid integer.")
        t.pop()


def manualVoltageMesurement():

    # TODO
    # Add voltage measurement on button click
    return 3


def startPeakFinding():
    # TODO
    # Create and implement peak finding algorithm, if possible using a 2D scanning, from the xps stage
    return 4

def returnToOptimum():
    # TODO
    # Create a variable for the optimum position, and return to it.
    # Also make an error message, when not yet reached optimum
    return 3

def goToPosition():

    index = getSelectorIndex()
    position = float(positionEntry.get())
    moveActuators(index, position)


    return 3

def manualMeasurementRun():
    referencePower = float(referencePowerEntry.get())
    lowerLimit = float(lowerLimitEntry.get())
    upperLimit = float(upperLimitEntry.get())
    axisIndex = getSelectorIndex()
    measurementRun(lowerLimit, upperLimit, NumberOfPoints, axisIndex, referencePower)

    # TODO set Reference Power
    return 3

def updatePosition():
    print("tehe")
    #TODO update positionlabels through positionlist

def moveActuators(AxisIndex: int, Position: float):
    XPos = PositionList[0]
    YPos = PositionList[1]

    #TODO Check if all defined constants are read only, or need to be globally overwritten, such as the PositionList Update
    PositionList[AxisIndex] = Position
    updatePosition()

    if not LimitList[AxisIndex].CheckLimit(Position=Position):
        abort()
        return False

    match AxisIndex:
        case 0:
            result = XPSStage.GroupMoveAbsolute("XYGroup", [Position, YPos], 2, str())
            if result != 0:
                return False

            result = XPSStage.WaitMotionEnd("XYGroup", 10000.0, [Position * 1000, YPos * 1000], str())
            if result == 0:
                return True
            else:
                return False

        case 1:
            result = XPSStage.GroupMoveAbsolute("XYGroup", [XPos, Position], 2, str())
            if result != 0:
                return False

            result = XPSStage.WaitMotionEnd("XYGroup", 10000.0, [XPos * 1000, Position * 1000], str())
            if result == 0:
                return True
            else:
                return False

        case 2:
            ZAxis.move_to(position=Position)
            ZAxis.wait_move(timeout=10)

            return True

        case 3:
            KCube.move_to(position=Position)
            KCube.wait_move(timeout=10)

            return True

def connectToStages():

    #Connect to XPS Stage
    if not connectToXPSStage(XPSStage):
        abort()

    #Connect to Thorlabs
    ZAxis.open()
    KCube.open()
    ZAxis.set_supported_channels(3)
    ZAxis._enable_channel(enabled=True, channel=1)

    if ZAxis.is_opened() and KCube.is_opened():
        return True
    else:
        return False

def homeActuators():

    #Home XPS Stage
    XPSStage.GroupHomeSearch("XYGroup", str())

    #Home Z and Rot Axes
    KCube.setup_homing(velocity=0.75, offset_distance=7.55) #TODO Find correct offsets
    ZAxis.setup_homing(velocity=0.75, offset_distance=2)

    ZAxis.home(force=True, sync=False)
    KCube.home(force=True, sync=False)

    ZAxis.wait_for_home(timeout=40)
    KCube.wait_for_home(timeout=40)

    #TODO establish correct limit switches, maybe contact thorlabs, or trial and error
    KCube.setup_limit_switch(hw_kind_cw='ignore', hw_kind_ccw='ignore')
    ZAxis.setup_limit_switch(hw_kind_cw='ignore', hw_kind_ccw='ignore')

    KCube.setup_velocity(min_velocity=0.0, acceleration=1.0, max_velocity=2.0)
    ZAxis.setup_velocity(min_velocity=0.0, acceleration=1.0, max_velocity=2.0)

    if KCube.is_opened() and KCube.is_opened():
        return True
    else:
        return False


def convertVoltageToCoupEff(voltages: [float], referenceP: float):

    length = len(voltages)
    coupEff = [0.0] * length

    for id, volt in enumerate(voltages):
        coupEff[id] = (convertVoltageToPower(volt) / referenceP) * 100

    return coupEff


def convertVoltageToPower(voltage: float):

    powermW = voltage * 0.0341 + 0.3435

    return powermW


def detectPeak(coupEff: [float]):

    length = len(coupEff)
    maximum = max(coupEff)
    lowerBoundary = 0
    upperBoundary = 0

    for id, ce in enumerate(coupEff):
        if (ce / maximum) > CouplingEfficiencyRatio:
            lowerBoundary = id
            break

    for id, ce in enumerate(reversed(coupEff)):
        if (ce / maximum) > CouplingEfficiencyRatio:
            upperBoundary = length - 1 - id
            break

    result = [lowerBoundary, upperBoundary]
    return result



def measurementRun(lowerLimit, upperLimit, numberOfPoints, axisIndex, referencePower):

    positions = linspace(lowerLimit, upperLimit, numberOfPoints)
    voltages = [0.0] * numberOfPoints
    for id, pos in enumerate(positions):
        if not moveActuators(axisIndex, pos):
            abort()
            break
        voltages[id] = XPS_VoltageGet(XPSStage)

    coupEff = convertVoltageToCoupEff(voltages, referencePower)
    return coupEff
    # TODO Update Plot, labels, and save to file


# Move the XY Stage to a position
def XPS_GroupMoveAbsolute(myXPS, TargetPosition, nbItems=2):

    GroupName = "XYGroup"
    result = myXPS.GroupMoveAbsolute(GroupName, TargetPosition, nbItems, str())
    if result == 0:
        return True
    else:
        return False

# Close connection to XY Stage
def XPS_Close(myXPS):
    myXPS.KillAll(str())
    myXPS.CloseInstrument()
    print('XPS closed')


#Get Voltage applied to pin XPS RDL Controller
def XPS_VoltageGet(myXPS):
    voltage = [1]
    result = myXPS.GPIOAnalogGet(["GPIO2.ADC1"], voltage, str())
    print("Voltage: ")
    print((result[1])[0])
    # TODO
    # Format the output correctly to give proper return value



def linspace(lower_limit, upper_limit, num_points):
    if num_points <= 0:
        return []
    points = [lower_limit + i * (upper_limit - lower_limit) / (num_points - 1) for i in range(num_points)]
    return points



def create_gui(root):
    # Create a frame to hold the plot
    global plot_frame
    plot_frame = tk.Frame(root)
    plot_frame.grid(row=0, column=0, rowspan=12)

    # Call the function to create the plot in the frame
    global t, y
    t = [0]
    y = [0]
    create_plot(plot_frame, t, y)

    # Create Label and LabelVars
    global testLabelVar, voltageLabelVar, referencePowerLabelVar, xPosLabelVar, yPosLabelVar, zPosLabelVar, rotPosLabelVar, unitLabelPosVar, unitLabelLLVar, unitLabelULVar
    global testLabel, voltageLabel, referencePowerLabel, xPosLabel, yPosLabel, zPosLabel, rotPosLabel, unitLabelPos, unitLabelLL, unitLabelUL

    # Assign standard values
    testLabelVar = tk.StringVar(root, "TestLabel")
    voltageLabelVar = tk.StringVar(root, "Measured: 0 mW")
    referencePowerLabelVar = tk.StringVar(root, "Reference:")
    xPosLabelVar = tk.StringVar(root, "XPos = 0 mm")
    yPosLabelVar = tk.StringVar(root, "YPos = 0 mm")
    zPosLabelVar = tk.StringVar(root, "ZPos = 0 mm")
    rotPosLabelVar = tk.StringVar(root, "Rot = 0 °")
    unitLabelPosVar = tk.StringVar(root, "mm")
    unitLabelLLVar = tk.StringVar(root, "mm")
    unitLabelULVar = tk.StringVar(root, "mm")

    #Create Label elements and place them on the grid
    testLabel = tk.Label(root, textvariable=testLabelVar, font=("Arial", 14))
    testLabel.grid(row=16, column=3, padx=5)

    voltageLabel = tk.Label(root, textvariable=voltageLabelVar, font=("Arial", 14))
    voltageLabel.grid(row=0, column=2, padx=5)

    referencePowerLabel = tk.Label(root, textvariable=referencePowerLabelVar, font=("Arial", 14))
    referencePowerLabel.grid(row=1, column=2, padx=5)

    xPosLabel = tk.Label(root, textvariable=xPosLabelVar, font=("Arial", 14))
    xPosLabel.grid(row=5, column=1, padx=5)

    yPosLabel = tk.Label(root, textvariable=yPosLabelVar, font=("Arial", 14))
    yPosLabel.grid(row=5, column=2, padx=5)

    zPosLabel = tk.Label(root, textvariable=zPosLabelVar, font=("Arial", 14))
    zPosLabel.grid(row=6, column=1, padx=5)

    rotPosLabel = tk.Label(root, textvariable=rotPosLabelVar, font=("Arial", 14))
    rotPosLabel.grid(row=6, column=2, padx=5)

    unitLabelPos = tk.Label(root, textvariable=unitLabelPosVar, font=("Arial", 14))
    unitLabelPos.grid(row=15, column=3, padx=5)

    unitLabelLL = tk.Label(root, textvariable=unitLabelLLVar, font=("Arial", 14))
    unitLabelLL.grid(row=10, column=3, padx=5)

    unitLabelUL = tk.Label(root, textvariable=unitLabelULVar, font=("Arial", 14))
    unitLabelUL.grid(row=11, column=3, padx=5)

    upperLimitTextLabel = tk.Label(root, text="Upper Limit:", font=("Arial", 14))
    upperLimitTextLabel.grid(row=11, column=1, padx=5)

    lowerLimitTextLabel = tk.Label(root, text="Lower Limit:", font=("Arial", 14))
    lowerLimitTextLabel.grid(row=10, column=1, padx=5)

    numberOfPointsTextLabel = tk.Label(root, text="Number of points:", font=("Arial", 14))
    numberOfPointsTextLabel.grid(row=12, column=1, padx=5)

    global abortButton, manualVoltageButton, homeActuatorsButton, peakFindingButton, returnToOptimumButton, goToPosButton, startMeasurementRunButton, inputButton, startWorkerThreadButton
    abortButton = tk.Button(root, text="ABORT!", command=abort)
    abortButton.grid(row=0, column=3)

    manualVoltageButton = tk.Button(root, text="Manual Voltage Measurement", command=manualVoltageMesurement)
    manualVoltageButton.grid(row=0, column=1)

    connectToStagesButton = tk.Button(root, text="Connect to Stages", command=connectToStages)
    connectToStagesButton.grid(row=2, column=1)

    homeActuatorsButton = tk.Button(root, text="Home Actuators", command=homeActuators)
    homeActuatorsButton.grid(row=5, column=3)

    peakFindingButton = tk.Button(root, text="Start peak finding", command=startPeakFinding)
    peakFindingButton.grid(row=2, column=3)

    returnToOptimumButton = tk.Button(root, text="Return to optimum", command=returnToOptimum)
    returnToOptimumButton.grid(row=6, column=3)

    goToPosButton = tk.Button(root, text="Go to position", command=goToPosition)
    goToPosButton.grid(row=15, column=1)

    startMeasurementRunButton = tk.Button(root, text="Start measurement run", command=manualMeasurementRun)
    startMeasurementRunButton.grid(row=9, column=1)

    inputButton = tk.Button(root, text="INPUT!", command=lambda: add_to_plot())
    inputButton.grid(row=15)

    startWorkerThreadButton = tk.Button(root, text="Start Worker Thread", command=workThread)
    startWorkerThreadButton.grid(row=16)

    testButton = tk.Button(root, text="Test Button", command=testFunction)
    testButton.grid(row=17)

    global addToPlotEntry, referencePowerEntry, lowerLimitEntry, upperLimitEntry, positionEntry, numberOfPointsEntry
    addToPlotEntry = tk.Entry(root, width=20)
    addToPlotEntry.grid(row=14)

    referencePowerEntry = tk.Entry(root, width=20)
    referencePowerEntry.grid(row=1, column=3)

    lowerLimitEntry = tk.Entry(root, width=20)
    lowerLimitEntry.grid(row=10, column=2)

    upperLimitEntry = tk.Entry(root, width=20)
    upperLimitEntry.grid(row=11, column=2)

    numberOfPointsEntry = tk.Entry(root, width=20)
    numberOfPointsEntry.grid(row=12, column=2)

    positionEntry = tk.Entry(root, width=20)
    positionEntry.grid(row=15, column=2)

    separatorOne = ttk.Separator(root, orient='horizontal')
    separatorOne.grid(row=4, column=1, columnspan=3, sticky="ew")

    separatorTwo = ttk.Separator(root, orient='horizontal')
    separatorTwo.grid(row=7, column=1, columnspan=3, sticky="ew")

    separatorThree = ttk.Separator(root, orient='horizontal')
    separatorThree.grid(row=13, column=1, columnspan=3, sticky="ew")
    
    
    global AxisSelectorMenue, clicked
    global options
    options = ["X axis", "Y axis", "Z axis", "Rot axis"]
    clicked = StringVar()
    clicked.set("X axis")
    AxisSelectorMenue = OptionMenu(root, clicked, *options)
    AxisSelectorMenue.grid(row=9, column=2)

    # TODO
    # Find a change option event, to change unit to degree when Rotation axis is selected, or just rename unit to mm/deg

    root.bind('<<UpdateLabel>>', on_update_label)


def getSelectorIndex():
    text = clicked.get()
    index = options.index(text)
    return index


def testFunction():
    messageObject = LabelUpdate(label=2, message="Hello World")
    messageObject.message = 'Process Done'
    q.put(messageObject)
    root.event_generate('<<UpdateLabel>>')

    #if not connectToStages():
    #    abort()

    #if not homeActuators():
    #    abort()

    #if not moveActuators(1, 1.0):
    #    abort()



def workThread():
    # Start the worker thread
    abort_event.clear()
    thread = threading.Thread(target=worker_thread, args=(q, root))
    thread.daemon = True  # Daemonize thread to exit with the program
    thread.start()


def connectToXPSStage(myXPS):

    # Connecting to XPS RDL controller for X and Y axis
    address = "192.168.0.254"
    port = 5001
    timeout = 1000

    result = myXPS.OpenInstrument(address, port, timeout)
    if result != 0:
        return False

    result = myXPS.GroupInitialize("XYGroup", str())
    if result != 0:
        return False
    return True



"""
main
"""

# TODO
# Create a close button, that also properly disconnects from the stages. The thorlabs one was funny if I remember correctly


# TODO
# Maybe include a relative or absolute selector, for the measurement run option to be around the optimum


# TODO
# make a error checking function, just a simple number check and throw error and suicide

# TODO
# disable other buttons when something is happening, maybe make a seperate function for it. using button.config(state="disabled")

now = datetime.datetime.now()
dt_string = now.strftime("%Y_%m_%d_%H_%M")

global root
root = tk.Tk()
root.title("Fiber Coupling Project")
root.geometry("10000x60000")  # set starting size of window
root.maxsize(1000, 600)  # width x height

create_gui(root)

# Create a queue to communicate between threads
global q
q = queue.Queue()
# Run the Tkinter main loop
root.mainloop()


